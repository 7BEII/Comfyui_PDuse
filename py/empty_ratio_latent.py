"""
PD empty ratio latent.py
根据比例生成空Latent节点
支持多种常用比例，自动计算宽高
"""

import torch


class PDEmptyRatioLatent:
    """
    根据比例生成空Latent
    支持常用比例：1:1, 3:4, 4:3, 16:9, 9:16, 1:2, 2:1
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "ratio": (["1:1", "3:4", "4:3", "16:9", "9:16", "1:2", "2:1"], {
                    "default": "1:1",
                    "tooltip": "图像宽高比例"
                }),
                "longgersize": ("INT", {
                    "default": 1024,
                    "min": 64,
                    "max": 8192,
                    "step": 64,
                    "display": "number",
                    "tooltip": "最长边的像素大小"
                }),
            },
        }
    
    RETURN_TYPES = ("LATENT",)
    RETURN_NAMES = ("latent",)
    FUNCTION = "generate_latent"
    CATEGORY = "PDuse/Latent"
    
    def generate_latent(self, ratio, longgersize):
        """
        根据比例和最长边尺寸生成空latent
        
        Args:
            ratio: 宽高比例字符串，如 "16:9"
            longgersize: 最长边的像素大小
            
        Returns:
            tuple: 包含latent字典的元组
        """
        # 解析比例
        ratio_parts = ratio.split(":")
        width_ratio = int(ratio_parts[0])
        height_ratio = int(ratio_parts[1])
        
        # 计算实际宽高
        if width_ratio >= height_ratio:
            # 宽边是最长边
            width = longgersize
            height = int(longgersize * height_ratio / width_ratio)
        else:
            # 高边是最长边
            height = longgersize
            width = int(longgersize * width_ratio / height_ratio)
        
        # 确保宽高是8的倍数（latent空间要求）
        width = (width // 8) * 8
        height = (height // 8) * 8
        
        # 计算latent尺寸（原图尺寸除以8）
        latent_width = width // 8
        latent_height = height // 8
        
        # 创建空latent张量
        # Latent格式: (batch_size, channels, height, width)
        # SD模型的latent有4个通道
        batch_size = 1
        channels = 4
        
        latent = torch.zeros([batch_size, channels, latent_height, latent_width])
        
        return ({"samples": latent},)


# ComfyUI节点注册
NODE_CLASS_MAPPINGS = {
    "PDEmptyRatioLatent": PDEmptyRatioLatent
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PDEmptyRatioLatent": "PD Empty Ratio Latent"
}

