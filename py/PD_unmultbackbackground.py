import torch

class PD_UnMultBlackBackground:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                # 新增：黑场阈值参数，用于过滤 JPG 压缩噪点
                "black_threshold": ("FLOAT", {"default": 0.02, "min": 0.0, "max": 0.5, "step": 0.005}),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    FUNCTION = "process"
    CATEGORY = "Image/Alpha"

    def process(self, image, black_threshold):
        # 1. 提取 Alpha 通道：取 RGB 三个通道中的最大值
        alpha, _ = torch.max(image, dim=-1, keepdim=True)

        # 2. 核心修复：过滤 JPG 噪点
        # 将所有低于阈值 (black_threshold) 的 alpha 强制归零，当做纯黑处理
        alpha = torch.where(alpha <= black_threshold, torch.zeros_like(alpha), alpha)

        # 3. 去预乘 (Unpremultiply)
        epsilon = 1e-6
        safe_alpha = torch.clamp(alpha, min=epsilon)
        
        unpremultiplied_image = image / safe_alpha
        unpremultiplied_image = torch.clamp(unpremultiplied_image, min=0.0, max=1.0)
        
        # 强制将 alpha 为 0 的区域渲染为纯黑，彻底消灭花屏
        out_image = torch.where(alpha == 0.0, torch.zeros_like(image), unpremultiplied_image)

        # 4. 整理 Mask 输出格式
        out_mask = alpha.squeeze(-1)

        return (out_image, out_mask)

# 注册节点
NODE_CLASS_MAPPINGS = {
    "PD_UnMultBlackBackground": PD_UnMultBlackBackground
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_UnMultBlackBackground": "PDTool:UnMultBlackBackground"
}