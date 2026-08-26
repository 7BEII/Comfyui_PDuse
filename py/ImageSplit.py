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


NODE_CLASS_MAPPINGS = {
    "ImageSplit": ImageSplit,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageSplit": "Split Image",
}
