import os
import shutil
from datetime import datetime
import comfy.utils

class PD_rename_batch_v1:
    """
    批量重命名节点
    支持自定义前缀、新文件名、序号格式等批量重命名功能
    可以复制文件到输出文件夹并重命名，或在原文件夹重命名
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "source_path": ("STRING", {"default": ""}),  # 源文件夹路径
                "new_name": ("STRING", {"default": "image"}),  # 新文件名基础
                "leading_zeros": ("INT", {"default": 2, "min": 0, "max": 10, "step": 1}),  # 前导零个数
                "start_number": ("INT", {"default": 1, "min": 0, "max": 9999, "step": 1}),  # 初始序号
                "step": ("INT", {"default": 1, "min": 1, "max": 100, "step": 1}),  # 序号步长
            },
            "optional": {
                "prefix": ("STRING", {"default": ""}),  # 前缀（可选）
                "output_path": ("STRING", {"default": ""}),  # 输出文件夹（可选）
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("result_info",)
    FUNCTION = "batch_rename_files"
    CATEGORY = "ZHO Tools"

    def batch_rename_files(self, source_path, new_name, leading_zeros=2, start_number=1, step=1, prefix="", output_path=""):
        """
        批量重命名文件
        
        Args:
            source_path (str): 源文件夹路径
            new_name (str): 新文件名基础
            leading_zeros (int): 前导零个数
            start_number (int): 初始序号
            step (int): 序号步长
            prefix (str): 前缀（可选）
            output_path (str): 输出文件夹路径（可选）
            
        Returns:
            tuple: 包含操作结果的字符串
        """
        result = {
            "processed": [],
            "errors": [],
            "total_files": 0,
            "output_folder": ""
        }
        
        # 验证源文件夹
        if not os.path.exists(source_path):
            return (f"❌ 错误: 源文件夹路径不存在 - {source_path}",)
            
        if not new_name.strip():
            return ("❌ 错误: 新文件名不能为空",)
            
        try:
            # 获取所有文件并按名称排序
            all_files = [f for f in os.listdir(source_path) if os.path.isfile(os.path.join(source_path, f))]
            
            if not all_files:
                return ("⚠️ 提示: 源文件夹为空，没有文件需要处理",)
            
            all_files.sort()  # 按文件名排序
            result["total_files"] = len(all_files)
            
            # 确定输出文件夹
            if not output_path.strip():
                # 如果没有指定输出路径，创建默认输出文件夹
                current_date = datetime.now().strftime("%Y%m%d")
                base_output_path = os.path.join(os.path.dirname(source_path), f"rename_{current_date}")
                final_output_path = base_output_path
                count = 1
                # 检查文件夹是否存在，存在则递增后缀
                while os.path.exists(final_output_path):
                    final_output_path = f"{base_output_path}_{count}"
                    count += 1
                os.makedirs(final_output_path, exist_ok=True)
            else:
                final_output_path = output_path.strip()
                os.makedirs(final_output_path, exist_ok=True)
            
            result["output_folder"] = final_output_path
            
            # 批量重命名处理
            current_number = start_number
            for file_name in all_files:
                try:
                    # 获取文件扩展名
                    file_ext = os.path.splitext(file_name)[1]
                    
                    # 构建新文件名
                    # 计算总位数（前导零个数 + 数字本身的位数）
                    if leading_zeros > 0:
                        # 计算实际需要的总位数
                        number_digits = len(str(current_number))
                        total_digits = max(leading_zeros + 1, number_digits)  # 至少保证能显示完整数字
                        formatted_number = f"{current_number:0{total_digits}d}"
                    else:
                        formatted_number = str(current_number)
                    
                    # 构建基础文件名
                    base_new_name = f"{new_name}_{formatted_number}{file_ext}"
                    
                    # 添加前缀（如果有）
                    if prefix.strip():
                        final_new_name = f"{prefix.strip()}_{base_new_name}"
                    else:
                        final_new_name = base_new_name
                    
                    # 源文件和目标文件路径
                    source_file = os.path.join(source_path, file_name)
                    target_file = os.path.join(final_output_path, final_new_name)
                    
                    # 检查目标文件是否已存在
                    if os.path.exists(target_file):
                        result["errors"].append({
                            "original": file_name,
                            "new_name": final_new_name,
                            "error": "目标文件已存在"
                        })
                        continue
                    
                    # 复制并重命名文件
                    shutil.copy2(source_file, target_file)
                    
                    result["processed"].append({
                        "original": file_name,
                        "new_name": final_new_name,
                        "number": current_number
                    })
                    
                    # 更新序号
                    current_number += step
                    
                except Exception as e:
                    result["errors"].append({
                        "original": file_name,
                        "new_name": f"处理失败",
                        "error": str(e)
                    })
            
            # 构建结果报告
            report = self._build_report(result, new_name, prefix, leading_zeros, start_number, step)
            return (report,)
                
        except Exception as e:
            return (f"❌ 严重错误: {str(e)}",)
    
    def _build_report(self, result, new_name, prefix, leading_zeros, start_number, step):
        """
        构建操作结果报告
        
        Args:
            result (dict): 操作结果数据
            new_name (str): 新文件名基础
            prefix (str): 前缀
            leading_zeros (int): 前导零个数
            start_number (int): 初始序号
            step (int): 序号步长
            
        Returns:
            str: 格式化的报告字符串
        """
        report = "批量重命名操作报告\n"
        report += "=" * 50 + "\n"
        
        # 操作参数信息
        prefix_info = f"前缀: {prefix}" if prefix.strip() else "前缀: 无"
        report += f"📋 重命名参数:\n"
        report += f"  • 新文件名基础: {new_name}\n"
        report += f"  • {prefix_info}\n"
        report += f"  • 前导零: {leading_zeros} 位\n"
        report += f"  • 初始序号: {start_number}\n"
        report += f"  • 序号步长: {step}\n"
        report += f"  • 输出文件夹: {result['output_folder']}\n\n"
        
        # 统计信息
        total_files = result["total_files"]
        processed_count = len(result["processed"])
        error_count = len(result["errors"])
        
        report += f"📊 统计信息:\n"
        report += f"  • 总文件数: {total_files} 个\n"
        report += f"  • 成功处理: {processed_count} 个\n"
        report += f"  • 失败: {error_count} 个\n\n"
        
        # 成功处理的文件列表（显示前10个）
        if processed_count > 0:
            report += f"✅ 成功重命名的文件:\n"
            for i, item in enumerate(result["processed"][:10]):
                report += f"  {item['original']} → {item['new_name']}\n"
            if processed_count > 10:
                report += f"  ... 还有 {processed_count - 10} 个文件成功处理\n"
            report += "\n"
        
        # 错误列表
        if error_count > 0:
            report += f"❌ 失败的文件:\n"
            for item in result["errors"]:
                report += f"  {item['original']} (错误: {item['error']})\n"
            report += "\n"
        
        # 操作提示
        if processed_count > 0:
            report += "✅ 批量重命名操作已完成！\n"
            report += f"📁 文件已保存到: {result['output_folder']}\n"
            if error_count == 0:
                report += "🎉 所有文件都成功处理！\n"
        elif error_count > 0:
            report += "⚠️ 批量重命名操作完成，但存在失败的文件\n"
        
        return report

# ComfyUI 节点映射配置
NODE_CLASS_MAPPINGS = {"PD_rename_batch_v1": PD_rename_batch_v1}
NODE_DISPLAY_NAME_MAPPINGS = {"PD_rename_batch_v1": "PD:rename_batch_v1"}