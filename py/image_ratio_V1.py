import torch
import numpy as np
from PIL import Image

class ImageRatioCrop:
    """
    * 图像比例裁切节点
    * 根据指定比例和最长边长度进行中心裁切
    * 支持自定义比例和输出尺寸
    """

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        """
        * 定义节点的输入参数类型
        * @return {dict} 包含required参数的字典
        """
        return {
            "required": {
                "image": ("IMAGE",),  # 输入图像
                "ratio_a": ("INT", {"default": 1, "min": 1, "max": 100, "step": 1}),  # 比例A
                "ratio_b": ("INT", {"default": 1, "min": 1, "max": 100, "step": 1}),  # 比例B
                "max_size": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 64}),  # 最长边长度
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("cropped_image",)
    FUNCTION = "crop_by_ratio"
    CATEGORY = "PDuse/Image"

    def crop_by_ratio(self, image, ratio_a, ratio_b, max_size):
        """
        * 根据比例和最长边长度裁切图像
        * @param {torch.Tensor} image - 输入图像张量 (B, H, W, C)
        * @param {int} ratio_a - 比例A
        * @param {int} ratio_b - 比例B
        * @param {int} max_size - 输出图像的最长边长度
        * @return {tuple} 返回裁切后的图像张量
        """
        # 获取批次中的第一张图片
        img = image[0]
        
        # 转换为PIL图像
        img = self._tensor_to_pil(img)
        
        # 计算实际比例（除以最小公因数）
        gcd = self._gcd(ratio_a, ratio_b)
        actual_ratio_a = ratio_a // gcd
        actual_ratio_b = ratio_b // gcd
        
        # 计算目标尺寸
        if actual_ratio_a >= actual_ratio_b:
            target_width = max_size
            target_height = int(max_size * actual_ratio_b / actual_ratio_a)
        else:
            target_height = max_size
            target_width = int(max_size * actual_ratio_a / actual_ratio_b)
            
        # 计算裁切区域
        current_ratio = img.width / img.height
        target_ratio = actual_ratio_a / actual_ratio_b
        
        if current_ratio > target_ratio:
            # 当前图像更宽，需要裁切宽度
            new_width = int(img.height * target_ratio)
            left = (img.width - new_width) // 2
            crop_box = (left, 0, left + new_width, img.height)
        else:
            # 当前图像更高，需要裁切高度
            new_height = int(img.width / target_ratio)
            top = (img.height - new_height) // 2
            crop_box = (0, top, img.width, top + new_height)
            
        # 执行裁切
        cropped_img = img.crop(crop_box)
        
        # 调整到目标尺寸
        resized_img = cropped_img.resize((target_width, target_height), Image.LANCZOS)
        
        # 转换回张量
        return (self._pil_to_tensor(resized_img),)

    def _gcd(self, a, b):
        """
        * 计算两个数的最大公约数
        * @param {int} a - 第一个数
        * @param {int} b - 第二个数
        * @return {int} 最大公约数
        """
        while b:
            a, b = b, a % b
        return a

    def _tensor_to_pil(self, tensor):
        """
        * 将张量转换为PIL图像
        * @param {torch.Tensor} tensor - 输入张量
        * @return {PIL.Image} PIL图像对象
        """
        # 确保张量在CPU上
        tensor = tensor.cpu()
        
        # 处理通道顺序
        if tensor.shape[0] <= 4:  # CHW格式
            tensor = tensor.permute(1, 2, 0)
            
        # 归一化处理
        if tensor.dtype == torch.float32 and tensor.max() <= 1.0:
            tensor = tensor * 255
            
        # 转换为uint8
        tensor = tensor.to(torch.uint8)
        
        return Image.fromarray(tensor.numpy())

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
    "ImageRatioCrop": ImageRatioCrop
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageRatioCrop": "PD:Image Ratio Crop"
}