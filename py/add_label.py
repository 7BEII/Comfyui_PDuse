import torch
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

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
            font_files = ["default"]
            
        return {
            "required": {
                "image": ("IMAGE",),
                # 逻辑更新：50为居中，1为起始，100为结束
                "text_x": ("INT", {"default": 50, "min": 1, "max": 100, "step": 1}),
                "text_y": ("INT", {"default": 50, "min": 1, "max": 100, "step": 1}),
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
    DESCRIPTION = "Adds text labels by concatenating tensors. 50=Center. Keeps original image pixels 100% intact."

    def add_custom_label(self, image, text_x, text_y, text, height, font_size, font, color, direction, caption=""):
        # image shape: [Batch, Height, Width, Channel]
        batch_size = image.shape[0]
        img_height = image.shape[1]
        img_width = image.shape[2]
        
        # 1. 设置配色
        if color == 'light':
            bg_color = (255, 255, 255)
            text_color = (0, 0, 0)
        else:
            bg_color = (0, 0, 0)
            text_color = (255, 255, 255)
        
        # 2. 加载字体
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

        # 3. 准备文字内容列表
        if caption == "":
            captions = [text] * batch_size
        else:
            captions = caption.split('\n') if caption else [text] * batch_size
            while len(captions) < batch_size:
                captions.append(text)

        result_images = []

        for i in range(batch_size):
            # === 关键点1：直接引用原图 Tensor，不做任何处理，保证原图色彩绝对不变 ===
            current_original_tensor = image[i] 
            
            # 获取当前文字
            current_text = captions[i] if i < len(captions) else text

            # 4. 创建 Label 条的画布 (纯色背景)
            # 根据方向决定 Label 的宽和高
            if direction in ['up', 'down']:
                label_w = img_width
                label_h = height
            else: # left, right
                label_w = height
                label_h = img_height

            label_img = Image.new("RGB", (label_w, label_h), bg_color)
            label_draw = ImageDraw.Draw(label_img)

            # 5. 计算文字坐标 (支持 50=居中 逻辑)
            # 获取文字实际渲染大小
            try:
                bbox = font_obj.getbbox(current_text) # (left, top, right, bottom)
            except AttributeError:
                bbox = label_draw.textbbox((0, 0), current_text, font=font_obj)
            
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]

            # 计算 X 轴位置 (剩余空间 * 百分比)
            # text_x: 1 -> ratio 0.0 (左/上对齐)
            # text_x: 50 -> ratio ~0.5 (居中)
            # text_x: 100 -> ratio 1.0 (右/下对齐)
            ratio_x = (text_x - 1) / 99.0
            available_w = label_w - text_w
            draw_x = available_w * ratio_x - bbox[0] # 减去bbox[0]以修正字体左边距

            # 计算 Y 轴位置
            ratio_y = (text_y - 1) / 99.0
            available_h = label_h - text_h
            draw_y = available_h * ratio_y - bbox[1] # 减去bbox[1]以修正字体上边距

            # 绘制文字到 Label 上
            label_draw.text((draw_x, draw_y), current_text, font=font_obj, fill=text_color)

            # 6. 将生成的 Label 转为 Tensor
            # 注意：只有这个新生成的色块经历了 float转换，原图没有
            label_numpy = np.array(label_img).astype(np.float32) / 255.0
            label_tensor = torch.from_numpy(label_numpy) # shape: [H, W, C]

            # === 关键点2：物理拼接 (Tensor Concatenation) ===
            # 直接把原图和Label拼在一起，而不是画在原图上
            
            if direction == 'up':
                # 高度方向拼接：Label在上，原图在下
                new_img = torch.cat((label_tensor, current_original_tensor), dim=0)
            elif direction == 'down':
                # 原图在上，Label在下
                new_img = torch.cat((current_original_tensor, label_tensor), dim=0)
            elif direction == 'left':
                # 宽度方向拼接：Label在左，原图在右
                new_img = torch.cat((label_tensor, current_original_tensor), dim=1)
            elif direction == 'right':
                # 原图在左，Label在右
                new_img = torch.cat((current_original_tensor, label_tensor), dim=1)
            
            result_images.append(new_img)

        # 重新堆叠为 Batch
        result_batch = torch.stack(result_images)
        
        return (result_batch,)

NODE_CLASS_MAPPINGS = {
    "CustomAddLabel": CustomAddLabel
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CustomAddLabel": "PD_Add Label"
}