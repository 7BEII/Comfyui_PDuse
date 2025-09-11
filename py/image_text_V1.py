import os
import torch
import numpy as np
from PIL import Image, ImageDraw, ImageFont

class ImageBlendText:
    """
    * 图片合并与文字标注节点
    * 将两张图片左右合并并在下方添加文字说明
    * 支持自定义字体、字号和间距调整
    * 支持最长边限制和等比例缩放
    * 支持黑底白字和白底黑字两种显示模式
    """

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        """
        * 定义节点的输入参数类型
        * @return {dict} 包含required参数的字典
        """
        # 获取当前脚本所在目录的 fonts 子目录
        current_file = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_file)
        plugin_root = os.path.dirname(current_dir)
        fonts_dir = os.path.join(plugin_root, "fonts")

        # 扫描 fonts 目录下的所有 .ttf 和 .otf 文件
        font_files = []
        if os.path.exists(fonts_dir):
            font_files = [
                f for f in os.listdir(fonts_dir)
                if f.lower().endswith(('.ttf', '.otf'))
            ]

        # 如果没有找到字体文件，则默认使用系统字体
        if not font_files:
            font_files = ["system"]  # 默认选项

        return {
            "required": {
                "image1": ("IMAGE",),  # 第一张图像，张量形状为B H W C
                "image2": ("IMAGE",),  # 第二张图像，张量形状为B H W C
                "text1": ("STRING", {"default": "before"}),  # 第一张图的文字标注
                "text2": ("STRING", {"default": "after"}),  # 第二张图的文字标注
                "longer_size": ("INT", {"default": 1024, "min": 128, "max": 2048, "step": 4}),  # 最长边尺寸限制
                "font_size": ("INT", {"default": 90, "min": 10, "max": 100, "step": 1}),  # 字体大小
                "padding_up": ("INT", {"default": 10, "min": 0, "max": 100, "step": 1}),   # 上方间距
                "padding_down": ("INT", {"default": 20, "min": 0, "max": 1000, "step": 1}),  # 下方间距
                "font_file": (font_files, {"default": font_files[0]}),  # 字体文件选择
                "text_style": (["dark", "white"], {"default": "dark"}),  # 文字显示模式
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("merged_image",)
    FUNCTION = "merge_images_with_text"
    CATEGORY = "PD/ImageProcessing"

    def merge_images_with_text(self, image1, image2, text1, text2, longer_size=1024, font_size=90, padding_up=10, padding_down=20, font_file="system", text_style="dark"):
        """
        * 合并两张图片并添加文字标注的主要函数
        * @param {torch.Tensor} image1 - 第一张图像张量 (B, H, W, C)
        * @param {torch.Tensor} image2 - 第二张图像张量 (B, H, W, C)
        * @param {str} text1 - 第一张图的文字说明
        * @param {str} text2 - 第二张图的文字说明
        * @param {int} longer_size - 最长边尺寸限制
        * @param {int} font_size - 字体大小
        * @param {int} padding_up - 文字区域上方间距
        * @param {int} padding_down - 文字区域下方间距
        * @param {str} font_file - 字体文件名
        * @param {str} text_style - 文字显示模式 ("dark": 黑底白字, "white": 白底黑字)
        * @return {tuple} 返回合并后的图像张量
        """
        
        # 转换张量为PIL图像
        img1 = self._safe_tensor_to_pil(image1)
        img2 = self._safe_tensor_to_pil(image2)

        # 根据指定的最长边限制缩放图片
        def resize_image_by_longer_side(img, target_longer_size):
            """
            * 根据最长边限制等比例缩放图像
            * @param {PIL.Image} img - 待缩放的图像
            * @param {int} target_longer_size - 目标最长边尺寸
            * @return {PIL.Image} 缩放后的图像
            """
            # 获取原始尺寸
            width, height = img.size
            current_longer_size = max(width, height)
            
            # 如果当前最长边已经小于等于目标尺寸，不需要缩放
            if current_longer_size <= target_longer_size:
                return img
            
            # 计算缩放比例
            scale_ratio = target_longer_size / current_longer_size
            
            # 计算新的尺寸
            new_width = int(width * scale_ratio)
            new_height = int(height * scale_ratio)
            
            return img.resize((new_width, new_height), Image.LANCZOS)

        # 对两张图片进行最长边限制缩放
        img1 = resize_image_by_longer_side(img1, longer_size)
        img2 = resize_image_by_longer_side(img2, longer_size)

        # 统一两张图片的高度（取较大值）
        target_height = max(img1.height, img2.height)
        
        # 如果图片高度不一致，需要等比例调整较小的图片
        if img1.height != target_height:
            scale_ratio = target_height / img1.height
            new_width = int(img1.width * scale_ratio)
            img1 = img1.resize((new_width, target_height), Image.LANCZOS)
            
        if img2.height != target_height:
            scale_ratio = target_height / img2.height
            new_width = int(img2.width * scale_ratio)
            img2 = img2.resize((new_width, target_height), Image.LANCZOS)

        # 合并图片 - 左右拼接
        merged_img = Image.new("RGB", (img1.width + img2.width, target_height))
        merged_img.paste(img1, (0, 0))
        merged_img.paste(img2, (img1.width, 0))

        # 加载字体
        font = self._load_font(font_size, font_file)

        # 计算文本尺寸（兼容新旧Pillow版本）
        try:
            # Pillow 10.0.0+ 使用新的textlength和textbbox方法
            text1_width = int(font.getlength(text1))
            text2_width = int(font.getlength(text2))
            _, _, _, text_height = font.getbbox("Ag")  # 使用包含下行字母的文本测量高度
        except AttributeError:
            # 旧版Pillow使用getsize方法
            text1_width, text_height = font.getsize(text1)
            text2_width, _ = font.getsize(text2)

        # 根据文字样式设置背景色和文字色
        if text_style == "white":
            bg_color = "white"
            text_color = "black"
        else:  # default to "dark"
            bg_color = "black"
            text_color = "white"

        # 创建最终图像（带文字区域）
        bg_height = text_height + padding_up + padding_down
        final_img = Image.new("RGB", (merged_img.width, merged_img.height + bg_height), bg_color)
        final_img.paste(merged_img, (0, 0))

        # 绘制文字
        draw = ImageDraw.Draw(final_img)
        text_y = merged_img.height + padding_up

        # 第一张图的文字居中
        text1_x = img1.width // 2 - text1_width // 2
        draw.text((text1_x, text_y), text1, font=font, fill=text_color)

        # 第二张图的文字居中
        text2_x = img1.width + img2.width // 2 - text2_width // 2
        draw.text((text2_x, text_y), text2, font=font, fill=text_color)

        # 转换回张量
        return (self._pil_to_tensor(final_img),)

    def _safe_tensor_to_pil(self, tensor):
        """
        * 安全地将张量转换为PIL图像
        * @param {torch.Tensor} tensor - 输入张量
        * @return {PIL.Image} PIL图像对象
        """
        tensor = tensor.cpu().detach()

        # 处理批次维度
        if tensor.dim() == 4:
            tensor = tensor[0]

        # 处理通道顺序
        if tensor.shape[0] <= 4:  # CHW格式
            tensor = tensor.permute(1, 2, 0)

        # 归一化处理
        if tensor.dtype == torch.float32 and tensor.max() <= 1.0:
            tensor = tensor * 255

        # 转换为uint8
        tensor = tensor.to(torch.uint8)

        # 处理单通道图像
        if tensor.dim() == 2 or tensor.shape[-1] == 1:
            tensor = tensor.unsqueeze(-1) if tensor.dim() == 2 else tensor
            tensor = torch.cat([tensor]*3, dim=-1)  # 转为RGB

        return Image.fromarray(tensor.numpy())

    def _load_font(self, font_size, font_file="system"):
        """
        * 加载字体，优先从 fonts 目录加载
        * @param {int} font_size - 字体大小
        * @param {str} font_file - 字体文件名
        * @return {ImageFont} 字体对象
        """
        if font_file == "system":
            try:
                return ImageFont.truetype("arial.ttf", font_size)
            except:
                return ImageFont.load_default()
        else:
            # 重新计算插件根目录
            current_file = os.path.abspath(__file__)
            current_dir = os.path.dirname(current_file)           # 当前 py 文件所在目录（py/）
            plugin_root = os.path.dirname(current_dir)           # 插件根目录（Comfyui_PDuse/）
            font_path = os.path.join(plugin_root, "fonts", font_file)  # 拼接字体路径

            try:
                return ImageFont.truetype(font_path, font_size)
            except Exception as e:
                print(f"⚠️ 字体加载失败: {font_file}, 回退到系统默认字体。错误: {e}")
                return ImageFont.load_default()

    def _pil_to_tensor(self, image):
        """
        * 将PIL图像转换为张量
        * @param {PIL.Image} image - PIL图像对象
        * @return {torch.Tensor} 图像张量 (1, H, W, C)
        """
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)

# ComfyUI节点注册映射
NODE_CLASS_MAPPINGS = {
    "ImageBlendText": ImageBlendText
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageBlendText": "PD:Image_and_Text"
}
