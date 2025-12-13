class AnyType(str):
    def __ne__(self, __value: object) -> bool:
        return False

any = AnyType("*")

class PD_if:

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "if": ("BOOLEAN", {"default": True}),
                "cond_1": (any,),
                "cond_2": (any,),
            },
        }

    RETURN_TYPES = ("BOOLEAN", "INT",)
    RETURN_NAMES = ("output", "count",)
    FUNCTION = "execute"
    CATEGORY = "PDuse/Logic"

    def execute(self, cond_1, cond_2, **kwargs):
        try:
            condition = kwargs.get("if", False)
            result = bool(cond_1) and bool(cond_2) and bool(condition)
            return (result, 1)
        except Exception:
            return (False, 0)


NODE_CLASS_MAPPINGS = {
    "PD_if": PD_if,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_if": "PD:if",
}

