import os
import torch
import numpy as np
from PIL import Image, ImageOps

class PD_LoadImagesFromDir:
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

    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    RETURN_NAMES = ("image_list", "name_list_str", "count")
    FUNCTION = "load_images"
    CATEGORY = "PDuse/Image"
    
    # 输出配置：image_list 是列表(True)，name_list_str 是单串文本(False)，count 是单值(False)
    OUTPUT_IS_LIST = (True, False, False)

    def load_images(self, directory_path, limit_count):
        image_list = []
        names = []
        
        # 1. 路径校验
        if not directory_path or not os.path.exists(directory_path):
            print(f"PD Loader: 路径不存在 -> {directory_path}")
            # 返回空数据防止报错崩溃
            empty_tensor = torch.zeros((1, 64, 64, 3))
            return ([empty_tensor], "", 0)

        # 2. 获取文件列表并排序
        valid_extensions = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff'}
        files = [f for f in os.listdir(directory_path) 
                 if os.path.splitext(f)[1].lower() in valid_extensions]
        
        # 按文件名排序，确保顺序稳定
        files.sort()
        
        # 应用数量限制
        if limit_count > 0:
            files = files[:limit_count]

        # 3. 循环读取图片
        for filename in files:
            file_path = os.path.join(directory_path, filename)
            try:
                img = Image.open(file_path)
                
                # 处理旋转信息 (EXIF)
                img = ImageOps.exif_transpose(img)
                
                # 统一转为 RGB
                img = img.convert("RGB")
                
                # 转为 Tensor (1, H, W, C)
                img_np = np.array(img).astype(np.float32) / 255.0
                img_tensor = torch.from_numpy(img_np)[None,]
                
                image_list.append(img_tensor)
                names.append(filename)
                
            except Exception as e:
                print(f"PD Loader: 无法读取图片 {filename} - {e}")
                continue

        # 4. 生成输出
        # 将名称列表合并为一个长字符串，用换行符分隔，直接传给匹配节点
        name_list_str = "\n".join(names)
        
        print(f"PD Loader: 已从 {directory_path} 读取 {len(image_list)} 张图片")
        
        # 如果没读到图，返回一张黑图防止后续节点报错
        if not image_list:
            empty_tensor = torch.zeros((1, 64, 64, 3))
            return ([empty_tensor], "", 0)

        return (image_list, name_list_str, len(image_list))

# 注册节点
NODE_CLASS_MAPPINGS = {
    "PD_LoadImagesFromDir": PD_LoadImagesFromDir
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_LoadImagesFromDir": "PD加载文件夹(输出列表)"
}