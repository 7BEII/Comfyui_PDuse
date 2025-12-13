class PD_TextListStringAddWord:
    """
    PD文本列表添加词语 节点
    功能：批量为字符串添加词语（前缀、后缀、插入等）
    支持列表批处理，保持输入输出顺序一致
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "输入文本内容（支持列表批处理）",
                    "forceInput": True
                }),
            },
            "optional": {
                "add_prefix": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "在文本前添加的词语（可选）"
                }),
                "add_suffix": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "在文本后添加的词语（可选）"
                }),
                "replace_from": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "要替换的词语（每行一个，可选）"
                }),
                "replace_to": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "替换为的词语（每行一个，与上面对应）"
                }),
                "insert_word": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "要插入的词语（可选）"
                }),
                "insert_position": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 10000,
                    "step": 1,
                    "display": "number",
                    "tooltip": "插入位置（字符索引，0表示开头）"
                }),
                "separator": ("STRING", {
                    "default": " ",
                    "multiline": False,
                    "placeholder": "词语之间的分隔符（默认空格）"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "add_word"
    CATEGORY = "PDuse/Text"
    
    # 支持列表输入和输出
    INPUT_IS_LIST = {"text": True}
    OUTPUT_IS_LIST = (True,)
    
    def add_word(self, text, add_prefix="", add_suffix="", replace_from="", 
                 replace_to="", insert_word="", insert_position=0, separator=" "):
        """
        批量为文本添加词语
        支持前缀、后缀、替换、插入等操作
        """
        # 确保text是列表
        if not isinstance(text, list):
            text = [text]
        
        result_list = []
        
        # 解析替换词列表（只解析一次，应用到所有项）
        from_words = []
        to_words = []
        if replace_from:
            if isinstance(replace_from, list):
                replace_from = replace_from[0] if replace_from else ""
            if isinstance(replace_from, str) and replace_from.strip():
                from_words = [line.strip() for line in replace_from.strip().split('\n') if line.strip()]
                
                if replace_to:
                    if isinstance(replace_to, list):
                        replace_to = replace_to[0] if replace_to else ""
                    if isinstance(replace_to, str):
                        to_words = [line.strip() for line in replace_to.strip().split('\n') if line.strip()]
                
                # 确保替换列表长度一致
                while len(to_words) < len(from_words):
                    to_words.append("")  # 如果替换词不够，用空字符串替换（即删除）
        
        # 处理分隔符
        sep = separator
        if isinstance(sep, list):
            sep = sep[0] if sep else " "
        if not isinstance(sep, str):
            sep = str(sep) if sep else " "
        
        # 处理每个文本
        for idx, item_text in enumerate(text):
            try:
                # 类型转换
                if isinstance(item_text, list):
                    item_text = str(item_text[0]) if item_text else ""
                if not isinstance(item_text, str):
                    item_text = str(item_text)
                
                processed_text = item_text
                
                # 1. 执行词语替换
                for from_word, to_word in zip(from_words, to_words):
                    if from_word:
                        processed_text = processed_text.replace(from_word, to_word)
                
                # 2. 插入词语（在指定位置）
                insert_val = insert_word
                if isinstance(insert_val, list):
                    insert_val = insert_val[0] if insert_val else ""
                if insert_val and isinstance(insert_val, str) and insert_val.strip():
                    insert_text = insert_val.strip()
                    insert_pos = insert_position
                    if isinstance(insert_pos, list):
                        insert_pos = insert_pos[0] if insert_pos else 0
                    if not isinstance(insert_pos, int):
                        insert_pos = int(insert_pos) if insert_pos else 0
                    
                    # 确保位置在有效范围内
                    insert_pos = max(0, min(insert_pos, len(processed_text)))
                    processed_text = processed_text[:insert_pos] + insert_text + processed_text[insert_pos:]
                
                # 3. 添加前缀
                prefix_val = add_prefix
                if isinstance(prefix_val, list):
                    prefix_val = prefix_val[0] if prefix_val else ""
                if prefix_val and isinstance(prefix_val, str) and prefix_val.strip():
                    prefix = prefix_val.strip()
                    # 如果需要分隔符且processed_text不为空
                    if processed_text and not prefix.endswith(sep) and not prefix.endswith(","):
                        prefix += sep
                    processed_text = prefix + processed_text
                
                # 4. 添加后缀
                suffix_val = add_suffix
                if isinstance(suffix_val, list):
                    suffix_val = suffix_val[0] if suffix_val else ""
                if suffix_val and isinstance(suffix_val, str) and suffix_val.strip():
                    suffix = suffix_val.strip()
                    # 如果需要分隔符
                    if processed_text and not suffix.startswith(sep) and not suffix.startswith(","):
                        suffix = sep + suffix
                    processed_text = processed_text + suffix
                
                result_list.append(processed_text)
                
            except Exception as e:
                print(f"PD TextListStringAddWord: 处理第{idx+1}项时出错: {e}")
                # 出错时保持原文本
                result_list.append(str(item_text) if item_text else "")
        
        print(f"PD TextListStringAddWord: 批量处理完成，共处理 {len(result_list)} 项")
        
        return (result_list,)


# 注册节点
NODE_CLASS_MAPPINGS = {
    "PD_TextListStringAddWord": PD_TextListStringAddWord
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_TextListStringAddWord": "PD text_list_string_add word"
}

