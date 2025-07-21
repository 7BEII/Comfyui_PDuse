"""
PD图像保存节点
该模块提供了自定义路径保存图像的功能，支持自定义输出目录和文件名前缀
"""

from PIL import Image, ImageOps, ImageSequence
from PIL.PngImagePlugin import PngInfo
import os
import numpy as np
import json
import re
from comfy.cli_args import args
import folder_paths
from datetime import datetime

class PD_imagesave_path:
    """
    PD图像保存路径节点
    功能：将图像保存到指定的自定义路径，支持自定义文件名前缀和输出目录
    """
    
    def __init__(self):
        """初始化保存参数"""
        self.output_dir = folder_paths.get_output_directory()  # 获取默认输出目录
        self.type = "output"  # 输出类型标识
        self.prefix_append = ""  # 文件名前缀追加内容
        self.compress_level = 4  # PNG压缩级别 (0-9, 0为无压缩, 9为最高压缩)

    @classmethod
    def INPUT_TYPES(s):
        """
        定义节点输入参数类型
        返回：
        - required: 必需参数
        - hidden: 隐藏参数
        """
        return {"required": 
                    {"images": ("IMAGE", ),  # 输入图像数组
                     "filename_prefix": ("STRING", {"default": "ComfyUI"}),  # 文件名前缀
                     "custom_output_dir": ("STRING", {"default": "", "optional": True})},  # 自定义输出目录(可选)
                "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},  # 隐藏的提示信息和额外PNG信息
                }

    RETURN_TYPES = ()  # 无返回值类型
    FUNCTION = "save_images"  # 主要执行函数名
    OUTPUT_NODE = True  # 标识为输出节点
    CATEGORY = "PD/Image"  # 节点分类

    def save_images(self, images, filename_prefix="ComfyUI", prompt=None, extra_pnginfo=None, custom_output_dir=""):
        """
        保存图像主方法
        
        参数：
        - images: 图像数组
        - filename_prefix: 文件名前缀，默认为"ComfyUI"
        - prompt: 提示词信息
        - extra_pnginfo: 额外的PNG元数据信息
        - custom_output_dir: 自定义输出目录路径
        
        返回：
        - 空字典（不显示预览图）
        """
        try:
            # 判断是否有自定义保存路径
            if not custom_output_dir:
                # 没有自定义路径时，使用默认路径，并创建以文件名和日期为标识的子文件夹
                date_str = datetime.now().strftime("%Y-%m-%d")  # 生成当前日期字符串
                custom_output_dir = os.path.join(self.output_dir, f"{filename_prefix}_{date_str}")
                os.makedirs(custom_output_dir, exist_ok=True)  # 创建目录，如果已存在则忽略
            
            # 调用私有方法保存图像到自定义目录
            self._save_images_to_dir(images, filename_prefix, prompt, extra_pnginfo, custom_output_dir)
            
            # 返回空的结果，不显示预览图
            return {}
        
        except Exception as e:
            print(f"保存图像时发生错误: {e}")
            return {}

    def _save_images_to_dir(self, images, filename_prefix, prompt, extra_pnginfo, output_dir):
        """
        私有方法：将图像保存到指定目录
        
        参数：
        - images: 图像数组
        - filename_prefix: 文件名前缀
        - prompt: 提示词信息
        - extra_pnginfo: 额外PNG信息
        - output_dir: 输出目录路径
        
        返回：
        - results: 保存结果列表
        """
        results = list()
        
        # 自定义计数器逻辑，只检查相同扩展名的文件
        counter = self._get_next_counter(output_dir, filename_prefix, ".png")
            
        # 遍历图像数组，逐个保存
        for (batch_number, image) in enumerate(images):
            # 将张量转换为numpy数组，并缩放到0-255范围
            i = 255. * image.cpu().numpy()
            # 转换为PIL图像对象，确保像素值在有效范围内
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            metadata = None
            
            # 如果没有禁用元数据，则添加元数据信息
            if not args.disable_metadata:
                metadata = PngInfo()  # 创建PNG信息对象
                # 添加提示词信息到元数据
                if prompt is not None:
                    metadata.add_text("prompt", json.dumps(prompt))
                # 添加额外PNG信息到元数据
                if extra_pnginfo is not None:
                    for x in extra_pnginfo:
                        metadata.add_text(x, json.dumps(extra_pnginfo[x]))
            
            # 生成最终文件名，包含计数器和扩展名
            file = f"{filename_prefix}_{counter:05}_.png"
            
            # 保存图像文件，包含元数据和指定的压缩级别
            img.save(os.path.join(output_dir, file), pnginfo=metadata, compress_level=self.compress_level)
                
            # 生成返回结果信息，包含文件名和路径
            results.append({
                "filename": file,         # 保存的文件名
                "subfolder": output_dir, # 子文件夹路径
                "type": self.type         # 文件类型
            })
            counter += 1  # 递增计数器
        
        return results
    
    def _get_next_counter(self, output_dir, filename_prefix, extension):
        """
        获取下一个可用的计数器值，只检查相同扩展名的文件
        
        Args:
            output_dir (str): 输出目录
            filename_prefix (str): 文件名前缀
            extension (str): 文件扩展名
            
        Returns:
            int: 下一个可用的计数器值
        """
        existing_counters = []
        try:
            # 构建匹配模式
            pattern = f"{re.escape(filename_prefix)}_(\d+)_"
            
            for filename in os.listdir(output_dir):
                # 只检查相同扩展名的文件
                file_ext = os.path.splitext(filename)[1].lower()
                if file_ext != extension.lower():
                    continue
                
                # 匹配文件名模式
                match = re.search(pattern, filename)
                if match:
                    existing_counters.append(int(match.group(1)))
        except Exception as e:
            print(f"读取目录失败: {e}")
        
        # 返回下一个可用的计数器值
        if existing_counters:
            return max(existing_counters) + 1
        else:
            return 1


# 节点类映射：将类名映射到实际的类
NODE_CLASS_MAPPINGS = {
    "PD_imagesave_path": PD_imagesave_path,
}

# 节点显示名称映射：定义在UI中显示的节点名称
NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_imagesave_path": "PDIMAGE:SAVE_PATH",
}
