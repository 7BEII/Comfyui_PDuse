import os
import cv2
import numpy as np
import torch
from PIL import Image


class PD_RemoveWhiteBorder:
    """
    自动识别图像中所有白色区域的节点
    输入单张图片，检测所有白色区域（包括内部白色），输出原始图像和白色区域遮罩（内部反转）
    """
  
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "threshold": ("INT", {
                    "default": 70,
                    "min": 0,
                    "max": 100,
                    "step": 1,
                    "tooltip": "白色区域检测灵敏度，0-100，值越大检测越严格"
                }),
            }
        }
  
    RETURN_TYPES = ("IMAGE", "MASK",)
    RETURN_NAMES = ("image", "mask",)
    FUNCTION = "extract_white_areas"
    CATEGORY = "PDuse/图像处理"
  
    def create_white_areas_mask(self, image_array, threshold=70):
        """
        从图像中识别所有白色区域的mask（包括内部白色区域）
        """
        # 阈值转换为0-255范围
        threshold_255 = int(threshold * 2.55)
      
        # 转换为灰度图
        if len(image_array.shape) == 3:
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = image_array.copy()
      
        # 检测所有白色区域：像素值大于等于阈值的都视为白色
        # 这里直接基于阈值创建mask，不区分边界还是内部
        mask = (gray >= threshold_255).astype(np.uint8) * 255
      
        # 动态计算去噪强度：基于图像尺寸和阈值
        h, w = gray.shape
        image_size = h * w
        
        # 根据图像大小和阈值动态调整去噪强度
        if image_size > 1000000:  # 大图像 (>1000x1000)
            denoise_strength = 5
        elif image_size > 250000:  # 中等图像 (>500x500)
            denoise_strength = 4
        else:  # 小图像
            denoise_strength = 3
            
        # 根据阈值微调去噪强度
        if threshold > 80:
            denoise_strength = max(1, denoise_strength - 1)  # 高阈值时减少去噪
        elif threshold < 50:
            denoise_strength = min(7, denoise_strength + 1)  # 低阈值时增加去噪
      
        # 应用去噪和平滑处理
        if denoise_strength > 0:
            # 应用中值滤波去噪，强度可调
            kernel_size = min(2 * denoise_strength + 1, 15)  # 限制最大核大小
            mask = cv2.medianBlur(mask, kernel_size)
          
            # 应用形态学操作来平滑边缘和连接近邻白色区域
            morph_kernel = np.ones((denoise_strength, denoise_strength), np.uint8)
            # 开运算：先腐蚀后膨胀，去除小噪点
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, morph_kernel)
            # 闭运算：先膨胀后腐蚀，连接断开的区域
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, morph_kernel)
      
        # 内部反转：将白色区域变为黑色，其他区域变为白色
        mask_inverted = 255 - mask
      
        # 将mask转换为float32格式，范围0-1
        mask_result = mask_inverted.astype(np.float32) / 255.0
      
        return mask_result
  
    def extract_white_areas(self, image, threshold=70):
        """
        识别所有白色区域，返回原始图像和反转的白色区域mask
        """
        # 确保输入张量格式为 (B, H, W, C)
        if len(image.shape) != 4:
            raise ValueError(f"输入图像张量格式错误，期望 (B, H, W, C)，实际 {image.shape}")
      
        batch_size = image.shape[0]
        result_images = []
        masks = []
      
        for i in range(batch_size):
            # 获取单张图片 (H, W, C)
            single_image = image[i]
          
            # 转换为numpy数组 (0-255)
            if single_image.dtype == torch.float32:
                # 假设输入是0-1范围的float32
                image_array = (single_image.cpu().numpy() * 255).astype(np.uint8)
            else:
                image_array = single_image.cpu().numpy()
          
            # 创建所有白色区域的反转mask
            mask_array = self.create_white_areas_mask(image_array, threshold)
          
            # 将mask转换为PyTorch张量，确保格式为(H, W)
            mask_tensor = torch.from_numpy(mask_array)
            masks.append(mask_tensor)
          
            # 保持原图不变
            result_tensor = single_image.clone()
            result_images.append(result_tensor)
      
        # 批次处理
        if len(result_images) == 1:
            result = result_images[0].unsqueeze(0)  # (1, H, W, C)
            mask_result = masks[0].unsqueeze(0)     # (1, H, W)
        else:
            result = torch.stack(result_images)     # (B, H, W, C)
            mask_result = torch.stack(masks)        # (B, H, W)
      
        return (result, mask_result,)


# 注册节点
NODE_CLASS_MAPPINGS = {
    "PD_RemoveWhiteBorder": PD_RemoveWhiteBorder,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_RemoveWhiteBorder": "PD_RemoveWhiteBorder",
} 