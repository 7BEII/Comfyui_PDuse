# PD_image_to_text_v1.py
import torch
import numpy as np

class PD_image_to_text_v1:
    """
    PD图像到文本节点
    接收一张图片和一个提示词，输出提示词的文本字符串
    """
    
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),  # 输入图片，格式为 B H W C
                "prompt": ("STRING", {
                    "default": "请在此输入提示词",
                    "multiline": True,
                    "placeholder": "输入你想要输出的文本内容"
                }),
            },
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text_output",)
    FUNCTION = "process"
    CATEGORY = "PD_Nodes/ImageToText"
    
    def process(self, image, prompt):
        """
        处理输入的图片和提示词，返回提示词文本
        
        Args:
            image: 输入图片张量，格式为 B H W C
            prompt: 输入的提示词字符串
            
        Returns:
            tuple: 包含提示词字符串的元组
        """
        try:
            # 验证图片张量格式
            if image.dim() == 4:
                batch, height, width, channels = image.shape
                print(f"接收到图片: Batch={batch}, Height={height}, Width={width}, Channels={channels}")
            else:
                print(f"图片张量维度: {image.shape}")
            
            # 输出提示词
            print(f"输出提示词: {prompt}")
            
            # 返回提示词字符串
            return (prompt,)
            
        except Exception as e:
            error_msg = f"处理过程中出现错误: {str(e)}"
            print(f"错误: {error_msg}")
            return (error_msg,)


# 节点注册
NODE_CLASS_MAPPINGS = {
    "PD_image_to_text_v1": PD_image_to_text_v1
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_image_to_text_v1": "PD_Image to Text V1"
}

# 节点描述
NODE_DESCRIPTIONS = {
    "PD_image_to_text_v1": "接收一张图片和提示词输入，输出提示词的文本字符串"
}

# 导出节点类
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'NODE_DESCRIPTIONS']

