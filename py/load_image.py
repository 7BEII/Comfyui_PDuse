import os
import re
import torch
import numpy as np
from PIL import Image, ImageOps
from typing import List, Tuple

class Load_Images_V1:
    """
    A ComfyUI node to recursively load multiple images from a directory and its subdirectories.
    """
    
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "directory": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "dynamicPrompts": False
                }),
            },
            "optional": {
                "image_load_cap": ("INT", {
                    "default": 0, 
                    "min": 0, 
                    "step": 1,
                    "display": "number"
                }),
                "start_index": ("INT", {
                    "default": 0, 
                    "min": 0, 
                    "max": 0xffffffffffffffff, 
                    "step": 1,
                    "display": "number"
                }),
                "load_always": ([False, True], {
                    "default": False
                }),
                "sort_method": (["numeric", "alphabetic", "natural"], {
                    "default": "numeric"
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                    "step": 1,
                    "display": "number",
                    "control_after_generate": True
                }),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK", "STRING", "STRING", "INT")
    RETURN_NAMES = ("images", "masks", "file_paths", "image_names", "image_numbers")
    FUNCTION = "load_images_recursive"
    CATEGORY = "PD_Image/Loading"
    OUTPUT_IS_LIST = (True, True, True, True, False)

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        if 'load_always' in kwargs and kwargs['load_always']:
            return float("NaN")
        
        # seed 的变化会触发重新加载
        seed = kwargs.get('seed', 0)
        return seed

    def numeric_sort_key(self, file_path: str) -> Tuple[int, str]:
        """
        数字排序键：专门处理纯数字文件名，如 1.jpg, 2.jpg, 10.jpg, 100.jpg
        """
        filename = os.path.basename(file_path)
        name, ext = os.path.splitext(filename)
        
        # 尝试提取文件名中的数字
        numbers = re.findall(r'\d+', name)
        if numbers:
            # 如果找到数字，使用第一个数字作为主要排序键
            return (int(numbers[0]), filename)
        else:
            # 如果没有数字，使用文件名作为次要排序键
            return (0, filename)

    def natural_sort_key(self, file_path: str) -> List:
        """
        自然排序键：智能处理数字和字母混合的文件名
        """
        filename = os.path.basename(file_path)
        # 将文件名分割成数字和非数字部分
        parts = re.split(r'(\d+)', filename)
        result = []
        for part in parts:
            if part.isdigit():
                result.append(int(part))
            else:
                result.append(part.lower())
        return result

    def get_all_image_files(self, directory: str, sort_method: str = "numeric") -> List[str]:
        """
        递归获取目录及其子目录中的所有图片文件，按指定方式排序
        特别优化了数字文件名的排序：1.jpg, 2.jpg, ..., 100.jpg
        """
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.gif']
        image_files = []
        searched_dirs = []
        
        print(f"开始递归搜索图片文件，根目录: {directory}")
        print(f"排序方式: {sort_method}")
        
        for root, dirs, files in os.walk(directory):
            searched_dirs.append(root)
            print(f"正在搜索目录: {root}")
            
            image_count_in_dir = 0
            for file in files:
                if any(file.lower().endswith(ext) for ext in valid_extensions):
                    full_path = os.path.join(root, file)
                    image_files.append(full_path)
                    image_count_in_dir += 1
            
            if image_count_in_dir > 0:
                print(f"  在目录 {root} 中找到 {image_count_in_dir} 张图片")
            
            if dirs:
                print(f"  发现 {len(dirs)} 个子文件夹: {dirs}")
        
        print(f"搜索完成！")
        print(f"总共搜索了 {len(searched_dirs)} 个目录")
        print(f"找到 {len(image_files)} 张图片")
        
        # 根据选择的排序方法进行排序
        if sort_method == "numeric":
            # 数字排序：专门处理 1.jpg, 2.jpg, 10.jpg, 100.jpg 这样的文件名
            image_files.sort(key=self.numeric_sort_key)
            print("使用数字排序：纯数字文件名按数值大小排序")
        elif sort_method == "alphabetic":
            # 字母排序：传统的字符串排序
            image_files.sort(key=lambda x: os.path.basename(x).lower())
            print("使用字母排序：按字符串顺序排序")
        elif sort_method == "natural":
            # 自然排序：处理混合的数字和字母
            image_files.sort(key=self.natural_sort_key)
            print("使用自然排序：智能处理数字和字母混合")
        else:
            # 默认使用数字排序
            image_files.sort(key=self.numeric_sort_key)
        
        print(f"排序完成，前10个文件:")
        for i, file_path in enumerate(image_files[:10]):
            filename = os.path.basename(file_path)
            print(f"  {i+1}. {filename}")
        
        return image_files

    def load_images_recursive(self, directory: str, image_load_cap: int = 0, start_index: int = 0, load_always=False, sort_method: str = "numeric", seed: int = 0):
        """
        递归加载目录及其子目录中的所有图片，按指定方式排序
        seed 参数用于触发重新加载
        """
        if not os.path.isdir(directory):
            raise FileNotFoundError(f"Directory '{directory}' cannot be found.")
        
        # 递归获取所有图片文件并按指定方式排序
        all_image_files = self.get_all_image_files(directory, sort_method)
        
        if len(all_image_files) == 0:
            error_msg = f"未在目录 '{directory}' 及其所有子目录中找到任何图片文件。\n"
            error_msg += f"支持的格式：png, jpg, jpeg, webp, bmp, tiff, gif\n"
            error_msg += f"请检查：\n"
            error_msg += f"1. 目录路径是否正确\n"
            error_msg += f"2. 目录及子目录中是否包含支持格式的图片文件\n"
            error_msg += f"3. 文件权限是否正确"
            raise FileNotFoundError(error_msg)

        print(f"Found {len(all_image_files)} image files in total (including subdirectories)")
        print(f"Files sorted by: {sort_method}")

        # 应用起始索引
        all_image_files = all_image_files[start_index:]

        images = []
        masks = []
        file_paths = []
        image_names = []

        limit_images = image_load_cap > 0
        image_count = 0

        for image_path in all_image_files:
            if limit_images and image_count >= image_load_cap:
                break
                
            try:
                # 加载图片
                i = Image.open(image_path)
                i = ImageOps.exif_transpose(i)
                image = i.convert("RGB")
                
                # 转换为张量格式 [B, H, W, C]
                image = np.array(image).astype(np.float32) / 255.0
                image = torch.from_numpy(image)[None,]  # 添加batch维度

                # 处理透明通道作为遮罩 [B, H, W]
                if 'A' in i.getbands():
                    mask = np.array(i.getchannel('A')).astype(np.float32) / 255.0
                    mask = 1. - torch.from_numpy(mask)  # 反转遮罩
                else:
                    # 如果没有透明通道，创建默认遮罩
                    height, width = image.shape[1], image.shape[2]
                    mask = torch.zeros((height, width), dtype=torch.float32, device="cpu")

                images.append(image)
                masks.append(mask)
                file_paths.append(str(image_path))
                image_names.append(os.path.basename(image_path))
                image_count += 1
                
                # 输出加载进度
                if image_count % 10 == 0:
                    print(f"Loaded {image_count} images...")
                    
            except Exception as e:
                print(f"Error loading image {image_path}: {e}")
                continue

        if not images:
            raise ValueError("No valid images could be loaded from the directory and its subdirectories.")

        print(f"Successfully loaded {len(images)} images")
        print(f"排序方式: {sort_method}")
        image_numbers = len(images)
        return (images, masks, file_paths, image_names, image_numbers)


# 节点映射配置
NODE_CLASS_MAPPINGS = {
    "PD_loadimage_path advance": Load_Images_V1
}

# 设置节点在 UI 中显示的名称
NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_loadimage_path advance": "PD_loadimage_path advance"
}