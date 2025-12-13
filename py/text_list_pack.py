class PD_TextListPack:
    """
    PD文本列表打包 节点
    功能：将多个文本内容和对应的文件名打包成列表格式
    可与 PD_LoadTextsFromDir、PD_TextListSort 等节点配合使用
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
            "optional": {
                "text_1": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "文本内容1"
                }),
                "filename_1": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "文件名1"
                }),
                "text_2": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "文本内容2（可选）"
                }),
                "filename_2": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "文件名2（可选）"
                }),
                "text_3": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "文本内容3（可选）"
                }),
                "filename_3": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "文件名3（可选）"
                }),
                "text_4": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "文本内容4（可选）"
                }),
                "filename_4": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "文件名4（可选）"
                }),
                "text_5": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "文本内容5（可选）"
                }),
                "filename_5": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "文件名5（可选）"
                }),
                # 支持直接接收列表输入
                "input_text_list": ("STRING", {
                    "default": "",
                    "forceInput": True,
                    "tooltip": "可选：直接输入text_list列表（会与单独输入的文本合并）"
                }),
                "input_filename_text": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "可选：输入filename_text（与text_list配套）"
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "INT")
    RETURN_NAMES = ("text_list", "filename_text", "count")
    FUNCTION = "pack_texts"
    CATEGORY = "PDuse/Text"
    
    # text_list 是列表输入和输出
    INPUT_IS_LIST = {"input_text_list": True}
    OUTPUT_IS_LIST = (True, False, False)

    def pack_texts(self, text_1="", filename_1="", 
                   text_2="", filename_2="",
                   text_3="", filename_3="",
                   text_4="", filename_4="",
                   text_5="", filename_5="",
                   input_text_list=None,
                   input_filename_text=""):
        """
        将多个文本和文件名打包成列表
        支持：1. 单独输入（text_1-5）2. 列表输入（input_text_list）3. 两者混合
        """
        text_list = []
        filename_list = []
        
        # 第一步：处理列表输入（如果有）
        if input_text_list and len(input_text_list) > 0:
            # 添加列表中的所有文本
            for item in input_text_list:
                if item and (not isinstance(item, str) or item.strip()):
                    text_list.append(str(item))
            
            # 解析对应的文件名
            if input_filename_text:
                # 类型检查
                if isinstance(input_filename_text, list):
                    input_filename_text = "\n".join(str(item) for item in input_filename_text if item)
                if not isinstance(input_filename_text, str):
                    input_filename_text = str(input_filename_text)
                
                if input_filename_text.strip():
                    parsed_filenames = [line.strip() for line in input_filename_text.strip().split('\n') if line.strip()]
                    filename_list.extend(parsed_filenames)
        
        # 第二步：处理单独输入的文本
        items = [
            (text_1, filename_1),
            (text_2, filename_2),
            (text_3, filename_3),
            (text_4, filename_4),
            (text_5, filename_5),
        ]
        
        for text, filename in items:
            # 类型检查和转换 - 确保兼容性
            if isinstance(text, list):
                text = "\n".join(str(item) for item in text if item)
            if not isinstance(text, str):
                text = str(text) if text else ""
            
            if isinstance(filename, list):
                filename = str(filename[0]) if filename else ""
            if not isinstance(filename, str):
                filename = str(filename) if filename else ""
            
            # 只添加非空的文本
            if text and text.strip():
                text_list.append(text)
                # 如果文件名为空，使用默认名称
                if filename and filename.strip():
                    filename_list.append(filename.strip())
                else:
                    filename_list.append(f"file_{len(text_list)}.txt")
        
        # 第三步：补齐文件名（如果文件名数量不够）
        while len(filename_list) < len(text_list):
            filename_list.append(f"file_{len(filename_list)+1}.txt")
        
        # 如果没有任何内容，返回空
        if not text_list:
            print("PD TextListPack: 警告 - 没有有效的文本内容")
            return ([""], "", 0)
        
        # 组合文件名列表为文本
        filename_text = "\n".join(filename_list)
        
        print(f"PD TextListPack: 已打包 {len(text_list)} 个文本")
        print(f"  文件名: {', '.join(filename_list)}")
        
        return (text_list, filename_text, len(text_list))


# 注册节点
NODE_CLASS_MAPPINGS = {
    "PD_TextListPack": PD_TextListPack
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_TextListPack": "PD文本列表打包"
}

