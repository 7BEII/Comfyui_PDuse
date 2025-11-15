import torch
import numpy as np
from PIL import Image, ImageOps
import folder_paths

class PDbananaImagesizeByRatio:
    """
    PD：banana imagesize by ratio
    图像按比例调整尺寸节点，支持多种预设比例、调整模式和图像位置
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "preset_size": (["1:1 (1024x1024)", "4:3 (1184x864)", "3:4 (864x1184)", 
                               "3:2 (1216x832)", "2:3 (832x1248)", "12:5 (1248x832)", 
                               "9:16 (768x1344)", "16:9 (1344x768)"], 
                               {"default": "4:3 (1184x864)"}),
                "resize_mode": (["crop", "pad", "stretch"], {"default": "pad"}),
                "image_location": (["top", "down", "left", "right", "center"], {"default": "center"}),
                "padding_color": (["black", "white", "noise"], {"default": "black"}),
            },
        }
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "resize_image"
    CATEGORY = "PDuse/Image"

    def resize_image(self, image, preset_size, resize_mode, image_location, padding_color):
        # 解析预设尺寸
        size_map = {
            "1:1 (1024x1024)": (1024, 1024),
            "4:3 (1184x864)": (1184, 864),
            "3:4 (864x1184)": (864, 1184),
            "3:2 (1216x832)": (1216, 832),
            "2:3 (832x1248)": (832, 1248),
            "12:5 (1248x832)": (1248, 832),
            "9:16 (768x1344)": (768, 1344),
            "16:9 (1344x768)": (1344, 768)
        }
        
        target_width, target_height = size_map[preset_size]
        target_size = (target_width, target_height)
        
        # 转换tensor到PIL图像
        if image.dim() == 4:
            image = image.squeeze(0)  # 移除batch维度
        
        # 将tensor转换为numpy数组，然后转换为PIL图像
        image_np = image.cpu().numpy()
        if image_np.dtype != np.uint8:
            image_np = (image_np * 255).astype(np.uint8)
        
        pil_image = Image.fromarray(image_np)
        original_width, original_height = pil_image.size
        
        processed_image = None
        
        if resize_mode == "crop":
            # 裁切模式：保持比例，裁切多余部分
            processed_image = self._crop_resize(pil_image, target_size, image_location)
        elif resize_mode == "pad":
            # 填充模式：保持比例，添加填充
            processed_image = self._pad_resize(pil_image, target_size, image_location, padding_color)
        elif resize_mode == "stretch":
            # 拉伸模式：直接拉伸到目标尺寸
            processed_image = pil_image.resize(target_size, Image.Resampling.LANCZOS)
        
        # 确保图像是RGB模式
        if processed_image.mode != 'RGB':
            processed_image = processed_image.convert('RGB')
        
        # 转换回tensor
        result_np = np.array(processed_image).astype(np.float32) / 255.0
        result_tensor = torch.from_numpy(result_np).unsqueeze(0)  # 添加batch维度
        
        return (result_tensor,)
    
    def _crop_resize(self, image, target_size, location):
        """裁切模式：保持比例，裁切多余部分"""
        target_width, target_height = target_size
        original_width, original_height = image.size
        
        # 计算缩放比例，保持较大的比例以填满目标尺寸
        scale_w = target_width / original_width
        scale_h = target_height / original_height
        scale = max(scale_w, scale_h)
        
        # 按比例缩放
        new_width = int(original_width * scale)
        new_height = int(original_height * scale)
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # 根据位置设置裁切区域 - 水平方向
        if location in ["left", "center", "right"]:
            if location == "left":
                left = 0
            elif location == "right":
                left = new_width - target_width
            else:  # center
                left = (new_width - target_width) // 2
            top = (new_height - target_height) // 2
        # 垂直方向
        else:  # top or down
            left = (new_width - target_width) // 2
            if location == "top":
                top = 0
            else:  # down
                top = new_height - target_height
        
        right = left + target_width
        bottom = top + target_height
        
        # 裁切
        cropped_image = resized_image.crop((left, top, right, bottom))
        return cropped_image
    
    def _pad_resize(self, image, target_size, location, padding_color):
        """填充模式：保持比例，添加填充"""
        target_width, target_height = target_size
        original_width, original_height = image.size
        
        # 计算缩放比例，保持较小的比例以适应目标尺寸
        scale_w = target_width / original_width
        scale_h = target_height / original_height
        scale = min(scale_w, scale_h)
        
        # 按比例缩放
        new_width = int(original_width * scale)
        new_height = int(original_height * scale)
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # 根据padding_color选择背景
        if padding_color == "white":
            bg_color = (255, 255, 255)
            result_image = Image.new('RGB', target_size, bg_color)
        elif padding_color == "noise":
            # 生成类似latent空间的噪声图
            # 使用正态分布生成噪声，均值128，标准差64，模拟灰色噪声
            noise_array = np.random.randn(target_height, target_width, 3) * 64 + 128
            noise_array = np.clip(noise_array, 0, 255).astype(np.uint8)
            result_image = Image.fromarray(noise_array, 'RGB')
        else:  # black
            bg_color = (0, 0, 0)
            result_image = Image.new('RGB', target_size, bg_color)
        
        # 根据位置设置粘贴位置 - 水平方向
        if location in ["left", "center", "right"]:
            if location == "left":
                paste_x = 0
            elif location == "right":
                paste_x = target_width - new_width
            else:  # center
                paste_x = (target_width - new_width) // 2
            paste_y = (target_height - new_height) // 2
        # 垂直方向
        else:  # top or down
            paste_x = (target_width - new_width) // 2
            if location == "top":
                paste_y = 0
            else:  # down
                paste_y = target_height - new_height
        
        # 将缩放后的图像粘贴到背景上
        result_image.paste(resized_image, (paste_x, paste_y))
        return result_image

# 节点映射
NODE_CLASS_MAPPINGS = {
    "PDbananaImagesizeByRatio": PDbananaImagesizeByRatio
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PDbananaImagesizeByRatio": "PD：banana imagesize by ratio"
}
