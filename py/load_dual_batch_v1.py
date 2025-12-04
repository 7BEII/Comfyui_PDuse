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
                "name1_suffix": ("STRING", {
                    "default": "R",
                    "multiline": False,
                    "placeholder": "图片1的命名后缀，如 _T"
                }),
                "image2_path": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "输入第二个图片文件夹路径"
                }),
                "name2_suffix": ("STRING", {
                    "default": "T",
                    "multiline": False,
                    "placeholder": "图片2的命名后缀，如 _R"
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,  # 最大值
                    "step": 1,
                    "control_after_generate": True  # 显示刷新按钮
                }),
                "only_first": ("BOOLEAN", {
                    "default": False,
                    "label_on": "仅第一张",
                    "label_off": "全部"
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
    
    def find_matching_pairs(self, folder1_dict, folder2_dict, name1_suffix="", name2_suffix=""):
        """基于文件名进行匹配（智能匹配：同时支持前缀、后缀和中间位置匹配）
        
        Args:
            folder1_dict: 文件夹1的文件字典 {文件名(无扩展名): 完整文件名}
            folder2_dict: 文件夹2的文件字典 {文件名(无扩展名): 完整文件名}
            name1_suffix: 文件夹1的标识符，如 "T" （可以是前缀、后缀或中间部分）
            name2_suffix: 文件夹2的标识符，如 "R" （可以是前缀、后缀或中间部分）
        
        Returns:
            匹配的文件对列表 [(文件1, 文件2, 基础名称, 匹配类型), ...]
        
        匹配示例：
            - 后缀匹配：65_T 对应 65_R
            - 前缀匹配：T1_00001 对应 R1_00001
            - 中间匹配：65_T_00001 对应 65_R_00001
        """
        matches = []
        matched_folder2 = set()  # 记录folder2中已匹配的文件，避免重复匹配
        
        # 如果两个标识符都为空，使用完全匹配模式
        if not name1_suffix and not name2_suffix:
            for name in folder1_dict:
                if name in folder2_dict:
                    matches.append((folder1_dict[name], folder2_dict[name], name, "完全匹配"))
            matches.sort(key=lambda x: x[2])
            return matches
        
        # 智能匹配模式：同时尝试多种匹配方式
        for name1, full_name1 in folder1_dict.items():
            found_match = False
            
            # 策略1：后缀匹配（最常见）- 例如：65_T 对应 65_R
            if not found_match and name1_suffix:
                # 尝试 _T 格式
                if name1.endswith(f"_{name1_suffix}"):
                    base_name = name1[:-len(f"_{name1_suffix}")]
                    target_name = f"{base_name}_{name2_suffix}"
                    if target_name in folder2_dict and target_name not in matched_folder2:
                        matches.append((full_name1, folder2_dict[target_name], base_name, "后缀匹配(_)"))
                        matched_folder2.add(target_name)
                        found_match = True
                
                # 尝试不带下划线的后缀格式：例如 65T 对应 65R
                if not found_match and name1.endswith(name1_suffix):
                    base_name = name1[:-len(name1_suffix)]
                    target_name = f"{base_name}{name2_suffix}"
                    if target_name in folder2_dict and target_name not in matched_folder2:
                        matches.append((full_name1, folder2_dict[target_name], base_name, "后缀匹配"))
                        matched_folder2.add(target_name)
                        found_match = True
            
            # 策略2：前缀匹配 - 例如：T1_00001 对应 R1_00001
            if not found_match and name1_suffix:
                # 尝试 T_ 格式
                if name1.startswith(f"{name1_suffix}_"):
                    base_name = name1[len(f"{name1_suffix}_"):]
                    target_name = f"{name2_suffix}_{base_name}"
                    if target_name in folder2_dict and target_name not in matched_folder2:
                        matches.append((full_name1, folder2_dict[target_name], base_name, "前缀匹配(_)"))
                        matched_folder2.add(target_name)
                        found_match = True
                
                # 尝试不带下划线的前缀格式：例如 T1_00001 对应 R1_00001
                if not found_match and name1.startswith(name1_suffix):
                    base_name = name1[len(name1_suffix):]
                    target_name = f"{name2_suffix}{base_name}"
                    if target_name in folder2_dict and target_name not in matched_folder2:
                        matches.append((full_name1, folder2_dict[target_name], base_name, "前缀匹配"))
                        matched_folder2.add(target_name)
                        found_match = True
            
            # 策略3：中间位置匹配 - 例如：65_T_00001 对应 65_R_00001
            if not found_match and name1_suffix and name2_suffix:
                # 尝试替换所有出现的标识符
                if f"_{name1_suffix}_" in name1:
                    target_name = name1.replace(f"_{name1_suffix}_", f"_{name2_suffix}_")
                    if target_name in folder2_dict and target_name not in matched_folder2:
                        base_name = name1.replace(f"_{name1_suffix}_", "_")
                        matches.append((full_name1, folder2_dict[target_name], base_name, "中间匹配"))
                        matched_folder2.add(target_name)
                        found_match = True
        
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

    def load_matched_images(self, image1_path, image2_path, name1_suffix, name2_suffix, seed, only_first):
        """主处理函数 - 真正的List输出模式，保留所有匹配图片
        
        Args:
            only_first: 是否只读取第一张匹配的图片对（用于测试）
        """
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
            
            matches = self.find_matching_pairs(folder1_dict, folder2_dict, name1_suffix, name2_suffix)
            
            if not matches:
                raise ValueError("没有找到匹配的图片对")
            
            # 可选：根据种子随机打乱配对顺序
            # random.shuffle(matches)
            
            # 如果只读取第一张，则只处理第一对
            if only_first:
                matches = matches[:1]
            
            # 加载所有匹配的图片对
            batch1_list = []
            batch2_list = []
            match_info = []
            size_info = {}
            match_type_info = {}
            
            for file1, file2, base_name, match_type in matches:
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
                    
                    # 记录匹配类型统计
                    match_type_info[match_type] = match_type_info.get(match_type, 0) + 1
                    
                    match_info.append(f"{base_name} [{match_type}]: {tensor1_batch.shape} + {tensor2_batch.shape}")
                    
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
            
            # 分析匹配类型分布
            match_type_summary = []
            for match_type, count in match_type_info.items():
                match_type_summary.append(f"{match_type}: {count}对")
            
            # 生成详细信息
            match_mode = "完全匹配模式" if (not name1_suffix and not name2_suffix) else "智能匹配模式（前缀+后缀+中间）"
            info_text = f"种子: {seed} (已规范化)\n"
            info_text += f"测试模式: {'仅第一张 ✓' if only_first else '读取全部'}\n"
            info_text += f"匹配模式: {match_mode}\n"
            if name1_suffix or name2_suffix:
                info_text += f"  - 图片1标识符: '{name1_suffix}'\n"
                info_text += f"  - 图片2标识符: '{name2_suffix}'\n"
            info_text += f"匹配类型分布: {', '.join(match_type_summary)}\n"
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
