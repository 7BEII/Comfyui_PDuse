import torch
import numpy as np
from PIL import Image

class PDImageResizeV3:
    """
    图片缩放裁切节点V3，支持：
    1. 通过最长边或最短边缩放图片
    2. 三种裁切模式：
       - none: 不改变比例，只缩放
       - crop: 按具体尺寸裁切后缩放
       - stretch: 强制拉伸到目标尺寸
    3. 支持多种对齐方向（左中右，上中下）
    输出为处理后的图片和对应的 mask。
    """
    RETURN_TYPES = ("IMAGE", "MASK",)
    FUNCTION = "resize_and_crop"
    CATEGORY = "PDuse/Image"

    @classmethod
    def INPUT_TYPES(cls):
        """
        返回节点的输入参数定义。
        @returns {dict} 输入参数定义
        """
        return {
            "required": {
                "pixels": ("IMAGE",),
                "resize_mode": (["longest", "shortest"], {"default": "longest"}),
                "target_size": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
                "crop_mode": (["none", "crop", "stretch"], {"default": "none"}),
                "target_width": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
                "target_height": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
                "horizontal_align": (["left", "center", "right"], {"default": "center"}),
                "vertical_align": (["top", "center", "bottom"], {"default": "center"}),
            },
            "optional": {
                "mask_optional": ("MASK",),
            },
        }

    @classmethod
    def VALIDATE_INPUTS(cls, resize_mode, target_size, target_width, target_height, **_):
        """
        校验输入参数。
        @param resize_mode {str} 缩放模式：longest 或 shortest
        @param target_size {int} 目标尺寸
        @param target_width {int} 目标宽度
        @param target_height {int} 目标高度
        @returns {True|str} 校验通过返回 True，否则返回错误信息
        """
        if target_size <= 0:
            return "目标尺寸必须大于0"
        if target_width <= 0 or target_height <= 0:
            return "目标宽度和高度必须大于0"
        return True

    def resize_and_crop(self, pixels, resize_mode, target_size, crop_mode, target_width, target_height, 
                       horizontal_align, vertical_align, mask_optional=None):
        """
        按照指定模式缩放和裁切图片。
        @param pixels {Tensor} 输入图片，形状为 (B, H, W, C)
        @param resize_mode {str} 缩放模式：longest 或 shortest
        @param target_size {int} 目标尺寸
        @param crop_mode {str} 裁切模式：none/crop/stretch
        @param target_width {int} 目标宽度
        @param target_height {int} 目标高度
        @param horizontal_align {str} 水平对齐方式
        @param vertical_align {str} 垂直对齐方式
        @param mask_optional {Tensor|None} 可选 mask，形状为 (B, H, W)
        @returns {tuple} (处理后的图片, 处理后的 mask)
        """
        validity = self.VALIDATE_INPUTS(resize_mode, target_size, target_width, target_height)
        if validity is not True:
            raise Exception(validity)

        batch_size = pixels.shape[0]
        result_images = []
        result_masks = []

        for i in range(batch_size):
            img_tensor = pixels[i]
            mask_tensor = mask_optional[i] if mask_optional is not None else None
            
            # 转换为PIL图像进行处理
            pil_image = self._tensor_to_pil(img_tensor)
            pil_mask = self._tensor_to_pil_mask(mask_tensor) if mask_tensor is not None else None
            
            # 根据裁切模式处理图像
            if crop_mode == "crop":
                # 尺寸裁切模式：先按目标尺寸比例裁切后缩放
                pil_image, pil_mask = self._crop_by_size_and_align(
                    pil_image, pil_mask, target_width, target_height, horizontal_align, vertical_align
                )
                pil_image, pil_mask = self._resize_image_and_mask(
                    pil_image, pil_mask, resize_mode, target_size
                )
            elif crop_mode == "stretch":
                # 强制拉伸模式：直接拉伸到目标尺寸
                pil_image, pil_mask = self._stretch_to_size(
                    pil_image, pil_mask, target_width, target_height
                )
            else:  # crop_mode == "none"
                # 无裁切模式：只按原比例缩放
                pil_image, pil_mask = self._resize_image_and_mask(
                    pil_image, pil_mask, resize_mode, target_size
                )
            
            # 转换回张量
            result_images.append(self._pil_to_tensor(pil_image))
            if pil_mask is not None:
                result_masks.append(self._pil_mask_to_tensor(pil_mask))
            else:
                # 如果没有mask，创建一个全零的mask
                h, w = pil_image.size[1], pil_image.size[0]
                result_masks.append(torch.zeros(h, w, dtype=torch.float32))

        # 合并批次
        final_images = torch.stack(result_images, dim=0)
        final_masks = torch.stack(result_masks, dim=0)

        return (final_images, final_masks)

    def _crop_by_size_and_align(self, image, mask, target_width, target_height, h_align, v_align):
        """
        根据目标尺寸和对齐方式裁切图像。
        @param image {PIL.Image} 输入图像
        @param mask {PIL.Image|None} 输入mask
        @param target_width {int} 目标宽度
        @param target_height {int} 目标高度
        @param h_align {str} 水平对齐方式
        @param v_align {str} 垂直对齐方式
        @returns {tuple} (裁切后的图像, 裁切后的mask)
        """
        # 计算目标比例
        target_ratio = target_width / target_height
        current_ratio = image.width / image.height
        
        if current_ratio > target_ratio:
            # 当前图像更宽，需要裁切宽度
            new_width = int(image.height * target_ratio)
            if h_align == "left":
                left = 0
            elif h_align == "right":
                left = image.width - new_width
            else:  # center
                left = (image.width - new_width) // 2
            crop_box = (left, 0, left + new_width, image.height)
        else:
            # 当前图像更高，需要裁切高度
            new_height = int(image.width / target_ratio)
            if v_align == "top":
                top = 0
            elif v_align == "bottom":
                top = image.height - new_height
            else:  # center
                top = (image.height - new_height) // 2
            crop_box = (0, top, image.width, top + new_height)
        
        # 执行裁切
        cropped_image = image.crop(crop_box)
        cropped_mask = mask.crop(crop_box) if mask is not None else None
        
        return cropped_image, cropped_mask

    def _resize_image_and_mask(self, image, mask, resize_mode, target_size):
        """
        缩放图像和mask。
        @param image {PIL.Image} 输入图像
        @param mask {PIL.Image|None} 输入mask
        @param resize_mode {str} 缩放模式
        @param target_size {int} 目标尺寸
        @returns {tuple} (缩放后的图像, 缩放后的mask)
        """
        width, height = image.size
        
        # 计算缩放因子
        if resize_mode == "shortest":
            scale_factor = float(target_size) / min(height, width)
        else:  # longest
            scale_factor = float(target_size) / max(height, width)
        
        # 计算新尺寸
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        
        # 缩放图像
        resized_image = image.resize((new_width, new_height), Image.LANCZOS)
        resized_mask = mask.resize((new_width, new_height), Image.LANCZOS) if mask is not None else None
        
        return resized_image, resized_mask

    def _stretch_to_size(self, image, mask, target_width, target_height):
        """
        强制拉伸图像到指定尺寸。
        @param image {PIL.Image} 输入图像
        @param mask {PIL.Image|None} 输入mask
        @param target_width {int} 目标宽度
        @param target_height {int} 目标高度
        @returns {tuple} (拉伸后的图像, 拉伸后的mask)
        """
        # 强制拉伸到目标尺寸（不保持原比例）
        stretched_image = image.resize((target_width, target_height), Image.LANCZOS)
        stretched_mask = mask.resize((target_width, target_height), Image.LANCZOS) if mask is not None else None
        
        return stretched_image, stretched_mask

    def _tensor_to_pil(self, tensor):
        """
        将张量转换为PIL图像。
        @param tensor {torch.Tensor} 输入张量，形状为 (H, W, C)
        @returns {PIL.Image} PIL图像对象
        """
        # 确保张量在CPU上并为float32类型
        if tensor.dtype != torch.float32:
            tensor = tensor.float()
        tensor = tensor.cpu()
        
        # 确保数据范围在[0, 1]
        tensor = torch.clamp(tensor, 0.0, 1.0)
        
        # 转换为uint8并创建PIL图像
        tensor_uint8 = (tensor * 255).to(torch.uint8)
        return Image.fromarray(tensor_uint8.numpy())

    def _tensor_to_pil_mask(self, tensor):
        """
        将mask张量转换为PIL图像。
        @param tensor {torch.Tensor} 输入张量，形状为 (H, W)
        @returns {PIL.Image} PIL图像对象
        """
        if tensor is None:
            return None
            
        # 确保张量在CPU上并为float32类型
        if tensor.dtype != torch.float32:
            tensor = tensor.float()
        tensor = tensor.cpu()
        
        # 确保数据范围在[0, 1]
        tensor = torch.clamp(tensor, 0.0, 1.0)
        
        # 转换为uint8并创建PIL图像
        tensor_uint8 = (tensor * 255).to(torch.uint8)
        return Image.fromarray(tensor_uint8.numpy(), mode='L')

    def _pil_to_tensor(self, image):
        """
        将PIL图像转换为张量。
        @param image {PIL.Image} PIL图像对象
        @returns {torch.Tensor} 图像张量，形状为 (H, W, C)
        """
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        elif image.mode == 'L':
            image = image.convert('RGB')
            
        return torch.from_numpy(np.array(image).astype(np.float32) / 255.0)

    def _pil_mask_to_tensor(self, mask):
        """
        将PIL mask转换为张量。
        @param mask {PIL.Image} PIL mask对象
        @returns {torch.Tensor} mask张量，形状为 (H, W)
        """
        if mask.mode != 'L':
            mask = mask.convert('L')
            
        return torch.from_numpy(np.array(mask).astype(np.float32) / 255.0)

# 节点注册
NODE_CLASS_MAPPINGS = {
    "PDImageResizeV3": PDImageResizeV3,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PDImageResizeV3": "PD:image_resize_V3",
}
