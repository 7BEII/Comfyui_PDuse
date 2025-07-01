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

class BatchImageRename:
    """
    简化版批量图片重命名
    输入: 文件路径, 后缀, 输出格式, 开始编号, 前缀
    输出: 处理结果文本摘要
    """
    
    """
    批量图片重命名(带输出路径选项)
    输入: 文件路径, 输出路径, 后缀, 输出格式, 开始编号, 前缀
    输出: 处理结果文本摘要
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_folder": ("STRING", {"default": "input", "multiline": False, "placeholder": "输入图片文件夹路径"}),
                "output_folder": ("STRING", {"default": "output", "multiline": False, "placeholder": "输出文件夹路径"}),
                "filename": ("STRING", {"default": "", "multiline": False, "placeholder": "新文件名(留空保留原文件名)"}),
                "suffix": ("STRING", {"default": "_", "multiline": False, "placeholder": "文件名后缀"}),
                "output_format": (["png", "jpg"], {"default": "png"}),
                "max_side_length": ("INT", {"default": 2048, "min": 64, "max": 8192, "step": 64}),
                "start_number": ("INT", {"default": 1, "min": 1, "max": 10000, "step": 1}),
            },
            "optional": {
                "keep_aspect_ratio": ("BOOLEAN", {"default": True}),
                "resize_enabled": ("BOOLEAN", {"default": True}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("result_summary",)
    FUNCTION = "process_images"
    CATEGORY = "image/utils"
    
    def process_images(self, input_folder: str, output_folder: str, filename: str, suffix: str, 
                     output_format: str, max_side_length: int, start_number: int,
                     keep_aspect_ratio: bool = True, resize_enabled: bool = True) -> Tuple[str]:
        
        # 处理 output_format 可能为索引的情况
        if isinstance(output_format, int):
            output_format = ["png", "jpg"][output_format]
        elif output_format not in ["png", "jpg"]:
            return (f"错误: 无效的输出格式 '{output_format}'，必须是 'png' 或 'jpg'",)
        
        # 验证输入文件夹
        if not os.path.isdir(input_folder):
            os.makedirs(input_folder, exist_ok=True)
            return (f"警告: 输入文件夹不存在，已自动创建: {input_folder}",)
        
        # 设置输出文件夹
        os.makedirs(output_folder, exist_ok=True)
            
        # 获取输入文件夹中的所有图片文件
        image_extensions = ['.png', '.jpg', '.jpeg', '.webp', '.bmp']
        input_files = []
        for file in os.listdir(input_folder):
            if any(file.lower().endswith(ext) for ext in image_extensions):
                input_files.append(os.path.join(input_folder, file))
        
        if not input_files:
            return (f"错误: 在文件夹中未找到图片文件: {input_folder}",)
        
        renamed_files = []
        counter = start_number
        processed_count = 0
        resize_info = []
        
        for input_file in sorted(input_files):
            try:
                # 获取原文件名（不带扩展名）
                original_name = os.path.splitext(os.path.basename(input_file))[0]
                
                # 确定新文件名
                if filename:  # 如果指定了新文件名
                    new_name = f"{filename}{suffix}{counter}"
                else:  # 否则保留原文件名
                    new_name = original_name
                
                new_filename = f"{new_name}.{output_format}"
                output_path = os.path.join(output_folder, new_filename)
                
                # 打开图片
                img = Image.open(input_file)
                original_width, original_height = img.size
                
                # 调整尺寸逻辑
                if resize_enabled and keep_aspect_ratio:
                    # 强制将最长边缩放到 max_side_length（无论原始尺寸大小）
                    if original_width >= original_height:
                        scale_ratio = max_side_length / original_width
                        new_width = max_side_length
                        new_height = floor(original_height * scale_ratio)
                    else:
                        scale_ratio = max_side_length / original_height
                        new_height = max_side_length
                        new_width = floor(original_width * scale_ratio)
                    
                    img = img.resize((new_width, new_height), Image.LANCZOS)
                    resize_info.append(
                        f"{os.path.basename(input_file)}: {img.size[0]}x{img.size[1]} (最长边已强制为 {max_side_length}px)"
                    )
                elif resize_enabled and not keep_aspect_ratio:
                    # 不保持宽高比，强制为正方形
                    img = ImageOps.fit(img, (max_side_length, max_side_length), method=Image.LANCZOS)
                    resize_info.append(
                        f"{os.path.basename(input_file)}: 强制调整为 {max_side_length}x{max_side_length}"
                    )
                
                # 保存图片
                if output_format.lower() == 'png':
                    img.save(output_path, format='PNG', compress_level=4)
                elif output_format.lower() == 'jpg':
                    img.save(output_path, format='JPEG', quality=90)
                
                renamed_files.append(new_filename)
                counter += 1
                processed_count += 1
            except Exception as e:
                return (f"处理文件 {os.path.basename(input_file)} 时出错: {str(e)}",)
        
        # 生成结果摘要
        summary_lines = [
            f"批量处理完成!",
            f"• 处理图片总数: {processed_count}张",
            f"• 输入文件夹: {input_folder}",
            f"• 输出文件夹: {output_folder}",
            f"• 命名模式: {'自定义' if filename else '原文件名'}{suffix}[编号].{output_format}",
            f"• 起始编号: {start_number}",
            f"• 最长边强制为: {max_side_length}px",
            f"• 保持宽高比: {'是' if keep_aspect_ratio else '否'}",
        ]
        
        if resize_info:
            summary_lines.append("\n尺寸调整详情:")
            for info in resize_info[:3]:
                summary_lines.append(f"  {info}")
            if len(resize_info) > 3:
                summary_lines.append(f"  (共处理 {len(resize_info)} 张图片...)")
        
        summary = "\n".join(summary_lines)
        
        return (summary,)

from PIL import Image, ImageOps

class Load_Images:
    """
    A ComfyUI node to load multiple images from a directory with various options.
    """
    
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "directory": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "dynamicPrompts": False
                }),
            },
            "optional": {
                "image_load_cap": ("INT", {
                    "default": 0, 
                    "min": 0, 
                    "step": 1,
                    "display": "number"
                }),
                "start_index": ("INT", {
                    "default": 0, 
                    "min": 0, 
                    "max": 0xffffffffffffffff, 
                    "step": 1,
                    "display": "number"
                }),
                "load_always": ([False, True], {
                    "default": False
                }),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK", "STRING")
    RETURN_NAMES = ("images", "masks", "file_paths")
    FUNCTION = "load_images"
    CATEGORY = "image/loading"
    OUTPUT_IS_LIST = (True, True, True)

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        if 'load_always' in kwargs and kwargs['load_always']:
            return float("NaN")
        else:
            return hash(frozenset(kwargs))

    def load_images(self, directory: str, image_load_cap: int = 0, start_index: int = 0, load_always=False):
        if not os.path.isdir(directory):
            raise FileNotFoundError(f"Directory '{directory}' cannot be found.")
        
        dir_files = os.listdir(directory)
        if len(dir_files) == 0:
            raise FileNotFoundError(f"No files in directory '{directory}'.")

        # Filter files by extension
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        dir_files = [f for f in dir_files if any(f.lower().endswith(ext) for ext in valid_extensions)]
        dir_files = sorted(dir_files)
        dir_files = [os.path.join(directory, x) for x in dir_files]

        # Apply start index
        dir_files = dir_files[start_index:]

        images = []
        masks = []
        file_paths = []

        limit_images = image_load_cap > 0
        image_count = 0

        for image_path in dir_files:
            if limit_images and image_count >= image_load_cap:
                break
                
            try:
                i = Image.open(image_path)
                i = ImageOps.exif_transpose(i)
                image = i.convert("RGB")
                image = np.array(image).astype(np.float32) / 255.0
                image = torch.from_numpy(image)[None,]

                if 'A' in i.getbands():
                    mask = np.array(i.getchannel('A')).astype(np.float32) / 255.0
                    mask = 1. - torch.from_numpy(mask)
                else:
                    mask = torch.zeros((64, 64), dtype=torch.float32, device="cpu")

                images.append(image)
                masks.append(mask)
                file_paths.append(str(image_path))
                image_count += 1
            except Exception as e:
                print(f"Error loading image {image_path}: {e}")

        if not images:
            raise ValueError("No valid images found in the directory.")

        return (images, masks, file_paths)
    
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


    
# 在 ComfyUI 中的节点映射配置
NODE_CLASS_MAPPINGS = {
    "PD_Image_Crop_Location": PD_Image_Crop_Location,
    "PD_Image_centerCrop": PD_Image_centerCrop,
    "PD_GetImageSize": PD_GetImageSize, 
    "PDIMAGE_Rename": BatchImageRename,
    "Load_Images": Load_Images,
    "PDIMAGE_LongerSize": PDIMAGE_LongerSize
    
}

# 设置节点在 UI 中显示的名称
NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_Image_Crop_Location": "PD:Image Crop Location",
    "PD_Image_centerCrop": "PD:Image centerCrop",
    "PD_GetImageSize": "PD:GetImageSize", 
    "PDIMAGE_Rename": "PDIMAGE:Rename",
    "Load_Images": "PDIMAGE:Load_Images",
    "PDIMAGE_LongerSize": "PDIMAGE:LongerSize",

}
