import json
import re


class PD_CaptionJSONEditor:
    """
    PD Caption JSON编辑器 节点
    功能：解析JSON格式的caption字符串，允许修改caption内容和语言
    支持替换词语、添加前后缀等操作
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "json_string": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": '输入JSON字符串，例如：\n{\n  "caption": "...",\n  "lang": "en"\n}',
                    "forceInput": True
                }),
            },
            "optional": {
                "new_caption": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "留空则使用原caption，填写则完全替换caption内容"
                }),
                "add_prefix": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "在caption前添加的文本（可选）"
                }),
                "add_suffix": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "在caption后添加的文本（可选）"
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
                "new_lang": ("STRING", {
                    "default": "en",
                    "multiline": False,
                    "placeholder": "语言代码(en/zh/ja等)，默认en"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("json_string", "caption", "lang")
    FUNCTION = "edit_caption_json"
    CATEGORY = "PDuse/Text"
    
    # 支持列表输入和输出
    INPUT_IS_LIST = {"json_string": True}
    OUTPUT_IS_LIST = (True, True, True)
    
    def edit_caption_json(self, json_string, new_caption="", add_prefix="", 
                         add_suffix="", replace_from="", replace_to="", new_lang="en"):
        """
        编辑Caption JSON字符串
        支持批处理：输入列表，输出列表
        """
        # 确保json_string是列表
        if not isinstance(json_string, list):
            json_string = [json_string]
        
        json_output_list = []
        caption_list = []
        lang_list = []
        
        # 解析替换词列表（只解析一次，应用到所有项）
        from_words = []
        to_words = []
        if replace_from and (isinstance(replace_from, str) and replace_from.strip()):
            from_words = [line.strip() for line in replace_from.strip().split('\n') if line.strip()]
            to_words = [line.strip() for line in replace_to.strip().split('\n') if line.strip()] if replace_to else []
            # 确保替换列表长度一致
            while len(to_words) < len(from_words):
                to_words.append("")  # 如果替换词不够，用空字符串替换（即删除）
        
        # 处理每个JSON字符串
        for idx, json_str in enumerate(json_string):
            try:
                # 类型转换
                if isinstance(json_str, list):
                    json_str = str(json_str[0]) if json_str else ""
                if not isinstance(json_str, str):
                    json_str = str(json_str)
                
                # 解析输入的JSON字符串
                try:
                    data = json.loads(json_str)
                    caption = data.get("caption", "")
                    lang = data.get("lang", "en")
                except json.JSONDecodeError as e:
                    print(f"PD CaptionJSONEditor: 第{idx+1}项JSON解析失败: {e}")
                    # 尝试直接作为普通文本处理
                    caption = json_str.strip()
                    lang = "en"
                
                # 处理caption内容
                # 1. 如果提供了新的caption，则完全替换
                if new_caption:
                    if isinstance(new_caption, list):
                        current_new_caption = new_caption[idx] if idx < len(new_caption) else ""
                    else:
                        current_new_caption = new_caption
                    
                    if isinstance(current_new_caption, str) and current_new_caption.strip():
                        caption = current_new_caption.strip()
                
                # 2. 执行词语替换
                for from_word, to_word in zip(from_words, to_words):
                    if from_word:
                        caption = caption.replace(from_word, to_word)
                
                # 3. 添加前缀
                prefix_val = add_prefix
                if isinstance(prefix_val, list):
                    prefix_val = prefix_val[0] if prefix_val else ""
                if prefix_val and isinstance(prefix_val, str) and prefix_val.strip():
                    prefix = prefix_val.strip()
                    # 如果前缀后面需要空格且caption不为空
                    if caption and not prefix.endswith(" ") and not prefix.endswith(","):
                        prefix += " "
                    caption = prefix + caption
                
                # 4. 添加后缀
                suffix_val = add_suffix
                if isinstance(suffix_val, list):
                    suffix_val = suffix_val[0] if suffix_val else ""
                if suffix_val and isinstance(suffix_val, str) and suffix_val.strip():
                    suffix = suffix_val.strip()
                    # 如果后缀前面需要空格
                    if caption and not suffix.startswith(" ") and not suffix.startswith(","):
                        suffix = " " + suffix
                    caption = caption + suffix
                
                # 5. 修改语言代码
                lang_val = new_lang
                if isinstance(lang_val, list):
                    lang_val = lang_val[idx] if idx < len(lang_val) else (lang_val[0] if lang_val else "en")
                if lang_val and isinstance(lang_val, str) and lang_val.strip():
                    lang = lang_val.strip().lower()
                
                # 构建新的JSON对象
                result = {
                    "caption": caption,
                    "lang": lang
                }
                
                # 转换为JSON字符串
                json_output = json.dumps(result, ensure_ascii=False)
                
                json_output_list.append(json_output)
                caption_list.append(caption)
                lang_list.append(lang)
                
            except Exception as e:
                print(f"PD CaptionJSONEditor: 编辑第{idx+1}项时出错: {e}")
                error_result = {
                    "caption": f"编辑出错: {str(e)}",
                    "lang": "en"
                }
                error_json = json.dumps(error_result, ensure_ascii=False)
                json_output_list.append(error_json)
                caption_list.append(f"错误: {str(e)}")
                lang_list.append("en")
        
        print(f"PD CaptionJSONEditor: 批量编辑完成，共处理 {len(json_output_list)} 项")
        
        return (json_output_list, caption_list, lang_list)


class PD_CaptionJSONParser:
    """
    PD Caption JSON解析器 节点
    功能：解析JSON格式的caption字符串，提取caption和lang字段
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "json_string": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": '输入JSON字符串',
                    "forceInput": True
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("caption", "lang")
    FUNCTION = "parse_json"
    CATEGORY = "PDuse/Text"
    
    # 支持列表输入和输出
    INPUT_IS_LIST = {"json_string": True}
    OUTPUT_IS_LIST = (True, True)
    
    def parse_json(self, json_string):
        """
        解析Caption JSON字符串，提取caption和lang
        支持批处理：输入列表，输出列表
        """
        # 确保json_string是列表
        if not isinstance(json_string, list):
            json_string = [json_string]
        
        caption_list = []
        lang_list = []
        
        # 处理每个JSON字符串
        for idx, json_str in enumerate(json_string):
            try:
                # 类型转换
                if isinstance(json_str, list):
                    json_str = str(json_str[0]) if json_str else ""
                if not isinstance(json_str, str):
                    json_str = str(json_str)
                
                # 解析JSON
                data = json.loads(json_str)
                caption = data.get("caption", "")
                lang = data.get("lang", "en")
                
                caption_list.append(caption)
                lang_list.append(lang)
                
            except json.JSONDecodeError as e:
                print(f"PD CaptionJSONParser: 第{idx+1}项JSON解析失败: {e}")
                # 如果解析失败，将整个字符串作为caption返回
                caption_list.append(json_str.strip())
                lang_list.append("en")
            except Exception as e:
                print(f"PD CaptionJSONParser: 解析第{idx+1}项时出错: {e}")
                caption_list.append(f"解析出错: {str(e)}")
                lang_list.append("en")
        
        print(f"PD CaptionJSONParser: 批量解析完成，共处理 {len(caption_list)} 项")
        
        return (caption_list, lang_list)


# 注册节点
NODE_CLASS_MAPPINGS = {
    "PD_CaptionJSONEditor": PD_CaptionJSONEditor,
    "PD_CaptionJSONParser": PD_CaptionJSONParser,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_CaptionJSONEditor": "PD_CaptionJSON编辑器",
    "PD_CaptionJSONParser": "PD_CaptionJSON解析器",
}

