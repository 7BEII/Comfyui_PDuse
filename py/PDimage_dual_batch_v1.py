import os
import torch
import numpy as np
from PIL import Image
import random

class PDimage_dual_batch_v1:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image1_path": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "输入第一个图片文件夹路径"
                }),
                "image2_path": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "输入第二个图片文件夹路径"
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 4294967295,  # 2**32 - 1
                    "step": 1
                })
            }
        }
    
    RETURN_TYPES = ("IMAGE", "IMAGE", "STRING")
    RETURN_NAMES = ("image1_batch", "image2_batch", "info")
    FUNCTION = "load_matched_images"
    CATEGORY = "PD_Tools/image_processing"
    OUTPUT_IS_LIST = (True, True, False)  # 关键：指定前两个输出是List
    
    def get_image_files(self, folder_path):
        """获取文件夹中所有图片文件"""
        if not os.path.exists(folder_path):
            return {}
        
        supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'}
        image_dict = {}
        
        for file in os.listdir(folder_path):
            if os.path.isfile(os.path.join(folder_path, file)):
                name, ext = os.path.splitext(file)
                if ext.lower() in supported_formats:
                    image_dict[name] = file
        
        return image_dict
    
    def find_matching_pairs(self, folder1_dict, folder2_dict):
        """基于文件名进行精确匹配"""
        matches = []
        for name in folder1_dict:
            if name in folder2_dict:
                matches.append((folder1_dict[name], folder2_dict[name], name))
        
        matches.sort(key=lambda x: x[2])
        return matches
    
    def pil_to_tensor(self, image):
        """PIL图片转张量 - 确保正确的格式和数据类型"""
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # 转换为numpy数组，确保数据类型
        np_image = np.array(image, dtype=np.float32) / 255.0
        
        # 转换为PyTorch张量，确保float32类型
        tensor = torch.from_numpy(np_image).float()
        
        # 确保张量形状为 (H, W, C)
        if len(tensor.shape) == 2:  # 灰度图
            tensor = tensor.unsqueeze(-1).repeat(1, 1, 3)
        elif tensor.shape[-1] == 4:  # RGBA
            tensor = tensor[:, :, :3]
        
        return tensor

    def load_matched_images(self, image1_path, image2_path, seed):
        """主处理函数 - 真正的List输出模式，保留所有匹配图片"""
        try:
            # 确保种子在有效范围内
            seed = int(seed) % (2**32)  # 限制在32位范围内
            
            # 使用种子（可以用于随机排序或其他随机操作）
            random.seed(seed)
            np.random.seed(seed)
            torch.manual_seed(seed)
            
            # 验证路径
            if not image1_path.strip() or not image2_path.strip():
                raise ValueError("请输入有效的文件夹路径")
                
            if not os.path.exists(image1_path):
                raise ValueError(f"文件夹1不存在: {image1_path}")
            if not os.path.exists(image2_path):
                raise ValueError(f"文件夹2不存在: {image2_path}")
            
            # 获取图片文件并匹配
            folder1_dict = self.get_image_files(image1_path)
            folder2_dict = self.get_image_files(image2_path)
            
            if not folder1_dict or not folder2_dict:
                raise ValueError("文件夹中没有找到图片文件")
            
            matches = self.find_matching_pairs(folder1_dict, folder2_dict)
            
            if not matches:
                raise ValueError("没有找到匹配的图片对")
            
            # 可选：根据种子随机打乱配对顺序
            # random.shuffle(matches)
            
            # 加载所有匹配的图片对
            batch1_list = []
            batch2_list = []
            match_info = []
            size_info = {}
            
            for file1, file2, base_name in matches:
                try:
                    img1_path = os.path.join(image1_path, file1)
                    img2_path = os.path.join(image2_path, file2)
                    
                    img1 = Image.open(img1_path)
                    img2 = Image.open(img2_path)
                    
                    # 确保正确转换为张量
                    tensor1 = self.pil_to_tensor(img1)
                    tensor2 = self.pil_to_tensor(img2)
                    
                    # 添加batch维度 (H, W, C) -> (1, H, W, C)
                    tensor1_batch = tensor1.unsqueeze(0)
                    tensor2_batch = tensor2.unsqueeze(0)
                    
                    # 验证张量格式
                    print(f"种子{seed} - 加载 {base_name}: tensor1_batch.shape={tensor1_batch.shape}, dtype={tensor1_batch.dtype}")
                    
                    # 添加到列表中
                    batch1_list.append(tensor1_batch)
                    batch2_list.append(tensor2_batch)
                    
                    # 记录尺寸信息
                    size_key = f"{tensor1.shape[1]}×{tensor1.shape[0]}"  # W×H
                    size_info[size_key] = size_info.get(size_key, 0) + 1
                    
                    match_info.append(f"{base_name}: {tensor1_batch.shape} + {tensor2_batch.shape}")
                    
                except Exception as e:
                    print(f"加载图片 {base_name} 失败: {str(e)}")
                    continue
            
            if not batch1_list:
                raise ValueError("没有成功加载任何图片对")
            
            # 验证最终输出
            print(f"种子{seed} - 最终输出: 列表长度 = {len(batch1_list)}")
            for i, (t1, t2) in enumerate(zip(batch1_list, batch2_list)):
                print(f"第{i+1}对: {t1.shape} + {t2.shape}")
            
            # 分析尺寸分布
            size_summary = []
            for size, count in size_info.items():
                size_summary.append(f"{size}: {count}张")
            
            # 生成详细信息
            info_text = f"种子: {seed} (已规范化)\n"
            info_text += f"List模式输出: {len(batch1_list)} 对图片\n"
            info_text += f"尺寸分布: {', '.join(size_summary)}\n"
            info_text += f"输出格式: List[Tensor(1,H,W,C)] - 包含所有尺寸\n"
            info_text += f"图片1列表长度: {len(batch1_list)}\n"
            info_text += f"图片2列表长度: {len(batch2_list)}\n"
            info_text += f"路径1: {image1_path}\n"
            info_text += f"路径2: {image2_path}\n"
            info_text += "\n匹配详情:\n" + "\n".join(match_info)
            
            # 返回List格式 - ComfyUI会识别OUTPUT_IS_LIST标志
            return (batch1_list, batch2_list, info_text)
            
        except Exception as e:
            print(f"种子{seed} - 错误详情: {str(e)}")
            # 创建错误图片
            error_img = Image.new('RGB', (512, 512), (128, 128, 128))
            error_tensor = self.pil_to_tensor(error_img).unsqueeze(0)
            error_info = f"种子: {seed}\n错误: {str(e)}"
            
            return ([error_tensor], [error_tensor], error_info)

NODE_CLASS_MAPPINGS = {
    "PDimage_dual_batch_v1": PDimage_dual_batch_v1
}

# 节点显示名称映射
NODE_DISPLAY_NAME_MAPPINGS = {
    "PDimage_dual_batch_v1": "PDimage_dual_batch_v1"
}

# 导出节点信息供ComfyUI使用
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
