import os
import torch
import numpy as np
import zipfile
from PIL import Image, ImageOps
import io
import folder_paths

class PD_LoadImagesFromZip:
    """
    PD加载ZIP(输出列表) 节点 - 优化上传机制
    功能：通过 ComfyUI 的标准上传控件处理 ZIP 文件，并输出图片列表和文件名列表字符串。
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # 使用 widget="upload" 启用 ComfyUI 的标准上传控件。
                "zip_file_upload": ("STRING", {
                    "default": "",
                }),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    RETURN_NAMES = ("image_list", "name_list_str", "count")
    FUNCTION = "load_zip_images"
    CATEGORY = "PDuse/Image"
    
    # 告诉ComfyUI，image_list 是一个列表，name_list_str 和 count 是单值
    OUTPUT_IS_LIST = (True, False, False)

    def load_zip_images(self, zip_file_upload):
        image_list = []
        names = []
        
        # 1. 路径校验
        if not zip_file_upload:
            print(f"PD ZipLoader: 未选择或上传 ZIP 文件。")
            empty_tensor = torch.zeros((1, 64, 64, 3))
            return ([empty_tensor], "", 0)
            
        # ComfyUI 的上传控件会将文件保存到 input 目录，并返回文件名或哈希值。
        # 我们需要从 input 目录构造完整路径。
        input_dir = folder_paths.get_input_directory()
        zip_path = os.path.join(input_dir, zip_file_upload)
        
        if not os.path.exists(zip_path):
            # 检查用户是否输入了相对路径（例如 ComfyUI/input/subfolder/file.zip）
            if os.path.exists(zip_file_upload):
                zip_path = zip_file_upload
            else:
                print(f"PD ZipLoader: 找不到文件 {zip_path}")
                return ([], "", 0)
            
        try:
            # 2. 解压并读取
            with zipfile.ZipFile(zip_path, 'r') as z:
                file_list = z.namelist()
                file_list.sort()
                
                valid_extensions = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff'}
                
                for filename in file_list:
                    # 过滤掉文件夹和特殊文件
                    if filename.endswith('/'): continue
                    if '__MACOSX' in filename: continue
                    
                    ext = os.path.splitext(filename)[1].lower()
                    if ext not in valid_extensions: continue
                    
                    try:
                        # 3. 读取图片
                        data = z.read(filename)
                        img = Image.open(io.BytesIO(data))
                        
                        img = ImageOps.exif_transpose(img)
                        img = img.convert("RGB")
                        
                        # 4. 转 Tensor
                        img_np = np.array(img).astype(np.float32) / 255.0
                        img_tensor = torch.from_numpy(img_np)[None,]
                        
                        image_list.append(img_tensor)
                        
                        # 提取纯文件名
                        base_name = os.path.basename(filename)
                        names.append(base_name)
                        
                    except Exception as e:
                        print(f"PD ZipLoader: 警告 - 读取 {filename} 失败: {e}")
                        continue
                         
        except Exception as e:
            error_msg = f"PD ZipLoader: ZIP文件处理失败: {e}"
            print(error_msg)
            empty_tensor = torch.zeros((1, 64, 64, 3))
            return ([empty_tensor], error_msg, 0)

        # 5. 生成输出
        name_list_str = "\n".join(names)
        
        print(f"PD ZipLoader: 从 {zip_file_upload} 读取了 {len(image_list)} 张图片")
        
        if not image_list:
            empty_tensor = torch.zeros((1, 64, 64, 3))
            return ([empty_tensor], "", 0)

        return (image_list, name_list_str, len(image_list))

# 注册节点
NODE_CLASS_MAPPINGS = {
    "PD_LoadImagesFromZip": PD_LoadImagesFromZip
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_LoadImagesFromZip": "PD加载图片ZIP(输出列表)"
}