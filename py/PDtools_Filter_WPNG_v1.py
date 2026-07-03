import cv2
import numpy as np
import torch


def _image_to_uint8(image):
    return (image.detach().cpu().numpy().clip(0.0, 1.0) * 255.0).round().astype(np.uint8)


def _uint8_to_image(image):
    return torch.from_numpy(image.astype(np.float32) / 255.0)


def _make_mask(rgb, threshold):
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0
    return (gray >= float(threshold)).astype(np.float32)


class PDtoolsFilterWPNGv1:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "threshold": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01}),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    FUNCTION = "filter_png"
    CATEGORY = "PDtools/Filter"

    def filter_png(self, image, threshold=0.5):
        batch = _image_to_uint8(image)
        out_images = []
        out_masks = []

        for item in batch:
            rgb = item[:, :, :3]
            mask = _make_mask(rgb, threshold=threshold)
            bw_image = np.repeat((mask[:, :, None] * 255.0).astype(np.uint8), 3, axis=2)
            out_images.append(bw_image)
            out_masks.append(mask)

        return (
            _uint8_to_image(np.stack(out_images, axis=0)),
            torch.from_numpy(np.stack(out_masks, axis=0)).float(),
        )


NODE_CLASS_MAPPINGS = {
    "PDtools_Filter_WPNG_v1": PDtoolsFilterWPNGv1
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PDtools_Filter_WPNG_v1": "PDtools_Filter_WPNG_v1"
}
