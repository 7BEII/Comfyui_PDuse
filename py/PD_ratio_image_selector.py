class PDRatioImageSelector:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "2:3": ("IMAGE",),
                "aspect_ratio": ("STRING", {"default": "2:3"}),
            },
            "optional": {
                "1:1": ("IMAGE",),
                "3:2": ("IMAGE",),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING", "INT", "INT")
    RETURN_NAMES = ("image", "ratio", "width", "height")
    FUNCTION = "select_image"
    CATEGORY = "PDuse/Image"

    def select_image(self, aspect_ratio, **images):
        ratio = aspect_ratio.strip()
        if ratio not in ("2:3", "1:1", "3:2"):
            ratio = "2:3"

        image = images.get(ratio)
        if image is None:
            image = images["2:3"]
        height = int(image.shape[1])
        width = int(image.shape[2])
        return (image, ratio, width, height)


NODE_CLASS_MAPPINGS = {
    "PDRatioImageSelector": PDRatioImageSelector,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PDRatioImageSelector": "PDselector-image",
}
