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
                     "filename_prefix": ("STRING", {"default": "R"}),  # 文件名前缀
                     "custom_output_dir": ("STRING", {"default": "", "optional": True}),  # 自定义输出目录(可选)
                     "format": (["png", "jpg"], {"default": "png"}),  # 图像格式选择
                     "numberfront": ("BOOLEAN", {"default": True}),  # 数字位置：True=前面，False=后面
                     "separator": ("STRING", {"default": "_"}),  # 分割符，默认为下划线
                     "show_preview": ("BOOLEAN", {"default": True}),  # 是否在前端显示预览图
                     },
                "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},  # 隐藏的提示信息和额外PNG信息
                }

    RETURN_TYPES = ()  # 无返回值类型
    FUNCTION = "save_images"  # 主要执行函数名
    OUTPUT_NODE = True  # 标识为输出节点
    CATEGORY = "PD/Image"  # 节点分类

    def save_images(self, images, filename_prefix="R", prompt=None, extra_pnginfo=None, 
                   custom_output_dir="", format="png", numberfront=True, separator="_", show_preview=True):
        """
        保存图像主方法
        """
        try:
            # 判断是否有自定义保存路径
            if not custom_output_dir:
                # 没有自定义路径时，使用默认路径，并创建以文件名和日期为标识的子文件夹
                date_str = datetime.now().strftime("%Y-%m-%d")  # 生成当前日期字符串
                custom_output_dir = os.path.join(self.output_dir, f"{filename_prefix}_{date_str}")
            
            # -------------------------------------------------------------------------
            # [关键修改] 
            # 无论路径是自动生成的，还是用户自定义填写的，都强制尝试创建文件夹
            # exist_ok=True 表示如果文件夹已存在，不会报错，继续执行
            # -------------------------------------------------------------------------
            try:
                os.makedirs(custom_output_dir, exist_ok=True)
            except Exception as e:
                print(f"创建目录失败: {custom_output_dir}, 错误: {e}")
                # 如果创建目录失败，可能因为权限问题，但这通常会让后续保存步骤报错
            
            # 调用私有方法保存图像到自定义目录，获取保存结果
            results = self._save_images_to_dir(images, filename_prefix, prompt, extra_pnginfo, 
                                   custom_output_dir, format, numberfront, separator)
            
            # 根据show_preview参数决定返回值
            if show_preview:
                # 返回UI预览信息，前端会显示图像预览
                return {"ui": {"images": results}}
            else:
                # 返回空UI字典，确保节点执行完成但不显示预览图
                return {"ui": {}}
        
        except Exception as e:
            print(f"保存图像时发生错误: {e}")
            return {"ui": {}}

    def _save_images_to_dir(self, images, filename_prefix, prompt, extra_pnginfo, 
                           output_dir, format, numberfront, separator):
        """
        私有方法：将图像保存到指定目录
        """
        results = list()
        
        # 根据格式确定文件扩展名
        extension = f".{format.lower()}"
        
        # 获取下一个可用的计数器值（从1到100）
        counter = self._get_next_counter(output_dir, filename_prefix, extension, 
                                       numberfront, separator)
            
        # 遍历图像数组，逐个保存
        for (batch_number, image) in enumerate(images):
            # 将张量转换为numpy数组，并缩放到0-255范围
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
            
            # 根据numberfront生成文件名
            if numberfront:
                # 数字在前面：1_R.ext
                file = f"{counter}{separator}{filename_prefix}{extension}"
            else:
                # 数字在后面：R_1.ext
                file = f"{filename_prefix}{separator}{counter}{extension}"
            
            # 根据格式保存图像
            if format.lower() == "png":
                # PNG格式：保存为RGBA，包含元数据和指定的压缩级别
                img.save(os.path.join(output_dir, file), 
                        pnginfo=metadata, 
                        compress_level=self.compress_level,
                        format='PNG')
            else:  # JPG格式
                # JPG格式：保存为RGB，设置质量
                img.save(os.path.join(output_dir, file), 
                        format='JPEG', 
                        quality=95,  # JPG质量设置
                        optimize=True)
                
            # 生成返回结果信息，包含文件名和路径
            results.append({
                "filename": file,         # 保存的文件名
                "subfolder": output_dir, # 子文件夹路径
                "type": self.type         # 文件类型
            })
            counter += 1  # 递增计数器
        
        return results
    
    def _get_next_counter(self, output_dir, filename_prefix, extension, numberfront, separator):
        """
        获取下一个可用的计数器值
        """
        try:
            # 获取目录中的所有文件
            existing_files = set(os.listdir(output_dir)) if os.path.exists(output_dir) else set()
            
            # 从1开始递增，找到第一个不存在的文件名
            counter = 1
            while True:
                if numberfront:
                    # 数字在前面：1_R.ext
                    filename = f"{counter}{separator}{filename_prefix}{extension}"
                else:
                    # 数字在后面：R_1.ext
                    filename = f"{filename_prefix}{separator}{counter}{extension}"
                
                # 如果文件不存在，返回这个计数器
                if filename not in existing_files:
                    return counter
                
                counter += 1
            
        except Exception as e:
            print(f"读取目录失败: {e}")
            return 1


# 节点类映射：将类名映射到实际的类
NODE_CLASS_MAPPINGS = {
    "PD_imagesave_path": PD_imagesave_path,
}

# 节点显示名称映射：定义在UI中显示的节点名称
NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_imagesave_path": "PD_save path",
}