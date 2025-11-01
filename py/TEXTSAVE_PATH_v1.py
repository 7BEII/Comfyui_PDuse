"""
PD文本保存节点 V1
该模块提供了文本保存功能，支持字符串或列表输入
"""

import os
import re
import time
from datetime import datetime
import folder_paths

class PDTEXT_SAVE_PATH_V1:
    """
    文本保存节点 V1 - 将文本内容保存到指定路径的文件中
    
    功能特性:
    - 支持字符串或列表输入
    - 支持自定义输出文件夹
    - 支持数字位置控制（开头或末尾）
    - 支持自定义分隔符和文件名
    """
    
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"forceInput": True}),  # 支持字符串或列表
                "output_folder": ("STRING", {"default": "text_output"}),  # 输出文件夹
                "filename": ("STRING", {"default": "text"}),  # 文件名
                "delimiter": ("STRING", {"default": "_"}),  # 分隔符
                "padding": ("INT", {"default": 1, "min": 0, "max": 9, "step": 1}),  # 数字填充位数
                "number_start": ("BOOLEAN", {"default": False}),  # 数字是否在开头
                "file_extension": (["txt", "json", "csv", "log", "md"], {"default": "txt"}),  # 文件扩展名
            },
        }

    RETURN_TYPES = ()
    RETURN_NAMES = ()
    FUNCTION = "save_text_file"
    CATEGORY = "PD/Text"
    OUTPUT_NODE = True

    def save_text_file(self, text, output_folder, filename, delimiter, padding, number_start, file_extension):
        """
        保存文本文件到指定路径
        
        Args:
            text: 要保存的文本内容（字符串或列表）
            output_folder: 输出文件夹名称
            filename: 文件名
            delimiter: 分隔符
            padding: 数字填充位数
            number_start: 数字是否在开头
            file_extension: 文件扩展名
        """
        try:
            # 处理输入数据
            if isinstance(text, str):
                # 尝试解析为列表（如果是JSON格式）
                try:
                    import json
                    text_list = json.loads(text)
                    if not isinstance(text_list, list):
                        text_list = [str(text)]
                except:
                    # 如果不是JSON，按行分割或作为单个文本
                    if '\n' in text and len(text.split('\n')) > 1:
                        text_list = [line.strip() for line in text.split('\n') if line.strip()]
                    else:
                        text_list = [text]
            elif isinstance(text, list):
                text_list = [str(item) for item in text]
            else:
                text_list = [str(text)]
            
            # 处理文件扩展名
            if not file_extension.startswith('.'):
                file_extension = f".{file_extension}"
            
            # 创建输出目录
            output_path = os.path.join(self.output_dir, output_folder)
            os.makedirs(output_path, exist_ok=True)
            
            saved_files = []
            
            # 为每个文本项保存文件
            for i, text_content in enumerate(text_list):
                if not text_content.strip():  # 跳过空内容
                    continue
                
                # 生成文件名
                if padding == 0:
                    # 不使用数字编号
                    if len(text_list) > 1:
                        full_filename = f"{filename}_{i+1}{file_extension}"
                    else:
                        full_filename = f"{filename}{file_extension}"
                else:
                    # 使用数字编号
                    if len(text_list) > 1:
                        # 多个文本时，使用索引编号
                        counter = i + 1
                    else:
                        # 单个文本时，查找现有文件的最大编号
                        counter = self._get_next_counter(output_path, filename, delimiter, padding, number_start, file_extension)
                    
                    # 根据number_start生成文件名
                    # 自动调整位数：如果counter位数超过padding，使用实际位数
                    actual_padding = max(padding, len(str(counter)))
                    if number_start:
                        # 数字在开头: 001_filename.txt
                        full_filename = f"{counter:0{actual_padding}}{delimiter}{filename}{file_extension}"
                    else:
                        # 数字在末尾: filename_001.txt
                        full_filename = f"{filename}{delimiter}{counter:0{actual_padding}}{file_extension}"
                
                # 确保文件名唯一
                original_filename = full_filename
                counter_suffix = 1
                while os.path.exists(os.path.join(output_path, full_filename)):
                    name_part, ext_part = os.path.splitext(original_filename)
                    full_filename = f"{name_part}_dup{counter_suffix}{ext_part}"
                    counter_suffix += 1
                
                # 写入文件
                file_path = os.path.join(output_path, full_filename)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text_content)
                
                saved_files.append(file_path)
                print(f"[PDTEXT_SAVE_PATH_V1] 文本已保存到: {file_path}")
            
            # 不需要返回值
            return ()
                
        except Exception as e:
            print(f"[PDTEXT_SAVE_PATH_V1] 保存文本时发生错误: {e}")
            return ()

    def _get_next_counter(self, output_path, filename, delimiter, padding, number_start, file_extension):
        """
        获取下一个可用的计数器值
        """
        try:
            # 根据number_start决定正则表达式模式
            if number_start:
                # 数字在开头: 001_filename.txt (匹配至少padding位数字)
                pattern = re.compile(
                    f"(\\d{{{padding},}}){re.escape(delimiter)}{re.escape(filename)}{re.escape(file_extension)}"
                )
            else:
                # 数字在末尾: filename_001.txt (匹配至少padding位数字)
                pattern = re.compile(
                    f"{re.escape(filename)}{re.escape(delimiter)}(\\d{{{padding},}}){re.escape(file_extension)}"
                )
            
            existing_files = [f for f in os.listdir(output_path) if pattern.match(f)] if os.path.exists(output_path) else []
            
            if existing_files:
                numbers = [int(pattern.match(f).group(1)) for f in existing_files]
                return max(numbers) + 1
            else:
                return 1
                
        except Exception as e:
            print(f"[PDTEXT_SAVE_PATH_V1] 获取计数器失败: {e}")
            return 1

# 节点类映射：将类名映射到实际的类
NODE_CLASS_MAPPINGS = {
    "PDTEXT_SAVE_PATH_V1": PDTEXT_SAVE_PATH_V1,
}

# 节点显示名称映射：定义在UI中显示的节点名称
NODE_DISPLAY_NAME_MAPPINGS = {
    "PDTEXT_SAVE_PATH_V1": "PDTEXT:SAVE_PATH_V1",
}
