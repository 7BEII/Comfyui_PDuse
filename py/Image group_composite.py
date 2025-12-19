import torch
import numpy as np
from PIL import Image, ImageDraw
from typing import List, Tuple

def tensor2pil(image):
    """将ComfyUI图像张量转换为PIL图像"""
    return Image.fromarray(np.clip(255. * image.cpu().numpy().squeeze(), 0, 255).astype(np.uint8))

def pil2tensor(image):
    """将PIL图像转换为ComfyUI图像张量"""
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)

def hex_to_rgb(hex_color):
    """将十六进制颜色转换为RGB元组"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def apply_border_and_outline(image, border_thickness, border_color, outline_thickness, outline_color):
    """给图像添加边框和描边"""
    # 计算新的尺寸
    total_padding = border_thickness + outline_thickness
    new_width = image.width + 2 * total_padding
    new_height = image.height + 2 * total_padding
    
    # 创建新图像
    new_image = Image.new('RGB', (new_width, new_height), outline_color)
    
    # 如果有描边，先画描边
    if outline_thickness > 0:
        draw = ImageDraw.Draw(new_image)
        # 画外圈描边
        for i in range(outline_thickness):
            draw.rectangle(
                [i, i, new_width - 1 - i, new_height - 1 - i],
                outline=outline_color,
                width=1
            )
    
    # 画边框
    if border_thickness > 0:
        draw = ImageDraw.Draw(new_image)
        # 画边框
        for i in range(outline_thickness, outline_thickness + border_thickness):
            draw.rectangle(
                [i, i, new_width - 1 - i, new_height - 1 - i],
                outline=border_color,
                width=1
            )
    
    # 粘贴原图像
    new_image.paste(image, (total_padding, total_padding))
    
    return new_image

def make_grid_panel(images, max_columns):
    """将图像列表排列成网格"""
    if not images:
        return Image.new('RGB', (100, 100), (255, 255, 255))
    
    # 计算网格尺寸
    num_images = len(images)
    num_columns = min(max_columns if max_columns > 0 else num_images, num_images)
    num_rows = (num_images + num_columns - 1) // num_columns
    
    # 获取单个图像的尺寸
    img_width, img_height = images[0].size
    
    # 创建网格图像
    grid_width = num_columns * img_width
    grid_height = num_rows * img_height
    grid_image = Image.new('RGB', (grid_width, grid_height), (255, 255, 255))
    
    # 排列图像
    for idx, img in enumerate(images):
        row = idx // num_columns
        col = idx % num_columns
        x = col * img_width
        y = row * img_height
        grid_image.paste(img, (x, y))
    
    return grid_image

class PD_ImageGroupComposite:
    """
    PD Image Group Composite
    用于把一批图片排成一个多列网格面板，同时给每张图统一添加边框和描边
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        # 定义颜色选项
        color_options = [
            "black", "white", "red", "green", "blue", 
            "yellow", "cyan", "magenta", "gray", "orange"
        ]
        
        return {
            "required": {
                "images": ("IMAGE",),
                "border_thickness": ("INT", {"default": 2, "min": 0, "max": 1024, "step": 1}),
                "border_color": (color_options, {"default": "black"}),
                "outline_thickness": ("INT", {"default": 1, "min": 0, "max": 1024, "step": 1}),
                "outline_color": (color_options[1:], {"default": "white"}),
                "max_columns": ("INT", {"default": 5, "min": 1, "max": 256, "step": 1}),
            },
            "optional": {
                "border_color_hex": ("STRING", {"multiline": False, "default": "#000000"}),
                "outline_color_hex": ("STRING", {"multiline": False, "default": "#FFFFFF"}),
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "composite_images"
    CATEGORY = "PD_Nodes"
    
    def composite_images(self, images, border_thickness, border_color, 
                        outline_thickness, outline_color, max_columns,
                        border_color_hex="#000000", outline_color_hex="#FFFFFF"):
        """
        将一批图片排列成网格并添加边框和描边
        
        Args:
            images: 输入图像批次张量
            border_thickness: 边框粗细
            border_color: 边框颜色
            outline_thickness: 描边粗细
            outline_color: 描边颜色
            max_columns: 最大列数
            border_color_hex: 边框十六进制颜色
            outline_color_hex: 描边十六进制颜色
            
        Returns:
            合成后的网格图像张量
        """
        # 颜色映射
        color_mapping = {
            "black": (0, 0, 0),
            "white": (255, 255, 255),
            "red": (255, 0, 0),
            "green": (0, 255, 0),
            "blue": (0, 0, 255),
            "yellow": (255, 255, 0),
            "cyan": (0, 255, 255),
            "magenta": (255, 0, 255),
            "gray": (128, 128, 128),
            "orange": (255, 165, 0),
        }
        
        # 处理颜色
        if border_color_hex.startswith('#'):
            border_rgb = hex_to_rgb(border_color_hex)
        else:
            border_rgb = color_mapping.get(border_color, (0, 0, 0))
            
        if outline_color_hex.startswith('#'):
            outline_rgb = hex_to_rgb(outline_color_hex)
        else:
            outline_rgb = color_mapping.get(outline_color, (255, 255, 255))
        
        # 转换张量为PIL图像列表
        pil_images = []
        for i in range(images.shape[0]):
            img_tensor = images[i:i+1]  # 保持批次维度
            pil_img = tensor2pil(img_tensor)
            pil_images.append(pil_img)
        
        # 给每张图添加边框和描边
        processed_images = []
        for img in pil_images:
            processed_img = apply_border_and_outline(
                img, border_thickness, border_rgb, 
                outline_thickness, outline_rgb
            )
            processed_images.append(processed_img)
        
        # 排列成网格
        grid_image = make_grid_panel(processed_images, max_columns)
        
        # 转换回张量
        result_tensor = pil2tensor(grid_image)
        
        return (result_tensor,)

# 节点注册
NODE_CLASS_MAPPINGS = {
    "PD_ImageGroupComposite": PD_ImageGroupComposite
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_ImageGroupComposite": "PD Image Group Composite"
}

# 导出节点信息供ComfyUI使用
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']