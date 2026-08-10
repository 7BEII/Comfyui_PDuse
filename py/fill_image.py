import torch

import comfy.utils
import nodes


class PDResizeAndFillImage:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "target_width": ("INT", {"default": 512, "min": 1, "max": nodes.MAX_RESOLUTION, "step": 1}),
                "target_height": ("INT", {"default": 512, "min": 1, "max": nodes.MAX_RESOLUTION, "step": 1}),
                "fill_color": (["white", "black"], {"default": "white"}),
                "interpolation": (["area", "bicubic", "nearest-exact", "bilinear", "lanczos"], {"default": "area"}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "resize_and_fill"
    CATEGORY = "PDuse/Image"

    def resize_and_fill(self, image, target_width, target_height, fill_color, interpolation):
        batch_size, original_height, original_width, channels = image.shape
        scale = min(target_width / original_width, target_height / original_height)
        resized_width = max(1, int(original_width * scale))
        resized_height = max(1, int(original_height * scale))

        resized = comfy.utils.common_upscale(
            image.movedim(-1, 1),
            resized_width,
            resized_height,
            interpolation,
            "disabled",
        )

        fill_value = 1.0 if fill_color == "white" else 0.0
        output = torch.full(
            (batch_size, channels, target_height, target_width),
            fill_value,
            dtype=image.dtype,
            device=image.device,
        )
        x = (target_width - resized_width) // 2
        y = (target_height - resized_height) // 2
        output[:, :, y:y + resized_height, x:x + resized_width] = resized

        return (output.movedim(1, -1),)


NODE_CLASS_MAPPINGS = {
    "PDResizeAndFillImage": PDResizeAndFillImage,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PDResizeAndFillImage": "PD:调整尺寸并填充图像",
}
