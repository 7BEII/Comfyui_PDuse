import torch
import numpy as np
from PIL import Image, ImageOps
import os
from typing import List, Tuple

class PD_image_ratio_size:
    """
    ComfyUI节点：图像缩放和裁剪处理
    功能：将图像缩放到指定的最大尺寸，然后裁剪到指定的宽高比
    """
    
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),  # 输入图像张量
                "max_size": ("INT", {
                    "default": 1024,
                    "min": 64,
                    "max": 4096,
                    "step": 1,
                    "display": "number"
                }),
                "aspect_width": ("INT", {
                    "default": 3,
                    "min": 1,
                    "max": 16,
                    "step": 1,
                    "display": "number"
                }),
                "aspect_height": ("INT", {
                    "default": 4,
                    "min": 1,
                    "max": 16,
                    "step": 1,
                    "display": "number"
                }),
                "resampling_method": (["LANCZOS", "BICUBIC", "BILINEAR", "NEAREST"], {
                    "default": "LANCZOS"
                })
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("processed_images", "info")
    FUNCTION = "process_images"
    CATEGORY = "PD_Image/Processing"
    OUTPUT_IS_LIST = (False, False)

    def pil_to_tensor(self, image: Image.Image) -> torch.Tensor:
        """将PIL图像转换为ComfyUI张量格式 (H, W, C)"""
        # 确保图像是RGB模式
        if image.mode == 'RGBA':
            # 创建白色背景
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # 转换为numpy数组并归一化到[0,1]
        np_image = np.array(image).astype(np.float32) / 255.0
        
        # 转换为PyTorch张量，形状为 (H, W, C)
        tensor = torch.from_numpy(np_image)
        
        return tensor

    def tensor_to_pil(self, tensor: torch.Tensor) -> Image.Image:
        """将ComfyUI张量格式转换为PIL图像"""
        # 确保张量在CPU上
        if tensor.is_cuda:
            tensor = tensor.cpu()
        
        # 移除batch维度（如果存在）
        if len(tensor.shape) == 4:
            tensor = tensor.squeeze(0)
        
        # 将[0,1]范围转换为[0,255]并转换为uint8
        np_image = (tensor.numpy() * 255).astype(np.uint8)
        
        # 创建PIL图像
        return Image.fromarray(np_image)

    def get_resampling_filter(self, method: str):
        """获取PIL重采样滤镜"""
        method_map = {
            "LANCZOS": Image.Resampling.LANCZOS,
            "BICUBIC": Image.Resampling.BICUBIC,
            "BILINEAR": Image.Resampling.BILINEAR,
            "NEAREST": Image.Resampling.NEAREST
        }
        return method_map.get(method, Image.Resampling.LANCZOS)

    def process_single_image(self, image_tensor: torch.Tensor, max_size: int, 
                           aspect_ratio: Tuple[int, int], resampling_method: str) -> Tuple[torch.Tensor, str]:
        """
        处理单张图像：缩放最长边到指定尺寸，然后裁剪到指定比例
        
        Args:
            image_tensor: 输入图像张量 (H, W, C)
            max_size: 最长边的目标尺寸
            aspect_ratio: (宽, 高) 的比例元组
            resampling_method: 重采样方法
        
        Returns:
            processed_tensor: 处理后的图像张量 (H, W, C)
            info: 处理信息
        """
        try:
            # 转换为PIL图像
            pil_image = self.tensor_to_pil(image_tensor)
            original_size = pil_image.size
            
            # 获取重采样滤镜
            resampling_filter = self.get_resampling_filter(resampling_method)
            
            # 步骤1：缩放最长边到max_size
            width, height = pil_image.size
            max_dimension = max(width, height)
            
            if max_dimension > max_size:
                scale = max_size / max_dimension
                new_width = int(width * scale)
                new_height = int(height * scale)
                pil_image = pil_image.resize((new_width, new_height), resampling_filter)
            
            # 步骤2：裁剪到指定比例
            current_width, current_height = pil_image.size
            target_ratio = aspect_ratio[0] / aspect_ratio[1]
            current_ratio = current_width / current_height
            
            crop_info = ""
            if abs(current_ratio - target_ratio) > 0.01:  # 如果比例不同才裁剪
                if current_ratio > target_ratio:
                    # 当前图片太宽，需要裁剪宽度
                    new_width = int(current_height * target_ratio)
                    new_height = current_height
                    left = (current_width - new_width) // 2
                    top = 0
                    right = left + new_width
                    bottom = current_height
                    crop_info = f"裁剪宽度: {current_width}→{new_width}"
                else:
                    # 当前图片太高，需要裁剪高度
                    new_width = current_width
                    new_height = int(current_width / target_ratio)
                    left = 0
                    top = (current_height - new_height) // 2
                    right = current_width
                    bottom = top + new_height
                    crop_info = f"裁剪高度: {current_height}→{new_height}"
                
                pil_image = pil_image.crop((left, top, right, bottom))
            
            # 转换回张量
            processed_tensor = self.pil_to_tensor(pil_image)
            final_size = pil_image.size
            
            # 生成处理信息
            info = f"原始尺寸: {original_size} → 最终尺寸: {final_size}"
            if crop_info:
                info += f" ({crop_info})"
            
            return processed_tensor, info
            
        except Exception as e:
            # 如果处理失败，返回原始图像和错误信息
            error_info = f"处理失败: {str(e)}"
            return image_tensor, error_info

    def process_images(self, images: torch.Tensor, max_size: int, aspect_width: int, 
                      aspect_height: int, resampling_method: str):
        """
        主处理函数：批量处理图像
        
        Args:
            images: 输入图像张量，形状为 (B, H, W, C)
            max_size: 最长边的目标尺寸
            aspect_width: 目标宽高比的宽度
            aspect_height: 目标宽高比的高度
            resampling_method: 重采样方法
        """
        try:
            # 验证输入参数
            if max_size <= 0:
                raise ValueError("最大尺寸必须大于0")
            if aspect_width <= 0 or aspect_height <= 0:
                raise ValueError("宽高比参数必须大于0")
            
            aspect_ratio = (aspect_width, aspect_height)
            
            # 处理输入张量
            if len(images.shape) == 3:
                # 单张图像，添加batch维度
                images = images.unsqueeze(0)
            
            batch_size = images.shape[0]
            processed_images = []
            processing_info = []
            
            print(f"开始处理 {batch_size} 张图像")
            print(f"目标配置: 最大尺寸={max_size}px, 宽高比={aspect_width}:{aspect_height}")
            print(f"重采样方法: {resampling_method}")
            
            # 逐张处理图像
            for i in range(batch_size):
                image_tensor = images[i]  # 形状: (H, W, C)
                
                processed_tensor, info = self.process_single_image(
                    image_tensor, max_size, aspect_ratio, resampling_method
                )
                
                processed_images.append(processed_tensor)
                processing_info.append(f"图像 {i+1}: {info}")
                
                print(f"处理完成 {i+1}/{batch_size}: {info}")
            
            # 将处理后的图像重新组合成批次张量
            processed_batch = torch.stack(processed_images, dim=0)  # 形状: (B, H, W, C)
            
            # 生成汇总信息
            final_shape = processed_batch.shape
            summary_info = f"批量处理完成:\n"
            summary_info += f"输入图像数量: {batch_size}\n"
            summary_info += f"输出张量形状: {final_shape}\n"
            summary_info += f"目标配置: 最大尺寸={max_size}px, 宽高比={aspect_width}:{aspect_height}\n"
            summary_info += f"重采样方法: {resampling_method}\n\n"
            summary_info += "详细处理信息:\n" + "\n".join(processing_info)
            
            print(f"批量处理完成！输出张量形状: {final_shape}")
            
            return (processed_batch, summary_info)
            
        except Exception as e:
            error_msg = f"处理错误: {str(e)}"
            print(error_msg)
            
            # 返回原始图像和错误信息
            return (images, error_msg)


# 节点映射配置
NODE_CLASS_MAPPINGS = {
    "PD_image_ratio_size": PD_image_ratio_size
}

# 设置节点在UI中显示的名称
NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_image_ratio_size": "PD_image ratio size"
}

