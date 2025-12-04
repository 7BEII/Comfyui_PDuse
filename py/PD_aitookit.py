import shutil
import os
from pathlib import Path

class PD_ImageFileTraining:
    """
    文件分类训练节点：根据自定义关键词分类复制文件
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_path": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "输入文件夹路径"
                }),
                "output_path": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "输出路径（留空则在输入文件夹下创建）"
                }),
                "training_folder": ("STRING", {
                    "default": "aitookit_training",
                    "multiline": False,
                    "placeholder": "训练文件夹名称"
                }),
                "folder_1": ("STRING", {
                    "default": "aitookit_R",
                    "multiline": False,
                    "placeholder": "包含关键词的文件存放文件夹"
                }),
                "word_1": ("STRING", {
                    "default": "R",
                    "multiline": False,
                    "placeholder": "关键词1（用于分类到folder_1）"
                }),
                "folder_2": ("STRING", {
                    "default": "aitookit_T",
                    "multiline": False,
                    "placeholder": "不包含关键词的文件存放文件夹"
                }),
                "word_2": ("STRING", {
                    "default": "T",
                    "multiline": False,
                    "placeholder": "关键词2（用于分类到folder_2）"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("message",)
    FUNCTION = "classify_files"
    CATEGORY = "PandyTool/File"
    DESCRIPTION = "根据文件名是否包含自定义关键词对文件进行分类复制"

    def classify_files(self, input_path, output_path, training_folder, folder_1, word_1, folder_2, word_2):
        """
        文件分类主函数
        """
        try:
            # 检查输入文件夹
            input_path = input_path.strip()
            if not input_path:
                return ("❌ 错误：请提供输入文件夹路径",)
            
            input_folder = Path(input_path)
            if not input_folder.exists():
                return (f"❌ 错误：文件夹不存在 - {input_path}",)
            
            if not input_folder.is_dir():
                return (f"❌ 错误：提供的路径不是文件夹 - {input_path}",)
            
            # 确定输出路径
            if output_path.strip():
                # 如果指定了输出路径，使用指定路径
                base_output_dir = Path(output_path.strip())
                training_dir = base_output_dir / training_folder
            else:
                # 如果没有指定输出路径，在输入文件夹下创建
                training_dir = input_folder / training_folder
            
            folder_1_path = training_dir / folder_1
            folder_2_path = training_dir / folder_2
            
            # 创建目标文件夹
            try:
                training_dir.mkdir(parents=True, exist_ok=True)
                folder_1_path.mkdir(exist_ok=True)
                folder_2_path.mkdir(exist_ok=True)
            except Exception as e:
                return (f"❌ 错误：无法创建输出文件夹 - {str(e)}",)
            
            # 统计变量
            count_1 = 0
            count_2 = 0
            error_count = 0
            processed_files = []
            
            # 获取所有文件（只处理输入文件夹根目录下的文件）
            try:
                files_to_process = [f for f in input_folder.iterdir() 
                                  if f.is_file() and f.parent == input_folder]
            except Exception as e:
                return (f"❌ 错误：无法读取文件夹内容 - {str(e)}",)
            
            if not files_to_process:
                return (f"📂 信息：文件夹中没有文件需要处理 - {input_path}",)
            
            # 遍历文件进行分类
            for file_path in files_to_process:
                try:
                    file_name = file_path.name
                    
                    # 判断是否包含关键词word_1
                    if word_1.strip() and word_1.strip() in file_name:
                        # 复制到 folder_1 文件夹
                        target_path = folder_1_path / file_name
                        target_path = self._get_unique_filename(target_path)
                        
                        shutil.copy2(str(file_path), str(target_path))
                        processed_files.append(f"✅ [{word_1}] {file_name}")
                        count_1 += 1
                    elif word_2.strip() and word_2.strip() in file_name:
                        # 如果包含关键词word_2，复制到 folder_2 文件夹
                        target_path = folder_2_path / file_name
                        target_path = self._get_unique_filename(target_path)
                        
                        shutil.copy2(str(file_path), str(target_path))
                        processed_files.append(f"📄 [{word_2}] {file_name}")
                        count_2 += 1
                    else:
                        # 如果都不包含，默认复制到 folder_2 文件夹
                        target_path = folder_2_path / file_name
                        target_path = self._get_unique_filename(target_path)
                        
                        shutil.copy2(str(file_path), str(target_path))
                        processed_files.append(f"📄 [其他] {file_name}")
                        count_2 += 1
                        
                except Exception as e:
                    error_count += 1
                    processed_files.append(f"❌ 复制失败: {file_path.name} - {str(e)}")
            
            # 生成结果消息
            result_message = self._generate_result_message(
                training_dir, count_1, count_2, error_count, 
                len(files_to_process), folder_1, folder_2, processed_files
            )
            
            return (result_message,)
            
        except Exception as e:
            return (f"❌ 未知错误：{str(e)}",)
    
    def _get_unique_filename(self, file_path):
        """
        获取唯一的文件名，如果文件已存在则添加编号
        """
        if not file_path.exists():
            return file_path
        
        counter = 1
        original_stem = file_path.stem
        original_suffix = file_path.suffix
        parent_dir = file_path.parent
        
        while file_path.exists():
            new_name = f"{original_stem}_{counter}{original_suffix}"
            file_path = parent_dir / new_name
            counter += 1
        
        return file_path
    
    def _generate_result_message(self, training_dir, count_1, count_2, error_count, 
                               total_files, folder_1, folder_2, processed_files):
        """
        生成结果消息
        """
        message_parts = []
        message_parts.append("🎉 文件分类完成！")
        message_parts.append(f"📁 输出路径: {str(training_dir)}")
        message_parts.append(f"📊 处理统计:")
        message_parts.append(f"   • 总文件数: {total_files}")
        message_parts.append(f"   • {folder_1}: {count_1} 个文件")
        message_parts.append(f"   • {folder_2}: {count_2} 个文件")
        
        if error_count > 0:
            message_parts.append(f"   • ❌ 失败: {error_count} 个文件")
        
        message_parts.append("\n📝 处理详情:")
        # 只显示前20个文件的处理情况，避免消息过长
        display_files = processed_files[:20]
        for file_info in display_files:
            message_parts.append(f"   {file_info}")
        
        if len(processed_files) > 20:
            message_parts.append(f"   ... 还有 {len(processed_files) - 20} 个文件")
        
        return "\n".join(message_parts)

# 节点映射字典
NODE_CLASS_MAPPINGS = {
    "PD_ImageFileTraining": PD_ImageFileTraining
}

# 节点显示名称映射
NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_ImageFileTraining": "PD：aitookitTraining v1"
}
