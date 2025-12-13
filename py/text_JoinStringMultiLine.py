"""
PD Nodes for ComfyUI
包含功能：
1. PD Join String Multi Line: 将两个字符串合并，中间用换行符分隔。
2. PD String Line Count: 统计字符串中有多少行有效内容。
"""

class PD_JoinStringMultiLine:
    """
    节点 1: 字符串合并 (多行)
    作用: 将输入 A 和输入 B 合并，并在中间插入换行符。
    """
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                # forceInput=True 强制显示左侧输入点
                "string_1": ("STRING", {"forceInput": True, "multiline": True, "default": ""}),
                "string_2": ("STRING", {"forceInput": True, "multiline": True, "default": ""}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("combined_string",)
    FUNCTION = "join_strings"
    CATEGORY = "PD Nodes"

    def join_strings(self, string_1, string_2):
        # 核心逻辑：中间加一个换行符 \n
        s1 = str(string_1) if string_1 is not None else ""
        s2 = str(string_2) if string_2 is not None else ""
        
        # 如果第一项为空，直接返回第二项，避免头部出现空行
        if s1 == "":
            return (s2,)
        if s2 == "":
            return (s1,)
            
        result = s1 + "\n" + s2
        return (result,)


class PD_StringLineCount:
    """
    接收字符串输入。
    如果输入是列表(Batch)，则统计列表中的项目数量。
    如果输入是单个多行文本，则统计行数。
    最终只输出一个整数 (Int)。
    """
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text": ("STRING", {"forceInput": True, "multiline": True}),
            }
        }

    # 【关键修改】开启列表模式，防止对列表中的每一项单独运行
    INPUT_IS_LIST = True

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("line_count",)
    FUNCTION = "count_lines"
    
    CATEGORY = "PD Nodes"

    def count_lines(self, text):
        # text 现在是一个列表 (list)
        if not text:
            return (0,)
        
        # 获取列表长度 (即 Batch Size / 项目总数)
        # 这样输入 3 个文件名时，就会直接返回 int 3
        count = len(text)
        
        return (count,)

# --------------------------------------------------------------------------------
# 节点注册映射
# --------------------------------------------------------------------------------

NODE_CLASS_MAPPINGS = {
    "PD_JoinStringMultiLine": PD_JoinStringMultiLine,
    "PD_StringLineCount": PD_StringLineCount
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_JoinStringMultiLine": "PD Join String Multi Line",
    "PD_StringLineCount": "PD String Line Count"
}