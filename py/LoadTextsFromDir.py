import os

class PD_LoadTextsFromDir:
    """
    PD加载文本文件夹(输出列表) 节点
    功能：通过输入文件夹路径，批量读取其中的 .txt 等文本文件内容，输出文本列表。
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "directory_path": ("STRING", {
                    "default": "", 
                    "multiline": False, 
                    "placeholder": "输入文件夹路径 (例如: C:/Notes/Project)"
                }),
                "limit_count": ("INT", {
                    "default": 0, 
                    "min": 0, 
                    "max": 10000, 
                    "step": 1,
                    "label": "限制读取数量(0为不限)"
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "INT")
    RETURN_NAMES = ("text_list", "concat_text", "filename_text", "file_count")
    FUNCTION = "load_texts_from_dir"
    CATEGORY = "PDuse/Text"
    
    # 告诉ComfyUI，text_list 是一个列表
    OUTPUT_IS_LIST = (True, False, False, False)

    def load_texts_from_dir(self, directory_path, limit_count):
        text_list = []
        names = []
        full_text_list = [] # 用于拼接
        
        # 1. 路径校验
        if not directory_path or not os.path.exists(directory_path):
            print(f"PD TextLoader: 路径不存在 -> {directory_path}")
            return ([""], "", "", 0)

        # 2. 获取文件列表并排序
        valid_extensions = {'.txt', '.csv', '.json', '.md', '.py', '.js', '.bat', '.sh', '.xml', '.yaml'}
        
        try:
            files = [f for f in os.listdir(directory_path) 
                     if os.path.isfile(os.path.join(directory_path, f)) and 
                     os.path.splitext(f)[1].lower() in valid_extensions]
        except Exception as e:
            print(f"PD TextLoader: 无法访问目录 {directory_path} - {e}")
            return ([""], "", "", 0)
        
        # 按文件名排序
        files.sort()
        
        # 应用数量限制
        if limit_count > 0:
            files = files[:limit_count]

        # 3. 循环读取文本
        for filename in files:
            file_path = os.path.join(directory_path, filename)
            try:
                with open(file_path, 'rb') as f:
                    data_bytes = f.read()
                    
                # 尝试解码
                text_content = ""
                try:
                    text_content = data_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        text_content = data_bytes.decode('gbk')
                    except UnicodeDecodeError:
                        text_content = data_bytes.decode('utf-8', errors='ignore')
                
                # 统一换行符
                text_content = text_content.replace('\r\n', '\n')
                
                text_list.append(text_content)
                names.append(filename)
                
                # 构建带标题的拼接文本
                full_text_list.append(f"=== File: {filename} ===\n{text_content}\n")
                
            except Exception as e:
                print(f"PD TextLoader: 无法读取文件 {filename} - {e}")
                continue

        # 4. 生成输出
        name_list_str = "\n".join(names)
        concatenated_text = "\n".join(full_text_list)
        
        print(f"PD TextLoader: 已从 {directory_path} 读取 {len(text_list)} 个文本文件")
        
        if not text_list:
            return ([""], "", "", 0)

        return (text_list, concatenated_text, name_list_str, len(text_list))

# 注册节点
NODE_CLASS_MAPPINGS = {
    "PD_LoadTextsFromDir": PD_LoadTextsFromDir
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_LoadTextsFromDir": "PD加载文本文件夹(输出列表)"
}

