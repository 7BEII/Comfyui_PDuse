class PDSelectorSumT3:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "front1": ("IMAGE",),
                "mask1": ("MASK",),
                "back1": ("IMAGE",),
                "aspect_ratio": ("STRING", {"default": "2:3"}),
                "int1": ("INT", {"default": 768, "min": 0, "max": 16777216, "step": 1}),
                "int2": ("INT", {"default": 680, "min": 0, "max": 16777216, "step": 1}),
                "int3": ("INT", {"default": 1024, "min": 0, "max": 16777216, "step": 1}),
                "X1": ("FLOAT", {"default": 50.0, "min": -999.0, "max": 999.0, "step": 0.01}),
                "Y1": ("FLOAT", {"default": 50.0, "min": -999.0, "max": 999.0, "step": 0.01}),
                "X2": ("FLOAT", {"default": 50.0, "min": -999.0, "max": 999.0, "step": 0.01}),
                "Y2": ("FLOAT", {"default": 50.0, "min": -999.0, "max": 999.0, "step": 0.01}),
                "X3": ("FLOAT", {"default": 50.0, "min": -999.0, "max": 999.0, "step": 0.01}),
                "Y3": ("FLOAT", {"default": 50.0, "min": -999.0, "max": 999.0, "step": 0.01}),
            },
            "optional": {
                "front2": ("IMAGE",),
                "mask2": ("MASK",),
                "back2": ("IMAGE",),
                "front3": ("IMAGE",),
                "mask3": ("MASK",),
                "back3": ("IMAGE",),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK", "IMAGE", "INT", "STRING", "INT", "INT", "FLOAT", "FLOAT")
    RETURN_NAMES = ("front", "mask", "back", "int", "ratio", "width", "height", "X", "Y")
    FUNCTION = "select"
    CATEGORY = "PDuse/Image"

    def select(
        self,
        front1,
        mask1,
        back1,
        aspect_ratio,
        int1=768,
        int2=680,
        int3=1024,
        X1=50.0,
        Y1=50.0,
        X2=50.0,
        Y2=50.0,
        X3=50.0,
        Y3=50.0,
        front2=None,
        mask2=None,
        back2=None,
        front3=None,
        mask3=None,
        back3=None,
    ):
        ratio = aspect_ratio.strip()
        groups = {
            "2:3": (front1, mask1, back1, int1, X1, Y1),
            "3:4": (front1, mask1, back1, int1, X1, Y1),
            "9:16": (front1, mask1, back1, int1, X1, Y1),
            "1:1": (front2, mask2, back2, int2, X2, Y2),
            "3:2": (front3, mask3, back3, int3, X3, Y3),
            "4:3": (front3, mask3, back3, int3, X3, Y3),
            "16:9": (front3, mask3, back3, int3, X3, Y3),
        }
        if ratio not in groups:
            ratio = "2:3"

        front, mask, back, value, x_value, y_value = groups[ratio]
        if front is None or mask is None or back is None:
            ratio = "2:3"
            front, mask, back, value, x_value, y_value = groups[ratio]

        height = int(back.shape[1])
        width = int(back.shape[2])
        return (front, mask, back, int(value), ratio, width, height, float(x_value), float(y_value))


NODE_CLASS_MAPPINGS = {
    "PDSelectorSumT3": PDSelectorSumT3,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PDSelectorSumT3": "PD-selector-sum-T3",
}
