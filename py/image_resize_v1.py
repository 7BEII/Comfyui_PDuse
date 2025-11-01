import torch

class PDImageResize:
    """
    图片缩放节点，支持通过最长边或最短边缩放图片。
    输出为缩放后的图片和对应的 mask。
    """
    RETURN_TYPES = ("IMAGE", "MASK",)
    FUNCTION = "resize"
    CATEGORY = "image"

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
            },
            "optional": {
                "mask_optional": ("MASK",),
            },
        }

    @classmethod
    def VALIDATE_INPUTS(cls, resize_mode, target_size, **_):
        """
        校验输入参数。
        @param resize_mode {str} 缩放模式：longest 或 shortest
        @param target_size {int} 目标尺寸
        @returns {True|str} 校验通过返回 True，否则返回错误信息
        """
        if target_size <= 0:
            return "目标尺寸必须大于0"
        return True

    def resize(self, pixels, resize_mode, target_size, mask_optional=None):
        """
        按照指定模式缩放图片。
        @param pixels {Tensor} 输入图片，形状为 (B, H, W, C)
        @param resize_mode {str} 缩放模式：longest 或 shortest
        @param target_size {int} 目标尺寸
        @param mask_optional {Tensor|None} 可选 mask，形状为 (B, H, W)
        @returns {tuple} (缩放后的图片, 缩放后的 mask)
        """
        validity = self.VALIDATE_INPUTS(resize_mode, target_size)
        if validity is not True:
            raise Exception(validity)

        height, width = pixels.shape[1:3]
        # 计算缩放因子
        if resize_mode == "shortest":
            scale_factor = float(target_size) / min(height, width)
        else:  # longest
            scale_factor = float(target_size) / max(height, width)

        # 缩放图片
        pixels = torch.nn.functional.interpolate(
            pixels.movedim(-1, 1),
            scale_factor=scale_factor,
            mode="bicubic",
            antialias=True
        ).movedim(1, -1).clamp(0.0, 1.0)
        new_height, new_width = pixels.shape[1:3]

        # 缩放 mask
        if mask_optional is None:
            mask = torch.zeros(1, new_height, new_width, dtype=torch.float32)
        else:
            mask = torch.nn.functional.interpolate(
                mask_optional.unsqueeze(0),
                scale_factor=scale_factor,
                mode="bicubic"
            ).squeeze(0).clamp(0.0, 1.0)

        return (pixels, mask)

# 节点注册
NODE_CLASS_MAPPINGS = {
    "PDImageResize": PDImageResize,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "PDImageResize": "PD:image_resize_v1",
}