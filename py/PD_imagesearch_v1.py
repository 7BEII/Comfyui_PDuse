import os
import torch
import numpy as np
from pathlib import Path
from PIL import Image, ImageOps
import folder_paths
import unicodedata

class PD_ImageSearch:
    """
    图片搜索节点：根据关键字在指定文件夹中搜索图片
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_path": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "输入文件夹路径"
                }),
                "word": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "搜索关键字"
                }),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("images", "image_names", "txts")
    FUNCTION = "search_images"
    CATEGORY = "PandyTool/Image"
    DESCRIPTION = "根据关键字在指定文件夹中搜索图片并返回所有匹配的图片列表和txt文本内容"
    OUTPUT_IS_LIST = (True, True, True)

    def search_images(self, input_path, word):
        """
        图片搜索主函数
        """
        try:
            # 检查输入参数
            input_path = input_path.strip()
            word = word.strip()
            
            if not input_path:
                raise ValueError("请提供输入文件夹路径")
            
            if not word:
                raise ValueError("请提供搜索关键字")
            
            # 检查文件夹是否存在
            input_folder = Path(input_path)
            if not input_folder.exists():
                raise ValueError(f"文件夹不存在: {input_path}")
            
            if not input_folder.is_dir():
                raise ValueError(f"提供的路径不是文件夹: {input_path}")
            
            # 支持的图片格式
            supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'}
            
            # 搜索包含关键字的图片文件和txt文件
            matching_image_files = []
            matching_txt_files = []
            
            # 预处理搜索关键字：归一化并转小写
            word_norm = unicodedata.normalize('NFKC', word).casefold()
            
            try:
                # 遍历文件夹中的所有文件
                for file_path in input_folder.iterdir():
                    if file_path.is_file():
                        # 归一化文件名并检查是否包含关键字
                        file_name_norm = unicodedata.normalize('NFKC', file_path.name).casefold()
                        
                        if word_norm in file_name_norm:
                            # 检查文件扩展名
                            if file_path.suffix.lower() in supported_formats:
                                matching_image_files.append(file_path)
                            elif file_path.suffix.lower() == '.txt':
                                matching_txt_files.append(file_path)
                
            except Exception as e:
                raise ValueError(f"无法读取文件夹内容: {str(e)}")
            
            if not matching_image_files:
                raise ValueError(f"在文件夹中未找到包含关键字 '{word}' 的图片文件")
            
            # 按文件名排序，确保结果的一致性
            matching_image_files.sort(key=lambda x: x.name.lower())
            matching_txt_files.sort(key=lambda x: x.name.lower())
            
            # 加载所有匹配的图片
            images = []
            image_names = []
            
            for file_path in matching_image_files:
                try:
                    image = Image.open(str(file_path))
                    
                    # 转换为RGB模式（如果不是的话）
                    if image.mode != 'RGB':
                        image = image.convert('RGB')
                    
                    # 处理EXIF旋转信息
                    image = ImageOps.exif_transpose(image)
                    
                    # 转换为numpy数组
                    image_array = np.array(image).astype(np.float32) / 255.0
                    
                    images.append(image_array)
                    image_names.append(file_path.stem)
                    
                except Exception as e:
                    print(f"跳过无法加载的图片 {file_path.name}: {str(e)}")
                    continue
            
            if not images:
                raise ValueError("没有成功加载任何图片")
            
            # 将每张图片转换为单独的张量 (1HWC格式)
            image_tensors = []
            for image_array in images:
                # 添加batch维度
                if len(image_array.shape) == 3:
                    image_array = np.expand_dims(image_array, axis=0)
                image_tensor = torch.from_numpy(image_array)
                image_tensors.append(image_tensor)
            
            # 读取所有匹配的txt文件内容
            txt_contents = []
            if matching_txt_files:
                for txt_file in matching_txt_files:
                    try:
                        with open(str(txt_file), 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                            txt_contents.append(content)
                    except Exception as e:
                        print(f"跳过无法读取的txt文件 {txt_file.name}: {str(e)}")
                        txt_contents.append(f"读取错误: {str(e)}")
            else:
                # 如果没有找到txt文件，返回"notxts"
                txt_contents = ["notxts"]
            
            # 返回图片张量列表、文件名列表和txt内容列表
            return (image_tensors, image_names, txt_contents)
            
        except Exception as e:
            # 如果出现错误，返回一个空白图片和错误信息
            error_message = f"错误: {str(e)}"
            print(f"PD_ImageSearch 错误: {error_message}")
            
            # 创建一个空白的错误图片 (1x1像素的红色图片)
            error_image = np.array([[[[1.0, 0.0, 0.0]]]], dtype=np.float32)  # 红色像素，BHWC格式
            error_tensor = torch.from_numpy(error_image)
            
            return ([error_tensor], [error_message], ["notxts"])

# 节点映射字典
NODE_CLASS_MAPPINGS = {
    "PD_ImageSearch": PD_ImageSearch
}

# 节点显示名称映射
NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_ImageSearch": "PD:imagesearch_v1"
}
