import os
from pathlib import Path

class PD_name_replacewordorder:
    """调整文件名中关键词位置顺序的节点"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "directory_path": ("STRING", {"default": r"C:\\path\\to\\your\\files"}),  # 目录路径
                "file_format": (["jpg", "png", "mp3", "txt", "all"], {"default": "txt"}),  # 文件格式选择
                "search_keyword": ("STRING", {"default": ""}),  # 要搜索的文件名关键词
                "wordorder": (["front", "end"], {"default": "front"}),  # 位置选择
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("show",)  # 用于显示处理日志
    FUNCTION = "process_files"
    CATEGORY = "PD Custom Nodes"
    
    def process_files(self, directory_path, file_format, search_keyword, wordorder):
        try:
            # 自动转义路径，兼容不同操作系统
            directory_path = os.path.normpath(directory_path)
            print(f"标准化路径: {directory_path}")
            
            # 验证目录是否存在
            if not os.path.isdir(directory_path):
                error_msg = f"错误：目录 {directory_path} 不存在！"
                print(error_msg)
                return (error_msg,)

            if not search_keyword.strip():
                error_msg = "错误：请输入要搜索的关键词！"
                print(error_msg)
                return (error_msg,)

            print(f"正在处理目录: {directory_path}")
            print(f"选择的文件格式: {file_format}")
            print(f"搜索文件名中的关键词: '{search_keyword}'")
            
            # 处理位置选择
            operation_desc = "移动到最前面" if wordorder == "front" else "移动到最后面"
            print(f"操作: 将关键词{operation_desc}")
            
            # 根据选择的格式获取文件
            directory = Path(directory_path)
            
            if file_format == "all":
                # 获取所有文件（排除子目录）
                target_files = [f for f in directory.iterdir() if f.is_file()]
                format_desc = "所有格式"
            else:
                # 获取指定格式的文件
                target_files = list(directory.glob(f"*.{file_format}"))
                format_desc = f".{file_format}"
            
            print(f"扫描到 {len(target_files)} 个 {format_desc} 文件")
            
            if not target_files:
                no_files_msg = f"未找到任何 {format_desc} 文件！"
                print(no_files_msg)
                return (no_files_msg,)
                
            processed_results = []
            modified_count = 0
            
            for file_path in target_files:
                try:
                    print(f"\n检查文件: {file_path.name}")
                    
                    # 检查文件名中是否包含关键词
                    if search_keyword in file_path.name:
                        # 分离文件名和扩展名
                        file_stem = file_path.stem  # 不含扩展名的文件名
                        file_suffix = file_path.suffix  # 扩展名
                        
                        # 移除关键词，保留原有的所有符号
                        remaining_name = file_stem.replace(search_keyword, "")
                        
                        # 根据选择的位置重新组合文件名，直接拼接不添加分隔符
                        if wordorder == "front":
                            if remaining_name:
                                new_stem = f"{search_keyword}{remaining_name}"
                            else:
                                new_stem = search_keyword
                        else:  # end
                            if remaining_name:
                                new_stem = f"{remaining_name}{search_keyword}"
                            else:
                                new_stem = search_keyword
                        
                        new_name = f"{new_stem}{file_suffix}"
                        new_path = file_path.with_name(new_name)
                        
                        # 跳过已经在正确位置的文件
                        if file_path.name == new_name:
                            result = f"⚪ {file_path.name}: 关键词已在目标位置"
                            print(f"  {result}")
                            processed_results.append(result)
                            continue
                        
                        # 检查目标文件名是否已存在
                        if new_path.exists():
                            error_result = f"⚠️ {file_path.name}: 跳过 - 目标文件名 '{new_name}' 已存在"
                            print(f"  {error_result}")
                            processed_results.append(error_result)
                            continue
                        
                        # 执行重命名操作
                        file_path.rename(new_path)
                        modified_count += 1
                        result = f"✅ {file_path.name} → {new_name}"
                        print(f"  {result}")
                        processed_results.append(result)
                    else:
                        result = f"⚪ {file_path.name}: 未找到关键词 '{search_keyword}'"
                        print(f"  {result}")
                        processed_results.append(result)

                except Exception as e:
                    error_result = f"❌ {file_path.name}: 处理失败 - {e}"
                    print(f"  {error_result}")
                    processed_results.append(error_result)
                    continue

            # 生成最终结果消息
            total_files = len(target_files)
            summary = f"""
================== 处理完成 ==================
📁 扫描目录: {os.path.normpath(directory_path)}
📄 文件格式: {format_desc}
📄 总文件数: {total_files} 个文件
🔍 关键词操作: '{search_keyword}' ({operation_desc})
✅ 成功修改: {modified_count} 个文件

详细结果:
{chr(10).join(processed_results)}
============================================
"""
            print(summary)
            return (summary,)

        except Exception as e:
            error_msg = f"处理出错：{e}"
            print(error_msg)
            return (error_msg,)


# 节点映射
NODE_CLASS_MAPPINGS = {
    "PD_name_replacewordorder": PD_name_replacewordorder,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_name_replacewordorder": "PD_Name_ReplaceWordOrder",
}
