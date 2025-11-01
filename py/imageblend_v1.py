import torch
import copy
import numpy as np
from PIL import Image, ImageChops

# 工具函数定义
def log(message, message_type='info'):
    """日志输出函数"""
    if message_type == 'warning':
        print(f"⚠️ {message}")
    elif message_type == 'finish':
        print(f"✅ {message}")
    else:
        print(f"ℹ️ {message}")

def pil2tensor(image):
    """将PIL图像转换为张量 (1, H, W, C)"""
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)

def tensor2pil(image):
    """将张量转换为PIL图像"""
    return Image.fromarray(np.clip(255. * image.cpu().numpy().squeeze(), 0, 255).astype(np.uint8))

def image2mask(image):
    """将PIL图像转换为遮罩张量"""
    if isinstance(image, Image.Image):
        image = np.array(image.convert('L'))
    return torch.from_numpy(image.astype(np.float32) / 255.0).unsqueeze(0)

def mask2image(mask):
    """将遮罩张量转换为PIL图像"""
    return Image.fromarray(np.clip(255. * mask.cpu().numpy().squeeze(), 0, 255).astype(np.uint8), mode='L')

# 混合模式列表
chop_mode_v2 = [
    'normal', 'multiply', 'screen', 'overlay', 'soft_light', 'hard_light',
    'color_dodge', 'color_burn', 'darken', 'lighten', 'difference', 'exclusion'
]

def chop_image_v2(image1, image2, blend_mode, opacity):
    """
    图像混合函数
    Args:
        image1: 背景图像 (PIL Image)
        image2: 前景图像 (PIL Image) 
        blend_mode: 混合模式
        opacity: 透明度 (0-100)
    Returns:
        混合后的PIL图像
    """
    if image1.size != image2.size:
        image2 = image2.resize(image1.size, Image.LANCZOS)
    
    # 转换透明度
    alpha = opacity / 100.0
    
    # 确保图像为RGB模式
    if image1.mode != 'RGB':
        image1 = image1.convert('RGB')
    if image2.mode != 'RGB':
        image2 = image2.convert('RGB')
    
    # 根据混合模式进行处理
    if blend_mode == 'normal':
        result = Image.blend(image1, image2, alpha)
    elif blend_mode == 'multiply':
        result = ImageChops.multiply(image1, image2)
        result = Image.blend(image1, result, alpha)
    elif blend_mode == 'screen':
        result = ImageChops.screen(image1, image2)
        result = Image.blend(image1, result, alpha)
    elif blend_mode == 'overlay':
        result = ImageChops.overlay(image1, image2)
        result = Image.blend(image1, result, alpha)
    elif blend_mode == 'soft_light':
        result = ImageChops.soft_light(image1, image2)
        result = Image.blend(image1, result, alpha)
    elif blend_mode == 'hard_light':
        result = ImageChops.hard_light(image1, image2)
        result = Image.blend(image1, result, alpha)
    elif blend_mode == 'difference':
        result = ImageChops.difference(image1, image2)
        result = Image.blend(image1, result, alpha)
    elif blend_mode == 'darken':
        result = ImageChops.darker(image1, image2)
        result = Image.blend(image1, result, alpha)
    elif blend_mode == 'lighten':
        result = ImageChops.lighter(image1, image2)
        result = Image.blend(image1, result, alpha)
    else:
        # 默认使用normal模式
        result = Image.blend(image1, image2, alpha)
    
    return result

class ImageBlendV1:
    """
    * 图片混合节点V1版本
    * 基于ImageBlendAdvanceV2简化而来，保留核心混合功能
    * 支持基础的图层混合、透明度控制和位置调整
    """
    
    def __init__(self):
        self.NODE_NAME = 'ImageBlendV1'

    @classmethod
    def INPUT_TYPES(cls):
        """
        * 定义节点的输入参数类型
        * @return {dict} 包含required和optional参数的字典
        """
        align_mode = ['default', 'top_align', 'bottom_align', 'left_align', 'right_align']
        
        return {
            "required": {
                "background_image": ("IMAGE", ),  # 背景图像，张量形状为B H W C
                "layer_image": ("IMAGE",),        # 图层图像，张量形状为B H W C
                "blend_mode": (chop_mode_v2,),    # 混合模式选择
                "opacity": ("INT", {"default": 100, "min": 0, "max": 100, "step": 1}),  # 透明度 0-100
                "x_percent": ("FLOAT", {"default": 50, "min": -999, "max": 999, "step": 0.01}),  # X轴位置百分比
                "y_percent": ("FLOAT", {"default": 50, "min": -999, "max": 999, "step": 0.01}),  # Y轴位置百分比
                "scale": ("FLOAT", {"default": 1, "min": 0.01, "max": 10, "step": 0.01}),        # 缩放比例
                "align_mode": (align_mode, {"default": "default"}),  # 对齐模式选择
            },
            "optional": {
                "layer_mask": ("MASK",),  # 可选的图层遮罩，张量形状为B H W
                "invert_mask": ("BOOLEAN", {"default": False}),  # 是否反转遮罩
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    FUNCTION = 'image_blend_v1'
    CATEGORY = 'PD/ImageBlend'

    def image_blend_v1(self, background_image, layer_image, invert_mask, blend_mode, opacity, 
                      x_percent, y_percent, scale, align_mode, layer_mask=None):
        """
        * 执行图片混合操作的主要函数
        * @param {torch.Tensor} background_image - 背景图像张量 (B, H, W, C)
        * @param {torch.Tensor} layer_image - 图层图像张量 (B, H, W, C)  
        * @param {str} blend_mode - 混合模式
        * @param {int} opacity - 透明度 (0-100)
        * @param {float} x_percent - X轴位置百分比
        * @param {float} y_percent - Y轴位置百分比
        * @param {float} scale - 缩放比例
        * @param {str} align_mode - 对齐模式 (default/top_align/bottom_align/left_align/right_align/center_align)
        * @param {torch.Tensor} layer_mask - 可选的图层遮罩 (B, H, W)
        * @param {bool} invert_mask - 是否反转遮罩
        * @return {tuple} 返回混合后的图像和遮罩
        """
        
        # 将输入张量分离为单独的图像列表
        b_images = []
        l_images = []
        l_masks = []
        ret_images = []
        ret_masks = []
        
        # 处理背景图像 - 确保维度为 (1, H, W, C)
        for b in background_image:
            b_images.append(torch.unsqueeze(b, 0))
            
        # 处理图层图像 - 确保维度为 (1, H, W, C)
        for l in layer_image:
            l_images.append(torch.unsqueeze(l, 0))
            # 从图层图像提取alpha通道作为默认遮罩
            m = tensor2pil(l)
            if m.mode == 'RGBA':
                l_masks.append(m.split()[-1])
            else:
                l_masks.append(Image.new('L', m.size, 'white'))
        
        # 如果提供了layer_mask，使用它替代默认遮罩
        if layer_mask is not None:
            # 确保遮罩维度正确 (B, H, W)
            if layer_mask.dim() == 2:
                layer_mask = torch.unsqueeze(layer_mask, 0)
            l_masks = []
            for m in layer_mask:
                # 处理遮罩反转
                if invert_mask:
                    m = 1 - m  # 反转遮罩值
                    log(f"遮罩已反转", message_type='info')
                l_masks.append(tensor2pil(torch.unsqueeze(m, 0)).convert('L'))

        # 批处理 - 取最大批次数
        max_batch = max(len(b_images), len(l_images), len(l_masks))
        
        for i in range(max_batch):
            # 获取当前批次的图像和遮罩
            background_image_current = b_images[i] if i < len(b_images) else b_images[-1]
            layer_image_current = l_images[i] if i < len(l_images) else l_images[-1]
            mask_current = l_masks[i] if i < len(l_masks) else l_masks[-1]
            
            # 转换为PIL图像进行处理
            _canvas = tensor2pil(background_image_current).convert('RGB')
            _layer = tensor2pil(layer_image_current)
            
            # 确保遮罩尺寸与图层匹配
            if mask_current.size != _layer.size:
                mask_current = Image.new('L', _layer.size, 'white')
                log(f"Warning: {self.NODE_NAME} mask size mismatch, using default white mask!", message_type='warning')

            # 应用缩放变换
            if scale != 1.0:
                orig_width, orig_height = _layer.size
                target_width = int(orig_width * scale)
                target_height = int(orig_height * scale)
                _layer = _layer.resize((target_width, target_height), Image.LANCZOS)
                mask_current = mask_current.resize((target_width, target_height), Image.LANCZOS)

            # 根据对齐模式计算图层在画布上的位置
            # 先计算基础对齐位置，然后应用百分比偏移
            if align_mode == 'default':
                # 默认模式：使用百分比定位
                base_x = _canvas.width // 2 - _layer.width // 2  # 水平居中为基础
                base_y = _canvas.height // 2 - _layer.height // 2  # 垂直居中为基础
            elif align_mode == 'top_align':
                # 顶对齐：图层顶部与背景顶部对齐为基础
                base_x = _canvas.width // 2 - _layer.width // 2  # 水平居中
                base_y = 0  # 顶部对齐
                log(f"顶对齐模式：以顶部对齐为基础进行位置调整", message_type='info')
            elif align_mode == 'bottom_align':
                # 底对齐：图层底部与背景底部对齐为基础
                base_x = _canvas.width // 2 - _layer.width // 2  # 水平居中
                base_y = _canvas.height - _layer.height  # 底部对齐
                log(f"底对齐模式：以底部对齐为基础进行位置调整", message_type='info')
            elif align_mode == 'left_align':
                # 左对齐：图层左边与背景左边对齐为基础
                base_x = 0  # 左边对齐
                base_y = _canvas.height // 2 - _layer.height // 2  # 垂直居中
                log(f"左对齐模式：以左边对齐为基础进行位置调整", message_type='info')
            elif align_mode == 'right_align':
                # 右对齐：图层右边与背景右边对齐为基础
                base_x = _canvas.width - _layer.width  # 右边对齐
                base_y = _canvas.height // 2 - _layer.height // 2  # 垂直居中
                log(f"右对齐模式：以右边对齐为基础进行位置调整", message_type='info')
            else:
                # 兜底：使用默认模式
                base_x = _canvas.width // 2 - _layer.width // 2
                base_y = _canvas.height // 2 - _layer.height // 2
            
            # 应用百分比偏移调整 (50%表示无偏移，0%表示向左/上偏移，100%表示向右/下偏移)
            # 计算可用的偏移范围
            max_x_offset = _canvas.width // 4  # 最大水平偏移为画布宽度的1/4
            max_y_offset = _canvas.height // 4  # 最大垂直偏移为画布高度的1/4
            
            # 计算实际偏移量 (50%为中心，0%到100%的范围)
            x_offset = int((x_percent - 50) / 50 * max_x_offset)
            y_offset = int((y_percent - 50) / 50 * max_y_offset)
            
            # 最终位置 = 基础对齐位置 + 百分比偏移
            x = base_x + x_offset
            y = base_y + y_offset

            # 执行图层合成
            _comp = copy.copy(_canvas)
            _compmask = Image.new("RGB", _comp.size, color='black')
            
            # 将图层粘贴到合成图像上
            _comp.paste(_layer, (x, y))
            _compmask.paste(mask_current.convert('RGB'), (x, y))
            _compmask = _compmask.convert('L')
            
            # 应用混合模式和透明度
            _comp = chop_image_v2(_canvas, _comp, blend_mode, opacity)

            # 最终合成到背景画布
            _canvas.paste(_comp, mask=_compmask)

            # 转换结果回张量格式
            ret_images.append(pil2tensor(_canvas))
            ret_masks.append(image2mask(_compmask))

        log(f"{self.NODE_NAME} Successfully processed {len(ret_images)} image(s).", message_type='finish')
        
        # 返回结果 - 确保张量形状正确 (B, H, W, C) 和 (B, H, W)
        return (torch.cat(ret_images, dim=0), torch.cat(ret_masks, dim=0))

# ComfyUI节点注册映射
NODE_CLASS_MAPPINGS = {
    "ImageBlendV1": ImageBlendV1
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageBlendV1": "PD:Image Blend V1"
}
