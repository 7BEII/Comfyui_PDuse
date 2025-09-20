import re

class PD_empty_word:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_string": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "输入需要格式化的文本..."
                }),
                "line_break_keyword": ("STRING", {
                    "default": "safetensors",
                    "placeholder": "输入换行关键词"
                }),
            },
            "optional": {
                "remove_empty_lines": ("BOOLEAN", {"default": True}),
                "trim_whitespace": ("BOOLEAN", {"default": True}),
            }
        }
  
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("formatted_string",)
    FUNCTION = "format_string"
    CATEGORY = "utils/text"
  
    def format_string(self, input_string, line_break_keyword, remove_empty_lines=True, trim_whitespace=True):
        """
        格式化字符串，去除多余空格，按关键词换行
      
        Args:
            input_string: 输入的原始字符串
            line_break_keyword: 用于换行的关键词
            remove_empty_lines: 是否移除空行
            trim_whitespace: 是否修剪首尾空白
      
        Returns:
            格式化后的字符串
        """
        if not input_string:
            return ("",)
      
        try:
            # 首先去除所有多余的空白字符，但保留单个空格
            # 将多个连续空白字符（包括空格、制表符、换行符）替换为单个空格
            cleaned_string = re.sub(r'\s+', ' ', input_string)
          
            # 去除首尾空白
            if trim_whitespace:
                cleaned_string = cleaned_string.strip()
          
            # 如果没有关键词，直接返回清理后的字符串
            if not line_break_keyword:
                return (cleaned_string,)
          
            # 在关键词后添加换行符
            # 使用正则表达式查找关键词，并在其后添加换行符
            pattern = f'({re.escape(line_break_keyword)})'
            formatted_string = re.sub(pattern, r'\1\n', cleaned_string)
          
            # 处理结果行
            lines = formatted_string.split('\n')
            processed_lines = []
          
            for line in lines:
                # 去除每行的首尾空白
                if trim_whitespace:
                    line = line.strip()
              
                # 根据选项决定是否保留空行
                if remove_empty_lines:
                    if line:  # 只添加非空行
                        processed_lines.append(line)
                else:
                    processed_lines.append(line)
          
            # 重新组合字符串
            result = '\n'.join(processed_lines)
          
            return (result,)
          
        except Exception as e:
            print(f"StringFormatter错误: {e}")
            return (input_string,)  # 发生错误时返回原始字符串

# 节点映射字典
NODE_CLASS_MAPPINGS = {
    "PD_empty_word": PD_empty_word,
}

# 节点显示名称映射
NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_empty_word": "PD_empty_word",
}
