class PDRatioSelector:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "aspect_ratio": ([
                    "1:1",
                    "3:4",
                    "4:3",
                    "2:3",
                    "3:2",
                    "9:16",
                    "16:9"
                ], {"default": "1:1"}),
                "max_size": ("INT", {
                    "default": 1024, 
                    "min": 256, 
                    "max": 8192, 
                    "step": 8
                }),
            }
        }

    RETURN_TYPES = ("*", "INT", "INT")
    RETURN_NAMES = ("ratio", "width", "height")
    FUNCTION = "calculate_dimensions"
    CATEGORY = "PDuse/Image"

    def calculate_dimensions(self, aspect_ratio, max_size):
        # 解析比例数字
        width_ratio, height_ratio = map(int, aspect_ratio.split(':'))
      
        # 根据 max_size 和比例计算尺寸
        if width_ratio >= height_ratio:
            # 宽图或方形：宽度为 max_size
            width = max_size
            height = int(max_size * height_ratio / width_ratio)
        else:
            # 竖图：高度为 max_size
            height = max_size
            width = int(max_size * width_ratio / height_ratio)

        # 确保输出尺寸能被 8 整除（标准 AI 图像生成的必要条件）
        width = round(width / 8) * 8
        height = round(height / 8) * 8

        return (aspect_ratio, width, height)

# 节点注册
NODE_CLASS_MAPPINGS = {
    "PDRatioSelector": PDRatioSelector,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PDRatioSelector": "PD:ratio selector",
}