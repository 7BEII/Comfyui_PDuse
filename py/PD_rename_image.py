import os
from PIL import Image
import folder_paths

class PD_rename_image:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "input_path": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "placeholder": "输入图片文件夹路径"
                }),
                "max_size": ("INT", {
                    "default": 1024,
                    "min": 128,
                    "max": 4096,
                    "step": 64,
                    "display": "number"
                }),
                "output_format": (["JPG", "PNG"], {
                    "default": "JPG"
                }),
                "rename_pattern": ("STRING", {
                    "multiline": False,
                    "default": "img_{index:04d}",
                    "placeholder": "重命名模式，如 img_{index:04d}"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("result",)
    FUNCTION = "process_images"
    CATEGORY = "PD_Tools"
    
    def resize_image_keep_ratio(self, image, max_size):
        """保持宽高比调整图片尺寸"""
        width, height = image.size
        
        # 计算缩放比例
        if width > height:
            if width > max_size:
                ratio = max_size / width
                new_width = max_size
                new_height = int(height * ratio)
            else:
                return image
        else:
            if height > max_size:
                ratio = max_size / height
                new_height = max_size
                new_width = int(width * ratio)
            else:
                return image
        
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    def process_images(self, input_path, max_size, output_format, rename_pattern):
        """处理图片批量重命名和格式转换"""
        
        if not os.path.exists(input_path):
            return (f"错误: 路径 {input_path} 不存在",)
        
        if not os.path.isdir(input_path):
            return (f"错误: {input_path} 不是一个文件夹",)
        
        # 支持的图片格式
        supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        
        # 获取所有图片文件
        image_files = []
        for file_name in os.listdir(input_path):
            file_path = os.path.join(input_path, file_name)
            if os.path.isfile(file_path):
                _, ext = os.path.splitext(file_name.lower())
                if ext in supported_formats:
                    image_files.append(file_name)
        
        if not image_files:
            return (f"在路径 {input_path} 中未找到支持的图片文件",)
        
        # 按文件名排序确保处理顺序一致
        image_files.sort()
        
        processed_count = 0
        error_count = 0
        error_messages = []
        
        for index, file_name in enumerate(image_files):
            try:
                old_file_path = os.path.join(input_path, file_name)
                
                # 生成新文件名
                new_name = rename_pattern.format(index=index + 1, original=os.path.splitext(file_name)[0])
                new_file_name = f"{new_name}.{output_format.lower()}"
                new_file_path = os.path.join(input_path, new_file_name)
                
                # 打开并处理图片
                with Image.open(old_file_path) as img:
                    # 转换为RGB模式（对于JPG格式）
                    if output_format.upper() == "JPG" and img.mode in ("RGBA", "LA", "P"):
                        # 创建白色背景
                        background = Image.new("RGB", img.size, (255, 255, 255))
                        if img.mode == "P":
                            img = img.convert("RGBA")
                        background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                        img = background
                    elif output_format.upper() == "PNG" and img.mode not in ("RGBA", "RGB", "L"):
                        img = img.convert("RGBA")
                    # 调整图片尺寸
                    resized_img = self.resize_image_keep_ratio(img, max_size)
                    
                    # 保存处理后的图片
                    save_kwargs = {}
                    if output_format.upper() == "JPG":
                        save_kwargs = {"format": "JPEG", "quality": 95, "optimize": True}
                    elif output_format.upper() == "PNG":
                        save_kwargs = {"format": "PNG", "optimize": True}
                    
                    resized_img.save(new_file_path, **save_kwargs)
                
                # 如果新文件名与原文件名不同，删除原文件
                if old_file_path != new_file_path and os.path.exists(new_file_path):
                    os.remove(old_file_path)
                
                processed_count += 1
                
            except Exception as e:
                error_count += 1
                error_messages.append(f"处理文件 {file_name} 时出错: {str(e)}")
                continue
        
        # 生成结果报告
        result_lines = [
            f"批量处理完成!",
            f"处理路径: {input_path}",
            f"最长边限制: {max_size}px",
            f"输出格式: {output_format}",
            f"成功处理: {processed_count} 张图片",
        ]
        
        if error_count > 0:
            result_lines.append(f"处理失败: {error_count} 张图片")
            result_lines.extend(error_messages[:5])  # 只显示前5个错误
            if len(error_messages) > 5:
                result_lines.append(f"... 还有 {len(error_messages) - 5} 个错误未显示")
        
        return ("\n".join(result_lines),)
# 节点映射注册
NODE_CLASS_MAPPINGS = {
    "PD_rename_image": PD_rename_image
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_rename_image": "PD_rename_image"
}
