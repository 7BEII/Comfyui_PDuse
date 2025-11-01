import torch
import numpy as np
from PIL import Image
import io

class PD_image_composize_v1:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "target_mb": ("FLOAT", {
                    "default": 3.0,
                    "min": 1.0,
                    "max": 100.0,
                    "step": 0.01,
                    "display": "number"
                }),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("compressed_image", "compression_info")
    FUNCTION = "compress_image"
    CATEGORY = "PD_Tools/Image"
    
    def detect_image_format(self, image_tensor):
        """检测图像格式和通道信息"""
        if len(image_tensor.shape) == 4:  # [batch, height, width, channels]
            channels = image_tensor.shape[3]
        elif len(image_tensor.shape) == 3:  # [height, width, channels]
            channels = image_tensor.shape[2]
        else:
            channels = 3  # 默认RGB
        
        # 根据通道数判断格式
        if channels == 4:
            return "PNG", "RGBA"
        elif channels == 1:
            return "PNG", "L"
        else:
            return "JPEG", "RGB"
    
    def compress_image(self, image, target_mb):
        # 检测图像格式和模式
        detected_format, detected_mode = self.detect_image_format(image)
        
        # 将tensor转换为PIL图像
        i = 255. * image[0].cpu().numpy()
        
        # 根据检测到的模式处理图像
        if detected_mode == "RGBA":
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8), mode='RGBA')
        elif detected_mode == "L":
            if len(i.shape) == 3 and i.shape[2] == 1:
                i = i[:, :, 0]
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8), mode='L')
        else:
            if len(i.shape) == 3 and i.shape[2] >= 3:
                i = i[:, :, :3]
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8), mode='RGB')
        
        # 获取原始图像文件大小
        original_buffer = io.BytesIO()
        img.save(original_buffer, format=detected_format, optimize=True)
        original_size = original_buffer.tell()
        original_size_mb = original_size / (1024 * 1024)
        
        # 目标文件大小（字节）
        target_size_bytes = target_mb * 1024 * 1024
        
        # 精确检查：只有严格小于目标大小才跳过压缩
        if original_size < target_size_bytes:
            info = f"Format: {detected_format} ({detected_mode})\n"
            info += f"Original size: {original_size_mb:.3f}MB\n"
            info += f"Target: {target_mb:.3f}MB\n"
            info += "✓ Already smaller than target - No compression needed"
            return (image, info)
        
        # 执行压缩
        print(f"[DEBUG] Starting compression: {original_size_mb:.3f}MB -> {target_mb:.3f}MB")
        
        compressed_img = None
        final_size = 0
        quality_used = 95
        
        if detected_format == "PNG":
            # PNG压缩策略
            buffer = io.BytesIO()
            img.save(buffer, format='PNG', optimize=True)
            final_size = buffer.tell()
            
            if final_size > target_size_bytes:
                # 需要缩放尺寸
                scale_factor = (target_size_bytes / final_size) ** 0.5
                scale_factor = min(scale_factor, 0.95)  # 确保有压缩效果
                new_width = max(1, int(img.width * scale_factor))
                new_height = max(1, int(img.height * scale_factor))
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                buffer = io.BytesIO()
                img.save(buffer, format='PNG', optimize=True)
                final_size = buffer.tell()
                quality_used = f"Resized to {new_width}x{new_height} (Scale: {scale_factor:.3f})"
            else:
                quality_used = "PNG Optimize"
            
            buffer.seek(0)
            compressed_img = Image.open(buffer).copy()
            buffer.close()
            
        else:
            # JPEG压缩策略
            best_quality = 95
            best_size = original_size
            
            # 二分搜索最佳质量
            for quality in range(95, 0, -5):
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=quality, optimize=True)
                current_size = buffer.tell()
                buffer.close()
                
                if current_size <= target_size_bytes:
                    best_quality = quality
                    best_size = current_size
                    break
                else:
                    best_quality = quality
                    best_size = current_size
            
            # 如果还是太大，尝试缩放
            if best_size > target_size_bytes:
                scale_factor = (target_size_bytes / best_size) ** 0.5
                scale_factor = min(scale_factor, 0.95)
                new_width = max(1, int(img.width * scale_factor))
                new_height = max(1, int(img.height * scale_factor))
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                quality_used = f"Quality {best_quality} + Resized to {new_width}x{new_height}"
            else:
                quality_used = f"Quality {best_quality}"
            
            # 最终压缩
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=best_quality, optimize=True)
            final_size = buffer.tell()
            buffer.seek(0)
            compressed_img = Image.open(buffer).copy()
            buffer.close()
        
        print(f"[DEBUG] Compression complete: {final_size / (1024 * 1024):.3f}MB")
        
        # 转换回tensor格式
        if detected_mode == "RGBA":
            if compressed_img.mode != 'RGBA':
                compressed_img = compressed_img.convert('RGBA')
            compressed_array = np.array(compressed_img).astype(np.float32) / 255.0
            if compressed_array.shape[2] == 3:
                alpha_channel = np.ones((compressed_array.shape[0], compressed_array.shape[1], 1))
                compressed_array = np.concatenate([compressed_array, alpha_channel], axis=2)
        elif detected_mode == "L":
            if compressed_img.mode != 'L':
                compressed_img = compressed_img.convert('L')
            compressed_array = np.array(compressed_img).astype(np.float32) / 255.0
            if len(compressed_array.shape) == 2:
                compressed_array = np.stack([compressed_array] * 3, axis=2)
        else:
            if compressed_img.mode != 'RGB':
                compressed_img = compressed_img.convert('RGB')
            compressed_array = np.array(compressed_img).astype(np.float32) / 255.0
        
        compressed_tensor = torch.from_numpy(compressed_array)[None,]
        
        # 生成压缩信息
        final_size_mb = final_size / (1024 * 1024)
        compression_ratio = (1 - final_size_mb / original_size_mb) * 100 if original_size_mb > 0 else 0
        
        info = f"Format: {detected_format} ({detected_mode})\n"
        info += f"Original: {original_size_mb:.3f}MB → Compressed: {final_size_mb:.3f}MB\n"
        info += f"Compression: {compression_ratio:.1f}% | {quality_used}"
        
        return (compressed_tensor, info)

# 节点映射
NODE_CLASS_MAPPINGS = {
    "PD_image_composize_v1": PD_image_composize_v1
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_image_composize_v1": "PD Image Compress v1"
}
