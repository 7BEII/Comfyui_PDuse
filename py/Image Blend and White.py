import torch
import numpy as np
from PIL import Image

def pil2tensor(image):
    """将PIL图像转换为张量 (1, H, W, C)"""
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)

def tensor2pil(image):
    """将张量转换为PIL图像"""
    return Image.fromarray(np.clip(255. * image.cpu().numpy().squeeze(), 0, 255).astype(np.uint8))

class ImageBlendAndWhite:
    """
    * 透明底图片加白色背景节点
    * 输入透明底图片，输出白底图片，尺寸完全一致
    """
    
    def __init__(self):
        self.NODE_NAME = 'ImageBlendAndWhite'

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),  # 输入图片
                "invert_mask": ("BOOLEAN", {"default": True}),  # 是否反转遮罩，默认True
            },
            "optional": {
                "mask": ("MASK",),   # 可选遮罩
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = 'add_white_background'
    CATEGORY = 'PD/ImageBlend'

    def add_white_background(self, image, invert_mask=True, mask=None):
        """
        * 给透明底图片添加白色背景
        * 保持原图尺寸不变
        * mask默认会被反转
        """
        ret_images = []
        
        print(f"ℹ️ 开始处理 {image.shape[0]} 张图像，遮罩反转: {invert_mask}")
        
        # 处理每张图像
        for i in range(image.shape[0]):
            # 获取当前图像
            current_image = image[i]
            
            # 转换为PIL图像
            pil_image = tensor2pil(torch.unsqueeze(current_image, 0))
            
            # 获取图像尺寸
            width, height = pil_image.size
            
            # 创建相同尺寸的白色背景
            white_bg = Image.new('RGB', (width, height), 'white')
            
            # 处理透明度/遮罩
            if mask is not None and i < mask.shape[0]:
                # 使用提供的遮罩
                current_mask = mask[i]
                
                # 根据参数决定是否反转遮罩
                if invert_mask:
                    current_mask = 1.0 - current_mask
                    print(f"ℹ️ 遮罩已反转")
                
                mask_pil = Image.fromarray(np.clip(255. * current_mask.cpu().numpy(), 0, 255).astype(np.uint8), mode='L')
                if mask_pil.size != pil_image.size:
                    mask_pil = mask_pil.resize(pil_image.size, Image.LANCZOS)
            elif pil_image.mode == 'RGBA':
                # 使用图像的Alpha通道
                mask_pil = pil_image.split()[-1]
                print(f"ℹ️ 使用图像Alpha通道作为遮罩")
            else:
                # 没有透明信息，创建全白遮罩
                mask_pil = Image.new('L', pil_image.size, 255)
                print(f"ℹ️ 创建全白遮罩")
            
            # 确保图像为RGB模式
            if pil_image.mode == 'RGBA':
                rgb_image = pil_image.convert('RGB')
            else:
                rgb_image = pil_image.convert('RGB')
            
            # 将图像粘贴到白色背景上
            result = white_bg.copy()
            result.paste(rgb_image, (0, 0), mask_pil)
            
            # 转换回张量
            ret_images.append(pil2tensor(result))
        
        print(f"✅ 成功处理完成")
        return (torch.cat(ret_images, dim=0),)

# ComfyUI节点注册
NODE_CLASS_MAPPINGS = {
    "ImageBlendAndWhite": ImageBlendAndWhite
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageBlendAndWhite": "PD:Add White Background"
}
