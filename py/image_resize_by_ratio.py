import torch
import numpy as np
from PIL import Image
from typing import Tuple


class PD_image_resize_by_ratio:
    """Crop images to an aspect ratio and resize the longest side to max_size."""

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "max_size": ("INT", {
                    "default": 1024,
                    "min": 64,
                    "max": 4096,
                    "step": 1,
                    "display": "number"
                }),
                "aspect_width": ("INT", {
                    "default": 3,
                    "min": 1,
                    "max": 16,
                    "step": 1,
                    "display": "number"
                }),
                "aspect_height": ("INT", {
                    "default": 4,
                    "min": 1,
                    "max": 16,
                    "step": 1,
                    "display": "number"
                }),
                "resampling_method": (["LANCZOS", "BICUBIC", "BILINEAR", "NEAREST"], {
                    "default": "LANCZOS"
                })
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("processed_images", "info")
    FUNCTION = "process_images"
    CATEGORY = "PD_Image/Processing"
    OUTPUT_IS_LIST = (False, False)

    def pil_to_tensor(self, image: Image.Image) -> torch.Tensor:
        """Convert PIL image to a ComfyUI IMAGE tensor in HWC format."""
        if image.mode == "RGBA":
            background = Image.new("RGB", image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background
        elif image.mode != "RGB":
            image = image.convert("RGB")

        np_image = np.array(image).astype(np.float32) / 255.0
        return torch.from_numpy(np_image)

    def tensor_to_pil(self, tensor: torch.Tensor) -> Image.Image:
        """Convert a ComfyUI IMAGE tensor to PIL."""
        if tensor.is_cuda:
            tensor = tensor.cpu()

        if len(tensor.shape) == 4:
            tensor = tensor.squeeze(0)

        np_image = (tensor.numpy() * 255).clip(0, 255).astype(np.uint8)
        return Image.fromarray(np_image)

    def get_resampling_filter(self, method: str):
        method_map = {
            "LANCZOS": Image.Resampling.LANCZOS,
            "BICUBIC": Image.Resampling.BICUBIC,
            "BILINEAR": Image.Resampling.BILINEAR,
            "NEAREST": Image.Resampling.NEAREST
        }
        return method_map.get(method, Image.Resampling.LANCZOS)

    def calculate_target_size(self, max_size: int, aspect_ratio: Tuple[int, int]) -> Tuple[int, int]:
        aspect_width, aspect_height = aspect_ratio
        if aspect_width >= aspect_height:
            target_width = max_size
            target_height = round(max_size * aspect_height / aspect_width)
        else:
            target_height = max_size
            target_width = round(max_size * aspect_width / aspect_height)

        return max(1, target_width), max(1, target_height)

    def process_single_image(
        self,
        image_tensor: torch.Tensor,
        max_size: int,
        aspect_ratio: Tuple[int, int],
        resampling_method: str
    ) -> Tuple[torch.Tensor, str]:
        try:
            pil_image = self.tensor_to_pil(image_tensor)
            original_size = pil_image.size
            resampling_filter = self.get_resampling_filter(resampling_method)

            current_width, current_height = pil_image.size
            target_ratio = aspect_ratio[0] / aspect_ratio[1]
            current_ratio = current_width / current_height

            crop_info = ""
            if abs(current_ratio - target_ratio) > 0.01:
                if current_ratio > target_ratio:
                    new_width = int(current_height * target_ratio)
                    left = (current_width - new_width) // 2
                    crop_box = (left, 0, left + new_width, current_height)
                    crop_info = f"cropped width: {current_width} -> {new_width}"
                else:
                    new_height = int(current_width / target_ratio)
                    top = (current_height - new_height) // 2
                    crop_box = (0, top, current_width, top + new_height)
                    crop_info = f"cropped height: {current_height} -> {new_height}"

                pil_image = pil_image.crop(crop_box)

            target_size = self.calculate_target_size(max_size, aspect_ratio)
            if pil_image.size != target_size:
                pil_image = pil_image.resize(target_size, resampling_filter)

            processed_tensor = self.pil_to_tensor(pil_image)
            final_size = pil_image.size

            info = f"original: {original_size} -> final: {final_size}"
            if crop_info:
                info += f" ({crop_info})"

            return processed_tensor, info

        except Exception as e:
            error_info = f"processing error: {str(e)}"
            return image_tensor, error_info

    def process_images(
        self,
        images: torch.Tensor,
        max_size: int,
        aspect_width: int,
        aspect_height: int,
        resampling_method: str
    ):
        try:
            if max_size <= 0:
                raise ValueError("max_size must be greater than 0")
            if aspect_width <= 0 or aspect_height <= 0:
                raise ValueError("aspect_width and aspect_height must be greater than 0")

            aspect_ratio = (aspect_width, aspect_height)

            if len(images.shape) == 3:
                images = images.unsqueeze(0)

            processed_images = []
            processing_info = []

            for i in range(images.shape[0]):
                image_tensor = images[i]
                processed_tensor, info = self.process_single_image(
                    image_tensor, max_size, aspect_ratio, resampling_method
                )
                processed_images.append(processed_tensor)
                processing_info.append(f"image {i + 1}: {info}")

            processed_batch = torch.stack(processed_images, dim=0)
            summary_info = "Processing complete:\n" + "\n".join(processing_info)

            return (processed_batch, summary_info)

        except Exception as e:
            error_msg = f"processing failed: {str(e)}"
            return (images, error_msg)


NODE_CLASS_MAPPINGS = {
    "PD_image_resize_by_ratio": PD_image_resize_by_ratio
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_image_resize_by_ratio": "PD_image resize by ratio"
}
