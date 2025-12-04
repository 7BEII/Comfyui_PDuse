import os
import torch
import numpy as np
from PIL import Image, ImageOps, ImageSequence
import folder_paths
import node_helpers

class PD_load_image_v1:
    @classmethod
    def INPUT_TYPES(s):
        input_dir = folder_paths.get_input_directory()
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        files = folder_paths.filter_files_content_types(files, ["image"])
        return {
            "required": {
                "image": (sorted(files), {"image_upload": True})
            },
        }

    CATEGORY = "PD:load image"
    
    RETURN_TYPES = ("IMAGE", "MASK", "STRING", "STRING")
    RETURN_NAMES = ("image", "mask", "image_name", "image_format")
    FUNCTION = "load_image"
    
    def load_image(self, image):
        """
        加载图片并返回图片数据、遮罩、图片名称和格式
        
        Args:
            image: 图片文件名
            
        Returns:
            tuple: (image_tensor, mask_tensor, image_name, image_format)
                - image_tensor: 图像张量 (B, H, W, C)
                - mask_tensor: 遮罩张量 (B, H, W)
                - image_name: 图片名称（不含扩展名）
                - image_format: 图片格式后缀（如 .jpg, .png）
        """
        # 获取图片路径
        image_path = folder_paths.get_annotated_filepath(image)
        
        # 提取图片名称和格式
        image_name, image_format = os.path.splitext(image)
        
        # 打开图片
        img = node_helpers.pillow(Image.open, image_path)

        output_images = []
        output_masks = []
        w, h = None, None

        excluded_formats = ['MPO']

        # 处理多帧图片（如GIF）
        for i in ImageSequence.Iterator(img):
            # 处理EXIF方向信息
            i = node_helpers.pillow(ImageOps.exif_transpose, i)

            # 处理特殊格式
            if i.mode == 'I':
                i = i.point(lambda i: i * (1 / 255))
            image_pil = i.convert("RGB")

            # 检查尺寸一致性
            if len(output_images) == 0:
                w = image_pil.size[0]
                h = image_pil.size[1]

            if image_pil.size[0] != w or image_pil.size[1] != h:
                continue

            # 转换为张量 (H, W, C)
            image_np = np.array(image_pil).astype(np.float32) / 255.0
            image_tensor = torch.from_numpy(image_np)[None,]  # 添加batch维度 (1, H, W, C)
            
            # 处理Alpha通道（遮罩）
            if 'A' in i.getbands():
                # 有Alpha通道，提取遮罩
                mask_np = np.array(i.getchannel('A')).astype(np.float32) / 255.0
                mask = 1. - torch.from_numpy(mask_np)  # 反转遮罩
            elif i.mode == 'P' and 'transparency' in i.info:
                # 调色板模式且有透明度信息
                mask_np = np.array(i.convert('RGBA').getchannel('A')).astype(np.float32) / 255.0
                mask = 1. - torch.from_numpy(mask_np)
            else:
                # 没有Alpha通道，创建全黑遮罩
                mask = torch.zeros((h, w), dtype=torch.float32, device="cpu")
            
            output_images.append(image_tensor)
            output_masks.append(mask.unsqueeze(0))  # 添加batch维度 (1, H, W)

        # 合并多帧或返回单帧
        if len(output_images) > 1 and img.format not in excluded_formats:
            output_image = torch.cat(output_images, dim=0)  # (B, H, W, C)
            output_mask = torch.cat(output_masks, dim=0)    # (B, H, W)
        else:
            output_image = output_images[0]  # (1, H, W, C)
            output_mask = output_masks[0]    # (1, H, W)

        # 打印调试信息
        print(f"✅ PD加载图片: {image}")
        print(f"   - 名称: {image_name}")
        print(f"   - 格式: {image_format}")
        print(f"   - 图像张量形状: {output_image.shape}")
        print(f"   - 遮罩张量形状: {output_mask.shape}")

        return (output_image, output_mask, image_name, image_format)


# 节点注册
NODE_CLASS_MAPPINGS = {
    "PD_load_image_v1": PD_load_image_v1
}

# 节点显示名称映射
NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_load_image_v1": "PD Load Image"
}

# 导出节点信息供ComfyUI使用
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

