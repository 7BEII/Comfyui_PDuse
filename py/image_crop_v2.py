import torch
import numpy as np
from PIL import Image
import cv2

class PDImageCropLocation_V2:
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "x": ("INT", {
                    "default": 50,
                    "min": 0,
                    "max": 4096,
                    "step": 1,
                    "display": "number"
                }),
                "crop_direction": (["left", "right", "top", "bottom"], {
                    "default": "left"
                }),
            },
            "optional": {
                "mask": ("MASK",),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "MASK",)
    RETURN_NAMES = ("cropped_image", "cropped_mask",)
    FUNCTION = "crop_image_location"
    CATEGORY = "PDuse/Image"
    
    def crop_image_location(self, image, x, crop_direction, mask=None):
        # 确保输入图像格式正确 (B, H, W, C)
        if len(image.shape) != 4:
            raise ValueError("Input image must have 4 dimensions (B, H, W, C)")
        
        batch_size, height, width, channels = image.shape
        
        # 根据裁切方向检查x参数的有效性
        if crop_direction in ["left", "right"]:
            if x >= width:
                raise ValueError(f"Crop width ({x}) exceeds image width ({width})")
        else:  # top, bottom
            if x >= height:
                raise ValueError(f"Crop height ({x}) exceeds image height ({height})")
        
        if x < 0:
            raise ValueError("Crop parameter must be non-negative")
        
        # 根据裁切方向进行不同的裁切操作
        if crop_direction == "left":
            # 从左边开始裁切x像素宽度，保持原图高度
            cropped_image = image[:, :, x:, :]
            
        elif crop_direction == "right":
            # 从右边开始裁切x像素宽度，保持原图高度
            cropped_image = image[:, :, :width-x, :]
            
        elif crop_direction == "top":
            # 从顶部开始裁切x像素高度，保持原图宽度
            cropped_image = image[:, x:, :, :]
            
        elif crop_direction == "bottom":
            # 从底部开始裁切x像素高度，保持原图宽度
            cropped_image = image[:, :height-x, :, :]
        
        # 处理遮罩
        if mask is not None:
            # 确保遮罩格式正确
            if len(mask.shape) == 2:
                # 如果遮罩是 (H, W)，添加批次维度
                mask = mask.unsqueeze(0)
            elif len(mask.shape) != 3:
                raise ValueError("Mask must have 2 or 3 dimensions")
            
            # 应用相同的裁切逻辑到遮罩
            if crop_direction == "left":
                cropped_mask = mask[:, :, x:]
            elif crop_direction == "right":
                cropped_mask = mask[:, :, :width-x]
            elif crop_direction == "top":
                cropped_mask = mask[:, x:, :]
            elif crop_direction == "bottom":
                cropped_mask = mask[:, :height-x, :]
        else:
            # 创建对应尺寸的全白遮罩
            if crop_direction in ["left", "right"]:
                new_width = width - x
                cropped_mask = torch.ones((batch_size, height, new_width), 
                                        dtype=torch.float32, device=image.device)
            else:  # top, bottom
                new_height = height - x
                cropped_mask = torch.ones((batch_size, new_height, width), 
                                        dtype=torch.float32, device=image.device)
        
        return (cropped_image, cropped_mask)



    # 节点映射字典
NODE_CLASS_MAPPINGS = {
    "PDImageCropLocation_V2": PDImageCropLocation_V2,
}

# 节点显示名称映射
NODE_DISPLAY_NAME_MAPPINGS = {
    "PDImageCropLocation_V2": "PD Image Crop Location_V2",
}

# 导出映射
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

