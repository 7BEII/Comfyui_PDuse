import cv2
import numpy as np
import torch


def _image_to_uint8(image):
    return (image.detach().cpu().numpy().clip(0.0, 1.0) * 255.0).round().astype(np.uint8)


def _uint8_to_image(image):
    return torch.from_numpy(image.astype(np.float32) / 255.0)


def _build_alpha(rgb, min_area, remove_white):
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    h, s, v = cv2.split(hsv)

    red = ((h < 12) | (h > 170)) & (s > 45) & (v > 60)
    gold = (h > 10) & (h < 52) & (s > 42) & (v > 55)
    mask = (red | gold).astype(np.uint8) * 255

    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    filled = np.zeros_like(mask)
    for contour in contours:
        if cv2.contourArea(contour) >= int(min_area):
            cv2.drawContours(filled, [contour], -1, 255, thickness=cv2.FILLED)

    soft = cv2.GaussianBlur(filled, (0, 0), sigmaX=0.6, sigmaY=0.6)
    alpha = np.maximum(filled, soft).astype(np.uint8)

    if remove_white:
        alpha[(s < 70) & (v > 120)] = 0

    return alpha


class PDtoolsFilterGodenPNGv1:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "remove_white": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    FUNCTION = "filter_png"
    CATEGORY = "PDtools/Filter"

    def filter_png(self, image, remove_white=True):
        batch = _image_to_uint8(image)
        out_images = []
        out_masks = []

        for item in batch:
            rgb = item[:, :, :3]
            alpha = _build_alpha(rgb, min_area=12, remove_white=remove_white)
            mask = alpha.astype(np.float32) / 255.0
            filtered_rgb = (rgb.astype(np.float32) * mask[:, :, None]).round().astype(np.uint8)
            out_images.append(filtered_rgb)
            out_masks.append(mask)

        return (
            _uint8_to_image(np.stack(out_images, axis=0)),
            torch.from_numpy(np.stack(out_masks, axis=0)).float(),
        )


NODE_CLASS_MAPPINGS = {
    "PDtools_Filter_GodenPNG_v1": PDtoolsFilterGodenPNGv1
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PDtools_Filter_GodenPNG_v1": "PDtools_Filter_GodenPNG_v1"
}
