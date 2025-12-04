"""
PD图像保存节点 V2
该模块提供了增强的自定义路径保存图像功能，支持多种格式和高级选项
"""

from PIL import Image, ImageOps, ImageSequence
from PIL.PngImagePlugin import PngInfo
import os
import numpy as np
import json
import torch
import re
import time
from datetime import datetime
from comfy.cli_args import args
import folder_paths

class PD_SAVE_PATH2:
    """
    PD图像保存路径节点 V2
    功能：将图像保存到指定的自定义路径，支持多种格式、自定义文件名和高级选项
    """
    
    def __init__(self):
        """初始化保存参数"""
        self.output_dir = folder_paths.get_output_directory()  # 获取默认输出目录
        self.type = "output"  # 输出类型标识
        self.prefix_append = ""  # 文件名前缀追加内容
        self.compress_level = 4  # PNG压缩级别 (0-9, 0为无压缩, 9为最高压缩)

    @classmethod
    def INPUT_TYPES(cls):
        """
        定义节点输入参数类型
        返回：
        - required: 必需参数
        - hidden: 隐藏参数
        """
        return {
            "required": {
                "images": ("IMAGE",),  # 输入图像数组
                "name": ("STRING", {"default": "T"}),  # 文件名前缀，空则不加前缀
                "output_dir": ("STRING", {"default": "", "multiline": False}),  # 自定义输出目录
                "number_start": ("BOOLEAN", {"default": True}),  # 数字是否在开头
                "number_padding": ("INT", {"default": 1, "min": 1, "max": 9, "step": 1}),  # 数字填充位数
                "filename_delimiter": ("STRING", {"default": "_"}),  # 文件名分隔符，空则不加分隔符
                "extension": (["png", "jpg", "jpeg", "webp", "bmp", "tiff"], {"default": "jpg"}),  # 文件扩展名
                "quality": ("INT", {"default": 100, "min": 1, "max": 100}),  # 图像质量
                "optimize_image": ("BOOLEAN", {"default": True}),  # 是否优化图像
                "lossless_webp": ("BOOLEAN", {"default": False}),  # WebP是否无损
                "embed_metadata": ("BOOLEAN", {"default": True}),  # 是否嵌入元数据
                "overwrite_mode": (["false", "prefix_as_filename"], {"default": "false"}),  # 覆盖模式
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

    def save_images(self, images, name="T_", output_dir="", 
                   number_start=True, number_padding=1, filename_delimiter="_", extension="jpg", quality=100, optimize_image=True, lossless_webp=False,
                   embed_metadata=True, overwrite_mode="false", prompt=None, extra_pnginfo=None):
        """
        保存图像主方法
        
        参数：
        - images: 图像数组
        - name: 文件名前缀，空则不加前缀，默认"T_"
        - output_dir: 自定义输出目录路径
        - number_start: 数字是否在开头，默认True
        - number_padding: 数字填充位数，默认1
        - filename_delimiter: 文件名分隔符，空则不加分隔符，默认"_"
        - extension: 文件扩展名
        - quality: 图像质量
        - optimize_image: 是否优化图像
        - lossless_webp: WebP是否无损
        - embed_metadata: 是否嵌入元数据
        - overwrite_mode: 覆盖模式
        - prompt: 提示词信息
        - extra_pnginfo: 额外的PNG元数据信息
        
        返回：
        - 空字典（不显示预览图）
        """
        try:
            # 解析文件名前缀中的令牌
            name = self._parse_tokens(name)
            
            # 判断是否有自定义保存路径
            if not output_dir or output_dir.strip() == "":
                # 没有自定义路径时，使用默认路径，并创建以文件名和日期为标识的子文件夹
                date_str = datetime.now().strftime("%Y-%m-%d")
                folder_name = name if name.strip() else "images"
                output_dir = os.path.join(self.output_dir, f"{folder_name}_{date_str}")
            else:
                # 解析自定义路径中的令牌
                output_dir = self._parse_tokens(output_dir)
                if not os.path.isabs(output_dir):
                    output_dir = os.path.join(self.output_dir, output_dir)
            
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 调用私有方法保存图像到自定义目录
            self._save_images_to_dir(
                images, name, output_dir, number_padding, number_start, filename_delimiter, extension, quality,
                optimize_image, lossless_webp, embed_metadata, overwrite_mode,
                prompt, extra_pnginfo
            )
            
            # 返回空的结果，不显示预览图
            return {}
        
        except Exception as e:
            print(f"保存图像时发生错误: {e}")
            return {}

    def _parse_tokens(self, text: str) -> str:
        """
        解析文本中的令牌
        
        Args:
            text (str): 包含令牌的文本
            
        Returns:
            str: 解析后的文本
        """
        tokens = {
            '[time]': str(int(time.time())),
            '[date]': datetime.now().strftime('%Y-%m-%d'),
            '[datetime]': datetime.now().strftime('%Y-%m-%d_%H-%M-%S'),
            '[hostname]': os.uname().nodename if hasattr(os, 'uname') else 'unknown',
            '[user]': os.getenv('USER', 'unknown')
        }
        
        # 处理自定义时间格式
        def replace_time_format(match):
            format_code = match.group(1)
            return datetime.now().strftime(format_code)
        
        # 替换时间格式令牌
        text = re.sub(r'\[time\((.*?)\)\]', replace_time_format, text)
        
        # 替换其他令牌
        for token, value in tokens.items():
            text = text.replace(token, value)
        
        return text

    def _generate_filename(self, name: str, number_padding: int, 
                          number_start: bool, filename_delimiter: str, extension: str, output_dir: str) -> str:
        """
        生成唯一的文件名
        
        Args:
            name (str): 文件名前缀，空则不加前缀
            number_padding (int): 数字填充位数
            number_start (bool): 数字是否在开头
            filename_delimiter (str): 文件名分隔符，空则不加分隔符
            extension (str): 文件扩展名
            output_dir (str): 输出目录
            
        Returns:
            str: 生成的文件名
        """
        # 确保扩展名有效
        if not extension.startswith('.'):
            extension = '.' + extension
        
        # 查找现有计数器值
        if name.strip():  # 有前缀的情况
            if number_start:
                # 数字在开头: 1_T_.jpg 或 1T_.jpg（无分隔符）
                if filename_delimiter:
                    pattern = f"(\\d+){re.escape(filename_delimiter)}{re.escape(name)}"
                else:
                    pattern = f"(\\d+){re.escape(name)}"
            else:
                # 数字在末尾: T_1.jpg 或 T1.jpg（无分隔符）
                if filename_delimiter:
                    pattern = f"{re.escape(name)}{re.escape(filename_delimiter)}(\\d+)"
                else:
                    pattern = f"{re.escape(name)}(\\d+)"
        else:  # 无前缀的情况
            # 只有数字: 1.jpg
            pattern = f"(\\d+)"
        
        existing_counters = []
        try:
            for filename in os.listdir(output_dir):
                # 只检查相同扩展名的文件
                file_ext = os.path.splitext(filename)[1].lower()
                if file_ext != extension.lower():
                    continue
                
                # 移除扩展名再匹配
                name_without_ext = os.path.splitext(filename)[0]
                match = re.match(pattern + "$", name_without_ext)
                if match:
                    existing_counters.append(int(match.group(1)))
        except Exception as e:
            print(f"读取目录失败: {e}")
        
        # 设置初始计数器值
        if existing_counters:
            counter = max(existing_counters) + 1
        else:
            counter = 1
        
        # 生成文件名
        if name.strip():  # 有前缀的情况
            if number_start:
                # 数字在开头: 1_T_.jpg 或 1T_.jpg（无分隔符）
                if filename_delimiter:
                    filename = f"{counter:0{number_padding}}{filename_delimiter}{name}{extension}"
                else:
                    filename = f"{counter:0{number_padding}}{name}{extension}"
            else:
                # 数字在末尾: T_1.jpg 或 T1.jpg（无分隔符）
                if filename_delimiter:
                    filename = f"{name}{filename_delimiter}{counter:0{number_padding}}{extension}"
                else:
                    filename = f"{name}{counter:0{number_padding}}{extension}"
        else:  # 无前缀的情况
            # 只有数字: 1.jpg
            filename = f"{counter:0{number_padding}}{extension}"
        
        # 确保文件名唯一
        while os.path.exists(os.path.join(output_dir, filename)):
            counter += 1
            if name.strip():  # 有前缀的情况
                if number_start:
                    # 数字在开头: 1_T_.jpg 或 1T_.jpg（无分隔符）
                    if filename_delimiter:
                        filename = f"{counter:0{number_padding}}{filename_delimiter}{name}{extension}"
                    else:
                        filename = f"{counter:0{number_padding}}{name}{extension}"
                else:
                    # 数字在末尾: T_1.jpg 或 T1.jpg（无分隔符）
                    if filename_delimiter:
                        filename = f"{name}{filename_delimiter}{counter:0{number_padding}}{extension}"
                    else:
                        filename = f"{name}{counter:0{number_padding}}{extension}"
            else:  # 无前缀的情况
                # 只有数字: 1.jpg
                filename = f"{counter:0{number_padding}}{extension}"
        
        return filename

    def _save_images_to_dir(self, images, name, output_dir, number_padding, number_start, filename_delimiter, extension, quality,
                           optimize_image, lossless_webp, embed_metadata, overwrite_mode,
                           prompt, extra_pnginfo):
        """
        私有方法：将图像保存到指定目录
        
        参数：
        - images: 图像数组
        - name: 文件名前缀，空则不加前缀
        - output_dir: 输出目录路径
        - 其他参数: 各种保存选项
        
        返回：
        - results: 保存结果列表
        """
        results = []
        
        # 遍历图像数组，逐个保存
        for batch_number, image in enumerate(images):
            try:
                # 转换图像格式
                if isinstance(image, torch.Tensor):
                    # 将张量转换为numpy数组，并缩放到0-255范围
                    i = 255. * image.cpu().numpy()
                    # 转换为PIL图像对象，确保像素值在有效范围内
                    img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
                elif isinstance(image, np.ndarray):
                    if image.dtype != np.uint8:
                        image = (image * 255).astype(np.uint8)
                    img = Image.fromarray(image)
                elif isinstance(image, Image.Image):
                    img = image
                else:
                    raise ValueError("不支持的图像格式")
                
                # 生成文件名
                if overwrite_mode == "prefix_as_filename":
                    file_name = f"{name}.{extension}"
                else:
                    # 为批次中的每个图像添加批次号（如果有多个图像）
                    if len(images) > 1:
                        batch_name = f"{name}_{batch_number+1:03d}" if name.strip() else f"batch_{batch_number+1:03d}"
                    else:
                        batch_name = name
                    
                    file_name = self._generate_filename(
                        name=batch_name,
                        number_padding=number_padding,
                        number_start=number_start,
                        filename_delimiter=filename_delimiter,
                        extension=extension,
                        output_dir=output_dir
                    )
                
                # 准备元数据
                metadata = None
                if embed_metadata and not args.disable_metadata:
                    if extension.lower() == 'webp':
                        # WebP格式使用EXIF
                        img_exif = img.getexif()
                        if prompt:
                            img_exif[0x010f] = f"Prompt: {json.dumps(prompt)}"
                        if extra_pnginfo:
                            workflow_metadata = json.dumps(extra_pnginfo)
                            img_exif[0x010e] = f"Workflow: {workflow_metadata}"
                        metadata = img_exif.tobytes()
                    else:
                        # 其他格式使用PNG信息
                        metadata = PngInfo()
                        if prompt:
                            metadata.add_text("prompt", json.dumps(prompt))
                        if extra_pnginfo:
                            for key, value in extra_pnginfo.items():
                                metadata.add_text(key, json.dumps(value))
                
                # 构建完整文件路径
                output_file = os.path.join(output_dir, file_name)
                
                # 保存图像
                if extension.lower() in ["jpg", "jpeg"]:
                    img.save(
                        output_file,
                        quality=quality,
                        optimize=optimize_image
                    )
                elif extension.lower() == 'webp':
                    img.save(
                        output_file,
                        quality=quality,
                        lossless=lossless_webp,
                        exif=metadata
                    )
                elif extension.lower() == 'png':
                    img.save(
                        output_file,
                        pnginfo=metadata,
                        optimize=optimize_image,
                        compress_level=self.compress_level
                    )
                elif extension.lower() == 'bmp':
                    img.save(output_file)
                elif extension.lower() == 'tiff':
                    img.save(
                        output_file,
                        quality=quality,
                        optimize=optimize_image
                    )
                else:
                    img.save(
                        output_file,
                        pnginfo=metadata,
                        optimize=optimize_image
                    )
                
                print(f"图像已保存到: {output_file}")
                
                # 生成返回结果信息
                results.append({
                    "filename": file_name,
                    "subfolder": output_dir,
                    "type": self.type
                })
                
            except Exception as e:
                print(f"保存第 {batch_number+1} 个图像失败: {e}")
        
        return results


# 节点类映射：将类名映射到实际的类
NODE_CLASS_MAPPINGS = {
    "PD_SAVE_PATH2": PD_SAVE_PATH2,
}

# 节点显示名称映射：定义在UI中显示的节点名称
NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_SAVE_PATH2": "PD:SAVE_PATH_V2",
} 