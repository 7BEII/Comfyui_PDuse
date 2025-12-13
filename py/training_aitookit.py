import os
import shutil
from pathlib import Path


class PD_AitoolkitTrainingRedux:
    """
    PD AI训练数据分类整理 节点
    功能：将配对的图片和文本文件分类到不同文件夹
    用途：整理训练数据集，将有标注的文件和无标注的文件分开
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "source_folder": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "输入源文件夹路径"
                }),
                "paired_folder_name": ("STRING", {
                    "default": "paired_files",
                    "multiline": False,
                    "placeholder": "配对文件的文件夹名称"
                }),
                "unpaired_folder_name": ("STRING", {
                    "default": "unpaired_files",
                    "multiline": False,
                    "placeholder": "未配对文件的文件夹名称"
                }),
            },
            "optional": {
                "image_extensions": ("STRING", {
                    "default": ".png,.jpg,.jpeg,.webp",
                    "multiline": False,
                    "placeholder": "图片扩展名（逗号分隔）"
                }),
                "text_extension": ("STRING", {
                    "default": ".txt",
                    "multiline": False,
                    "placeholder": "文本扩展名"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("message",)
    FUNCTION = "organize_files"
    CATEGORY = "PDuse/File"
    
    def organize_files(self, source_folder, paired_folder_name="paired_files", 
                      unpaired_folder_name="unpaired_files",
                      image_extensions=".png,.jpg,.jpeg,.webp", 
                      text_extension=".txt"):
        """
        整理训练数据文件
        将配对的图片和文本文件分类到不同文件夹
        """
        try:
            # 检查源文件夹是否存在
            if not os.path.exists(source_folder):
                return (f"❌ 错误：源文件夹不存在: {source_folder}",)
            
            if not os.path.isdir(source_folder):
                return (f"❌ 错误：路径不是文件夹: {source_folder}",)
            
            # 解析图片扩展名
            img_exts = [ext.strip().lower() for ext in image_extensions.split(',')]
            # 确保扩展名以点开头
            img_exts = [ext if ext.startswith('.') else f'.{ext}' for ext in img_exts]
            
            # 解析文本扩展名
            txt_ext = text_extension.strip().lower()
            if not txt_ext.startswith('.'):
                txt_ext = f'.{txt_ext}'
            
            # 创建子文件夹
            paired_folder = os.path.join(source_folder, paired_folder_name)
            unpaired_folder = os.path.join(source_folder, unpaired_folder_name)
            
            os.makedirs(paired_folder, exist_ok=True)
            os.makedirs(unpaired_folder, exist_ok=True)
            
            # 扫描源文件夹中的所有文件
            all_files = []
            for item in os.listdir(source_folder):
                item_path = os.path.join(source_folder, item)
                # 只处理文件，跳过文件夹
                if os.path.isfile(item_path):
                    all_files.append(item)
            
            # 分类文件
            image_files = {}  # {basename: [full_filename1, full_filename2, ...]}
            text_files = {}   # {basename: full_filename}
            other_files = []
            
            for filename in all_files:
                file_ext = os.path.splitext(filename)[1].lower()
                file_basename = os.path.splitext(filename)[0]
                
                if file_ext in img_exts:
                    # 图片文件
                    if file_basename not in image_files:
                        image_files[file_basename] = []
                    image_files[file_basename].append(filename)
                elif file_ext == txt_ext:
                    # 文本文件
                    text_files[file_basename] = filename
                else:
                    # 其他文件
                    other_files.append(filename)
            
            # 统计信息
            paired_count = 0
            unpaired_count = 0
            paired_list = []
            unpaired_list = []
            
            # 处理配对的文件
            for basename, img_filenames in image_files.items():
                if basename in text_files:
                    # 找到配对的文本文件
                    txt_filename = text_files[basename]
                    
                    # 复制图片文件到配对文件夹
                    for img_filename in img_filenames:
                        src_path = os.path.join(source_folder, img_filename)
                        dst_path = os.path.join(paired_folder, img_filename)
                        
                        # 避免复制到自身（如果文件已经在目标文件夹中）
                        if os.path.abspath(src_path) != os.path.abspath(dst_path):
                            shutil.copy2(src_path, dst_path)
                            paired_count += 1
                            paired_list.append(img_filename)
                    
                    # 复制文本文件到配对文件夹
                    src_path = os.path.join(source_folder, txt_filename)
                    dst_path = os.path.join(paired_folder, txt_filename)
                    
                    if os.path.abspath(src_path) != os.path.abspath(dst_path):
                        shutil.copy2(src_path, dst_path)
                        paired_count += 1
                        paired_list.append(txt_filename)
                    
                    # 从文本文件字典中移除已处理的
                    del text_files[basename]
                else:
                    # 没有配对的文本文件
                    for img_filename in img_filenames:
                        src_path = os.path.join(source_folder, img_filename)
                        dst_path = os.path.join(unpaired_folder, img_filename)
                        
                        if os.path.abspath(src_path) != os.path.abspath(dst_path):
                            shutil.copy2(src_path, dst_path)
                            unpaired_count += 1
                            unpaired_list.append(img_filename)
            
            # 处理剩余的未配对文本文件
            for basename, txt_filename in text_files.items():
                src_path = os.path.join(source_folder, txt_filename)
                dst_path = os.path.join(unpaired_folder, txt_filename)
                
                if os.path.abspath(src_path) != os.path.abspath(dst_path):
                    shutil.copy2(src_path, dst_path)
                    unpaired_count += 1
                    unpaired_list.append(txt_filename)
            
            # 处理其他文件
            for other_file in other_files:
                src_path = os.path.join(source_folder, other_file)
                dst_path = os.path.join(unpaired_folder, other_file)
                
                if os.path.abspath(src_path) != os.path.abspath(dst_path):
                    shutil.copy2(src_path, dst_path)
                    unpaired_count += 1
                    unpaired_list.append(other_file)
            
            # 生成详细报告
            message = "=" * 60 + "\n"
            message += "✅ AI训练数据整理完成\n"
            message += "=" * 60 + "\n\n"
            message += f"📁 源文件夹: {source_folder}\n\n"
            message += f"📊 统计信息:\n"
            message += f"  • 配对文件总数: {paired_count} 个\n"
            message += f"  • 未配对文件总数: {unpaired_count} 个\n"
            message += f"  • 总处理文件数: {paired_count + unpaired_count} 个\n\n"
            
            message += f"📂 配对文件夹: {paired_folder_name}/\n"
            if paired_list:
                message += f"  包含 {len(paired_list)} 个文件\n"
                # 显示前5个文件作为示例
                for i, filename in enumerate(paired_list[:5]):
                    message += f"    - {filename}\n"
                if len(paired_list) > 5:
                    message += f"    ... 还有 {len(paired_list) - 5} 个文件\n"
            else:
                message += "  (空)\n"
            
            message += f"\n📂 未配对文件夹: {unpaired_folder_name}/\n"
            if unpaired_list:
                message += f"  包含 {len(unpaired_list)} 个文件\n"
                # 显示前5个文件作为示例
                for i, filename in enumerate(unpaired_list[:5]):
                    message += f"    - {filename}\n"
                if len(unpaired_list) > 5:
                    message += f"    ... 还有 {len(unpaired_list) - 5} 个文件\n"
            else:
                message += "  (空)\n"
            
            message += "\n" + "=" * 60
            
            print(message)
            
            return (message,)
            
        except Exception as e:
            error_message = f"❌ 处理出错: {str(e)}"
            print(error_message)
            return (error_message,)


# 注册节点
NODE_CLASS_MAPPINGS = {
    "PD_AitoolkitTrainingRedux": PD_AitoolkitTrainingRedux
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_AitoolkitTrainingRedux": "PD aitookit training redux"
}

