import os
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
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK", "STRING")
    RETURN_NAMES = ("images", "masks", "file_paths")
    FUNCTION = "load_images_recursive"
    CATEGORY = "PD_Image/Loading"
    OUTPUT_IS_LIST = (True, True, True)

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        if 'load_always' in kwargs and kwargs['load_always']:
            return float("NaN")
        else:
            return hash(frozenset(kwargs))

    def get_all_image_files(self, directory: str) -> List[str]:
        """
        递归获取目录及其子目录中的所有图片文件
        """
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        image_files = []
        searched_dirs = []
        
        print(f"开始递归搜索图片文件，根目录: {directory}")
        
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
            
            # 显示子文件夹信息
            if dirs:
                print(f"  发现 {len(dirs)} 个子文件夹: {dirs}")
        
        print(f"搜索完成！")
        print(f"总共搜索了 {len(searched_dirs)} 个目录")
        print(f"找到 {len(image_files)} 张图片")
        
        # 按文件路径排序以确保一致性
        return sorted(image_files)

    def load_images_recursive(self, directory: str, image_load_cap: int = 0, start_index: int = 0, load_always=False):
        """
        递归加载目录及其子目录中的所有图片
        """
        if not os.path.isdir(directory):
            raise FileNotFoundError(f"Directory '{directory}' cannot be found.")
        
        # 递归获取所有图片文件
        all_image_files = self.get_all_image_files(directory)
        
        if len(all_image_files) == 0:
            error_msg = f"未在目录 '{directory}' 及其所有子目录中找到任何图片文件。\n"
            error_msg += f"支持的格式：png, jpg, jpeg, webp\n"
            error_msg += f"请检查：\n"
            error_msg += f"1. 目录路径是否正确\n"
            error_msg += f"2. 目录及子目录中是否包含支持格式的图片文件\n"
            error_msg += f"3. 文件权限是否正确"
            raise FileNotFoundError(error_msg)

        print(f"Found {len(all_image_files)} image files in total (including subdirectories)")

        # 应用起始索引
        all_image_files = all_image_files[start_index:]

        images = []
        masks = []
        file_paths = []

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
                image_count += 1
                
                # 输出加载进度
                if image_count % 10 == 0:
                    print(f"Loaded {image_count} images...")
                    
            except Exception as e:
                print(f"Error loading image {image_path}: {e}")
                continue

        if not images:
            raise ValueError("No valid images could be loaded from the directory and its subdirectories.")

        print(f"Successfully loaded {len(images)} images from '{directory}' and subdirectories")
        return (images, masks, file_paths)


# 节点映射配置
NODE_CLASS_MAPPINGS = {
    "Load_Images_V1": Load_Images_V1
}

# 设置节点在 UI 中显示的名称
NODE_DISPLAY_NAME_MAPPINGS = {
    "Load_Images_V1": "PDIMAGE:Load_Images_V1"
} 