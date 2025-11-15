import torch
from comfy.utils import common_upscale  # 确保 common_upscale 已正确导入

class Imagecombine2:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image1": ("IMAGE",),
                "image2": ("IMAGE",),
                "direction": (
                    ['right', 'down', 'left', 'up'],
                    {
                        "default": 'right'
                    }
                ),
                "match_image_size": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "Imagecombine2"
    CATEGORY = "PDuse/Image"

    DESCRIPTION = """
    Concatenates image2 to image1 in the specified direction.
    """

    def concatenate(self, image1, image2, direction, match_image_size, first_image_shape=None):
        # 检查 batch size 是否相同
        batch_size1 = image1.shape[0]
        batch_size2 = image2.shape[0]

        if batch_size1 != batch_size2:
            # 计算需要重复的次数
            max_batch_size = max(batch_size1, batch_size2)
            repeats1 = max_batch_size // batch_size1
            repeats2 = max_batch_size // batch_size2
            
            # 通过重复来匹配最大的 batch size
            image1 = image1.repeat(repeats1, 1, 1, 1)
            image2 = image2.repeat(repeats2, 1, 1, 1)

        if match_image_size:
            # 如果提供了 first_image_shape，则使用它；否则，默认为 image1 的 shape
            target_shape = first_image_shape if first_image_shape is not None else image1.shape

            original_height = image2.shape[1]
            original_width = image2.shape[2]
            original_aspect_ratio = original_width / original_height

            if direction in ['left', 'right']:
                # 匹配高度并根据宽度调整以保持长宽比
                target_height = target_shape[1]  # B, H, W, C 格式
                target_width = int(target_height * original_aspect_ratio)
            elif direction in ['up', 'down']:
                # 匹配宽度并根据高度调整以保持长宽比
                target_width = target_shape[2]  # B, H, W, C 格式
                target_height = int(target_width / original_aspect_ratio)
            
            # 调整 image2 到预期的格式以便进行 common_upscale
            image2_for_upscale = image2.movedim(-1, 1)  # 将 C 维移到第二位 (B, C, H, W)

            # 使用常见的 upscale 函数调整 image2 大小，同时保持长宽比
            image2_resized = common_upscale(image2_for_upscale, target_width, target_height, "lanczos", "disabled")
            
            # 调整 image2 回到原始格式 (B, H, W, C) 后进行 resize
            image2_resized = image2_resized.movedim(1, -1)
        else:
            image2_resized = image2

        # 确保两个图像的通道数一致
        channels_image1 = image1.shape[-1]
        channels_image2 = image2_resized.shape[-1]

        if channels_image1 != channels_image2:
            if channels_image1 < channels_image2:
                # 如果 image2 多了通道，给 image1 增加 alpha 通道
                alpha_channel = torch.ones((*image1.shape[:-1], channels_image2 - channels_image1), device=image1.device)
                image1 = torch.cat((image1, alpha_channel), dim=-1)
            else:
                # 如果 image1 多了通道，给 image2 增加 alpha 通道
                alpha_channel = torch.ones((*image2_resized.shape[:-1], channels_image1 - channels_image2), device=image2_resized.device)
                image2_resized = torch.cat((image2_resized, alpha_channel), dim=-1)

        # 根据指定的方向拼接图像
        if direction == 'right':
            concatenated_image = torch.cat((image1, image2_resized), dim=2)  # 沿宽度拼接
        elif direction == 'down':
            concatenated_image = torch.cat((image1, image2_resized), dim=1)  # 沿高度拼接
        elif direction == 'left':
            concatenated_image = torch.cat((image2_resized, image1), dim=2)  # 沿宽度拼接
        elif direction == 'up':
            concatenated_image = torch.cat((image2_resized, image1), dim=1)  # 沿高度拼接
        
        return concatenated_image,


# 节点类映射配置
NODE_CLASS_MAPPINGS = {
    "PDIMAGE_ImageCombine": Imagecombine2,  # 映射节点名称到类
}

# 设置节点在 UI 中显示的名称
NODE_DISPLAY_NAME_MAPPINGS = {
    "PDIMAGE_ImageCombine": "PDIMAGE:ImageCombine",  # 在 UI 显示的节点名称
}
