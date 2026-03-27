import os
import zipfile
import io
import tempfile
import numpy as np
import torch
import re
from PIL import Image
import folder_paths

class AnyType(str):
    def __ne__(self, __value: object) -> bool:
        return False
ANY = AnyType("*")

class PD_ZIP_Packingsave:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "data": (ANY, ),
                "filename_prefix": ("STRING", {"default": "PD_ZIP_Archive"}),
            },
            "optional": {
                "custom_names": ("STRING", {"forceInput": True}), 
            }
        }

    INPUT_IS_LIST = True 
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("zip_path", "file_size")
    FUNCTION = "save_to_zip"
    OUTPUT_NODE = True
    CATEGORY = "PDTool"

    def format_bytes(self, size_in_bytes):
        power = 1024
        n = 0
        power_labels = {0: 'Bytes', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
        while size_in_bytes >= power and n < 4:
            size_in_bytes /= power
            n += 1
        return f"{size_in_bytes:.2f} {power_labels[n]}"

    def sanitize_filename(self, name):
        if not isinstance(name, str):
            name = str(name)
        name = name.replace('\n', ' ').replace('\r', '').strip()
        name = re.sub(r'[\\/*?:"<>|]', '_', name)
        if len(name) > 120:
            name = name[:120].strip('_ ')
        return name if name else "unnamed_file"

    def save_to_zip(self, data, filename_prefix, custom_names=None):
        prefix = filename_prefix[0] if isinstance(filename_prefix, list) else filename_prefix
        prefix = self.sanitize_filename(prefix)
        
        # 获取路径参数
        full_output_folder, filename, counter, subfolder, final_prefix = folder_paths.get_save_image_path(prefix, self.output_dir)
        zip_filename = f"{filename}_{counter:05d}.zip"
        zip_path = os.path.join(full_output_folder, zip_filename)
        
        saved_count = 0
        used_names = set()
        flat_names = []

        if custom_names is not None:
            def extract_names(item):
                if isinstance(item, (list, tuple)):
                    for x in item:
                        extract_names(x)
                elif isinstance(item, str):
                    item = item.strip()
                    if '\n' in item:
                        flat_names.extend([x.strip() for x in item.split('\n') if x.strip()])
                    elif ',' in item:
                        flat_names.extend([x.strip() for x in item.split(',') if x.strip()])
                    elif re.search(r'\.(png|jpg|jpeg|webp|txt)\s+', item, re.IGNORECASE):
                        item = re.sub(r'(\.(png|jpg|jpeg|webp|txt))\s+', r'\1|', item, flags=re.IGNORECASE)
                        flat_names.extend([x.strip() for x in item.split('|') if x.strip()])
                    else:
                        flat_names.append(item)
                elif item is not None:
                    flat_names.append(str(item))
            extract_names(custom_names)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            def get_internal_name(ext, default_name):
                if flat_names and saved_count < len(flat_names):
                    n = self.sanitize_filename(flat_names[saved_count])
                    if not n.lower().endswith(ext.lower()):
                        n += ext
                else:
                    n = default_name

                if n not in used_names:
                    used_names.add(n)
                    return n
                
                base_name, current_ext = os.path.splitext(n)
                duplicate_counter = 1
                while True:
                    new_name = f"{base_name}_{duplicate_counter}{current_ext}"
                    if new_name not in used_names:
                        used_names.add(new_name)
                        return new_name
                    duplicate_counter += 1

            def process_item(item, base_name):
                nonlocal saved_count
                if item is None: return
                if isinstance(item, (list, tuple)):
                    for sub_item in item: process_item(sub_item, base_name)
                elif isinstance(item, str):
                    if os.path.isfile(item):
                        file_name = os.path.basename(item)
                        ext = os.path.splitext(file_name)[1]
                        default_name = f"{saved_count:03d}_{file_name}"
                        zip_internal_path = get_internal_name(ext, default_name)
                        zipf.write(item, arcname=zip_internal_path)
                        saved_count += 1
                    else:
                        default_name = f"{base_name}_{saved_count:03d}.txt"
                        zip_internal_path = get_internal_name('.txt', default_name)
                        zipf.writestr(zip_internal_path, item.encode('utf-8'))
                        saved_count += 1
                elif isinstance(item, torch.Tensor):
                    if len(item.shape) == 4:
                        for i in range(item.shape[0]): process_item(item[i], base_name)
                    elif len(item.shape) == 3 and item.shape[-1] in [1, 3, 4]:
                        i_tensor = 255. * item.cpu().numpy()
                        img = Image.fromarray(np.clip(i_tensor, 0, 255).astype(np.uint8))
                        img_byte_arr = io.BytesIO()
                        img.save(img_byte_arr, format='PNG')
                        default_name = f"{base_name}_{saved_count:03d}.png"
                        zip_internal_path = get_internal_name('.png', default_name)
                        zipf.writestr(zip_internal_path, img_byte_arr.getvalue())
                        saved_count += 1
                elif isinstance(item, dict) and "waveform" in item and "sample_rate" in item:
                    try:
                        import torchaudio
                        waveform = item["waveform"]
                        sample_rate = item["sample_rate"]
                        if len(waveform.shape) == 3: waveform = waveform.squeeze(0)
                        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
                            temp_path = tmp_wav.name
                        torchaudio.save(temp_path, waveform, sample_rate)
                        default_name = f"{base_name}_{saved_count:03d}.wav"
                        zip_internal_path = get_internal_name('.wav', default_name)
                        with open(temp_path, "rb") as f: zipf.writestr(zip_internal_path, f.read())
                        os.remove(temp_path)
                        saved_count += 1
                    except Exception as e:
                        print(f"Zip Audio Error: {e}")

            process_item(data, filename)

        if saved_count == 0:
            if os.path.exists(zip_path):
                os.remove(zip_path)
            return {"ui": {"text": ["No valid data recognized to save."]}, "result": ([], [])}

        file_size_bytes = os.path.getsize(zip_path)
        formatted_size = self.format_bytes(file_size_bytes)

        # 🌟 核心修改点：给前端发送 ZIP 的详细信息
        ui_result = {
            "text": [f"Saved {saved_count} files.\nSize: {formatted_size}"],
            "zip": [{"filename": zip_filename, "subfolder": subfolder, "type": "output"}]
        }

        return {"ui": ui_result, "result": ([zip_path], [formatted_size])}

# 节点注册
NODE_CLASS_MAPPINGS = {
    "PD_ZIP_Packingsave": PD_ZIP_Packingsave
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_ZIP_Packingsave": "PDTool:ZIP Packingsave 📦"
}
