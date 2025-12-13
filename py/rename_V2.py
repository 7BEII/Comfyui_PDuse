import os
import shutil
from pathlib import Path

class PD_RenameV2:
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "folder_path": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "placeholder": "输入文件夹路径"
                }),
                "keyword_to_remove": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "placeholder": "输入要从文件名中移除的关键词"
                }),
                "output_path": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "placeholder": "输出路径(可选，不填则覆盖原图)"
                })
            }
        }
    
    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("result_message", "renamed_count")
    FUNCTION = "batch_rename_files"
    CATEGORY = "PD_Tools/file_operations"
    
    def batch_rename_files(self, folder_path, keyword_to_remove, output_path=""):
        try:
            # 验证文件夹路径
            if not os.path.exists(folder_path):
                return f"错误: 文件夹路径不存在: {folder_path}", 0
            
            if not os.path.isdir(folder_path):
                return f"错误: 指定路径不是文件夹: {folder_path}", 0
            
            # 验证关键词
            if not keyword_to_remove.strip():
                return "错误: 请输入要移除的关键词", 0
            
            # 处理输出路径
            output_path = output_path.strip()
            if output_path:
                if not os.path.exists(output_path):
                    try:
                        os.makedirs(output_path, exist_ok=True)
                    except Exception as e:
                        return f"错误: 无法创建输出目录 {output_path}: {str(e)}", 0
                if not os.path.isdir(output_path):
                    return f"错误: 输出路径不是文件夹: {output_path}", 0
            
            # 支持的图像格式
            image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
            
            # 查找包含关键词的文件并计算新名称
            files_to_process = []
            folder_path_obj = Path(folder_path)
            
            for file_path in folder_path_obj.iterdir():
                if file_path.is_file():
                    file_ext = file_path.suffix.lower()
                    if file_ext in image_extensions and keyword_to_remove in file_path.name:
                        # 计算新文件名（移除关键词）
                        new_name = file_path.name.replace(keyword_to_remove, "")
                        # 确保新文件名不为空或只有扩展名
                        if new_name and new_name != file_path.suffix:
                            if output_path:
                                new_path = Path(output_path) / new_name
                            else:
                                new_path = folder_path_obj / new_name
                            files_to_process.append((file_path, new_path, file_path.name, new_name))
            
            if not files_to_process:
                return f"未找到包含关键词 '{keyword_to_remove}' 的图像文件", 0
            
            # 执行重命名或复制
            processed_count = 0
            processed_files = []
            failed_files = []
            
            for old_path, new_path, old_name, new_name in files_to_process:
                try:
                    # 检查目标文件是否已存在
                    if new_path.exists():
                        failed_files.append(f"{old_name} → {new_name} (目标文件已存在)")
                        continue
                    
                    if output_path:
                        # 复制到新路径
                        shutil.copy2(old_path, new_path)
                        processed_files.append(f"复制: {old_name} → {new_name}")
                    else:
                        # 重命名原文件
                        old_path.rename(new_path)
                        processed_files.append(f"重命名: {old_name} → {new_name}")
                    
                    processed_count += 1
                    
                except Exception as e:
                    failed_files.append(f"{old_name} → {new_name} (错误: {str(e)})")
            
            # 构建结果消息
            result_parts = []
            
            if processed_files:
                action_type = "复制" if output_path else "重命名"
                result_parts.append(f"成功{action_type} {len(processed_files)} 个文件:")
                result_parts.extend([f"  ✓ {process_info}" for process_info in processed_files])
            
            if failed_files:
                result_parts.append(f"\n处理失败 {len(failed_files)} 个文件:")
                result_parts.extend([f"  ✗ {fail_info}" for fail_info in failed_files])
            
            result_message = '\n'.join(result_parts)
            
            return result_message, processed_count
            
        except Exception as e:
            return f"执行过程中发生错误: {str(e)}", 0

# 节点注册
NODE_CLASS_MAPPINGS = {
    "PD_RenameV2": PD_RenameV2
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_RenameV2": "PD_rename_V2"
}
