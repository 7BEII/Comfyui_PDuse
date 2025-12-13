import json
import re


class PD_StringToCaptionJSON:
    """
    PD字符串转Caption JSON 节点
    功能：将输入的字符串转换为包含caption和lang字段的JSON格式字符串
    自动检测语言（中文/英文）
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "输入文本内容...",
                    "forceInput": True
                }),
            },
            "optional": {
                "lang": ("STRING", {
                    "default": "en",
                    "multiline": False,
                    "placeholder": "语言代码(en/zh/ja等)，留空为en"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("json_string",)
    FUNCTION = "convert_to_json"
    CATEGORY = "PDuse/Text"
    
    # 支持列表输入和输出
    INPUT_IS_LIST = {"text": True}
    OUTPUT_IS_LIST = (True,)
    
    def detect_language(self, text):
        """
        检测文本语言
        返回语言代码：en(英文), zh(中文), ja(日文) 等
        """
        if not text or not text.strip():
            return "en"
        
        # 检测中文字符
        chinese_pattern = re.compile(r'[\u4e00-\u9fff]')
        chinese_count = len(chinese_pattern.findall(text))
        
        # 检测日文字符（平假名、片假名）
        japanese_pattern = re.compile(r'[\u3040-\u309f\u30a0-\u30ff]')
        japanese_count = len(japanese_pattern.findall(text))
        
        # 检测韩文字符
        korean_pattern = re.compile(r'[\uac00-\ud7a3]')
        korean_count = len(korean_pattern.findall(text))
        
        # 检测英文字符
        english_pattern = re.compile(r'[a-zA-Z]')
        english_count = len(english_pattern.findall(text))
        
        # 根据字符数量判断语言
        total_chars = len(text)
        
        if chinese_count > total_chars * 0.3:
            return "zh"
        elif japanese_count > total_chars * 0.2:
            return "ja"
        elif korean_count > total_chars * 0.2:
            return "ko"
        else:
            return "en"
    
    def convert_to_json(self, text, lang="en"):
        """
        将文本转换为JSON格式字符串
        支持批处理：输入列表，输出列表
        """
        # 确保text是列表
        if not isinstance(text, list):
            text = [text]
        
        result_list = []
        
        # 处理每个文本
        for idx, caption_text in enumerate(text):
            try:
                # 类型转换和清理
                if isinstance(caption_text, list):
                    caption_text = str(caption_text[0]) if caption_text else ""
                if not isinstance(caption_text, str):
                    caption_text = str(caption_text)
                
                caption = caption_text.strip()
                
                # 如果文本为空，返回空的JSON
                if not caption:
                    result = {
                        "caption": "",
                        "lang": "en"
                    }
                    result_list.append(json.dumps(result, ensure_ascii=False))
                    continue
                
                # 处理语言参数（可能是单个值或列表）
                if isinstance(lang, list):
                    current_lang = lang[idx] if idx < len(lang) else lang[0] if lang else "en"
                else:
                    current_lang = lang
                
                # 确保lang是字符串
                if not isinstance(current_lang, str):
                    current_lang = str(current_lang) if current_lang else "en"
                
                # 检测语言
                if not current_lang or current_lang.strip() == "" or current_lang.strip().lower() == "auto":
                    detected_lang = self.detect_language(caption)
                else:
                    detected_lang = current_lang.strip().lower()
                
                # 构建JSON对象
                result = {
                    "caption": caption,
                    "lang": detected_lang
                }
                
                # 转换为JSON字符串（ensure_ascii=False 保留中文等非ASCII字符）
                json_string = json.dumps(result, ensure_ascii=False)
                result_list.append(json_string)
                
            except Exception as e:
                print(f"PD StringToCaptionJSON: 转换第{idx+1}项时出错: {e}")
                error_result = {
                    "caption": f"转换出错: {str(e)}",
                    "lang": "en"
                }
                result_list.append(json.dumps(error_result, ensure_ascii=False))
        
        print(f"PD StringToCaptionJSON: 批量转换完成，共处理 {len(result_list)} 项")
        
        return (result_list,)


# 注册节点
NODE_CLASS_MAPPINGS = {
    "PD_StringToCaptionJSON": PD_StringToCaptionJSON
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_StringToCaptionJSON": "PD 字符串转json (语言自动检测)"
}

