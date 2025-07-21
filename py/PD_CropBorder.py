import os
import cv2
import numpy as np
import torch
from PIL import Image, ImageOps
import glob

class PD_CropBorderBatch:
    """
    批量裁切图片边框节点
    读取指定路径下的所有图片，自动检测并去除与边缘连接的黑色或白色边框，然后保存
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_path": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "输入图片文件夹路径"
                }),
                "border_color": (["black", "white"], {
                    "default": "black",
                    "tooltip": "选择要删除的边框颜色"
                }),
                "threshold": ("INT", {
                    "default": 10,
                    "min": 0,
                    "max": 255,
                    "step": 1,
                    "tooltip": "颜色检测阈值，0-255，值越小检测越严格"
                }),
                "padding": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 100,
                    "step": 1,
                    "tooltip": "裁切后额外保留的边距像素"
                }),
            },
            "optional": {
                "output_path": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "输出路径（可选，不填则覆盖原图）"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("处理结果",)
    FUNCTION = "batch_crop_border"
    CATEGORY = "PDuse/图像处理"
    OUTPUT_NODE = True
    
    def detect_border(self, image_array, border_color="black", threshold=10):
        """
        检测图像边缘连接的边框区域 - 简化版本
        """
        # 转换为灰度图
        if len(image_array.shape) == 3:
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = image_array.copy()
        
        height, width = gray.shape
        
        # 根据边框颜色设置检测条件
        if border_color == "black":
            # 检测黑色：像素值小于等于阈值
            is_border = gray <= threshold
        else:  # white
            # 检测白色：像素值大于等于255-阈值
            is_border = gray >= (255 - threshold)
        
        # 从四个边缘向内扫描，找到第一个非边框像素
        # 上边缘
        top = 0
        for y in range(height):
            if not np.all(is_border[y, :]):
                top = y
                break
        else:
            # 整个图像都是边框
            return None
        
        # 下边缘
        bottom = height - 1
        for y in range(height - 1, -1, -1):
            if not np.all(is_border[y, :]):
                bottom = y + 1
                break
        
        # 左边缘
        left = 0
        for x in range(width):
            if not np.all(is_border[:, x]):
                left = x
                break
        
        # 右边缘
        right = width - 1
        for x in range(width - 1, -1, -1):
            if not np.all(is_border[:, x]):
                right = x + 1
                break
        
        # 验证边界框有效性
        if left >= right or top >= bottom:
            return None
        
        return (left, top, right, bottom)
    
    def crop_image_border(self, image_path, border_color="black", threshold=10, padding=0):
        """
        裁切单张图片的边框
        """
        try:
            # 读取图像
            image = Image.open(image_path)
            image_array = np.array(image)
            
            # 检测边框
            bbox = self.detect_border(image_array, border_color, threshold)
            
            if bbox is None:
                print(f"警告: {os.path.basename(image_path)} 整个图像都是边框，跳过处理")
                return False
            
            x_min, y_min, x_max, y_max = bbox
            
            # 添加padding
            height, width = image_array.shape[:2]
            x_min = max(0, x_min - padding)
            y_min = max(0, y_min - padding)
            x_max = min(width, x_max + padding)
            y_max = min(height, y_max + padding)
            
            # 裁切图像
            cropped_image = image.crop((x_min, y_min, x_max, y_max))
            
            return cropped_image
            
        except Exception as e:
            print(f"处理图片 {image_path} 时出错: {str(e)}")
            return False
    
    def get_image_files(self, path):
        """
        获取路径下的所有图片文件
        """
        supported_formats = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff', '*.tif', '*.webp']
        image_files = []
        
        for format in supported_formats:
            image_files.extend(glob.glob(os.path.join(path, format)))
            image_files.extend(glob.glob(os.path.join(path, format.upper())))
        
        return image_files
    
    def batch_crop_border(self, input_path, border_color="black", threshold=10, padding=0, output_path=""):
        """
        批量处理图片
        """
        # 验证输入路径
        if not input_path or not os.path.exists(input_path):
            return (f"错误: 输入路径不存在: {input_path}",)
        
        if not os.path.isdir(input_path):
            return (f"错误: 输入路径不是文件夹: {input_path}",)
        
        # 设置输出路径
        if output_path and output_path.strip():
            output_dir = output_path.strip()
            # 创建输出目录
            if not os.path.exists(output_dir):
                try:
                    os.makedirs(output_dir)
                except Exception as e:
                    return (f"错误: 无法创建输出目录 {output_dir}: {str(e)}",)
        else:
            # 覆盖原图
            output_dir = input_path
        
        # 获取所有图片文件
        image_files = self.get_image_files(input_path)
        
        if not image_files:
            return (f"警告: 在路径 {input_path} 中没有找到任何图片文件",)
        
        # 批量处理
        processed_count = 0
        failed_files = []
        
        color_name = "黑色" if border_color == "black" else "白色"
        print(f"开始批量处理{color_name}边框，共 {len(image_files)} 个文件...")
        
        for image_file in image_files:
            try:
                # 裁切图片
                cropped_image = self.crop_image_border(image_file, border_color, threshold, padding)
                
                if cropped_image:
                    # 确定输出文件路径
                    filename = os.path.basename(image_file)
                    output_file = os.path.join(output_dir, filename)
                    
                    # 保存裁切后的图片
                    cropped_image.save(output_file, quality=95)
                    processed_count += 1
                    print(f"成功处理: {filename}")
                else:
                    failed_files.append(os.path.basename(image_file))
                    
            except Exception as e:
                failed_files.append(f"{os.path.basename(image_file)} (错误: {str(e)})")
                print(f"处理 {image_file} 失败: {str(e)}")
        
        # 生成结果报告
        result_message = f"🎨 {color_name}边框批量裁切完成！\n\n"
        result_message += f"📊 处理统计:\n"
        result_message += f"• 总文件数: {len(image_files)}\n"
        result_message += f"• 成功处理: {processed_count}\n"
        result_message += f"• 处理失败: {len(failed_files)}\n\n"
        result_message += f"📁 路径信息:\n"
        result_message += f"• 输入路径: {input_path}\n"
        result_message += f"• 输出路径: {output_dir}\n\n"
        result_message += f"⚙️ 处理参数:\n"
        result_message += f"• 边框颜色: {color_name}\n"
        result_message += f"• 检测阈值: {threshold}\n"
        result_message += f"• 边距像素: {padding}\n"
        
        if failed_files:
            result_message += f"\n❌ 失败文件:\n"
            for failed_file in failed_files[:10]:  # 只显示前10个失败文件
                result_message += f"• {failed_file}\n"
            if len(failed_files) > 10:
                result_message += f"• ... 还有 {len(failed_files) - 10} 个文件失败\n"
        
        if processed_count > 0:
            result_message += f"\n✅ 批量处理任务完成！"
        else:
            result_message += f"\n⚠️ 没有文件被成功处理。"
        
        return (result_message,)


class PD_CropBorder:
    """
    单张图片裁切边框节点
    输入单张图片，自动检测并去除与边缘连接的黑色或白色边框，输出裁切后的图片
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "border_color": (["black", "white"], {
                    "default": "black",
                    "tooltip": "选择要删除的边框颜色"
                }),
                "threshold": ("INT", {
                    "default": 10,
                    "min": 0,
                    "max": 255,
                    "step": 1,
                    "tooltip": "颜色检测阈值，0-255，值越小检测越严格"
                }),
                "padding": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 100,
                    "step": 1,
                    "tooltip": "裁切后额外保留的边距像素"
                }),
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("crop image",)
    FUNCTION = "crop_border"
    CATEGORY = "PDuse/图像处理"
    
    def detect_border(self, image_array, border_color="black", threshold=10):
        """
        检测图像边缘连接的边框区域 - 简化版本
        """
        # 转换为灰度图
        if len(image_array.shape) == 3:
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = image_array.copy()
        
        height, width = gray.shape
        
        # 根据边框颜色设置检测条件
        if border_color == "black":
            # 检测黑色：像素值小于等于阈值
            is_border = gray <= threshold
        else:  # white
            # 检测白色：像素值大于等于255-阈值
            is_border = gray >= (255 - threshold)
        
        # 从四个边缘向内扫描，找到第一个非边框像素
        # 上边缘
        top = 0
        for y in range(height):
            if not np.all(is_border[y, :]):
                top = y
                break
        else:
            # 整个图像都是边框
            return None
        
        # 下边缘
        bottom = height - 1
        for y in range(height - 1, -1, -1):
            if not np.all(is_border[y, :]):
                bottom = y + 1
                break
        
        # 左边缘
        left = 0
        for x in range(width):
            if not np.all(is_border[:, x]):
                left = x
                break
        
        # 右边缘
        right = width - 1
        for x in range(width - 1, -1, -1):
            if not np.all(is_border[:, x]):
                right = x + 1
                break
        
        # 验证边界框有效性
        if left >= right or top >= bottom:
            return None
        
        return (left, top, right, bottom)
    
    def crop_border(self, image, border_color="black", threshold=10, padding=0):
        """
        裁切单张图片的边框
        """
        # 确保输入张量格式为 (B, H, W, C)
        if len(image.shape) != 4:
            raise ValueError(f"输入图像张量格式错误，期望 (B, H, W, C)，实际 {image.shape}")
        
        batch_size = image.shape[0]
        cropped_images = []
        
        for i in range(batch_size):
            # 获取单张图片 (H, W, C)
            single_image = image[i]
            
            # 转换为numpy数组 (0-255)
            if single_image.dtype == torch.float32:
                # 假设输入是0-1范围的float32
                image_array = (single_image.cpu().numpy() * 255).astype(np.uint8)
            else:
                image_array = single_image.cpu().numpy()
            
            # 检测边框
            bbox = self.detect_border(image_array, border_color, threshold)
            
            if bbox is None:
                print(f"警告: 第{i+1}张图片整个都是边框，返回原图")
                cropped_images.append(single_image)
                continue
            
            left, top, right, bottom = bbox
            
            # 添加padding
            height, width = image_array.shape[:2]
            left = max(0, left - padding)
            top = max(0, top - padding)
            right = min(width, right + padding)
            bottom = min(height, bottom + padding)
            
            # 裁切图像
            cropped_array = image_array[top:bottom, left:right, :]
            
            # 转换回张量格式
            if single_image.dtype == torch.float32:
                # 转换回0-1范围
                cropped_tensor = torch.from_numpy(cropped_array.astype(np.float32) / 255.0)
            else:
                cropped_tensor = torch.from_numpy(cropped_array)
            
            cropped_images.append(cropped_tensor)
            
            color_name = "黑色" if border_color == "black" else "白色"
            print(f"成功裁切第{i+1}张图片的{color_name}边框: {left},{top},{right},{bottom}")
        
        # 将所有裁切后的图片组合成批次
        # 由于裁切后尺寸可能不同，需要找到最大尺寸并padding
        if len(cropped_images) == 1:
            result = cropped_images[0].unsqueeze(0)
        else:
            # 多图情况下，需要统一尺寸
            max_h = max(img.shape[0] for img in cropped_images)
            max_w = max(img.shape[1] for img in cropped_images)
            
            padded_images = []
            for img in cropped_images:
                h, w, c = img.shape
                if h < max_h or w < max_w:
                    # 创建空白图像并复制
                    padded = torch.zeros(max_h, max_w, c, dtype=img.dtype)
                    padded[:h, :w, :] = img
                    padded_images.append(padded)
                else:
                    padded_images.append(img)
            
            result = torch.stack(padded_images)
        
        return (result,)


NODE_CLASS_MAPPINGS = {
    "PD_BatchCropBlackBorder": PD_CropBorderBatch,
    "PD_CropBorder": PD_CropBorder,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_BatchCropBlackBorder": "PD_BatchCropBlackBorder",
    "PD_CropBorder": "PD_CropBorder",
} 