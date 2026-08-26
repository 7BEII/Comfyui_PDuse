import comfy.utils
import nodes


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
    "PDCropByMask": PDCropByMask,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PDCropByMask": "PD-crop by mask",
}
