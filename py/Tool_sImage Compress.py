import torch
import numpy as np
from PIL import Image
import io
import os
import folder_paths

class PD_ImageCompress:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.prefix_append = ""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "target_kb": ("INT", {"default": 160, "min": 10, "max": 10240, "step": 1, "display": "number"}),
                "save_to_disk": ("BOOLEAN", {"default": True, "label_on": "Yes", "label_off": "No"}),
                "filename_prefix": ("STRING", {"default": "PD_compress"}),
            },
            "optional": {
                "mask": ("MASK",),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING",)
    RETURN_NAMES = ("compressed_image", "size_info",)
    FUNCTION = "compress"
    CATEGORY = "PDtools"
    OUTPUT_NODE = True

    def compress(self, image, target_kb, save_to_disk, filename_prefix, mask=None):
        target_bytes = target_kb * 1024
        output_tensors = []
        size_info_lines = []
        
        total_frames = image.shape[0]
        print(f"[PDtools] 开始处理，共 {total_frames} 帧，目标: {target_kb}KB")

        for i, img_tensor in enumerate(image):
            i_np = 255. * img_tensor.cpu().numpy()

            has_alpha = False
            if img_tensor.shape[-1] == 4:
                has_alpha = True
                img_pil = Image.fromarray(np.clip(i_np, 0, 255).astype(np.uint8), 'RGBA')
            else:
                img_pil = Image.fromarray(np.clip(i_np, 0, 255).astype(np.uint8), 'RGB')

            if mask is not None:
                has_alpha = True
                mask_tensor = mask[i] if i < mask.shape[0] else mask[0]
                alpha_np = 255. * mask_tensor.cpu().numpy()
                alpha_pil = Image.fromarray(np.clip(alpha_np, 0, 255).astype(np.uint8), mode='L')
                if img_pil.mode != 'RGBA':
                    img_pil = img_pil.convert('RGBA')
                img_pil.putalpha(alpha_pil)

            best_buffer = None
            saved = False

            buffer = io.BytesIO()
            img_pil.save(buffer, format="PNG", optimize=True)

            if len(buffer.getvalue()) <= target_bytes:
                best_buffer = buffer
                saved = True
                print(f"[PDtools] 帧 {i+1}/{total_frames} : 无损直接达标")
            else:
                color_steps = [256, 128, 64, 32]
                
                # 【核心修复】：不再分离 RGB 和 Alpha，把整图交给高级算法统一处理颜色
                for colors in color_steps:
                    try:
                        print(f"  > 帧 {i+1} 尝试 {colors} 色...")
                        
                        try:
                            # 终极大招：尝试调用 PIL 内置的 pngquant 内核 (method=3: LIBIMAGEQUANT)
                            # 它可以完美处理带有透明度的发光渐变，绝不变色
                            q_img = img_pil.quantize(colors=colors, method=3, dither=Image.Dither.FLOYDSTEINBERG)
                        except Exception:
                            # 如果你的环境没有编译 libimagequant，退而求其次使用 FASTOCTREE (method=2)
                            # method=2 也支持完整的 RGBA 调色板计算，比之前拆分通道强得多
                            q_img = img_pil.quantize(colors=colors, method=2, dither=Image.Dither.FLOYDSTEINBERG)

                        buffer = io.BytesIO()
                        q_img.save(buffer, format="PNG", optimize=True)

                        if len(buffer.getvalue()) <= target_bytes:
                            best_buffer = buffer
                            saved = True
                            print(f"[PDtools] 帧 {i+1}/{total_frames} : 降至 {colors} 色达标")
                            break
                    except Exception as e:
                        print(f"  > 帧 {i+1} 报错跳过: {e}")
                        pass
                
                if not saved and best_buffer is None:
                    best_buffer = buffer

            compressed_size = len(best_buffer.getvalue())
            w, h = img_pil.size
            info = f"[{i+1}] {w}x{h} | {compressed_size/1024:.1f} KB"
            if has_alpha: info += " | 带透明通道"
            size_info_lines.append(info)

            if save_to_disk:
                full_output_folder, filename, counter, subfolder, filename_prefix_final = folder_paths.get_save_image_path(filename_prefix, self.output_dir, w, h)
                file_name = f"{filename}_{counter:05d}.png"
                file_path = os.path.join(full_output_folder, file_name)
                with open(file_path, "wb") as f:
                    f.write(best_buffer.getvalue())

            best_buffer.seek(0)
            if has_alpha:
                best_img_pil = Image.open(best_buffer).convert("RGBA")
            else:
                best_img_pil = Image.open(best_buffer).convert("RGB")
            
            out_tensor = torch.from_numpy(np.array(best_img_pil).astype(np.float32) / 255.0)
            output_tensors.append(out_tensor)

        print(f"[PDtools] 全部处理完成！")
        size_info = "\n".join(size_info_lines)
        return (torch.stack(output_tensors, dim=0), size_info,)

NODE_CLASS_MAPPINGS = {"PD_ImageCompress": PD_ImageCompress}
NODE_DISPLAY_NAME_MAPPINGS = {"PD_ImageCompress": "PDtools: Image Compress"}