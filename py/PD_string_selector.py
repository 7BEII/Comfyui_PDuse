class PDStringSelector:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "aspect_ratio": ("STRING", {"default": "2:3"}),
                "2:3": ("STRING", {"default": "768"}),
                "1:1": ("STRING", {"default": "680"}),
                "3:2": ("STRING", {"default": "1024"}),
            }
        }

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("string", "int")
    FUNCTION = "select_value"
    CATEGORY = "PDuse/Text"

    def select_value(self, aspect_ratio, **values):
        ratio = aspect_ratio.strip()
        if ratio not in values:
            ratio = "2:3"
        value = str(values[ratio]).strip()
        return (value, int(float(value)))


NODE_CLASS_MAPPINGS = {
    "PDStringSelector": PDStringSelector,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PDStringSelector": "PDselector-string",
}
