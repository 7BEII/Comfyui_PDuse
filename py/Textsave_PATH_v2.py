import os
import re
import time

class PDTEXT_SAVE_PATH_V2:
    """
    文本保存节点 - 将文本内容保存到指定路径的文件中
    
    功能特性:
    - 支持自定义保存路径和文件名
    - 支持时间变量替换
    - 自动文件编号避免冲突
    - 多种文件格式支持
    - 错误处理和备用保存位置
    """
    
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"forceInput": True}),
                "path": ("STRING", {"default": './output/[time(%Y-%m-%d)]', "multiline": False}),
                "filename": ("STRING", {"default": "text"}),
                "filename_delimiter": ("STRING", {"default": "_"}),
                "filename_number_padding": ("INT", {"default": 4, "min": 0, "max": 9, "step": 1}),
                "file_extension": (["txt", "json", "csv", "log", "md"], {"default": "txt"}),
            },
            "hidden": {
                "prompt": "PROMPT", 
                "extra_pnginfo": "EXTRA_PNGINFO",
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ()
    RETURN_NAMES = ()
    FUNCTION = "save_text_file"
    CATEGORY = "PowerDiffusion/IO"
    OUTPUT_NODE = True

    def save_text_file(self, text, path, filename, filename_delimiter, filename_number_padding, file_extension, prompt=None, extra_pnginfo=None, unique_id=None):
        """
        保存文本文件到指定路径
        
        Args:
            text: 要保存的文本内容
            path: 保存路径，支持时间变量
            filename: 文件名
            filename_delimiter: 文件名分隔符
            filename_number_padding: 文件编号位数
            file_extension: 文件扩展名
            prompt: 提示信息（隐藏参数）
            extra_pnginfo: 额外PNG信息（隐藏参数）
            unique_id: 唯一ID（隐藏参数）
        """
        # 处理文件扩展名
        if not file_extension.startswith('.'):
            file_extension = f".{file_extension}"
        
        # 获取ComfyUI根目录
        comfy_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # 处理路径中的时间变量
        if '[time(' in path:
            try:
                time_format = path.split('[time(')[1].split(')]')[0]
                formatted_time = time.strftime(time_format)
                path = path.replace(f'[time({time_format})]', formatted_time)
            except:
                path = path.replace('[time(%Y-%m-%d)]', time.strftime("%Y-%m-%d"))
        
        # 处理路径
        if not os.path.isabs(path):
            path = os.path.join(comfy_dir, path)
        
        path = os.path.normpath(path)
        
        # 创建目录（如果不存在）
        os.makedirs(path, exist_ok=True)

        # 生成文件名
        if filename_number_padding == 0:
            full_filename = f"{filename}{file_extension}"
        else:
            pattern = re.compile(
                f"{re.escape(filename)}{re.escape(filename_delimiter)}(\\d{{{filename_number_padding},}}){re.escape(file_extension)}"
            )
            existing_files = [f for f in os.listdir(path) if pattern.match(f)] if os.path.exists(path) else []
            
            next_num = 1
            if existing_files:
                numbers = [int(pattern.match(f).group(1)) for f in existing_files]
                next_num = max(numbers) + 1 if numbers else 1
            
            # 自动调整位数：如果next_num位数超过padding，使用实际位数
            actual_padding = max(filename_number_padding, len(str(next_num)))
            full_filename = f"{filename}{filename_delimiter}{next_num:0{actual_padding}}{file_extension}"
            
            # 处理可能的冲突
            while os.path.exists(os.path.join(path, full_filename)):
                next_num += 1
                actual_padding = max(filename_number_padding, len(str(next_num)))
                full_filename = f"{filename}{filename_delimiter}{next_num:0{actual_padding}}{file_extension}"

        # 写入文件
        file_path = os.path.join(path, full_filename)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"[PDTEXT_SAVE_PATH_V2] 文本已保存到: {file_path}")
        except Exception as e:
            error_path = os.path.join(comfy_dir, "output", "txt", f"error_{filename}{file_extension}")
            with open(error_path, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"[PDTEXT_SAVE_PATH_V2] 无法保存到 {file_path}, 错误: {e}")
            print(f"[PDTEXT_SAVE_PATH_V2] 文本已保存到备用位置: {error_path}")

        return ()

    @staticmethod
    def IS_CHANGED(*args, **kwargs):
        return float("NaN")

# 节点映射
NODE_CLASS_MAPPINGS = {
    "PDTEXT_SAVE_PATH_V2": PDTEXT_SAVE_PATH_V2,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PDTEXT_SAVE_PATH_V2": "PDTEXT:SAVE_PATH_V2",
}
