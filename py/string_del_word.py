import re

class PD_del_word:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_string": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "输入需要处理的文本..."
                }),
                "keyword": ("STRING", {
                    "default": "",
                    "placeholder": "输入要删除的关键词"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("result_string",)
    FUNCTION = "delete_keyword"
    CATEGORY = "utils/text"
    
    def delete_keyword(self, input_string, keyword):
        """
        从字符串中删除指定关键词
        
        Args:
            input_string: 输入的原始字符串
            keyword: 要删除的关键词
        
        Returns:
            删除关键词后的字符串
        """
        if not input_string or not keyword:
            return (input_string,)
        
        try:
            # 直接替换关键词为空字符串
            result_string = input_string.replace(keyword, "")
            
            return (result_string,)
            
        except Exception as e:
            print(f"PD_del_word错误: {e}")
            return (input_string,)

# 节点映射字典
NODE_CLASS_MAPPINGS = {
    "PD_del_word": PD_del_word,
}

# 节点显示名称映射
NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_del_word": "PD_del_word",
}
