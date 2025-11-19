import torch
import numpy as np
import random

class PDimage_dual_batch_by_list:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image1_list": ("IMAGE",),
                "image2_list": ("IMAGE",),
                "name1_list": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "输入图片1的名称列表，每行一个名称"
                }),
                "name2_list": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "输入图片2的名称列表，每行一个名称"
                }),
                "name1_suffix": ("STRING", {
                    "default": "R",
                    "multiline": False,
                    "placeholder": "图片1的命名后缀，如 _T"
                }),
                "name2_suffix": ("STRING", {
                    "default": "T",
                    "multiline": False,
                    "placeholder": "图片2的命名后缀，如 _R"
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                    "step": 1,
                    "control_after_generate": True
                }),
                "only_first": ("BOOLEAN", {
                    "default": False,
                    "label_on": "仅第一对",
                    "label_off": "全部"
                })
            }
        }
    
    RETURN_TYPES = ("IMAGE", "IMAGE", "STRING")
    RETURN_NAMES = ("image1_batch", "image2_batch", "info")
    FUNCTION = "match_images_by_name"
    CATEGORY = "PDuse/Image"
    
    # 【关键修复】开启列表输入模式，防止ComfyUI自动拆分Batch导致数量不匹配
    INPUT_IS_LIST = True
    OUTPUT_IS_LIST = (True, True, False)
    
    def parse_name_list(self, name_string):
        """解析名称列表字符串，每行一个名称"""
        if not name_string or not name_string.strip():
            return []
        
        names = []
        for line in name_string.strip().split('\n'):
            line = line.strip()
            if line:
                names.append(line)
        return names
    
    def find_matching_pairs(self, names1, names2, images1, images2, name1_suffix="", name2_suffix=""):
        """基于文件名进行匹配逻辑"""
        matches = []
        matched_indices2 = set()
        
        # 创建名称到索引和图片的映射
        name2_dict = {name: (idx, img) for idx, (name, img) in enumerate(zip(names2, images2))}
        
        # 如果两个标识符都为空，使用完全匹配模式
        if not name1_suffix and not name2_suffix:
            for idx1, (name1, img1) in enumerate(zip(names1, images1)):
                if name1 in name2_dict and name2_dict[name1][0] not in matched_indices2:
                    idx2, img2 = name2_dict[name1]
                    matches.append((img1, img2, name1, "完全匹配"))
                    matched_indices2.add(idx2)
            return matches
        
        # 智能匹配模式
        for idx1, (name1, img1) in enumerate(zip(names1, images1)):
            found_match = False
            
            # 策略1：后缀匹配（最常见）- 例如：65_T 对应 65_R
            if not found_match and name1_suffix:
                # 尝试 _T 格式
                if name1.endswith(f"_{name1_suffix}"):
                    base_name = name1[:-len(f"_{name1_suffix}")]
                    target_name = f"{base_name}_{name2_suffix}"
                    if target_name in name2_dict and name2_dict[target_name][0] not in matched_indices2:
                        idx2, img2 = name2_dict[target_name]
                        matches.append((img1, img2, base_name, "后缀匹配(_)"))
                        matched_indices2.add(idx2)
                        found_match = True
                
                # 尝试不带下划线的后缀格式
                if not found_match and name1.endswith(name1_suffix):
                    base_name = name1[:-len(name1_suffix)]
                    target_name = f"{base_name}{name2_suffix}"
                    if target_name in name2_dict and name2_dict[target_name][0] not in matched_indices2:
                        idx2, img2 = name2_dict[target_name]
                        matches.append((img1, img2, base_name, "后缀匹配"))
                        matched_indices2.add(idx2)
                        found_match = True
            
            # 策略2：前缀匹配 - 例如：T1_00001 对应 R1_00001
            if not found_match and name1_suffix:
                # 尝试 T_ 格式
                if name1.startswith(f"{name1_suffix}_"):
                    base_name = name1[len(f"{name1_suffix}_"):]
                    target_name = f"{name2_suffix}_{base_name}"
                    if target_name in name2_dict and name2_dict[target_name][0] not in matched_indices2:
                        idx2, img2 = name2_dict[target_name]
                        matches.append((img1, img2, base_name, "前缀匹配(_)"))
                        matched_indices2.add(idx2)
                        found_match = True
                
                # 尝试不带下划线的前缀格式
                if not found_match and name1.startswith(name1_suffix):
                    base_name = name1[len(name1_suffix):]
                    target_name = f"{name2_suffix}{base_name}"
                    if target_name in name2_dict and name2_dict[target_name][0] not in matched_indices2:
                        idx2, img2 = name2_dict[target_name]
                        matches.append((img1, img2, base_name, "前缀匹配"))
                        matched_indices2.add(idx2)
                        found_match = True

            # 策略3：中间匹配 (简单的替换)
            if not found_match and name1_suffix in name1 and name2_suffix:
                 # 尝试简单替换
                 target_name = name1.replace(name1_suffix, name2_suffix)
                 if target_name in name2_dict and name2_dict[target_name][0] not in matched_indices2:
                        idx2, img2 = name2_dict[target_name]
                        matches.append((img1, img2, name1, "替换匹配"))
                        matched_indices2.add(idx2)
                        found_match = True
        
        return matches
    
    def match_images_by_name(self, image1_list, image2_list, name1_list, name2_list, 
                            name1_suffix, name2_suffix, seed, only_first):
        """主处理函数"""
        try:
            # 【数据解包】由于开启了 INPUT_IS_LIST，所有输入（包括字符串和数字）都会被包装在列表中
            # 我们需要取出第一个元素
            if isinstance(name1_list, list): name1_list = name1_list[0]
            if isinstance(name2_list, list): name2_list = name2_list[0]
            if isinstance(name1_suffix, list): name1_suffix = name1_suffix[0]
            if isinstance(name2_suffix, list): name2_suffix = name2_suffix[0]
            if isinstance(seed, list): seed = seed[0]
            if isinstance(only_first, list): only_first = only_first[0]

            # 设置随机种子
            seed = int(seed) % (2**32)
            random.seed(seed)
            np.random.seed(seed)
            torch.manual_seed(seed)
            
            # 解析名称列表
            names1 = self.parse_name_list(name1_list)
            names2 = self.parse_name_list(name2_list)
            
            # 【图片列表扁平化处理】
            # INPUT_IS_LIST=True 时，image_list 可能是 [Tensor(B,H,W,C)] 也可能是 [Tensor(1,H,W,C), Tensor(1,H,W,C)...]
            # 我们统一将其展开为单张图片的列表
            flat_images1 = []
            raw_list1 = image1_list if isinstance(image1_list, list) else [image1_list]
            for item in raw_list1:
                if isinstance(item, torch.Tensor):
                    # 如果是 batch tensor (B>1)，拆分它
                    for i in range(item.shape[0]):
                        flat_images1.append(item[i:i+1])
                else:
                    flat_images1.append(item) # 防御性代码，防止有非Tensor混入
            
            flat_images2 = []
            raw_list2 = image2_list if isinstance(image2_list, list) else [image2_list]
            for item in raw_list2:
                if isinstance(item, torch.Tensor):
                    for i in range(item.shape[0]):
                        flat_images2.append(item[i:i+1])
                else:
                    flat_images2.append(item)

            images1 = flat_images1
            images2 = flat_images2
            
            # 验证输入
            if not names1 or not names2:
                raise ValueError("请输入有效的名称列表")
            
            if len(names1) != len(images1):
                raise ValueError(f"图片1的数量({len(images1)})与名称列表长度({len(names1)})不匹配。请检查是否连错了线。")
            
            if len(names2) != len(images2):
                raise ValueError(f"图片2的数量({len(images2)})与名称列表长度({len(names2)})不匹配。")
            
            # 查找匹配的图片对
            matches = self.find_matching_pairs(names1, names2, images1, images2, 
                                              name1_suffix, name2_suffix)
            
            if not matches:
                raise ValueError(f"没有找到匹配的图片对。请检查后缀/标识符是否正确。\n图1示例: {names1[0] if names1 else '空'}\n图2示例: {names2[0] if names2 else '空'}")
            
            # 如果只输出第一对
            if only_first:
                matches = matches[:1]
            
            # 构建输出列表
            batch1_list = []
            batch2_list = []
            match_info = []
            
            for img1, img2, base_name, match_type in matches:
                # 确保张量格式正确 (1, H, W, C)
                if len(img1.shape) == 3: img1 = img1.unsqueeze(0)
                if len(img2.shape) == 3: img2 = img2.unsqueeze(0)
                
                batch1_list.append(img1)
                batch2_list.append(img2)
                
                match_info.append(f"{base_name} [{match_type}]")
            
            info_text = f"种子: {seed}\n"
            info_text += f"输入1: {len(images1)}张 | 输入2: {len(images2)}张\n"
            info_text += f"匹配成功: {len(batch1_list)} 对\n"
            info_text += f"标识符: '{name1_suffix}' -> '{name2_suffix}'\n"
            info_text += "\n匹配详情:\n" + "\n".join(match_info[:20])
            if len(match_info) > 20: info_text += "\n..."
            
            print(f"PD双图匹配: 成功匹配 {len(batch1_list)} 对图片")
            
            return (batch1_list, batch2_list, info_text)
            
        except Exception as e:
            print(f"PD双图匹配错误: {str(e)}")
            # 创建错误图片
            error_tensor = torch.zeros((1, 512, 512, 3), dtype=torch.float32)
            error_info = f"错误: {str(e)}"
            return ([error_tensor], [error_tensor], error_info)

# 节点注册
NODE_CLASS_MAPPINGS = {
    "PDimage_dual_batch_by_list": PDimage_dual_batch_by_list
}

# 节点显示名称映射
NODE_DISPLAY_NAME_MAPPINGS = {
    "PDimage_dual_batch_by_list": "PD双图批处理(列表输入)"
}