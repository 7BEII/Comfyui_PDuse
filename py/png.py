import torch
import numpy as np
from PIL import Image

def tensor2pil(image):
    """将ComfyUI图像张量转换为PIL图像"""
    return Image.fromarray(np.clip(255. * image.cpu().numpy().squeeze(), 0, 255).astype(np.uint8))

def pil2tensor(image):
    """将PIL图像转换为ComfyUI图像张量"""
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)

class PD_RemoveBlackBackground:
    """
    去除图像黑色背景节点
    输入图像，去掉黑底保留白色区域，输出透明底PNG
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),  # 输入图像张量 [B, H, W, C]
                "threshold": ("FLOAT", {
                    "default": 0.9, 
                    "min": 0.0, 
                    "max": 1.0, 
                    "step": 0.01
                }),  # 黑色检测阈值，低于此值的像素被认为是黑色
            },
            "optional": {
                "smooth_edges": ("BOOLEAN", {"default": True}),  # 是否平滑边缘
                "invert_mask": ("BOOLEAN", {"default": True}),  # 是否反转掩码
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")  # 返回原图像和掩码
    RETURN_NAMES = ("image", "mask")  # 返回值的名称
    FUNCTION = "remove_black_background"  # 指定执行的方法名称
    CATEGORY = "PDuse/Image"  # 定义节点的类别

    def remove_black_background(self, image, threshold=0.9, smooth_edges=True, invert_mask=True):
        """
        去除图像黑色背景，分别输出掩码和原图像
        
        参数：
            image (tensor): 输入图像张量 [B, H, W, C]
            threshold (float): 黑色检测阈值，0.0-1.0，低于此值的像素被认为是黑色
            smooth_edges (bool): 是否平滑边缘
            invert_mask (bool): 是否反转掩码，True时黑色区域变透明，False时黑色区域保留
            
        返回：
            image (tensor): 原始图像张量 [B, H, W, C]
            mask (tensor): 透明度掩码张量 [B, H, W]，根据invert_mask设置确定黑白含义
        """
        # 确保输入图像张量的格式正确 [B, H, W, C]
        if image.dim() != 4:
            raise ValueError("输入图像张量必须是 4 维的 [B, H, W, C]")
        
        batch_size, height, width, channels = image.shape
        
        # 处理每张图像生成掩码
        result_masks = []
        
        for i in range(batch_size):
            # 获取单张图像 [H, W, C]
            single_image = image[i]
            
            # 计算像素亮度（使用加权平均：R*0.299 + G*0.587 + B*0.114）
            rgb = single_image.cpu().numpy()
            brightness = np.dot(rgb, [0.299, 0.587, 0.114])
            
            # 调试信息：显示亮度统计
            if i == 0:  # 只为第一张图像打印调试信息
                min_brightness = brightness.min()
                max_brightness = brightness.max()
                mean_brightness = brightness.mean()
                print(f"🔍 图像亮度分析:")
                print(f"   最暗像素: {min_brightness:.3f}")
                print(f"   最亮像素: {max_brightness:.3f}") 
                print(f"   平均亮度: {mean_brightness:.3f}")
                print(f"   当前阈值: {threshold:.3f}")
                print(f"   反转掩码: {'开启' if invert_mask else '关闭'}")
                print(f"   保留区域: {'亮色区域' if invert_mask else '暗色区域'}")
            
            # 创建黑色像素掩码：亮度低于阈值的像素被认为是黑色背景
            black_mask = brightness < threshold
            
            # 调试信息：显示检测结果
            if i == 0:
                black_pixel_count = black_mask.sum()
                total_pixels = black_mask.size
                black_percentage = (black_pixel_count / total_pixels) * 100
                preserved_percentage = black_percentage if not invert_mask else (100 - black_percentage)
                print(f"   检测到暗色像素: {black_pixel_count}/{total_pixels} ({black_percentage:.1f}%)")
                print(f"   最终保留区域: {preserved_percentage:.1f}%")
            
            # 如果需要平滑边缘，对掩码进行轻微模糊处理
            if smooth_edges:
                try:
                    from scipy.ndimage import gaussian_filter
                    # 对掩码进行高斯模糊以平滑边缘
                    smoothed_mask = gaussian_filter(black_mask.astype(np.float32), sigma=1.0)
                    # 保留平滑过渡
                    black_mask = np.clip(smoothed_mask, 0, 1)
                except ImportError:
                    # 如果scipy不可用，则使用硬边模式
                    black_mask = black_mask.astype(np.float32)
            else:
                black_mask = black_mask.astype(np.float32)
            
            # 创建alpha掩码：1表示保留（不透明），0表示透明
            if invert_mask:
                # 反转掩码：保留非黑色区域（亮色区域）
                alpha_mask = 1.0 - black_mask
            else:
                # 直接使用掩码：保留黑色区域（暗色区域）
                alpha_mask = black_mask
            
            # 转换为张量格式 [H, W]
            mask_tensor = torch.from_numpy(alpha_mask).float()
            result_masks.append(mask_tensor)
        
        # 堆叠所有掩码 [B, H, W]
        final_masks = torch.stack(result_masks, dim=0)
        
        return (image, final_masks)

# 节点注册
NODE_CLASS_MAPPINGS = {
    "PD_RemoveBlackBackground": PD_RemoveBlackBackground
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_RemoveBlackBackground": "PD:remove_background"
}
