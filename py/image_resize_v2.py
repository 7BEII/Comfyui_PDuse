import torch
import numpy as np
import math
from PIL import Image

class PDImageResizeV2:
    """
    图片缩放裁切节点V2 
    (外部接口保持原有命名，底层逻辑与参数选项 1:1 完美复刻 LayerUtility: ImageScaleByAspectRatio V2)
    """
    RETURN_TYPES = ("IMAGE", "MASK",)
    FUNCTION = "image_scale"
    CATEGORY = "PDuse/Image"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "pixels": ("IMAGE",),
                "aspect_ratio": (["original", "custom", "1:1", "3:2", "4:3", "16:9", "21:9", "2:3", "3:4", "9:16", "9:21"], {"default": "original"}),
                # 上限放宽至 9999 对齐 LayerUtility V2
                "proportional_width": ("INT", {"default": 1, "min": 1, "max": 9999, "step": 1}),
                "proportional_height": ("INT", {"default": 1, "min": 1, "max": 9999, "step": 1}),
                "fit": (["letterbox", "crop", "fill"], {"default": "crop"}),
                "method": (["lanczos", "bicubic", "hamming", "bilinear", "box", "nearest"], {"default": "lanczos"}),
                # 选项对齐 LayerUtility V2 (新增 total_pixel(kilo pixel))
                "scale_to_side": (["longest", "shortest", "width", "height", "total_pixel(kilo pixel)"], {"default": "longest"}),
                "scale_to_length": ("INT", {"default": 1024, "min": 16, "max": 16777216, "step": 1}),
                # 选项对齐 LayerUtility V2 (新增 256, 512, 保留原有的 4)
                "round_to_multiple": (["None", "4", "8", "16", "32", "64", "128", "256", "512"], {"default": "8"}),
                "background_color": ("STRING", {"default": "#000000"}),
            },
            "optional": {
                "mask_optional": ("MASK",),
            },
        }

    def image_scale(self, pixels, aspect_ratio, proportional_width, proportional_height, 
                   fit, method, scale_to_side, scale_to_length, 
                   round_to_multiple, background_color, mask_optional=None):
        
        batch_size = pixels.shape[0]
        result_images = []
        result_masks = []
        
        # 采样算法映射
        method_map = {
            "lanczos": Image.LANCZOS,
            "bicubic": Image.BICUBIC,
            "hamming": Image.HAMMING,
            "bilinear": Image.BILINEAR,
            "box": Image.BOX,
            "nearest": Image.NEAREST
        }
        resample_filter = method_map[method]
        
        # 解析背景色HEX为RGB tuple
        bg_color_rgb = self._parse_hex_color(background_color)

        for i in range(batch_size):
            img_tensor = pixels[i]
            mask_tensor = mask_optional[i] if mask_optional is not None else None
            
            # 转换为PIL图像
            pil_image = self._tensor_to_pil(img_tensor)
            pil_mask = self._tensor_to_pil_mask(mask_tensor) if mask_tensor is not None else None
            
            orig_w, orig_h = pil_image.size
            
            # 1. 确定目标比例 (Target Aspect Ratio)
            if aspect_ratio == "original":
                target_ratio = orig_w / orig_h
            elif aspect_ratio == "custom":
                target_ratio = proportional_width / proportional_height
            else:
                w_str, h_str = aspect_ratio.split(":")
                target_ratio = float(w_str) / float(h_str)

            # 2. 计算基准尺寸 (Base Dimensions) - 完全对齐 LayerUtility V2
            if scale_to_side == "longest":
                if target_ratio > 1:
                    target_w = scale_to_length
                    target_h = target_w / target_ratio
                else:
                    target_h = scale_to_length
                    target_w = target_h * target_ratio
            elif scale_to_side == "shortest":
                if target_ratio > 1:
                    target_h = scale_to_length
                    target_w = target_h * target_ratio
                else:
                    target_w = scale_to_length
                    target_h = target_w / target_ratio
            elif scale_to_side == "width":
                target_w = scale_to_length
                target_h = target_w / target_ratio
            elif scale_to_side == "height":
                target_h = scale_to_length
                target_w = target_h * target_ratio
            elif scale_to_side == "total_pixel(kilo pixel)":
                # Kilo Pixel (千像素) 逻辑，总面积 = scale_to_length * 1000
                target_area = scale_to_length * 1000
                target_h = math.sqrt(target_area / target_ratio)
                target_w = target_h * target_ratio

            # 3. 对齐/取整 (Round to Multiple)
            if round_to_multiple != "None":
                multiple = int(round_to_multiple)
                target_w = max(multiple, round(target_w / multiple) * multiple)
                target_h = max(multiple, round(target_h / multiple) * multiple)
            else:
                target_w = max(1, int(round(target_w)))
                target_h = max(1, int(round(target_h)))
                
            target_w, target_h = int(target_w), int(target_h)

            # 4. 根据 fit 模式处理图像 (默认绝对居中)
            if fit == "fill":
                # 强制拉伸
                pil_image = pil_image.resize((target_w, target_h), resample_filter)
                if pil_mask:
                    pil_mask = pil_mask.resize((target_w, target_h), resample_filter)
                    
            elif fit == "crop":
                # 裁剪：先等比放大/缩小至填满目标画布，再裁切多余部分
                scale = max(target_w / orig_w, target_h / orig_h)
                scaled_w, scaled_h = int(round(orig_w * scale)), int(round(orig_h * scale))
                
                pil_image = pil_image.resize((scaled_w, scaled_h), resample_filter)
                if pil_mask:
                    pil_mask = pil_mask.resize((scaled_w, scaled_h), resample_filter)
                    
                left = max(0, (scaled_w - target_w) // 2)
                top = max(0, (scaled_h - target_h) // 2)
                
                crop_box = (left, top, left + target_w, top + target_h)
                pil_image = pil_image.crop(crop_box)
                if pil_mask:
                    pil_mask = pil_mask.crop(crop_box)
                    
            elif fit == "letterbox":
                # 留白：先等比缩放至完全包含在目标画布内，不足的部分填色
                scale = min(target_w / orig_w, target_h / orig_h)
                scaled_w, scaled_h = int(round(orig_w * scale)), int(round(orig_h * scale))
                
                pil_image = pil_image.resize((scaled_w, scaled_h), resample_filter)
                
                bg_img = Image.new("RGB", (target_w, target_h), bg_color_rgb)
                
                left = max(0, (target_w - scaled_w) // 2)
                top = max(0, (target_h - scaled_h) // 2)
                
                bg_img.paste(pil_image, (left, top))
                pil_image = bg_img
                
                if pil_mask:
                    pil_mask = pil_mask.resize((scaled_w, scaled_h), resample_filter)
                    bg_mask = Image.new("L", (target_w, target_h), 0) # 遮罩的背景填黑色(0)
                    bg_mask.paste(pil_mask, (left, top))
                    pil_mask = bg_mask

            # 5. 转换回张量
            result_images.append(self._pil_to_tensor(pil_image))
            if pil_mask is not None:
                result_masks.append(self._pil_mask_to_tensor(pil_mask))
            else:
                # 缺失mask时补充全黑张量
                result_masks.append(torch.zeros(target_h, target_w, dtype=torch.float32))

        # 合并批次
        final_images = torch.stack(result_images, dim=0)
        final_masks = torch.stack(result_masks, dim=0)

        return (final_images, final_masks)

    def _parse_hex_color(self, hex_color):
        """将HEX字符串解析为RGB元组"""
        hex_color = hex_color.strip().lstrip('#')
        try:
            if len(hex_color) == 6:
                return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            elif len(hex_color) == 3:
                return tuple(int(hex_color[i]*2, 16) for i in range(3))
        except ValueError:
            pass
        return (0, 0, 0)

    # ---------------- 基础数据转换辅助函数 ---------------- #
    def _tensor_to_pil(self, tensor):
        if tensor.dtype != torch.float32:
            tensor = tensor.float()
        tensor = tensor.cpu()
        tensor = torch.clamp(tensor, 0.0, 1.0)
        tensor_uint8 = (tensor * 255).to(torch.uint8)
        return Image.fromarray(tensor_uint8.numpy())

    def _tensor_to_pil_mask(self, tensor):
        if tensor is None:
            return None
        if tensor.dtype != torch.float32:
            tensor = tensor.float()
        tensor = tensor.cpu()
        tensor = torch.clamp(tensor, 0.0, 1.0)
        tensor_uint8 = (tensor * 255).to(torch.uint8)
        return Image.fromarray(tensor_uint8.numpy(), mode='L')

    def _pil_to_tensor(self, image):
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        elif image.mode == 'L':
            image = image.convert('RGB')
        return torch.from_numpy(np.array(image).astype(np.float32) / 255.0)

    def _pil_mask_to_tensor(self, mask):
        if mask.mode != 'L':
            mask = mask.convert('L')
        return torch.from_numpy(np.array(mask).astype(np.float32) / 255.0)

# 节点注册 (保持你的原命名)
NODE_CLASS_MAPPINGS = {
    "PDImageResizeV2": PDImageResizeV2,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PDImageResizeV2": "PDimage_resize_V2",
}