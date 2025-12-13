import os

class PD_SaveTextPathAndName:
    """
    PD保存文本(路径+文件名) 节点
    功能：接收文本列表和文件名列表，将文本内容按文件名保存到指定路径。
    与 PD_LoadTextsFromDir 节点配套使用。
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "output_directory": ("STRING", {
                    "default": "", 
                    "multiline": False, 
                    "placeholder": "输入保存路径 (例如: C:/Output/Texts)"
                }),
                "text_list": ("STRING", {
                    "default": "",
                    "forceInput": True
                }),
                "filename_text": ("STRING", {
                    "default": "",
                    "forceInput": True
                }),
            }
        }

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("status_message", "saved_count")
    FUNCTION = "save_texts"
    CATEGORY = "PDuse/Text"
    
    # text_list 是列表输入
    INPUT_IS_LIST = {"text_list": True}

    def save_texts(self, output_directory, text_list, filename_text):
        """
        将文本列表按文件名保存到指定目录
        
        参数说明：
        - text_list: 文本内容列表，例如 [content1, content2, content3, ...]
        - filename_text: 多行文件名字符串，每行一个文件名，例如:
          "10_R.txt\n11_R.txt\n12_R.txt\n..."
        
        逻辑：
        按行拆分 filename_text，得到文件名列表，然后一一对应保存：
        - filenames[0] (如 10_R.txt) 对应 text_list[0] 的内容
        - filenames[1] (如 11_R.txt) 对应 text_list[1] 的内容
        - 依此类推，按照输入顺序进行对应
        """
        # 0. 输入参数类型转换（容错处理）
        # 如果 output_directory 是列表，取第一个元素
        if isinstance(output_directory, list):
            print("[PD SaveText] 警告: output_directory 是列表，取第一个元素")
            output_directory = output_directory[0] if output_directory else ""
        
        # 确保 output_directory 是字符串
        if not isinstance(output_directory, str):
            output_directory = str(output_directory)
        
        # 1. 检查输出路径
        if not output_directory or output_directory.strip() == "":
            return ("错误：输出路径为空", 0)
        
        # 2. 自动创建目录（如果不存在）
        try:
            os.makedirs(output_directory, exist_ok=True)
            print(f"[PD SaveText] 输出目录: {output_directory}")
        except Exception as e:
            error_msg = f"错误：无法创建目录 {output_directory} - {e}"
            print(error_msg)
            return (error_msg, 0)
        
        # 3. 解析文件名列表 - 将多行文本按换行符拆分
        if not filename_text:
            return ("错误：文件名列表为空", 0)
        
        # 容错处理：如果 filename_text 是列表，转换为字符串
        if isinstance(filename_text, list):
            print("[PD SaveText] 警告: filename_text 是列表，自动合并为多行文本")
            # 过滤掉空值，并转换为字符串
            filename_text = "\n".join(str(item).strip() for item in filename_text if item)
        
        # 确保是字符串类型
        if not isinstance(filename_text, str):
            filename_text = str(filename_text)
        
        # 再次检查是否为空
        filename_text = filename_text.strip()
        if not filename_text:
            return ("错误：文件名列表为空", 0)
        
        # 按换行符分割文件名，保持输入顺序
        filenames = [line.strip() for line in filename_text.split('\n') if line.strip()]
        print(f"[PD SaveText] 解析到 {len(filenames)} 个文件名")
        
        # 4. 检查文本列表
        if not text_list or len(text_list) == 0:
            return ("错误：文本列表为空", 0)
        
        print(f"[PD SaveText] 接收到 {len(text_list)} 个文本内容")
        
        # 5. 检查数量是否匹配
        if len(filenames) != len(text_list):
            warning_msg = f"警告：文件名数量({len(filenames)})与文本数量({len(text_list)})不匹配，将按最小数量保存"
            print(f"[PD SaveText] {warning_msg}")
            count = min(len(filenames), len(text_list))
        else:
            count = len(filenames)
            print(f"[PD SaveText] 文件名与文本数量匹配，共 {count} 个")
        
        # 6. 逐个保存文件（按照输入顺序一一对应）
        saved_count = 0
        failed_files = []
        
        for i in range(count):
            filename = filenames[i]
            text_content = text_list[i]
            
            # 确保文件名有扩展名，如果没有则添加 .txt
            if not os.path.splitext(filename)[1]:
                filename = filename + ".txt"
            
            file_path = os.path.join(output_directory, filename)
            
            try:
                # 以UTF-8编码保存文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text_content)
                
                saved_count += 1
                print(f"[PD SaveText] [{i+1}/{count}] 已保存: {filename}")
                
            except Exception as e:
                error_msg = f"无法保存文件 {filename} - {e}"
                print(f"[PD SaveText] 错误: {error_msg}")
                failed_files.append(filename)
                continue
        
        # 7. 生成状态信息
        status_msg = f"成功保存 {saved_count}/{count} 个文件到 {output_directory}"
        
        if failed_files:
            status_msg += f"\n失败的文件: {', '.join(failed_files)}"
        
        print(f"[PD SaveText] 完成: {status_msg}")
        
        return (status_msg, saved_count)


# 注册节点
NODE_CLASS_MAPPINGS = {
    "PD_SaveTextPathAndName": PD_SaveTextPathAndName
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_SaveTextPathAndName": "PD保存文本(路径+文件名)"
}

