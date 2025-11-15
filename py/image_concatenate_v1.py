import os
import torch
import numpy as np
from PIL import Image
from comfy.utils import common_upscale

class PDImageConcante:
    """
    @classdesc
    加载两张图片并按指定方向合并，可选自动匹配尺寸。如果只接收到一张图片，则直接返回该图片。
    """
    @classmethod
    def INPUT_TYPES(cls):
        """
        @returns {dict} 节点输入参数类型
        """
        return {
            "required": {
                "image1": ("IMAGE",),
                "direction": (["right", "down", "left", "up"], {"default": "right"}),
                "match_size": (["longest", "crop by image1"], {"default": "longest"}),
                "image2_crop": (["center", "top", "bottom", "left", "right"], {"default": "center"}),
            },
            "optional": {
                "image2": ("IMAGE",),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "concat_and_load"
    CATEGORY = "PDuse/Image"

    def crop_tensor(self, img, target_h, target_w, crop_type="center"):
        """
        按指定方式裁切图片到目标尺寸
        @param {torch.Tensor} img - 输入图片 (B, H, W, C)
        @param {int} target_h - 目标高度
        @param {int} target_w - 目标宽度
        @param {str} crop_type - 裁切方式 center/top/bottom/left/right
        @returns {torch.Tensor} 裁切后的图片
        """
        _, h, w, _ = img.shape
        if crop_type == "center":
            top = max((h - target_h) // 2, 0)
            left = max((w - target_w) // 2, 0)
        elif crop_type == "top":
            top = 0
            left = max((w - target_w) // 2, 0)
        elif crop_type == "bottom":
            top = max(h - target_h, 0)
            left = max((w - target_w) // 2, 0)
        elif crop_type == "left":
            top = max((h - target_h) // 2, 0)
            left = 0
        elif crop_type == "right":
            top = max((h - target_h) // 2, 0)
            left = max(w - target_w, 0)
        else:
            top = max((h - target_h) // 2, 0)
            left = max((w - target_w) // 2, 0)
        return img[:, top:top+target_h, left:left+target_w, :]

    def concat_and_load(self, image1, direction, match_size, image2_crop="center", image2=None):
        """
        @functiondesc
        合并两张图片，支持最长边等比缩放和按image1尺寸裁切两种模式。
        @param {torch.Tensor} image1 - 第一张图片
        @param {str} direction - 合并方向
        @param {str} match_size - 尺寸匹配模式
        @param {str} image2_crop - image2裁切方式
        @param {torch.Tensor} image2 - 第二张图片（可选）
        @returns {tuple} 合并后的图片张量
        """
        if image2 is None:
            return (image1,)

        # 统一为4维 (B, H, W, C)
        if image1.dim() == 3:
            image1 = image1.unsqueeze(0)
        if image2.dim() == 3:
            image2 = image2.unsqueeze(0)

        h1, w1 = image1.shape[1], image1.shape[2]
        h2, w2 = image2.shape[1], image2.shape[2]
        aspect2 = w2 / h2

        if match_size == "longest":
            # 按最长边等比缩放
            if direction in ["left", "right"]:
                target_h = max(h1, h2)
                target_w1 = int(target_h * (w1 / h1))
                target_w2 = int(target_h * aspect2)
                image1_for_up = image1.movedim(-1, 1)
                image1_resized = common_upscale(image1_for_up, target_w1, target_h, "lanczos", "disabled").movedim(1, -1)
                image2_for_up = image2.movedim(-1, 1)
                image2_resized = common_upscale(image2_for_up, target_w2, target_h, "lanczos", "disabled").movedim(1, -1)
            else:
                target_w = max(w1, w2)
                target_h1 = int(target_w / (w1 / h1))
                target_h2 = int(target_w / aspect2)
                image1_for_up = image1.movedim(-1, 1)
                image1_resized = common_upscale(image1_for_up, target_w, target_h1, "lanczos", "disabled").movedim(1, -1)
                image2_for_up = image2.movedim(-1, 1)
                image2_resized = common_upscale(image2_for_up, target_w, target_h2, "lanczos", "disabled").movedim(1, -1)
        elif match_size == "crop by image1":
            # 先等比缩放image2，使其一边与image1对齐，另一边大于等于image1，再按image2_crop裁切
            scale_h = h1 / h2
            scale_w = w1 / w2
            scale = max(scale_h, scale_w)
            resize_h = int(h2 * scale + 0.5)
            resize_w = int(w2 * scale + 0.5)
            image2_for_up = image2.movedim(-1, 1)
            image2_resized = common_upscale(image2_for_up, resize_w, resize_h, "lanczos", "disabled").movedim(1, -1)
            image2_resized = self.crop_tensor(image2_resized, h1, w1, image2_crop)
            image1_resized = image1
        else:
            image1_resized = image1
            image2_resized = image2

        # 通道对齐
        c1, c2 = image1_resized.shape[-1], image2_resized.shape[-1]
        if c1 != c2:
            if c1 < c2:
                alpha = torch.ones((*image1_resized.shape[:-1], c2 - c1), device=image1_resized.device)
                image1_resized = torch.cat((image1_resized, alpha), dim=-1)
            else:
                alpha = torch.ones((*image2_resized.shape[:-1], c1 - c2), device=image2_resized.device)
                image2_resized = torch.cat((image2_resized, alpha), dim=-1)

        # 合并
        if direction == "right":
            merged = torch.cat((image1_resized, image2_resized), dim=2)
        elif direction == "down":
            merged = torch.cat((image1_resized, image2_resized), dim=1)
        elif direction == "left":
            merged = torch.cat((image2_resized, image1_resized), dim=2)
        elif direction == "up":
            merged = torch.cat((image2_resized, image1_resized), dim=1)
        else:
            raise ValueError("direction参数无效")
        return (merged,)

    def _load_image(self, path):
        """
        @private
        加载图片为 (B, H, W, C) 的 torch.Tensor
        @param {str} path - 图片路径
        @returns {torch.Tensor} 图像张量
        """
        if not os.path.isfile(path):
            raise FileNotFoundError(f"图片文件不存在: {path}")
        img = Image.open(path).convert("RGB")
        arr = np.array(img).astype(np.float32) / 255.0
        tensor = torch.from_numpy(arr).unsqueeze(0)  # (1, H, W, C)
        return tensor

# 节点注册
NODE_CLASS_MAPPINGS = {
    "PDImageConcante": PDImageConcante,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "PDImageConcante": "PD:imageconcante_V1",
}
