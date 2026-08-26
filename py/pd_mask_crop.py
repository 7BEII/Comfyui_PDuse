from collections import deque

import numpy as np
import torch

import comfy.utils
import nodes


class ImageSplit:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"image": ("IMAGE",)}}

    RETURN_TYPES = ("IMAGE", "IMAGE")
    RETURN_NAMES = ("left", "right")
    FUNCTION = "split"
    CATEGORY = "PDuse/Image"

    def split(self, image):
        midpoint = (image.shape[2] + 1) // 2
        return (image[:, :, :midpoint, :], image[:, :, midpoint:, :])


class PDRemoveWhiteBackground:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "white_threshold": ("FLOAT", {"default": 0.95, "min": 0.0, "max": 1.0, "step": 0.01}),
                "edge_black_threshold": ("FLOAT", {"default": 0.1, "min": 0.0, "max": 0.5, "step": 0.01, "tooltip": "Treat edge-connected pixels at or below this brightness as background. Set to 0 to disable."}),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    FUNCTION = "remove"
    CATEGORY = "PDuse/Image"

    def remove(self, image, white_threshold, edge_black_threshold):
        pixels = image[..., :3].detach().to(device="cpu", dtype=torch.float32).numpy()
        masks = []
        for item in pixels:
            white = np.all(item >= white_threshold, axis=2)
            dark = np.all(item <= edge_black_threshold, axis=2) if edge_black_threshold > 0 else np.zeros_like(white)
            height, width = white.shape

            def find_outer(candidate):
                outer = np.zeros_like(candidate)
                queue = deque()

                def add_pixel(y, x):
                    if candidate[y, x] and not outer[y, x]:
                        outer[y, x] = True
                        queue.append((y, x))

                for x in range(width):
                    add_pixel(0, x)
                    add_pixel(height - 1, x)
                for y in range(1, height - 1):
                    add_pixel(y, 0)
                    add_pixel(y, width - 1)

                while queue:
                    y, x = queue.popleft()
                    if y > 0:
                        add_pixel(y - 1, x)
                    if y + 1 < height:
                        add_pixel(y + 1, x)
                    if x > 0:
                        add_pixel(y, x - 1)
                    if x + 1 < width:
                        add_pixel(y, x + 1)
                return outer

            masks.append(find_outer(white) | find_outer(dark))

        mask = torch.from_numpy(np.stack(masks)).to(device=image.device, dtype=image.dtype)
        return (image, mask)


class PDCropByMask:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "mask": ("MASK",),
                "padding": ("INT", {"default": 0, "min": -nodes.MAX_RESOLUTION, "max": nodes.MAX_RESOLUTION, "step": 1, "tooltip": "Positive values add a border; negative values trim inside the mask boundary."}),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    FUNCTION = "crop"
    CATEGORY = "PDuse/Image"

    def crop(self, image, mask, padding):
        if mask.shape[-2:] != image.shape[1:3]:
            mask = comfy.utils.common_upscale(mask.unsqueeze(1), image.shape[2], image.shape[1], "nearest-exact", "disabled").squeeze(1)
        if mask.shape[0] == 1 and image.shape[0] > 1:
            mask = mask.expand(image.shape[0], -1, -1)
        elif mask.shape[0] != image.shape[0]:
            raise ValueError(f"Mask batch {mask.shape[0]} does not match image batch {image.shape[0]}")

        keep = (mask <= 0.5).any(dim=0)
        rows = keep.any(dim=1).nonzero().flatten()
        cols = keep.any(dim=0).nonzero().flatten()
        if rows.numel() == 0 or cols.numel() == 0:
            return (image, mask)

        y_start = max(0, rows[0].item() - padding)
        y_end = min(image.shape[1], rows[-1].item() + padding + 1)
        x_start = max(0, cols[0].item() - padding)
        x_end = min(image.shape[2], cols[-1].item() + padding + 1)
        if y_start >= y_end or x_start >= x_end:
            max_shrink = min((rows.numel() - 1) // 2, (cols.numel() - 1) // 2)
            raise ValueError(f"Padding {padding} removes the entire mask. The minimum padding for this mask is {-max_shrink}.")
        return (image[:, y_start:y_end, x_start:x_end, :], mask[:, y_start:y_end, x_start:x_end])


NODE_CLASS_MAPPINGS = {
    "ImageSplit": ImageSplit,
    "PDRemoveWhiteBackground": PDRemoveWhiteBackground,
    "PDCropByMask": PDCropByMask,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageSplit": "Split Image",
    "PDRemoveWhiteBackground": "PD-remove white background",
    "PDCropByMask": "PD-crop by mask",
}
