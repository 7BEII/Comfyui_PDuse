import re
from datetime import datetime

class PD_TextListSort:
    """
    PD文本列表排序 节点
    功能：根据文件名排序规则，同步调整文本列表和文件名列表的顺序。
    与 PD_LoadTextsFromDir 节点配套使用。
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
                "sort_mode": (["字母顺序(正序)", "字母顺序(倒序)", "数字顺序(正序)", "数字顺序(倒序)", "自然排序(正序)", "自然排序(倒序)", "日期顺序(正序)", "日期顺序(倒序)"], {
                    "default": "自然排序(正序)"
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("text_list", "filename_text", "sort_info")
    FUNCTION = "sort_text_list"
    CATEGORY = "PDuse/Text"
    
    # text_list 是列表输入和输出
    INPUT_IS_LIST = {"text_list": True}
    OUTPUT_IS_LIST = (True, False, False)

    def extract_number(self, filename):
        """从文件名中提取第一个数字"""
        match = re.search(r'\d+', filename)
        if match:
            return int(match.group())
        return 0
    
    def extract_date(self, filename):
        """从文件名中提取日期（支持多种格式）"""
        # 尝试多种日期格式
        date_patterns = [
            (r'(\d{4})[-_](\d{2})[-_](\d{2})', '%Y-%m-%d'),  # 2024-01-15 或 2024_01_15
            (r'(\d{4})(\d{2})(\d{2})', '%Y%m%d'),            # 20240115
            (r'(\d{2})[-_](\d{2})[-_](\d{4})', '%d-%m-%Y'),  # 15-01-2024
            (r'(\d{2})[-_](\d{2})[-_](\d{2})', '%y-%m-%d'),  # 24-01-15
        ]
        
        for pattern, fmt in date_patterns:
            match = re.search(pattern, filename)
            if match:
                try:
                    date_str = '-'.join(match.groups())
                    return datetime.strptime(date_str, fmt)
                except:
                    continue
        
        # 如果找不到日期，返回一个很早的日期
        return datetime(1900, 1, 1)
    
    def natural_sort_key(self, text):
        """
        自然排序的键函数
        将文本分割成数字和非数字部分，数字部分转换为整数进行比较
        例如: file1.txt, file2.txt, file10.txt 会按正确顺序排序
        """
        parts = []
        for part in re.split(r'(\d+)', text):
            if part.isdigit():
                parts.append(int(part))
            else:
                parts.append(part.lower())
        return parts

    def sort_text_list(self, text_list, filename_text, sort_mode):
        """
        根据文件名排序规则，同步排序文本列表和文件名列表
        """
        # 1. 检查输入 - 添加类型检查和自动转换
        if not filename_text:
            return ([""], "", "错误：文件名列表为空")
        
        # 检查 filename_text 是否是列表（容错处理）
        if isinstance(filename_text, list):
            print("PD TextListSort: 警告 - filename_text 是列表，自动转换为字符串")
            filename_text = "\n".join(str(item) for item in filename_text if item)
        
        # 确保是字符串后再调用 strip()
        if not isinstance(filename_text, str):
            filename_text = str(filename_text)
        
        if filename_text.strip() == "":
            return ([""], "", "错误：文件名列表为空")
        
        if not text_list or len(text_list) == 0:
            return ([""], "", "错误：文本列表为空")
        
        # 2. 解析文件名列表
        filenames = [line.strip() for line in filename_text.strip().split('\n') if line.strip()]
        
        # 3. 检查数量是否匹配
        if len(filenames) != len(text_list):
            warning_msg = f"警告：文件名数量({len(filenames)})与文本数量({len(text_list)})不匹配，将使用较小数量"
            print(f"PD TextListSort: {warning_msg}")
            count = min(len(filenames), len(text_list))
            filenames = filenames[:count]
            text_list = text_list[:count]
        else:
            count = len(filenames)
        
        # 4. 创建索引对（文件名，文本，原始索引）
        items = list(zip(filenames, text_list, range(count)))
        
        # 5. 根据排序模式进行排序
        reverse = "倒序" in sort_mode
        
        try:
            if "字母顺序" in sort_mode:
                # 按字母顺序排序（不区分大小写）
                items.sort(key=lambda x: x[0].lower(), reverse=reverse)
                sort_desc = f"字母顺序({'倒序' if reverse else '正序'})"
                
            elif "数字顺序" in sort_mode:
                # 按文件名中的数字排序
                items.sort(key=lambda x: self.extract_number(x[0]), reverse=reverse)
                sort_desc = f"数字顺序({'倒序' if reverse else '正序'})"
                
            elif "自然排序" in sort_mode:
                # 自然排序（类似文件管理器）
                items.sort(key=lambda x: self.natural_sort_key(x[0]), reverse=reverse)
                sort_desc = f"自然排序({'倒序' if reverse else '正序'})"
                
            elif "日期顺序" in sort_mode:
                # 按文件名中的日期排序
                items.sort(key=lambda x: self.extract_date(x[0]), reverse=reverse)
                sort_desc = f"日期顺序({'倒序' if reverse else '正序'})"
            
            else:
                # 默认：自然排序
                items.sort(key=lambda x: self.natural_sort_key(x[0]), reverse=reverse)
                sort_desc = "自然排序(正序)"
        
        except Exception as e:
            error_msg = f"排序失败: {e}"
            print(f"PD TextListSort: {error_msg}")
            return (text_list, filename_text, error_msg)
        
        # 6. 提取排序后的结果
        sorted_filenames = [item[0] for item in items]
        sorted_texts = [item[1] for item in items]
        
        # 7. 重新组合文件名为文本
        sorted_filename_text = "\n".join(sorted_filenames)
        
        # 8. 生成排序信息
        sort_info = f"✅ 排序完成：{sort_desc}\n"
        sort_info += f"文件数量：{count}\n"
        sort_info += f"排序前3项：{', '.join(filenames[:3])}\n"
        sort_info += f"排序后3项：{', '.join(sorted_filenames[:3])}"
        
        print(f"PD TextListSort: 已按 {sort_desc} 对 {count} 个文件进行排序")
        
        return (sorted_texts, sorted_filename_text, sort_info)


# 注册节点
NODE_CLASS_MAPPINGS = {
    "PD_TextListSort": PD_TextListSort
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_TextListSort": "PD文本列表排序"
}

