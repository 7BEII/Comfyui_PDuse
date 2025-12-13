import os
import comfy.utils
from PIL import Image

class PD_number_star:
    """
    文件批量重命名节点
    支持两种重命名模式：
    1. 完全重命名：使用新的文件名
    2. 添加前缀：保留原文件名，添加前缀
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "folder_path": ("STRING", {"default": ""}),
                "new_name": ("STRING", {"default": ""}),
                "prefix": ("STRING", {"default": ""}),
                "delimiter": ("STRING", {"default": "_"}),  # 分隔符
                "number_start": ("BOOLEAN", {"default": False}),  # 数字是否在开头
                "padding": ("INT", {"default": 1, "min": 0, "max": 9, "step": 1}),  # 数字填充位数
                "format_convert": (["NONE", "jpg", "png", "txt"], {"default": "不修改"}),  # 格式转换
                "max_size": ("INT", {"default": 1024, "min": 64, "max": 4096, "step": 64}),  # 图片最长边
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("result_info",)
    FUNCTION = "rename_files"
    CATEGORY = "ZHO Tools"

    def rename_files(self, folder_path, new_name="", prefix="", delimiter="_", number_start=False, padding=1, format_convert="不修改", max_size=1024):
        """
        重命名文件夹中的文件
        
        Args:
            folder_path (str): 目标文件夹路径
            new_name (str): 新的文件名（如果提供，将完全替换原文件名）
            prefix (str): 要添加的前缀（如果提供，将在原文件名前添加）
            delimiter (str): 分隔符
            number_start (bool): 数字是否在开头
            padding (int): 数字填充位数
            format_convert (str): 格式转换选项
            max_size (int): 图片最长边尺寸
            
        Returns:
            tuple: 包含操作结果的字符串
        """
        result = {
            "success": [],
            "errors": [],
            "total_processed": 0
        }
        
        if not os.path.exists(folder_path):
            return (f"错误: 文件夹路径不存在 - {folder_path}",)
            
        try:
            # 获取文件夹中的所有文件
            files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
            
            if not files:
                return ("提示: 文件夹为空，没有文件需要处理",)
            
            # 检查是否同时提供了新文件名和前缀
            if new_name and prefix:
                return ("错误: 不能同时使用新文件名和前缀，请只选择其中一种方式",)
                
            for index, filename in enumerate(files, 1):
                file_path = os.path.join(folder_path, filename)
                
                # 分离文件名和扩展名
                name, ext = os.path.splitext(filename)
                
                # 处理格式转换
                original_ext = ext
                if format_convert != "不修改":
                    if format_convert == "jpg":
                        ext = ".jpg"
                    elif format_convert == "png":
                        ext = ".png"
                    elif format_convert == "txt":
                        ext = ".txt"
                
                # 构建新文件名
                if new_name:
                    # 如果提供了新文件名，使用新文件名+序号+原扩展名
                    if padding == 0:
                        # 不使用数字编号
                        new_name_with_ext = f"{new_name}{ext}"
                    else:
                        # 使用数字编号，根据number_start决定位置
                        if number_start:
                            # 数字在开头: 001_filename.ext
                            new_name_with_ext = f"{index:0{padding}}{delimiter}{new_name}{ext}"
                        else:
                            # 数字在末尾: filename_001.ext
                            new_name_with_ext = f"{new_name}{delimiter}{index:0{padding}}{ext}"
                elif prefix:
                    # 如果提供了前缀，在原文件名前添加前缀
                    if padding == 0:
                        # 不使用数字编号
                        new_name_with_ext = f"{prefix}{name}{ext}"
                    else:
                        # 使用数字编号，根据number_start决定位置
                        if number_start:
                            # 数字在开头: 001_prefix_filename.ext
                            new_name_with_ext = f"{index:0{padding}}{delimiter}{prefix}{name}{ext}"
                        else:
                            # 数字在末尾: prefix_filename_001.ext
                            new_name_with_ext = f"{prefix}{name}{delimiter}{index:0{padding}}{ext}"
                else:
                    # 如果没有提供任何参数，跳过该文件
                    continue
                
                new_path = os.path.join(folder_path, new_name_with_ext)
                
                try:
                    # 检查是否需要图片处理
                    is_input_image = self._is_image_file(file_path)
                    needs_image_processing = (is_input_image and format_convert in ["jpg", "png"]) or (is_input_image and format_convert == "不修改")
                    
                    if needs_image_processing:
                        # 处理图片格式转换和尺寸调整
                        self._process_image(file_path, new_path, format_convert, max_size, original_ext)
                    else:
                        # 普通文件重命名
                        os.rename(file_path, new_path)
                    
                    result["success"].append({
                        "original": filename,
                        "new_name": new_name_with_ext
                    })
                    result["total_processed"] += 1
                except Exception as e:
                    result["errors"].append({
                        "filename": filename,
                        "error": str(e)
                    })
            
            # 构建结果信息
            success_count = len(result["success"])
            error_count = len(result["errors"])
            
            report = f"操作完成\n成功: {success_count}\n失败: {error_count}"
            
            if success_count > 0:
                report += "\n\n成功重命名的文件:\n"
                report += "\n".join([f" - {item['original']} → {item['new_name']}" for item in result["success"]])
            
            if error_count > 0:
                report += "\n\n失败的文件:\n"
                report += "\n".join([f" - {item['filename']}: {item['error']}" for item in result["errors"]])
            
            return (report,)
                
        except Exception as e:
            return (f"严重错误: {str(e)}",)
    
    def _is_image_file(self, file_path):
        """
        检查文件是否为图片格式
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            bool: 是否为图片文件
        """
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}
        _, ext = os.path.splitext(file_path)
        return ext.lower() in image_extensions
    
    def _process_image(self, input_path, output_path, format_convert, max_size, original_ext):
        """
        处理图片：调整尺寸和格式转换
        
        Args:
            input_path (str): 输入文件路径
            output_path (str): 输出文件路径
            format_convert (str): 目标格式
            max_size (int): 最长边尺寸
            original_ext (str): 原始扩展名
        """
        try:
            # 打开图片
            with Image.open(input_path) as img:
                # 转换为RGB模式（适用于JPG）
                if format_convert == "jpg" and img.mode in ('RGBA', 'LA', 'P'):
                    # 创建白色背景
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                
                # 调整图片尺寸
                if max_size > 0:
                    img = self._resize_image(img, max_size)
                
                # 保存图片
                if format_convert == "jpg":
                    img.save(output_path, 'JPEG', quality=95, optimize=True)
                elif format_convert == "png":
                    img.save(output_path, 'PNG', optimize=True)
                else:
                    # 保持原格式但调整尺寸
                    img.save(output_path, optimize=True)
            
            # 删除原文件（如果路径不同）
            if input_path != output_path:
                os.remove(input_path)
                
        except Exception as e:
            # 如果图片处理失败，回退到普通重命名
            print(f"图片处理失败，回退到普通重命名: {e}")
            os.rename(input_path, output_path)
    
    def _resize_image(self, img, max_size):
        """
        调整图片尺寸，保持宽高比
        
        Args:
            img: PIL图片对象
            max_size (int): 最长边尺寸
            
        Returns:
            PIL.Image: 调整后的图片
        """
        width, height = img.size
        
        # 如果图片已经小于等于目标尺寸，不需要调整
        if max(width, height) <= max_size:
            return img
        
        # 计算缩放比例
        if width > height:
            new_width = max_size
            new_height = int(height * max_size / width)
        else:
            new_height = max_size
            new_width = int(width * max_size / height)
        
        # 使用高质量重采样
        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)

# 在 ComfyUI 中的节点映射配置
NODE_CLASS_MAPPINGS = {"PD_number_star": PD_number_star}
# 设置节点在 UI 中显示的名称
NODE_DISPLAY_NAME_MAPPINGS = {"PD_number_star": "PD_number_star"} 