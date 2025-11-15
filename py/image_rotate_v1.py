import torch
from PIL import Image
import numpy as np
import math

def tensor2pil(tensor):
    # 将 tensor 转换为 PIL Image
    return Image.fromarray((tensor.cpu().numpy().squeeze() * 255).astype(np.uint8))

def pil2tensor(pil_image):
    # 将 PIL Image 转换为 tensor
    return torch.from_numpy(np.array(pil_image).astype(np.float32) / 255.0).unsqueeze(0)

def get_min_bounding_rect(width, height, angle):
    """
    计算旋转后的最小外接矩形尺寸
    """
    angle_rad = math.radians(angle)
    cos_angle = abs(math.cos(angle_rad))
    sin_angle = abs(math.sin(angle_rad))
    
    # 计算旋转后的四个角点
    corners = [
        (0, 0),
        (width, 0),
        (width, height),
        (0, height)
    ]
    
    # 旋转角点
    rotated_corners = []
    for x, y in corners:
        # 将坐标原点移到中心
        x -= width / 2
        y -= height / 2
        # 旋转
        new_x = x * cos_angle - y * sin_angle
        new_y = x * sin_angle + y * cos_angle
        rotated_corners.append((new_x, new_y))
    
    # 计算最小外接矩形的尺寸
    min_x = min(x for x, _ in rotated_corners)
    max_x = max(x for x, _ in rotated_corners)
    min_y = min(y for _, y in rotated_corners)
    max_y = max(y for _, y in rotated_corners)
    
    new_width = int(max_x - min_x)
    new_height = int(max_y - min_y)
    
    return new_width, new_height

class PD_Image_Rotate_v1:
    """
    对输入的图片进行旋转，支持任意角度旋转，并且可以选择不同的插值方式（nearest、bilinear、bicubic），还可以选择旋转模式（internal 或 transpose）。
    使用最小外接矩形避免裁切。
    """
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "mode": (["transpose", "internal"],),
                "rotation": ("INT", {"default": 90, "min": -360, "max": 360, "step": 1}),
                "sampler": (["nearest", "bilinear", "bicubic"],),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "image_rotate"

    CATEGORY = "PDuse/Image"

    def image_rotate(self, images, mode, rotation, sampler):
        batch_tensor = []
        for image in images:
            # PIL Image
            image = tensor2pil(image)
            original_width, original_height = image.size

            # Check rotation
            if rotation > 360:
                rotation = int(360)
            if rotation < -360:
                rotation = int(-360)

            # Set Sampler
            if sampler:
                if sampler == 'nearest':
                    sampler = Image.NEAREST
                elif sampler == 'bicubic':
                    sampler = Image.BICUBIC
                elif sampler == 'bilinear':
                    sampler = Image.BILINEAR
                else:
                    sampler = Image.BILINEAR

            # Rotate Image
            if mode == 'internal':
                # 先转为RGBA，背景透明
                image_rgba = image.convert('RGBA')
                rotated = image_rgba.rotate(rotation, sampler, expand=True)
                # 自动裁剪非透明内容
                bbox = rotated.getbbox()
                if bbox:
                    rotated = rotated.crop(bbox)
                # 转回RGB，透明部分填充为黑色
                image = rotated.convert('RGB')
            else:
                # 对于非90度倍数的角度，强制使用internal模式
                if rotation % 90 != 0:
                    # 计算最小外接矩形尺寸
                    new_width, new_height = get_min_bounding_rect(original_width, original_height, rotation)
                    # 创建新的透明背景
                    new_image = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))
                    # 将原图粘贴到中心位置
                    paste_x = (new_width - original_width) // 2
                    paste_y = (new_height - original_height) // 2
                    new_image.paste(image, (paste_x, paste_y))
                    # 旋转图片
                    image_rgba = new_image.convert('RGBA')
                    rotated = image_rgba.rotate(rotation, sampler, expand=True)
                    bbox = rotated.getbbox()
                    if bbox:
                        rotated = rotated.crop(bbox)
                    image = rotated.convert('RGB')
                else:
                    rot = int(rotation / 90)
                    for _ in range(rot):
                        image = image.transpose(2)

            batch_tensor.append(pil2tensor(image))

        batch_tensor = torch.cat(batch_tensor, dim=0)

        return (batch_tensor,)

# 节点映射
NODE_CLASS_MAPPINGS = {
    "PD_Image_Rotate_v1": PD_Image_Rotate_v1
}

# 节点显示名称映射
NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_Image_Rotate_v1": "PD:Image Rotate"
} 
    