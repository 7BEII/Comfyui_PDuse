import os
import torch
import numpy as np
from PIL import Image, ImageOps

class PD_LoadImagesPath:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "directory_path": ("STRING", {
                    "default": "", 
                    "multiline": False, 
                    "placeholder": "输入文件夹路径 (例如: C:/Images/Lineart)"
                }),
                "limit_count": ("INT", {
                    "default": 0, 
                    "min": 0, 
                    "max": 10000, 
                    "step": 1,
                    "label": "限制读取数量(0为不限)"
                }),
            }
        }

    # 更新返回类型，增加 MASK 列表
    RETURN_TYPES = ("IMAGE", "MASK", "STRING", "INT")
    RETURN_NAMES = ("image_list", "mask_list", "name_list_str", "count")
    FUNCTION = "load_images"
    CATEGORY = "PDuse/Image"
    
    # 配置：image_list 和 mask_list 均为列表(True)
    OUTPUT_IS_LIST = (True, True, False, False)

    def load_images(self, directory_path, limit_count):
        image_list = []
        mask_list = []
        names = []
        
        # 1. 路径校验
        if not directory_path or not os.path.exists(directory_path):
            print(f"PD Loader: 路径不存在 -> {directory_path}")
            empty_img = torch.zeros((1, 64, 64, 3))
            empty_mask = torch.zeros((1, 64, 64))
            return ([empty_img], [empty_mask], "", 0)

        # 2. 获取文件列表
        valid_extensions = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff'}
        files = [f for f in os.listdir(directory_path) 
                 if os.path.splitext(f)[1].lower() in valid_extensions]
        
        files.sort()
        
        if limit_count > 0:
            files = files[:limit_count]

        # 3. 循环读取图片和生成 Mask
        for filename in files:
            file_path = os.path.join(directory_path, filename)
            try:
                img = Image.open(file_path)
                img = ImageOps.exif_transpose(img) # 处理旋转
                
                # --- 处理 Mask ---
                if 'A' in img.getbands():
                    # 如果有 Alpha 通道，提取它
                    mask = np.array(img.getchannel('A')).astype(np.float32) / 255.0
                    mask = torch.from_numpy(mask)
                else:
                    # 如果没有 Alpha 通道，创建一个全白（不透明）的 Mask
                    mask = torch.ones((img.height, img.width), dtype=torch.float32)
                
                # --- 处理 Image ---
                img = img.convert("RGB")
                img_np = np.array(img).astype(np.float32) / 255.0
                img_tensor = torch.from_numpy(img_np)[None,]
                
                image_list.append(img_tensor)
                mask_list.append(mask[None,]) # Mask 格式通常为 (1, H, W)
                names.append(filename)
                
            except Exception as e:
                print(f"PD Loader: 无法读取图片 {filename} - {e}")
                continue

        # 4. 生成输出
        name_list_str = "\n".join(names)
        
        if not image_list:
            empty_img = torch.zeros((1, 64, 64, 3))
            empty_mask = torch.zeros((1, 64, 64))
            return ([empty_img], [empty_mask], "", 0)

        print(f"PD Loader: 已从 {directory_path} 读取 {len(image_list)} 张图片及对应 Mask")
        return (image_list, mask_list, name_list_str, len(image_list))

# 注册节点名称修改
NODE_CLASS_MAPPINGS = {
    "PD_LoadImagesPath": PD_LoadImagesPath
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_LoadImagesPath": "PD_load image path"
}