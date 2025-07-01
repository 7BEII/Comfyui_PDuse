import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import torch

class TextOverlayNode:
    @classmethod
    def INPUT_TYPES(cls):
        # 获取当前脚本所在目录（py目录）
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # 定位到节点根目录（也就是py的上一级）
        root_dir = os.path.abspath(os.path.join(current_dir, ".."))

        # 构建 fonts 文件夹的路径（根目录下的fonts文件夹）
        fonts_dir = os.path.join(root_dir, "fonts")

        font_files = []
        if os.path.exists(fonts_dir):
            font_files = [f for f in os.listdir(fonts_dir) if f.lower().endswith(".ttf")]

        # 如果没有找到字体文件，提供一个默认选项
        if not font_files:
            font_files = ["Arial.ttf"]  # 或者其他默认字体文件名

        return {
            "required": {
                "image": ("IMAGE",),
                "text": ("STRING", {"default": "Hello, ComfyUI!"}),
                "font_size": ("FLOAT", {"default": 24.0}),
                "font_color": ("STRING", {"default": "#000000"}),
                "position_x": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.001}),
                "position_y": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.001}),
                "letter_gap": ("FLOAT", {"default": 0.0, "min": -10.0, "max": 10.0, "step": 0.01}),
                "font_name": (font_files,),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "apply_text_overlay"
    CATEGORY = "image"

    def apply_text_overlay(self, image, text, font_size, font_color, position_x, position_y, letter_gap, font_name):
        # 确保图像张量在 CPU 上
        if image.device.type != 'cpu':
            image = image.cpu()

        # 提取批量中的第一张图像
        image_np = image[0].numpy()  # 形状为 [H, W, C]

        # 将像素值从 [0,1] 范围转换为 [0,255]，并转换为 uint8 类型
        image_np = (image_np * 255).clip(0, 255).astype(np.uint8)

        # 创建 PIL 图像
        pil_image = Image.fromarray(image_np)

        draw = ImageDraw.Draw(pil_image)

        # 定位到根目录的fonts文件夹
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.abspath(os.path.join(current_dir, ".."))
        fonts_dir = os.path.join(root_dir, "fonts")
        font_path = os.path.join(fonts_dir, font_name)

        # 加载字体，添加错误处理
        try:
            font = ImageFont.truetype(font_path, int(font_size))
        except OSError:
            print(f"警告：无法加载字体文件 '{font_path}'，将使用默认字体。")
            font = ImageFont.load_default()

        # 计算文本尺寸（考虑单字绘制）
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0] + (len(text) - 1) * letter_gap
        text_height = bbox[3] - bbox[1]

        # 计算文本位置
        x = int(position_x * pil_image.width - text_width / 2)
        y = int(position_y * pil_image.height - text_height / 2)

        # 绘制文本，逐个字绘制加字距
        current_x = x
        for char in text:
            draw.text((current_x, y), char, fill=font_color, font=font)
            char_bbox = draw.textbbox((0, 0), char, font=font)
            char_width = char_bbox[2] - char_bbox[0]
            current_x += char_width + letter_gap

        # 将 PIL 图像转换回 NumPy 数组，并归一化到 [0,1]
        result_np = np.array(pil_image).astype(np.float32) / 255.0

        # 添加批量维度，并转换为 PyTorch 张量
        result_tensor = torch.from_numpy(result_np).unsqueeze(0)

        return (result_tensor,)



# 节点映射
NODE_CLASS_MAPPINGS = {
    "PD_Text Overlay Node": TextOverlayNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_Text Overlay Node": "PD_Text Overlay Node",
}