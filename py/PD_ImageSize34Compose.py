"""
PD: Image Size 3-4 Compose Node
批量处理图片：缩放最长边到指定尺寸，然后裁剪到3:4比例
"""

import os
from PIL import Image

class PD_ImageSize34Compose:
    """
    ComfyUI节点：批量处理图片，缩放最长边并裁剪到3:4比例
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "longer_size": ("INT", {
                    "default": 1024,
                    "min": 64,
                    "max": 4096,
                    "step": 1,
                    "display": "number"
                }),
                "input_path": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "输入图片文件夹路径"
                }),
                "output_path": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "输出图片文件夹路径（可选，留空则覆盖原图）"
                }),
                "rename_image": ("BOOLEAN", {
                    "default": True,
                    "label_on": "启用重命名",
                    "label_off": "保持原名"
                }),
                "rename_prefix": ("STRING", {
                    "default": "resize_",
                    "multiline": False,
                    "placeholder": "重命名前缀"
                })
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("message",)
    FUNCTION = "process_images"
    CATEGORY = "PD/Image Processing"
    
    def process_single_image(self, image_path, longer_size, aspect_ratio=(3, 4)):
        """
        处理单张图片：缩放最长边到指定尺寸，然后裁剪到指定比例
        
        Args:
            image_path: 图片路径
            longer_size: 最长边的目标尺寸
            aspect_ratio: (宽, 高) 的比例元组
        
        Returns:
            处理后的图片对象，或None（如果失败）
        """
        try:
            # 打开图片
            img = Image.open(image_path)
            
            # 如果是RGBA模式，转换为RGB
            if img.mode == 'RGBA':
                # 创建白色背景
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 步骤1：缩放最长边到longer_size
            width, height = img.size
            max_dimension = max(width, height)
            
            if max_dimension > longer_size:
                scale = longer_size / max_dimension
                new_width = int(width * scale)
                new_height = int(height * scale)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 步骤2：裁剪到指定比例
            current_width, current_height = img.size
            target_ratio = aspect_ratio[0] / aspect_ratio[1]
            current_ratio = current_width / current_height
            
            if abs(current_ratio - target_ratio) > 0.01:  # 如果比例不同才裁剪
                if current_ratio > target_ratio:
                    # 当前图片太宽，需要裁剪宽度
                    new_width = int(current_height * target_ratio)
                    new_height = current_height
                    left = (current_width - new_width) // 2
                    top = 0
                    right = left + new_width
                    bottom = current_height
                else:
                    # 当前图片太高，需要裁剪高度
                    new_width = current_width
                    new_height = int(current_width / target_ratio)
                    left = 0
                    top = (current_height - new_height) // 2
                    right = current_width
                    bottom = top + new_height
                
                img = img.crop((left, top, right, bottom))
            
            return img
            
        except Exception as e:
            print(f"  ❌ 处理图片失败 {image_path}: {str(e)}")
            return None
    
    def process_images(self, longer_size, input_path, output_path, rename_image, rename_prefix):
        """
        批量处理图片
        """
        try:
            # 验证输入路径
            if not input_path or not os.path.exists(input_path):
                return (f"❌ 错误: 输入路径 '{input_path}' 不存在或为空",)
            
            # 如果没有指定输出路径，使用输入路径
            if not output_path:
                output_path = input_path
            else:
                # 确保输出目录存在
                os.makedirs(output_path, exist_ok=True)
            
            # 支持的图片格式
            supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp')
            
            # 获取所有图片文件
            image_files = []
            for file in os.listdir(input_path):
                if file.lower().endswith(supported_formats):
                    image_files.append(file)
            
            if not image_files:
                return (f"❌ 在 '{input_path}' 中没有找到图片文件",)
            
            # 排序文件列表以确保一致的重命名顺序
            image_files.sort()
            
            print(f"\n📁 输入文件夹: {input_path}")
            print(f"📁 输出文件夹: {output_path}")
            print(f"🖼️  找到 {len(image_files)} 张图片")
            print(f"⚙️  配置: 最长边={longer_size}px, 比例=3:4")
            if rename_image:
                print(f"✏️  重命名: 启用 (前缀: {rename_prefix})")
            else:
                print(f"✏️  重命名: 禁用")
            print("=" * 60)
            
            success_count = 0
            fail_count = 0
            aspect_ratio = (3, 4)  # 固定3:4比例
            
            # 如果需要重命名，先处理所有图片并临时保存
            processed_images = []
            
            for i, filename in enumerate(image_files, 1):
                old_path = os.path.join(input_path, filename)
                print(f"\n[{i}/{len(image_files)}] 处理: {filename}")
                
                # 处理图片
                img = self.process_single_image(old_path, longer_size, aspect_ratio)
                
                if img:
                    if rename_image:
                        # 获取文件扩展名
                        _, ext = os.path.splitext(filename)
                        if not ext:
                            ext = '.jpg'
                        # 生成新文件名
                        new_filename = f"{rename_prefix}{i:02d}{ext}"
                        new_path = os.path.join(output_path, new_filename)
                        
                        # 保存到临时列表
                        processed_images.append((img, new_path, old_path))
                        print(f"  ✅ 处理成功 -> 将重命名为: {new_filename} -> 尺寸: {img.size}")
                    else:
                        # 保存到输出路径
                        if input_path == output_path:
                            # 覆盖原图
                            save_path = old_path
                        else:
                            # 保存到新路径
                            save_path = os.path.join(output_path, filename)
                        
                        img.save(save_path, quality=95)
                        print(f"  ✅ 处理成功 -> 尺寸: {img.size}")
                    
                    success_count += 1
                else:
                    fail_count += 1
            
            # 如果需要重命名，删除原图并保存新图
            if rename_image and processed_images:
                print("\n" + "=" * 60)
                print("正在重命名文件...")
                
                # 如果输入输出是同一个目录，先删除原图
                if input_path == output_path:
                    for _, _, old_path in processed_images:
                        try:
                            os.remove(old_path)
                        except:
                            pass
                
                # 保存所有新图
                for img, new_path, _ in processed_images:
                    img.save(new_path, quality=95)
                    print(f"  ✅ 已保存: {os.path.basename(new_path)}")
            
            # 生成结果消息
            result_message = f"✨ 处理完成! 成功: {success_count} 张, 失败: {fail_count} 张"
            print("\n" + "=" * 60)
            print(result_message)
            print("=" * 60)
            
            return (result_message,)
            
        except Exception as e:
            error_msg = f"❌ 处理过程中发生错误: {str(e)}"
            print(error_msg)
            return (error_msg,)

# 节点类映射
NODE_CLASS_MAPPINGS = {
    "PD_ImageSize34Compose": PD_ImageSize34Compose
}

# 节点显示名称映射
NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_ImageSize34Compose": "PD: Image Size 3-4 Compose"
}
