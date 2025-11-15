"""
PD Image Resize Crop 节点
支持多种图像调整方法：拉伸、保持比例、填充裁剪、边缘填充
"""

import torch
import torch.nn.functional as F

# 最大分辨率设置
MAX_RESOLUTION = 8192

class PDImageResize:
    """
    图像调整和裁剪节点
    
    参数说明:
    - image: 输入图像 (B, H, W, C)
    - width/height: 目标宽高
    - interpolation: 插值方法（图像缩放算法）
      - nearest: 最近邻（速度快，质量低）
      - bilinear: 双线性（平衡）
      - bicubic: 双三次（质量好）
      - area: 区域插值（缩小时效果好）
      - lanczos: Lanczos算法（质量最好，速度慢）
    - method: 调整方式
      - stretch: 直接拉伸到目标尺寸
      - longest size: 按最长边缩放（横图按宽度，竖图按高度）
      - fill / crop: 放大填充后裁剪多余部分
      - pad: 保持比例后在边缘填充黑色
    - multiple_of: 倍数约束，确保输出尺寸是该数字的倍数
      （例如设为8，则输出宽高都是8的倍数，常用于AI模型输入）
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "width": ("INT", {"default": 512, "min": 0, "max": MAX_RESOLUTION, "step": 1}),
                "height": ("INT", {"default": 512, "min": 0, "max": MAX_RESOLUTION, "step": 1}),
                "interpolation": (["nearest", "bilinear", "bicubic", "area", "lanczos"],),
                "method": (["stretch", "longest size", "fill / crop", "pad"],),
                "multiple_of": ("INT", {"default": 0, "min": 0, "max": 512, "step": 1}),
            }
        }

    RETURN_TYPES = ("IMAGE", "INT", "INT",)
    RETURN_NAMES = ("IMAGE", "width", "height",)
    FUNCTION = "execute"
    CATEGORY = "PDuse/Image"

    def execute(self, image, width, height, interpolation="bilinear", method="stretch", multiple_of=0):
        """
        执行图像调整
        
        @param image: 输入图像张量 (B, H, W, C)
        @param width: 目标宽度
        @param height: 目标高度
        @param interpolation: 插值方法
        @param method: 调整方式
        @param multiple_of: 倍数约束
        @return: (调整后的图像, 最终宽度, 最终高度)
        """
        # 获取原始尺寸
        batch_size, orig_height, orig_width, channels = image.shape
        
        # 初始化裁剪和填充参数
        crop_x = crop_y = crop_x2 = crop_y2 = 0
        pad_left = pad_right = pad_top = pad_bottom = 0

        # 如果设置了倍数约束，先调整目标尺寸
        if multiple_of > 1:
            width = width - (width % multiple_of)
            height = height - (height % multiple_of)

        # 根据不同方法处理尺寸
        if method == 'longest size' or method == 'pad':
            # 按最长边缩放模式
            # 📐 横图（宽≥高）：将宽度缩放到设定的 width 值，高度自动等比例缩放
            # 📏 竖图（高>宽）：将高度缩放到设定的 height 值，宽度自动等比例缩放
            
            if orig_width >= orig_height:
                # 横图：按宽度缩放
                if width == 0:
                    width = orig_width
                ratio = width / orig_width
                new_width = width
                new_height = round(orig_height * ratio)
            else:
                # 竖图：按高度缩放
                if height == 0:
                    height = orig_height
                ratio = height / orig_height
                new_height = height
                new_width = round(orig_width * ratio)

            # 如果是pad模式，计算填充量
            if method == 'pad':
                # pad模式需要目标尺寸
                target_width = width if orig_width >= orig_height else new_width
                target_height = height if orig_width < orig_height else new_height
                pad_left = (target_width - new_width) // 2
                pad_right = target_width - new_width - pad_left
                pad_top = (target_height - new_height) // 2
                pad_bottom = target_height - new_height - pad_top

            width = new_width
            height = new_height
            
        elif method == 'fill / crop':
            # 填充裁剪模式
            width = width if width > 0 else orig_width
            height = height if height > 0 else orig_height

            # 计算缩放比例（选择较大的比例以确保图像能填满目标尺寸）
            ratio = max(width / orig_width, height / orig_height)
            new_width = round(orig_width * ratio)
            new_height = round(orig_height * ratio)
            
            # 计算裁剪位置（居中裁剪）
            crop_x = (new_width - width) // 2
            crop_y = (new_height - height) // 2
            crop_x2 = crop_x + width
            crop_y2 = crop_y + height
            
            # 边界检查
            if crop_x2 > new_width:
                crop_x -= (crop_x2 - new_width)
            if crop_x < 0:
                crop_x = 0
            if crop_y2 > new_height:
                crop_y -= (crop_y2 - new_height)
            if crop_y < 0:
                crop_y = 0
                
            width = new_width
            height = new_height
        else:
            # stretch 模式：直接使用目标尺寸
            width = width if width > 0 else orig_width
            height = height if height > 0 else orig_height

        # 执行图像调整
        # 将图像从 (B, H, W, C) 转换为 (B, C, H, W) 用于 PyTorch 处理
        outputs = image.permute(0, 3, 1, 2)

        # 根据插值方法进行缩放
        if interpolation == "lanczos":
            # Lanczos 需要特殊处理
            try:
                import comfy.utils
                outputs = comfy.utils.lanczos(outputs, width, height)
            except:
                # 如果 lanczos 不可用，回退到 bicubic
                outputs = F.interpolate(outputs, size=(height, width), mode="bicubic")
        else:
            outputs = F.interpolate(outputs, size=(height, width), mode=interpolation)

        # 如果是 pad 模式，添加填充
        if method == 'pad':
            if pad_left > 0 or pad_right > 0 or pad_top > 0 or pad_bottom > 0:
                outputs = F.pad(outputs, (pad_left, pad_right, pad_top, pad_bottom), value=0)

        # 转换回 (B, H, W, C) 格式
        outputs = outputs.permute(0, 2, 3, 1)

        # 如果是 fill/crop 模式，执行裁剪
        if method == 'fill / crop':
            if crop_x > 0 or crop_y > 0 or crop_x2 > 0 or crop_y2 > 0:
                outputs = outputs[:, crop_y:crop_y2, crop_x:crop_x2, :]

        # 如果设置了倍数约束，最后再检查并调整
        if multiple_of > 1:
            current_height, current_width = outputs.shape[1], outputs.shape[2]
            if current_width % multiple_of != 0 or current_height % multiple_of != 0:
                # 居中裁剪到倍数
                adjust_x = (current_width % multiple_of) // 2
                adjust_y = (current_height % multiple_of) // 2
                adjust_x2 = current_width - ((current_width % multiple_of) - adjust_x)
                adjust_y2 = current_height - ((current_height % multiple_of) - adjust_y)
                outputs = outputs[:, adjust_y:adjust_y2, adjust_x:adjust_x2, :]

        # 限制输出值在 [0, 1] 范围内
        outputs = torch.clamp(outputs, 0, 1)

        # 获取最终尺寸
        final_height, final_width = outputs.shape[1], outputs.shape[2]

        return (outputs, final_width, final_height,)


# 节点注册
NODE_CLASS_MAPPINGS = {
    "PDImageResize": PDImageResize,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD Image Resize_V1": "PD Image Resize_V1",
}

