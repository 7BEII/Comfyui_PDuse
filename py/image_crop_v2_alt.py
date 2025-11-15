import torch
import numpy as np

class PDimage_corp_v2:
    """
    @classdesc
    按指定像素尺寸和方向裁切图片，可精准裁切画面某个区域，支持同步裁切mask。
    """
    @classmethod
    def INPUT_TYPES(cls):
        """
        @returns {dict} 节点输入参数类型
        """
        return {
            "required": {
                "image": ("IMAGE",),
                "size_width": ("INT", {"default": 512, "min": 1, "max": 8192, "step": 1}),
                "size_height": ("INT", {"default": 512, "min": 1, "max": 8192, "step": 1}),
                "axis": (["x", "y"], {"default": "x"}),
                "direction": (["left", "right", "top", "bottom"], {"default": "left"}),
            },
            "optional": {
                "mask": ("MASK",),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("cropped_image", "cropped_mask")
    FUNCTION = "crop_by_pixels"
    CATEGORY = "PDuse/Image"

    def crop_by_pixels(self, image, size_width, size_height, axis, direction, mask=None):
        """
        * 按像素尺寸和方向裁切图片（始终从direction指定边缘开始）
        * @param {torch.Tensor} image - 输入图像张量 (B, H, W, C)
        * @param {int} size_width - 裁切宽度（像素）
        * @param {int} size_height - 裁切高度（像素）
        * @param {str} axis - 裁切轴 x/y
        * @param {str} direction - 裁切方向 left/right/top/bottom
        * @param {torch.Tensor|None} mask - 可选mask (B, H, W)
        * @return {tuple} 裁切后的图像和mask
        """
        B, H, W, C = image.shape
        cropped_images = []
        cropped_masks = [] if mask is not None else None
        for i in range(B):
            img = image[i]
            msk = mask[i] if mask is not None else None
            if axis == "x":
                # 按宽度裁切
                crop_w = min(size_width, W)  # 确保不超过原图宽度
                if direction == "left":
                    x0 = 0
                    x1 = x0 + crop_w
                else:  # right
                    x1 = W
                    x0 = max(0, W - crop_w)
                crop_img = img[:, x0:x1, :]
                crop_msk = msk[:, x0:x1] if msk is not None else None
            else:  # axis == "y"
                # 按高度裁切
                crop_h = min(size_height, H)  # 确保不超过原图高度
                if direction == "top":
                    y0 = 0
                    y1 = y0 + crop_h
                else:  # bottom
                    y1 = H
                    y0 = max(0, H - crop_h)
                crop_img = img[y0:y1, :, :]
                crop_msk = msk[y0:y1, :] if msk is not None else None
            cropped_images.append(crop_img.unsqueeze(0))
            if mask is not None:
                cropped_masks.append(crop_msk.unsqueeze(0) if crop_msk is not None else None)
        out_img = torch.cat(cropped_images, dim=0)
        if mask is not None:
            out_mask = torch.cat([m for m in cropped_masks if m is not None], dim=0)
        else:
            out_mask = None
        return (out_img, out_mask)

NODE_CLASS_MAPPINGS = {
    "PDimage_corp_v2": PDimage_corp_v2,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "PDimage_corp_v2": "PD:Image Crop V2",
} 