import os
import re


class PD_RemoveColorWords:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "directory_path": ("STRING", {"default": r"G:\\download\\宫廷圣诞猫gongyan_V1"}),  # 文件夹路径
                "words_to_remove": ("STRING", {"default": ""}),  # 要删除的单词，支持换行或空行
                "words_to_add": ("STRING", {"default": ""}),  # 要添加的单词
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("Result",)
    FUNCTION = "process_directory"
    CATEGORY = "PDuse/Text"

    def process_directory(self, directory_path, words_to_remove, words_to_add):
        try:
            if not os.path.isdir(directory_path):
                return (f"错误：目录 {directory_path} 不存在！",)

            print(f"正在处理目录: {directory_path}")

            # 支持 \n 和多行内容的解析
            words_to_remove = [word.encode('utf-8').decode('unicode_escape').strip()
                               for word in words_to_remove.split(",") if word.strip()] or None

            words_to_add = words_to_add.strip() if words_to_add.strip() else None

            if words_to_remove:
                patterns = [
                    rf'\b{re.escape(word)}(?:\s*\([^)]*\)|_[^\s,]*|\s+[^\s,]*)?\b'
                    if word != '\n' else r'\n+'
                    for word in words_to_remove
                ]
                combined_pattern = '|'.join(patterns)

            processed_files = 0
            total_files = 0
            modified_files = 0

            for root, dirs, files in os.walk(directory_path):
                for file in files:
                    if file.endswith('.txt'):
                        total_files += 1
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()

                            original_content = content

                            if words_to_remove:
                                content = re.sub(combined_pattern, '', content, flags=re.IGNORECASE)

                            if words_to_add:
                                content = words_to_add + " " + content.lstrip()

                            if content != original_content:
                                modified_files += 1
                                with open(file_path, 'w', encoding='utf-8') as f:
                                    f.write(content)
                                print(f"处理完成: {file_path}")

                            processed_files += 1
                        except Exception as e:
                            print(f"跳过文件 {file_path}，错误: {e}")
                            continue

            if processed_files == 0:
                return (f"未找到符合条件的文件",)

            result_message = f"处理完成，共扫描了 {total_files} 个文件，实际修改了 {modified_files} 个文件"
            if words_to_remove:
                result_message += f"，已删除内容：{', '.join(words_to_remove)}"
            if words_to_add:
                result_message += f"，已添加单词：'{words_to_add}'"
            return (result_message,)

        except Exception as e:
            return (f"处理出错：{e}",)


class Empty_Line:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # 加入 forceInput=True 让字段变成可连线的输入口
                "text": ("STRING", {"multiline": True, "default": "", "forceInput": True}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "remove_empty_lines"
    CATEGORY = "PDuse/Text"

    def remove_empty_lines(self, text):
        cleaned_text = re.sub(r'^[\r\n]+', '', text)
        return (cleaned_text,)
    

# 节点映射
NODE_CLASS_MAPPINGS = {
    "PD_RemoveColorWords": PD_RemoveColorWords,
    "Empty_Line": Empty_Line,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_RemoveColorWords": "PDstring:removecolorwords",
    "Empty_Line": "PDstring:del_EmptyLine",
}
