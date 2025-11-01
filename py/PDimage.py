import os
import torch
from torchvision import transforms
from PIL import Image
import numpy as np
import shutil
from pathlib import Path
from typing import List, Tuple, Dict, Optional
import folder_paths
import comfy.utils

def pil2tensor(image):
        return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)

class PD_Image_Crop_Location:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),  # 输入图像张量 [B, H, W, C]
                "x": ("INT", {"default": 0, "min": 0, "max": 10000000, "step": 1}),  # 裁剪区域左上角 X 坐标
                "y": ("INT", {"default": 0, "min": 0, "max": 10000000, "step": 1}),  # 裁剪区域左上角 Y 坐标
                "width": ("INT", {"default": 256, "min": 1, "max": 10000000, "step": 1}),  # 裁剪区域宽度
                "height": ("INT", {"default": 256, "min": 1, "max": 10000000, "step": 1}),  # 裁剪区域高度
            }
        }

    RETURN_TYPES = ("IMAGE",)  # 返回裁切后的图像张量
    RETURN_NAMES = ("Result",)  # 返回值的名称
    FUNCTION = "image_crop_location"  # 指定执行的方法名称
    CATEGORY = "PD_Image/Process"  # 定义节点的类别

    def image_crop_location(self, image, x=0, y=0, width=256, height=256):
        """
        通过给定的 x, y 坐标和裁切的宽度、高度裁剪图像。

        参数：
            image (tensor): 输入图像张量 [B, H, W, C]
            x (int): 裁剪区域左上角 X 坐标
            y (int): 裁剪区域左上角 Y 坐标
            width (int): 裁剪区域宽度
            height (int): 裁剪区域高度

        返回：
            (tensor): 裁剪后的图像张量 [B, H', W', C]
        """
        # 确保输入图像张量的格式正确 [B, H, W, C]
        if image.dim() != 4:
            raise ValueError("输入图像张量必须是 4 维的 [B, H, W, C]")

        # 获取输入图像的尺寸
        batch_size, img_height, img_width, channels = image.shape

        # 检查裁剪区域是否超出图像范围
        if x >= img_width or y >= img_height:
            raise ValueError("裁剪区域超出图像范围")

        # 计算裁剪区域的右下边界坐标
        crop_left = max(x, 0)
        crop_top = max(y, 0)
        crop_right = min(crop_left + width, img_width)
        crop_bottom = min(crop_top + height, img_height)

        # 确保裁剪区域的宽度和高度大于零
        crop_width = crop_right - crop_left
        crop_height = crop_bottom - crop_top
        if crop_width <= 0 or crop_height <= 0:
            raise ValueError("裁剪区域无效，请检查 x, y, width 和 height 的值")

        # 裁剪图像张量
        cropped_image = image[:, crop_top:crop_bottom, crop_left:crop_right, :]

        # 调整裁剪后的图像尺寸为 8 的倍数（可选）
        new_height = (cropped_image.shape[1] // 8) * 8
        new_width = (cropped_image.shape[2] // 8) * 8
        if new_height != cropped_image.shape[1] or new_width != cropped_image.shape[2]:
            cropped_image = torch.nn.functional.interpolate(
                cropped_image.permute(0, 3, 1, 2),  # [B, C, H, W]
                size=(new_height, new_width),
                mode="bilinear",
                align_corners=False,
            ).permute(0, 2, 3, 1)  # [B, H, W, C]

        return (cropped_image,)

class PD_Image_centerCrop:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),  # 输入图像张量 [B, H, W, C]
                "W": ("INT", {"default": 0, "min": 0, "max": 10000000, "step": 1}),  # 左右两边各自裁切的宽度
                "H": ("INT", {"default": 0, "min": 0, "max": 10000000, "step": 1}),  # 上下两边各自裁切的高度
            }
        }

    RETURN_TYPES = ("IMAGE",)  # 返回裁切后的图像张量
    RETURN_NAMES = ("Result",)  # 返回值的名称
    FUNCTION = "center_crop"  # 指定执行的方法名称
    CATEGORY = "PD_Image/Process"  # 定义节点的类别

    def center_crop(self, image, W, H):
        """
        根据动态输入的 W 和 H 值，在左右和上下两边等边裁切，确保裁切后的图像居中。

        参数：
            image (tensor): 输入图像张量 [B, H, W, C]
            W (int): 动态输入的 W 值（左右两边各自裁切的宽度）
            H (int): 动态输入的 H 值（上下两边各自裁切的高度）

        返回：
            (tensor): 裁切后的图像张量 [B, H', W', C]
        """
        # 确保输入图像张量的格式正确 [B, H, W, C]
        if image.dim() != 4:
            raise ValueError("输入图像张量必须是 4 维的 [B, H, W, C]")

        # 获取输入图像的尺寸
        batch_size, img_height, img_width, channels = image.shape

        # 检查 W 和 H 是否有效
        if W < 0 or W >= img_width / 2:
            raise ValueError(f"W 的值无效，必须满足 0 <= W < {img_width / 2}")
        if H < 0 or H >= img_height / 2:
            raise ValueError(f"H 的值无效，必须满足 0 <= H < {img_height / 2}")

        # 计算左右裁切的起始点 x 和裁切宽度 width
        x = W
        width = img_width - 2 * W

        # 计算上下裁切的起始点 y 和裁切高度 height
        y = H
        height = img_height - 2 * H

        # 裁剪图像张量
        cropped_image = image[:, y:y + height, x:x + width, :]

        return (cropped_image,)

class PD_GetImageSize:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES = ("INT", "INT")  # 输出宽高
    RETURN_NAMES = ("width", "height")
    FUNCTION = "get_size"
    CATEGORY = "Masquerade Nodes"
    OUTPUT_NODE = True  # 启用输出节点功能

    def get_size(self, image, unique_id=None, extra_pnginfo=None):
        # 检查 image 是否为 None
        if image is None:
            raise ValueError("No image provided to PD:GetImageSize node")

        # 获取宽高信息
        image_size = image.size()
        image_width = int(image_size[2])
        image_height = int(image_size[1])

        # 将宽高信息转换为字符串
        size_info = f"Width: {image_width}, Height: {image_height}"

        # 更新节点界面显示
        if extra_pnginfo and isinstance(extra_pnginfo, list) and "workflow" in extra_pnginfo[0]:
            workflow = extra_pnginfo[0]["workflow"]
            node = next((x for x in workflow["nodes"] if str(x["id"]) == unique_id), None)
            if node:
                node["widgets_values"] = [size_info]  # 将宽高信息显示在节点界面上

        # 返回宽高信息
        return (image_width, image_height, {"ui": {"text": [size_info]}})
    
import folder_paths
from typing import Tuple
from math import floor

from PIL import Image, ImageOps


from torchvision.transforms import InterpolationMode
import torch.nn.functional as F
from comfy.utils import common_upscale

class PDIMAGE_LongerSize:
    """
    Resizes an image by scaling the longer side to the specified size while maintaining aspect ratio.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "size": ("INT", {
                    "default": 512, 
                    "min": 1,  # Changed from 0 to 1 since size 0 doesn't make sense
                    "max": 99999, 
                    "step": 1
                }),
                "interpolation": (["nearest", "bilinear", "bicubic", "area", "nearest-exact"], {
                    "default": "bicubic"
                }),
            },
        }
    
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "resize_longer_side"
    CATEGORY = "image/transform"

    def resize_longer_side(self, image: torch.Tensor, size: int, interpolation: str = "bicubic"):
        if len(image.shape) != 4:
            raise ValueError("Input image must be 4-dimensional (BxHxWxC)")
            
        _, h, w, _ = image.shape
        
        # Calculate new dimensions while maintaining aspect ratio
        if h >= w:
            new_h = size
            new_w = int(w * (size / h))
        else:
            new_w = size
            new_h = int(h * (size / w))
        
        # Convert to CHW format for upscaling
        samples = image.movedim(-1, 1)
        
        # Map interpolation string to ComfyUI's method
        if interpolation == "nearest-exact":
            interpolation = "nearest_exact"
            
        samples = common_upscale(
            samples, 
            new_w, 
            new_h, 
            interpolation, 
            False
        )
        
        # Convert back to HWC format
        image = samples.movedim(1, -1)
        
        return (image,)


class PD_GetImageRatio:
    """
    获取图像比例节点
    输入单张图片，计算并输出图像的宽高比例，格式为字符串（如"4:3"、"16:9"等）
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("ratio",)
    FUNCTION = "get_image_ratio"
    CATEGORY = "PD_Image/Process"
    
    def get_greatest_common_divisor(self, a, b):
        """
        计算最大公约数（欧几里得算法）
        """
        while b:
            a, b = b, a % b
        return a
    
    def simplify_ratio(self, width, height):
        """
        简化比例到最简形式
        """
        gcd = self.get_greatest_common_divisor(width, height)
        simplified_width = width // gcd
        simplified_height = height // gcd
        return simplified_width, simplified_height
    
    def get_image_ratio(self, image):
        """
        获取图像比例
        """
        # 确保输入张量格式为 (B, H, W, C)
        if len(image.shape) != 4:
            raise ValueError(f"输入图像张量格式错误，期望 (B, H, W, C)，实际 {image.shape}")
        
        # 获取图像尺寸 (取第一张图片的尺寸)
        batch_size, height, width, channels = image.shape
        
        # 简化比例
        simplified_width, simplified_height = self.simplify_ratio(width, height)
        
        # 格式化为字符串
        ratio_string = f"{simplified_width}:{simplified_height}"
        
        print(f"图像尺寸: {width}x{height}, 简化比例: {ratio_string}")
        
        return (ratio_string,)


    
# 在 ComfyUI 中的节点映射配置
NODE_CLASS_MAPPINGS = {
    "PD_Image_Crop_Location": PD_Image_Crop_Location,
    "PD_Image_centerCrop": PD_Image_centerCrop,
    "PD_GetImageSize": PD_GetImageSize, 
    "PD_GetImageRatio": PD_GetImageRatio,

    "PDIMAGE_LongerSize": PDIMAGE_LongerSize
    
}

# 设置节点在 UI 中显示的名称
NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_Image_Crop_Location": "PD:Image Crop Location",
    "PD_Image_centerCrop": "PD:Image centerCrop",
    "PD_GetImageSize": "PD:GetImageSize", 
    "PD_GetImageRatio": "PD:GetImageRatio",

    "PDIMAGE_LongerSize": "PDIMAGE:LongerSize",

}
