class PD_TextListUnpack:
    """
    PD文本列表解包 节点
    功能：将文本列表解包为单独的文本内容和文件名
    可与 PD_LoadTextsFromDir、PD_TextListSort 等节点配合使用
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text_list": ("STRING", {
                    "default": "",
                    "forceInput": True
                }),
                "filename_text": ("STRING", {
                    "default": "",
                    "forceInput": True
                }),
                "index": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 9999,
                    "step": 1,
                    "label": "提取索引(从0开始)"
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "INT")
    RETURN_NAMES = ("text_content", "filename", "total_count")
    FUNCTION = "unpack_text"
    CATEGORY = "PDuse/Text"
    
    # text_list 是列表输入
    INPUT_IS_LIST = {"text_list": True}

    def unpack_text(self, text_list, filename_text, index):
        """
        从文本列表中提取指定索引的文本和文件名
        """
        # 1. 检查输入
        if not text_list or len(text_list) == 0:
            return ("", "", 0)
        
        total_count = len(text_list)
        
        # 2. 解析文件名列表 - 添加类型检查
        filenames = []
        if filename_text:
            # 检查 filename_text 是否是列表（容错处理）
            if isinstance(filename_text, list):
                print("PD TextListUnpack: 警告 - filename_text 是列表，自动转换为字符串")
                filename_text = "\n".join(str(item) for item in filename_text if item)
            
            # 确保是字符串
            if not isinstance(filename_text, str):
                filename_text = str(filename_text)
            
            if filename_text.strip():
                filenames = [line.strip() for line in filename_text.strip().split('\n') if line.strip()]
        
        # 3. 检查索引范围
        if index < 0 or index >= total_count:
            print(f"PD TextListUnpack: 警告 - 索引 {index} 超出范围 (0-{total_count-1})")
            # 返回第一个或最后一个
            index = max(0, min(index, total_count - 1))
        
        # 4. 提取文本内容
        text_content = text_list[index]
        
        # 5. 提取文件名
        if index < len(filenames):
            filename = filenames[index]
        else:
            filename = f"file_{index}.txt"
            print(f"PD TextListUnpack: 警告 - 文件名不足，使用默认名称: {filename}")
        
        print(f"PD TextListUnpack: 已提取索引 {index}/{total_count-1} - {filename}")
        
        return (text_content, filename, total_count)


# 注册节点
NODE_CLASS_MAPPINGS = {
    "PD_TextListUnpack": PD_TextListUnpack
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_TextListUnpack": "PD文本列表解包"
}

