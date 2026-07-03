import cv2
import numpy as np
import torch


def _image_to_float(image):
    return image.detach().cpu().numpy().clip(0.0, 1.0).astype(np.float32)


def _make_soft_alpha(rgb, black_threshold, gamma, blur):
    alpha = np.max(rgb, axis=2)
    alpha = np.where(alpha <= float(black_threshold), 0.0, alpha)

    if float(gamma) != 1.0:
        alpha = np.power(np.clip(alpha, 0.0, 1.0), float(gamma))

    if float(blur) > 0:
        alpha = cv2.GaussianBlur(alpha, (0, 0), sigmaX=float(blur), sigmaY=float(blur))

    return np.clip(alpha, 0.0, 1.0)


class PDtoolsFilterWPNGv2:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "black_threshold": ("FLOAT", {"default": 0.02, "min": 0.0, "max": 0.5, "step": 0.005}),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    FUNCTION = "filter_png"
    CATEGORY = "PDtools/Filter"

    def filter_png(self, image, black_threshold=0.02):
        batch = _image_to_float(image)
        out_images = []
        out_masks = []

        for rgb in batch:
            rgb = rgb[:, :, :3]
            alpha = _make_soft_alpha(rgb, black_threshold=black_threshold, gamma=1.0, blur=0.8)
            restored = rgb / np.clip(alpha[:, :, None], 1e-6, 1.0)
            restored = np.where(alpha[:, :, None] > 0.0, restored, 0.0)
            out_images.append(np.clip(restored, 0.0, 1.0))
            out_masks.append(alpha)

        return (
            torch.from_numpy(np.stack(out_images, axis=0)).float(),
            torch.from_numpy(np.stack(out_masks, axis=0)).float(),
        )


NODE_CLASS_MAPPINGS = {
    "PDtools_Filter_WPNG_v2": PDtoolsFilterWPNGv2
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PDtools_Filter_WPNG_v2": "PDtools_Filter_WPNG_v2"
}
