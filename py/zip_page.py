import os
import zipfile
import io
import numpy as np
import torch
from PIL import Image
import folder_paths

class PD_Zip_Simple:
    """
    PD_Zip Simple (互斥优先版):
    1. 【优先级机制】：Images 输入优先。
       - 如果连接了 Images：只打包图片 (忽略 folder_path)。
       - 如果没连 Images：才打包 folder_path 指定的文件夹。
    2. 【文件夹模式】：原样打包，字节级无损复制。
    3. 【图像流模式】：支持 PNG (无损) 和 JPG (100%画质)。
    4. 【防覆盖】：自动重命名 (_1, _2)。
    """
    
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "zip_filename": ("STRING", {"default": "PD_Archive"}),
                # 仅在 images 优先模式下生效
                "save_format": (["png", "jpg"], {"default": "png"}), 
            },
            "optional": {
                "images": ("IMAGE",),
                "folder_path": ("STRING", {"default": "", "multiline": False, "placeholder": "文件夹路径：当 Images 未连接时才生效"}),
                "save_to": ("STRING", {"default": "", "placeholder": "保存路径 (留空则存到 ComfyUI/output)"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("message",)
    FUNCTION = "process"
    CATEGORY = "PD_Image/Saving"

    def process(self, zip_filename, save_format, images=None, folder_path="", save_to=""):

        # 1. 确定保存目录
        if save_to and save_to.strip() != "":
            output_dir = save_to
        else:
            output_dir = folder_paths.get_output_directory()
        
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                return (f"Error creating dir: {str(e)}",)

        # 2. 自动重命名逻辑 (防覆盖)
        if zip_filename.lower().endswith(".zip"):
            base_name = zip_filename[:-4]
        else:
            base_name = zip_filename

        counter = 0
        while True:
            if counter == 0:
                candidate_name = f"{base_name}.zip"
            else:
                candidate_name = f"{base_name}_{counter}.zip"
            
            full_zip_path = os.path.join(output_dir, candidate_name)
            
            if not os.path.exists(full_zip_path):
                break
            counter += 1

        # 绝对路径用于防死循环
        abs_zip_path = os.path.abspath(full_zip_path)
        files_count = 0
        images_count = 0
        
        try:
            print(f"--- PD_Zip_Simple: Saving to {candidate_name} ---")

            # 使用 Level 9 极限压缩容器
            with zipfile.ZipFile(full_zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
                
                # Logic: 互斥判断
                
                # === 情况 A: 检测到 Images 输入 (优先级最高) ===
                if images is not None:
                    print(">> Mode: Images Input Detected (Folder path ignored)")
                    
                    for i, image in enumerate(images):
                        # 转换 Tensor -> Numpy -> PIL
                        img_array = 255. * image.cpu().numpy()
                        img_array = np.clip(img_array, 0, 255).astype(np.uint8)
                        img_pil = Image.fromarray(img_array)
                        
                        img_buffer = io.BytesIO()
                        
                        # 根据格式编码
                        if save_format == "png":
                            # PNG 无损
                            img_pil.save(img_buffer, format="PNG", optimize=True, compress_level=9)
                            ext = "png"
                        else: 
                            # JPG 100% 画质
                            if img_pil.mode == 'RGBA':
                                img_pil = img_pil.convert('RGB')
                            img_pil.save(img_buffer, format="JPEG", quality=100, optimize=True, subsampling=0)
                            ext = "jpg"
                        
                        archive_name = f"img_{i+1:05d}.{ext}"
                        zipf.writestr(archive_name, img_buffer.getvalue())
                        images_count += 1

                # === 情况 B: 没有 Images，但有文件夹路径 ===
                elif folder_path and os.path.isdir(folder_path):
                    print(f">> Mode: Path Input Detected (Packing folder: {folder_path})")
                    
                    base_len = len(folder_path.rstrip(os.sep)) + 1
                    for root, dirs, files in os.walk(folder_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # 跳过自己
                            if os.path.abspath(file_path) == abs_zip_path:
                                continue
                            
                            archive_name = os.path.join("files", file_path[base_len:])
                            try:
                                # 原样字节复制，忽略 save_format
                                zipf.write(file_path, archive_name)
                                files_count += 1
                            except:
                                pass
                                
                else:
                    print(">> Warning: No valid input (Images or Folder Path) provided.")

            msg = f"Saved: {candidate_name} (Img:{images_count}, File:{files_count})"
            print(msg)
            return (full_zip_path,)

        except Exception as e:
            return (f"Error: {str(e)}",)

# 注册节点
NODE_CLASS_MAPPINGS = {
    "PD_Zip_Simple": PD_Zip_Simple
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_Zip_Simple": "PD_Zip Simple"
}