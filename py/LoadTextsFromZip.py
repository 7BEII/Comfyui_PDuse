import os
import torch
import zipfile
import folder_paths

class PD_LoadTextsFromZip:
    """
    PD加载文本ZIP(输出列表) 节点
    功能：通过上传 ZIP 文件，解压并提取其中的 .txt 文件内容，输出文本列表。
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # 前端 JS 会自动在此输入框下方添加上传按钮
                "zip_file_upload": ("STRING", {
                    "default": "",
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "INT")
    RETURN_NAMES = ("text_list", "concat_text", "filename_text", "file_count")
    FUNCTION = "load_zip_texts"
    CATEGORY = "PDuse/Text"
    
    # 告诉ComfyUI，text_list 是一个列表，其他是单值
    OUTPUT_IS_LIST = (True, False, False, False)

    def load_zip_texts(self, zip_file_upload):
        text_list = []
        names = []
        full_text_list = [] # 用于拼接
        
        # 1. 路径校验
        if not zip_file_upload:
            print(f"PD ZipLoader: 未选择或上传 ZIP 文件。")
            return ([""], "", "", 0)
            
        input_dir = folder_paths.get_input_directory()
        zip_path = os.path.join(input_dir, zip_file_upload)
        
        if not os.path.exists(zip_path):
            if os.path.exists(zip_file_upload):
                zip_path = zip_file_upload
            else:
                print(f"PD ZipLoader: 找不到文件 {zip_path}")
                return ([""], "", "", 0)
            
        try:
            # 2. 解压并读取
            with zipfile.ZipFile(zip_path, 'r') as z:
                file_list = z.namelist()
                file_list.sort()
                
                valid_extensions = {'.txt', '.csv', '.json', '.md', '.py', '.js', '.bat', '.sh', '.xml', '.yaml'}
                
                for filename in file_list:
                    # 过滤掉文件夹和特殊文件
                    if filename.endswith('/'): continue
                    if '__MACOSX' in filename: continue
                    
                    ext = os.path.splitext(filename)[1].lower()
                    if ext not in valid_extensions: continue
                    
                    try:
                        # 3. 读取文本内容
                        data_bytes = z.read(filename)
                        
                        # 尝试解码
                        text_content = ""
                        try:
                            text_content = data_bytes.decode('utf-8')
                        except UnicodeDecodeError:
                            try:
                                text_content = data_bytes.decode('gbk')
                            except UnicodeDecodeError:
                                # 如果都失败，忽略错误读取
                                text_content = data_bytes.decode('utf-8', errors='ignore')
                        
                        # 统一换行符
                        text_content = text_content.replace('\r\n', '\n')
                        
                        text_list.append(text_content)
                        
                        # 保留相对路径，不仅是文件名
                        names.append(filename)
                        
                        # 构建带标题的拼接文本
                        full_text_list.append(f"=== File: {filename} ===\n{text_content}\n")
                        
                    except Exception as e:
                        print(f"PD ZipLoader: 警告 - 读取文本 {filename} 失败: {e}")
                        continue
                        
        except Exception as e:
            error_msg = f"PD ZipLoader: ZIP文件处理失败: {e}"
            print(error_msg)
            return ([error_msg], error_msg, error_msg, 0)

        # 5. 生成输出
        name_list_str = "\n".join(names)
        concatenated_text = "\n".join(full_text_list)
        
        print(f"PD ZipLoader: 从 {zip_file_upload} 读取了 {len(text_list)} 个文本文件")
        
        if not text_list:
            return ([""], "", "", 0)

        return (text_list, concatenated_text, name_list_str, len(text_list))

# 注册节点
NODE_CLASS_MAPPINGS = {
    "PD_LoadTextsFromZip": PD_LoadTextsFromZip
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_LoadTextsFromZip": "PD加载文本ZIP(输出列表)"
}

