import numpy as np
from PIL import Image
from scipy.ndimage import label

class mask_edge_selector:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "mode": (["max", "min"], {"default": "max"})
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK", "IMAGE")
    RETURN_NAMES = ("filtered_image", "filtered_mask", "filtered_mask_image")
    CATEGORY = "Custom/MaskTools"
    FUNCTION = "select_extreme"

    def expand_array(self, arr):
        while isinstance(arr, (list, tuple)) and len(arr) == 1:
            arr = arr[0]
        if hasattr(arr, "cpu"):
            arr = arr.cpu().numpy()
        return arr

    def select_extreme(self, image, mode):
        image = self.expand_array(image)

        if isinstance(image, Image.Image):
            image = np.array(image.convert("RGBA"))

        if image.ndim == 3 and image.shape[-1] == 4:
            image_rgb = image[..., :3]
            alpha = image[..., 3]
            mask = (alpha == 0).astype(np.uint8)
        else:
            image_rgb = image if image.ndim == 3 else np.stack([image] * 3, axis=-1)
            gray = np.mean(image_rgb, axis=-1).astype(np.uint8)
            mask = (gray == 0).astype(np.uint8)

        seg, num_labels = label(mask)

        if num_labels == 0:
            result_mask = np.zeros_like(mask, dtype=np.float32)
            result_mask[0:1, 0:1] = 1.0
            result_image = np.zeros_like(image_rgb, dtype=np.uint8)
        else:
            areas = [(seg == i).sum() for i in range(1, num_labels + 1)]
            target_index = np.argmax(areas) + 1 if mode == "max" else np.argmin(areas) + 1

            selected_mask = (seg == target_index).astype(np.uint8)

            result_image = np.zeros_like(image_rgb, dtype=np.uint8)
            for c in range(3):
                result_image[..., c][selected_mask == 1] = image_rgb[..., c][selected_mask == 1]

            result_mask = (selected_mask > 0).astype(np.float32)
            if result_mask.sum() == 0:
                result_mask[0:1, 0:1] = 1.0

        result_mask_array = result_mask[None, None, ...].astype(np.float32)  # (1, 1, H, W)
        result_image_array = result_image.transpose(2, 0, 1)[None, ...].astype(np.uint8)  # (1, 3, H, W)

        mask_rgb = (result_mask * 255).astype(np.uint8)
        mask_rgb = np.stack([mask_rgb] * 3, axis=-1)
        mask_rgb_array = mask_rgb.transpose(2, 0, 1)[None, ...].astype(np.uint8)

        return (result_image_array, result_mask_array, mask_rgb_array)

NODE_CLASS_MAPPINGS = {
    "mask_edge_selector": mask_edge_selector
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "mask_edge_selector": "PD:Select_Mask"
}
