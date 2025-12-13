import os
import re
import comfy.utils

class PD_number_start:
    """
    文件排序重命名节点
    将 "T_1", "T_2", "T_3" 格式的文件名重命名为 "1_T", "2_T", "3_T"
    T参数可以自定义为其他单词，直接执行重命名操作
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "folder_path": ("STRING", {"default": ""}),
                "target_prefix": ("STRING", {"default": "T"}),  # 目标前缀，默认为T
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("result_info",)
    FUNCTION = "rename_order_files"
    CATEGORY = "ZHO Tools"

    def rename_order_files(self, folder_path, target_prefix="T"):
        """
        重命名文件，将前缀_数字格式改为数字_前缀格式
        
        Args:
            folder_path (str): 目标文件夹路径
            target_prefix (str): 目标前缀词（默认为T）
            
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
            
        if not target_prefix.strip():
            return ("❌ 错误: 目标前缀不能为空",)
            
        try:
            # 获取文件夹中的所有文件
            all_files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
            
            if not all_files:
                return ("⚠️ 提示: 文件夹为空，没有文件需要处理",)
            
            # 构建正则表达式，匹配 "前缀_数字" 格式的文件名
            # 例如：T_1.jpg, T_10.png, MyWord_5.txt 等
            pattern = rf"^{re.escape(target_prefix)}_(\d+)(\..+)?$"
            
            # 查找匹配的文件并按数字排序
            matched_files = []
            for filename in all_files:
                match = re.match(pattern, filename)
                if match:
                    number = int(match.group(1))
                    extension = match.group(2) if match.group(2) else ""
                    matched_files.append({
                        "original": filename,
                        "number": number,
                        "extension": extension
                    })
                    result["matched"].append(filename)
                else:
                    result["skipped"].append(filename)
            
            if not matched_files:
                return (f"⚠️ 提示: 在文件夹中没有找到匹配 '{target_prefix}_数字' 格式的文件",)
            
            # 按数字排序
            matched_files.sort(key=lambda x: x["number"])
            
            # 执行重命名操作
            for file_info in matched_files:
                old_path = os.path.join(folder_path, file_info["original"])
                new_filename = f"{file_info['number']}_{target_prefix}{file_info['extension']}"
                new_path = os.path.join(folder_path, new_filename)
                
                try:
                    # 检查目标文件是否已存在
                    if os.path.exists(new_path):
                        result["errors"].append({
                            "original": file_info["original"],
                            "new_name": new_filename,
                            "error": "目标文件已存在"
                        })
                        continue
                    
                    # 执行重命名
                    os.rename(old_path, new_path)
                    
                    result["renamed"].append({
                        "original": file_info["original"],
                        "new_name": new_filename,
                        "number": file_info["number"]
                    })
                    
                except Exception as e:
                    result["errors"].append({
                        "original": file_info["original"],
                        "new_name": new_filename,
                        "error": str(e)
                    })
            
            # 构建结果报告
            report = self._build_report(result, target_prefix)
            return (report,)
                
        except Exception as e:
            return (f"❌ 严重错误: {str(e)}",)
    
    def _build_report(self, result, target_prefix):
        """
        构建操作结果报告
        
        Args:
            result (dict): 操作结果数据
            target_prefix (str): 目标前缀
            
        Returns:
            str: 格式化的报告字符串
        """
        report = "文件重命名操作报告\n"
        report += "=" * 50 + "\n"
        
        # 统计信息
        matched_count = len(result["matched"])
        renamed_count = len(result["renamed"])
        error_count = len(result["errors"])
        skipped_count = len(result["skipped"])
        
        report += f"📊 统计信息:\n"
        report += f"  • 匹配 '{target_prefix}_数字' 格式的文件: {matched_count} 个\n"
        report += f"  • 成功重命名: {renamed_count} 个\n"
        report += f"  • 失败: {error_count} 个\n"
        report += f"  • 跳过（不匹配格式）: {skipped_count} 个\n\n"
        
        # 成功重命名的文件列表
        if renamed_count > 0:
            report += f"✅ 已重命名的文件:\n"
            for item in result["renamed"]:
                report += f"  {item['original']} → {item['new_name']}\n"
            report += "\n"
        
        # 错误列表
        if error_count > 0:
            report += f"❌ 失败的文件:\n"
            for item in result["errors"]:
                report += f"  {item['original']} → {item['new_name']} (错误: {item['error']})\n"
            report += "\n"
        
        # 跳过的文件列表（仅在有跳过文件时显示）
        if skipped_count > 0 and skipped_count <= 10:  # 只显示前10个跳过的文件
            report += f"⏭️ 跳过的文件（不匹配 '{target_prefix}_数字' 格式）:\n"
            for filename in result["skipped"][:10]:
                report += f"  {filename}\n"
            if skipped_count > 10:
                report += f"  ... 还有 {skipped_count - 10} 个文件被跳过\n"
            report += "\n"
        
        # 操作提示
        if renamed_count > 0:
            report += "✅ 重命名操作已完成！\n"
        
        return report

# ComfyUI 节点映射配置
NODE_CLASS_MAPPINGS = {"PD_number_start": PD_number_start}
NODE_DISPLAY_NAME_MAPPINGS = {"PD_number_start": "PD:number_start"}
#
