"""
PD图像覆盖保存节点
该模块提供了保存图像并覆盖同名文件的功能
"""

from PIL import Image
from PIL.PngImagePlugin import PngInfo
import os
import numpy as np
import json
from comfy.cli_args import args
import folder_paths
from datetime import datetime


class PD_image_coversaver:
    """
    PD图像覆盖保存节点
    功能：将图像保存到指定路径，如果存在同名文件则直接覆盖
    """
    
    def __init__(self):
        """初始化保存参数"""
        self.output_dir = folder_paths.get_output_directory()  # 获取默认输出目录
        self.type = "output"  # 输出类型标识
        self.compress_level = 4  # PNG压缩级别 (0-9, 0为无压缩, 9为最高压缩)

    @classmethod
    def INPUT_TYPES(s):
        """
        定义节点输入参数类型
        返回：
        - required: 必需参数
        - hidden: 隐藏参数
        """
        return {
            "required": {
                "images": ("IMAGE", ),  # 输入图像数组，张量形状为 B H W C
                "filename": ("STRING", {"default": "output"}),  # 文件名（可含或不含扩展名，会智能处理）
                "custom_output_dir": ("STRING", {"default": ""}),  # 自定义输出目录
                "format": (["png", "jpg"], {"default": "png"}),  # 图像格式选择
                "show_preview": ("BOOLEAN", {"default": True}),  # 是否在前端显示预览图
            },
            "hidden": {
                "prompt": "PROMPT", 
                "extra_pnginfo": "EXTRA_PNGINFO"
            },  # 隐藏的提示信息和额外PNG信息
        }

    RETURN_TYPES = ()  # 无返回值类型
    FUNCTION = "save_images"  # 主要执行函数名
    OUTPUT_NODE = True  # 标识为输出节点
    CATEGORY = "PD/Image"  # 节点分类

    def save_images(self, images, filename="output", custom_output_dir="", 
                   format="png", show_preview=True, prompt=None, extra_pnginfo=None):
        """
        保存图像主方法（覆盖模式）
        
        参数：
        - images: 图像数组，张量形状为 B H W C
        - filename: 文件名（可含或不含扩展名，会智能处理）
        - custom_output_dir: 自定义输出目录路径
        - format: 图像格式（png或jpg）
        - show_preview: 是否在前端显示预览图
        - prompt: 提示词信息
        - extra_pnginfo: 额外的PNG元数据信息
        
        返回：
        - 如果show_preview=True，返回包含图像预览信息的字典
        - 如果show_preview=False，返回空字典（不显示预览图）
        """
        try:
            # 确定输出目录
            if not custom_output_dir:
                # 没有自定义路径时，使用默认输出目录
                output_dir = self.output_dir
            else:
                output_dir = custom_output_dir
            
            # 创建目录（如果不存在）
            os.makedirs(output_dir, exist_ok=True)
            
            # 保存图像到指定目录
            results = self._save_images_to_dir(
                images, filename, output_dir, format, prompt, extra_pnginfo
            )
            
            # 根据show_preview参数决定返回值
            if show_preview:
                # 返回UI预览信息，前端会显示图像预览
                return {"ui": {"images": results}}
            else:
                # 返回空字典，不显示预览图
                return {}
        
        except Exception as e:
            print(f"保存图像时发生错误: {e}")
            return {}

    def _get_filename_with_extension(self, filename, format):
        """
        智能处理文件名后缀
        
        参数：
        - filename: 原始文件名
        - format: 目标格式（png或jpg）
        
        返回：
        - 带有正确后缀的文件名
        """
        # 支持的图像格式后缀
        supported_extensions = ['.png', '.jpg', '.jpeg']
        
        # 检查文件名是否已经有后缀
        filename_lower = filename.lower()
        has_extension = any(filename_lower.endswith(ext) for ext in supported_extensions)
        
        if has_extension:
            # 如果已经有后缀，直接返回原文件名
            return filename
        else:
            # 如果没有后缀，根据format参数添加对应后缀
            target_extension = f".{format.lower()}"
            return f"{filename}{target_extension}"

    def _save_images_to_dir(self, images, filename, output_dir, format, prompt, extra_pnginfo):
        """
        私有方法：将图像保存到指定目录（覆盖模式）
        
        参数：
        - images: 图像数组，张量形状为 B H W C
        - filename: 文件名（可能含或不含扩展名）
        - output_dir: 输出目录路径
        - format: 图像格式（png或jpg）
        - prompt: 提示词信息
        - extra_pnginfo: 额外PNG信息
        
        返回：
        - results: 保存结果列表
        """
        results = list()
        
        # 遍历图像数组，逐个保存
        for batch_number, image in enumerate(images):
            # 将张量转换为numpy数组，并缩放到0-255范围
            # 输入张量形状为 B H W C
            i = 255. * image.cpu().numpy()
            
            # 处理alpha通道
            if format.lower() == "png":
                # PNG格式：支持alpha通道
                if i.shape[2] == 4:  # 已有alpha通道
                    img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8), 'RGBA')
                else:  # 创建透明背景
                    # 添加alpha通道，设置为完全不透明
                    alpha = np.ones((i.shape[0], i.shape[1], 1), dtype=i.dtype) * 255
                    i_with_alpha = np.concatenate([i, alpha], axis=2)
                    img = Image.fromarray(np.clip(i_with_alpha, 0, 255).astype(np.uint8), 'RGBA')
            else:  # JPG格式
                # JPG不支持alpha通道，转换为RGB
                if i.shape[2] == 4:  # 如果有alpha通道，移除它
                    i = i[:, :, :3]
                img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8), 'RGB')
            
            metadata = None
            
            # 如果没有禁用元数据且为PNG格式，则添加元数据信息
            if not args.disable_metadata and format.lower() == "png":
                metadata = PngInfo()  # 创建PNG信息对象
                # 添加提示词信息到元数据
                if prompt is not None:
                    metadata.add_text("prompt", json.dumps(prompt))
                # 添加额外PNG信息到元数据
                if extra_pnginfo is not None:
                    for x in extra_pnginfo:
                        metadata.add_text(x, json.dumps(extra_pnginfo[x]))
            
            # 智能处理文件名后缀
            if len(images) > 1:
                # 多张图片时，在文件名后添加批次编号，然后处理后缀
                base_filename = f"{filename}_{batch_number:03d}"
                file = self._get_filename_with_extension(base_filename, format)
            else:
                # 单张图片时，直接处理文件名后缀
                file = self._get_filename_with_extension(filename, format)
            
            # 完整文件路径
            filepath = os.path.join(output_dir, file)
            
            # 根据格式保存图像（直接覆盖）
            if format.lower() == "png":
                # PNG格式：保存为RGBA，包含元数据和指定的压缩级别
                img.save(
                    filepath,
                    pnginfo=metadata,
                    compress_level=self.compress_level,
                    format='PNG'
                )
            else:  # JPG格式
                # JPG格式：保存为RGB，设置质量
                img.save(
                    filepath,
                    format='JPEG',
                    quality=95,  # JPG质量设置
                    optimize=True
                )
            
            print(f"图像已保存: {filepath}")
            
            # 生成返回结果信息，包含文件名和路径
            results.append({
                "filename": file,         # 保存的文件名
                "subfolder": output_dir,  # 子文件夹路径
                "type": self.type         # 文件类型
            })
        
        return results


# 节点类映射：将类名映射到实际的类
NODE_CLASS_MAPPINGS = {
    "PD_image_coversaver": PD_image_coversaver,
}

# 节点显示名称映射：定义在UI中显示的节点名称
NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_image_coversaver": "PD_IMAGE:COVER_SAVER",
}

