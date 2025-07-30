import os
import re
import comfy.utils

class PD_replace_word:
    """
    文件名关键词替换/删除节点
    在文件夹中查找包含指定关键词的文件，将关键词替换为新的关键词或删除关键词
    支持格式筛选（jpg/png/txt等），严格匹配（区分大小写）
    当new_keyword为空时，执行删除操作
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "folder_path": ("STRING", {"default": ""}),
                "old_keyword": ("STRING", {"default": "R"}),  # 要替换的关键词
                "new_keyword": ("STRING", {"default": "start"}),  # 新的关键词
                "file_format": (["full", "jpg", "png", "txt", "jpeg", "bmp", "gif", "webp"], {"default": "full"}),  # 文件格式筛选
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("result_info",)
    FUNCTION = "replace_keyword_in_filenames"
    CATEGORY = "ZHO Tools"

    def replace_keyword_in_filenames(self, folder_path, old_keyword, new_keyword, file_format="full"):
        """
        替换或删除文件名中的关键词
        
        Args:
            folder_path (str): 目标文件夹路径
            old_keyword (str): 要替换/删除的关键词
            new_keyword (str): 新的关键词（为空时执行删除操作）
            file_format (str): 文件格式筛选（full为不限制）
            
        Returns:
            tuple: 包含操作结果的字符串
        """
        result = {
            "matched": [],
            "renamed": [],
            "errors": [],
            "skipped": []
        }
        
        if not os.path.exists(folder_path):
            return (f"❌ 错误: 文件夹路径不存在 - {folder_path}",)
            
        if not old_keyword.strip():
            return ("❌ 错误: 原关键词不能为空",)
            

            
        # 如果新关键词不为空且与原关键词相同，则返回错误
        if new_keyword.strip() and old_keyword.strip() == new_keyword.strip():
            return ("❌ 错误: 原关键词和新关键词不能相同",)
            
        try:
            # 获取文件夹中的所有文件
            all_files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
            
            if not all_files:
                return ("⚠️ 提示: 文件夹为空，没有文件需要处理",)
            
            # 根据指定格式筛选文件
            if file_format != "full":
                filtered_files = []
                for filename in all_files:
                    _, ext = os.path.splitext(filename)
                    if ext.lower() == f".{file_format.lower()}":
                        filtered_files.append(filename)
                all_files = filtered_files
                
                if not all_files:
                    return (f"⚠️ 提示: 在文件夹中没有找到 {file_format.upper()} 格式的文件",)
            
            # 查找包含关键词的文件
            for filename in all_files:
                # 检查文件名是否包含要替换的关键词（严格匹配，区分大小写）
                if old_keyword in filename:
                    result["matched"].append(filename)
                    
                    # 执行关键词替换或删除（严格匹配）
                    if new_keyword.strip():
                        # 替换操作
                        new_filename = filename.replace(old_keyword, new_keyword)
                    else:
                        # 删除操作
                        new_filename = filename.replace(old_keyword, "")
                    
                    old_path = os.path.join(folder_path, filename)
                    new_path = os.path.join(folder_path, new_filename)
                    
                    try:
                        # 检查目标文件是否已存在
                        if os.path.exists(new_path) and old_path != new_path:
                            result["errors"].append({
                                "original": filename,
                                "new_name": new_filename,
                                "error": "目标文件已存在"
                            })
                            continue
                        
                        # 如果新文件名和原文件名相同，跳过
                        if filename == new_filename:
                            result["skipped"].append(filename)
                            continue
                        
                        # 执行重命名
                        os.rename(old_path, new_path)
                        
                        result["renamed"].append({
                            "original": filename,
                            "new_name": new_filename
                        })
                        
                    except Exception as e:
                        result["errors"].append({
                            "original": filename,
                            "new_name": new_filename,
                            "error": str(e)
                        })
                else:
                    result["skipped"].append(filename)
            
            if not result["matched"]:
                return (f"⚠️ 提示: 在文件夹中没有找到包含关键词 '{old_keyword}' 的文件",)
            
            # 构建结果报告
            report = self._build_report(result, old_keyword, new_keyword, file_format)
            return (report,)
                
        except Exception as e:
            return (f"❌ 严重错误: {str(e)}",)
    

    def _build_report(self, result, old_keyword, new_keyword, file_format="full"):
        """
        构建操作结果报告
        
        Args:
            result (dict): 操作结果数据
            old_keyword (str): 原关键词
            new_keyword (str): 新关键词
            file_format (str): 文件格式筛选
            
        Returns:
            str: 格式化的报告字符串
        """
        report = "文件名关键词替换操作报告\n"
        report += "=" * 50 + "\n"
        
        # 操作信息
        format_info = "所有格式" if file_format == "full" else f"{file_format.upper()} 格式"
        
        if new_keyword.strip():
            operation_info = f"🔄 替换操作: '{old_keyword}' → '{new_keyword}' (严格匹配)"
        else:
            operation_info = f"🗑️ 删除操作: 删除 '{old_keyword}' (严格匹配)"
        
        report += f"{operation_info}\n"
        report += f"📁 目标格式: {format_info}\n\n"
        
        # 统计信息
        matched_count = len(result["matched"])
        renamed_count = len(result["renamed"])
        error_count = len(result["errors"])
        skipped_count = len(result["skipped"]) - renamed_count  # 排除已重命名的文件
        
        operation_text = "删除" if not new_keyword.strip() else "重命名"
        
        report += f"📊 统计信息:\n"
        report += f"  • 匹配包含 '{old_keyword}' 的文件: {matched_count} 个\n"
        report += f"  • 成功{operation_text}: {renamed_count} 个\n"
        report += f"  • 失败: {error_count} 个\n"
        report += f"  • 跳过（不包含关键词或无需更改）: {skipped_count} 个\n\n"
        
        # 成功处理的文件列表
        if renamed_count > 0:
            report += f"✅ 已{operation_text}的文件:\n"
            for item in result["renamed"]:
                report += f"  {item['original']} → {item['new_name']}\n"
            report += "\n"
        
        # 错误列表
        if error_count > 0:
            report += f"❌ 失败的文件:\n"
            for item in result["errors"]:
                report += f"  {item['original']} → {item['new_name']} (错误: {item['error']})\n"
            report += "\n"
        
        # 跳过的文件列表（仅显示前10个不包含关键词的文件）
        skipped_no_keyword = [f for f in result["skipped"] if f not in [item['original'] for item in result["renamed"]]]
        if len(skipped_no_keyword) > 0 and len(skipped_no_keyword) <= 10:
            report += f"⏭️ 跳过的文件（不包含关键词 '{old_keyword}'）:\n"
            for filename in skipped_no_keyword[:10]:
                report += f"  {filename}\n"
            if len(skipped_no_keyword) > 10:
                report += f"  ... 还有 {len(skipped_no_keyword) - 10} 个文件被跳过\n"
            report += "\n"
        
        # 操作提示
        if renamed_count > 0:
            if new_keyword.strip():
                report += "✅ 关键词替换操作已完成！\n"
            else:
                report += "✅ 关键词删除操作已完成！\n"
        elif matched_count > 0 and renamed_count == 0:
            operation_verb = "删除" if not new_keyword.strip() else "重命名"
            report += f"⚠️ 找到了匹配的文件，但没有进行{operation_verb}（可能因为目标文件已存在或无需更改）\n"
        
        return report

# ComfyUI 节点映射配置
NODE_CLASS_MAPPINGS = {"PD_replace_word": PD_replace_word}
NODE_DISPLAY_NAME_MAPPINGS = {"PD_replace_word": "PD:replace_word"}