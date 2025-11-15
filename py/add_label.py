import torch
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import folder_paths
from comfy.utils import common_upscale

# 获取当前脚本目录
script_directory = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

class CustomAddLabel:
    @classmethod
    def INPUT_TYPES(s):
        # 获取字体文件列表
        fonts_dir = os.path.join(script_directory, "fonts")
        if not os.path.exists(fonts_dir):
            os.makedirs(fonts_dir)
        
        font_files = []
        for file in os.listdir(fonts_dir):
            if file.lower().endswith(('.ttf', '.otf')):
                font_files.append(file)
        
        if not font_files:
            font_files = ["default"]  # 如果没有字体文件，使用默认字体
            
        return {
            "required": {
                "image": ("IMAGE",),
                "text_x": ("INT", {"default": 5, "min": 1, "max": 100, "step": 1}),
                "text_y": ("INT", {"default": 45, "min": 1, "max": 100, "step": 1}),
                "height": ("INT", {"default": 90, "min": 1, "max": 1000, "step": 1}),
                "font_size": ("INT", {"default": 40, "min": 8, "max": 200, "step": 1}),
                "font": (font_files,),
                "text": ("STRING", {"default": "Text"}),
                "color": ([
                    'light',  # 白底黑字
                    'dark'    # 黑底白字
                ], {
                    "default": 'light'
                }),
                "direction": ([
                    'up',
                    'down', 
                    'left',
                    'right'
                ], {
                    "default": 'down'
                }),
            },
            "optional": {
                "caption": ("STRING", {"default": "", "forceInput": True}),
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "add_custom_label"
    CATEGORY = "PDuse/Image"
    DESCRIPTION = """
    Adds text labels to images with percentage-based positioning.
    text_x: 1-100 (1=left aligned, 100=right aligned)
    text_y: 1-100 (position within the added label area)
    color: light (white background, black text) or dark (black background, white text)
    Supports batch processing with individual captions.
    """
    def add_custom_label(self, image, text_x, text_y, text, height, font_size, font, color, direction, caption=""):
        batch_size = image.shape[0]
        img_height = image.shape[1]
        img_width = image.shape[2]
        
        # 根据color模式设置颜色
        if color == 'light':
            bg_color = (255, 255, 255)  # 白色背景
            text_color = (0, 0, 0)      # 黑色文字
        else:  # dark
            bg_color = (0, 0, 0)        # 黑色背景
            text_color = (255, 255, 255) # 白色文字
        
        # 获取字体路径
        fonts_dir = os.path.join(script_directory, "fonts")
        if font == "default" or not os.path.exists(os.path.join(fonts_dir, font)):
            try:
                font_obj = ImageFont.load_default()
            except:
                font_obj = ImageFont.truetype("arial.ttf", font_size)
        else:
            font_path = os.path.join(fonts_dir, font)
            try:
                font_obj = ImageFont.truetype(font_path, font_size)
            except:
                font_obj = ImageFont.load_default()
        
        def process_single_image(input_image, text_content):
            # 转换图像为PIL格式
            pil_image = Image.fromarray((input_image.cpu().numpy() * 255).astype(np.uint8))
            
            # 创建标签区域
            if direction in ['up', 'down']:
                label_img = Image.new("RGB", (img_width, height), bg_color)
                label_draw = ImageDraw.Draw(label_img)
                
                # 计算文本位置 - 基于百分比
                # text_x: 1-100 转换为实际x坐标
                actual_x = int((text_x - 1) / 99.0 * (img_width - 10))  # 留10像素边距
                actual_x = max(5, min(actual_x, img_width - 5))  # 确保在边界内
                
                # text_y: 1-100 转换为标签区域内的y坐标
                actual_y = int((text_y - 1) / 99.0 * (height - font_size))
                actual_y = max(5, min(actual_y, height - font_size - 5))  # 确保文字完整显示
                
                # 绘制文本
                try:
                    label_draw.text((actual_x, actual_y), text_content, font=font_obj, fill=text_color)
                except:
                    label_draw.text((actual_x, actual_y), text_content, fill=text_color)
                
                # 组合图像
                if direction == 'up':
                    combined_img = Image.new("RGB", (img_width, img_height + height))
                    combined_img.paste(label_img, (0, 0))
                    combined_img.paste(pil_image, (0, height))
                else:  # down
                    combined_img = Image.new("RGB", (img_width, img_height + height))
                    combined_img.paste(pil_image, (0, 0))
                    combined_img.paste(label_img, (0, img_height))
            
            elif direction in ['left', 'right']:
                label_img = Image.new("RGB", (height, img_height), bg_color)
                label_draw = ImageDraw.Draw(label_img)
                
                # 对于左右方向，需要旋转文本或调整坐标系
                # 这里简化处理，将文本放在标签区域中央
                actual_x = int((text_x - 1) / 99.0 * (height - 10))
                actual_x = max(5, min(actual_x, height - 5))
                
                actual_y = int((text_y - 1) / 99.0 * (img_height - font_size))
                actual_y = max(5, min(actual_y, img_height - font_size - 5))
                
                try:
                    label_draw.text((actual_x, actual_y), text_content, font=font_obj, fill=text_color)
                except:
                    label_draw.text((actual_x, actual_y), text_content, fill=text_color)
                
                # 组合图像
                if direction == 'left':
                    combined_img = Image.new("RGB", (img_width + height, img_height))
                    combined_img.paste(label_img, (0, 0))
                    combined_img.paste(pil_image, (height, 0))
                else:  # right
                    combined_img = Image.new("RGB", (img_width + height, img_height))
                    combined_img.paste(pil_image, (0, 0))
                    combined_img.paste(label_img, (img_width, 0))
            
            # 转换回tensor格式
            result_array = np.array(combined_img).astype(np.float32) / 255.0
            return torch.from_numpy(result_array).unsqueeze(0)
        # 批量处理
        processed_images = []
        
        if caption == "":
            # 使用统一文本
            for i in range(batch_size):
                processed_img = process_single_image(image[i], text)
                processed_images.append(processed_img)
        else:
            # 使用个别caption
            captions = caption.split('\n') if caption else [text] * batch_size
            
            # 确保caption数量匹配图像数量
            while len(captions) < batch_size:
                captions.append(text)
            
            for i in range(batch_size):
                caption_text = captions[i] if i < len(captions) else text
                processed_img = process_single_image(image[i], caption_text)
                processed_images.append(processed_img)
        
        # 合并批次
        result_batch = torch.cat(processed_images, dim=0)
        
        return (result_batch,)

# 节点注册
NODE_CLASS_MAPPINGS = {
    "CustomAddLabel": CustomAddLabel
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CustomAddLabel": "PD_Add Label"
}
