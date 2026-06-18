RATIO_COMBO_TYPE = ["1:1", "3:4", "4:3", "2:3", "3:2", "9:16", "16:9"]


class PDStringToRatioCombo:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "string": ("STRING", {"default": "2:3"}),
                "fallback": (RATIO_COMBO_TYPE, {"default": "2:3"}),
            }
        }

    RETURN_TYPES = (RATIO_COMBO_TYPE,)
    RETURN_NAMES = ("combo",)
    FUNCTION = "convert"
    CATEGORY = "PDuse/Text"

    def convert(self, string, fallback):
        value = string.strip()
        if value not in RATIO_COMBO_TYPE:
            value = fallback
        return (value,)


NODE_CLASS_MAPPINGS = {
    "PDStringToRatioCombo": PDStringToRatioCombo,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PDStringToRatioCombo": "PD:string-to-ratio-combo",
}
