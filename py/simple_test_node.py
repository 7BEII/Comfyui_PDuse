"""
简单测试节点 - 用于排除导入问题
"""

class PD_SimpleTest:
    """简单的测试节点"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"default": "测试文本"}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_text",)
    FUNCTION = "process"
    CATEGORY = "PD/测试"
    
    def process(self, text):
        """简单的文本处理"""
        return (f"处理结果: {text}",)

# 节点映射
NODE_CLASS_MAPPINGS = {
    "PD_SimpleTest": PD_SimpleTest,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_SimpleTest": "PD简单测试",
} 