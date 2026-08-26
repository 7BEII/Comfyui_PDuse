from collections import deque

import numpy as np
import torch


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


NODE_CLASS_MAPPINGS = {
    "PDRemoveWhiteBackground": PDRemoveWhiteBackground,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PDRemoveWhiteBackground": "PD-remove white background",
}
