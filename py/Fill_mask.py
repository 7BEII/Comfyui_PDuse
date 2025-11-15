import torch
import numpy as np
from scipy.ndimage import binary_fill_holes
import cv2

class PD_MaskFillHoles:
    """
    Mask Fill Holes节点
    智能填充mask图像中的内部空洞，只处理完全被前景像素包围的空洞，不处理连接到边界的开口区域
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mask": ("MASK",),  # 输入mask图像张量 [B, H, W]
            },
            "optional": {
                "fill_method": (["scipy", "opencv"], {
                    "default": "scipy"
                }),  # 填充方法选择
                "min_hole_size": ("INT", {
                    "default": 0, 
                    "min": 0, 
                    "max": 10000, 
                    "step": 1
                }),  # 最小空洞尺寸（0表示填充所有空洞）
                "iterations": ("INT", {
                    "default": 1, 
                    "min": 1, 
                    "max": 10, 
                    "step": 1
                }),  # 形态学操作迭代次数（仅opencv方法）
            }
        }

    RETURN_TYPES = ("MASK",)  # 返回填充后的mask
    RETURN_NAMES = ("filled_mask",)  # 返回值的名称
    FUNCTION = "fill_holes"  # 指定执行的方法名称
    CATEGORY = "PDuse/Mask"  # 定义节点的类别

    def fill_holes(self, mask, fill_method="scipy", min_hole_size=0, iterations=1):
        """
        填充mask图像中的空洞
        
        参数：
            mask (tensor): 输入mask张量 [B, H, W]
            fill_method (str): 填充方法 ("scipy" 或 "opencv")
            min_hole_size (int): 最小空洞尺寸，小于此尺寸的空洞不会被填充
            iterations (int): 形态学操作迭代次数（仅opencv方法）
            
        返回：
            filled_mask (tensor): 填充空洞后的mask张量 [B, H, W]
        """
        # 确保输入mask张量的格式正确 [B, H, W]
        if mask.dim() != 3:
            raise ValueError("输入mask张量必须是 3 维的 [B, H, W]")
        
        batch_size, height, width = mask.shape
        
        # 处理每张mask
        filled_masks = []
        
        for i in range(batch_size):
            # 获取单张mask [H, W]
            single_mask = mask[i].cpu().numpy()
            
            # 转换为二值图像 (0 和 1)
            # ComfyUI的mask: 1.0=前景(白色), 0.0=背景(黑色)
            binary_mask = (single_mask > 0.5).astype(np.uint8)
            
            print(f"🔍 处理第 {i+1} 张mask，原始前景像素: {np.sum(binary_mask)}")
            
            if fill_method == "scipy":
                # 使用改进的方法，只填充真正的内部空洞（不连接边界的空洞）
                filled_binary = self._fill_internal_holes_only(binary_mask)
                
            elif fill_method == "opencv":
                # 使用OpenCV方法，但仍然只填充内部空洞
                # 先使用形态学操作预处理
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
                
                # 轻微的形态学闭运算来连接断开的边缘
                preprocessed = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel, iterations=iterations)
                
                # 然后使用改进的方法只填充内部空洞
                filled_binary = self._fill_internal_holes_only(preprocessed)
            
            # 如果设置了最小空洞尺寸过滤
            if min_hole_size > 0:
                # 计算新增的像素（填充的空洞）
                newly_filled = filled_binary - binary_mask
                
                # 使用连通组件分析找到各个空洞
                num_labels, labels = cv2.connectedComponents(newly_filled.astype(np.uint8))
                
                # 过滤掉小于最小尺寸的空洞
                for label in range(1, num_labels):
                    component_mask = (labels == label)
                    component_size = np.sum(component_mask)
                    
                    if component_size < min_hole_size:
                        # 如果空洞太小，恢复为原始状态
                        filled_binary[component_mask] = binary_mask[component_mask]
            
            # 统计填充结果
            original_foreground = np.sum(binary_mask)
            filled_foreground = np.sum(filled_binary)
            filled_pixels = filled_foreground - original_foreground
            
            print(f"  ✅ 填充完成，新增前景像素: {filled_pixels}")
            
            # 转换回浮点数格式 [H, W]
            filled_mask_float = filled_binary.astype(np.float32)
            
            # 转换回张量格式
            filled_tensor = torch.from_numpy(filled_mask_float)
            filled_masks.append(filled_tensor)
        
        # 堆叠所有处理后的mask [B, H, W]
        result_masks = torch.stack(filled_masks, dim=0)
        
        # 统计整批的处理结果
        original_total = torch.sum(mask > 0.5).item()
        filled_total = torch.sum(result_masks > 0.5).item()
        total_filled = filled_total - original_total
        
        print(f"🎯 批处理完成: 共处理 {batch_size} 张mask，总计填充 {total_filled} 个像素")
        
        return (result_masks,)

    def _fill_internal_holes_only(self, binary_mask):
        """
        只填充真正的内部空洞，不处理连接到边界的开口区域
        
        参数：
            binary_mask (numpy.ndarray): 二值mask图像 [H, W]
            
        返回：
            filled_binary (numpy.ndarray): 只填充内部空洞的mask [H, W]
        """
        h, w = binary_mask.shape
        
        # 创建一个稍大的图像用于flood fill操作
        padded_mask = np.zeros((h + 2, w + 2), dtype=np.uint8)
        padded_mask[1:-1, 1:-1] = binary_mask
        
        # 反转mask：0变成1，1变成0
        # 这样背景变成前景，我们可以flood fill背景区域
        inverted_mask = 1 - padded_mask
        
        # 从边界开始flood fill，标记所有连接到边界的背景区域
        external_background = inverted_mask.copy()
        
        # 从四条边的所有边界点开始flood fill
        # 上边界
        for x in range(w + 2):
            if external_background[0, x] == 1:
                cv2.floodFill(external_background, None, (x, 0), 2)
        
        # 下边界
        for x in range(w + 2):
            if external_background[h + 1, x] == 1:
                cv2.floodFill(external_background, None, (x, h + 1), 2)
        
        # 左边界
        for y in range(h + 2):
            if external_background[y, 0] == 1:
                cv2.floodFill(external_background, None, (0, y), 2)
        
        # 右边界
        for y in range(h + 2):
            if external_background[y, w + 1] == 1:
                cv2.floodFill(external_background, None, (w + 1, y), 2)
        
        # 提取原始区域
        external_background = external_background[1:-1, 1:-1]
        
        # 现在 external_background 中：
        # 2 = 连接到边界的背景区域（外部背景）
        # 1 = 内部空洞（不连接边界的背景区域）
        # 0 = 原始前景区域
        
        # 识别内部空洞
        internal_holes = (external_background == 1)
        
        # 创建填充结果：原始前景 + 内部空洞
        filled_binary = binary_mask.copy()
        filled_binary[internal_holes] = 1
        
        # 统计内部空洞
        hole_count = np.sum(internal_holes)
        if hole_count > 0:
            print(f"    🕳️  识别到 {hole_count} 个内部空洞像素（不连接边界）")
        else:
            print(f"    ℹ️  未发现内部空洞")
        
        return filled_binary.astype(np.uint8)

class PD_MaskRemoveSmallObjects:
    """
    Mask Remove Small Objects节点
    移除mask图像中的小对象，与填充空洞功能互补
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mask": ("MASK",),  # 输入mask图像张量 [B, H, W]
                "min_size": ("INT", {
                    "default": 100, 
                    "min": 1, 
                    "max": 50000, 
                    "step": 1
                }),  # 最小对象尺寸
            },
            "optional": {
                "connectivity": ("INT", {
                    "default": 2, 
                    "min": 1, 
                    "max": 2, 
                    "step": 1
                }),  # 连通性 (1=4连通, 2=8连通)
            }
        }

    RETURN_TYPES = ("MASK",)  # 返回清理后的mask
    RETURN_NAMES = ("cleaned_mask",)  # 返回值的名称
    FUNCTION = "remove_small_objects"  # 指定执行的方法名称
    CATEGORY = "PDuse/Mask"  # 定义节点的类别

    def remove_small_objects(self, mask, min_size=100, connectivity=2):
        """
        移除mask图像中的小对象
        
        参数：
            mask (tensor): 输入mask张量 [B, H, W]
            min_size (int): 最小对象尺寸，小于此尺寸的对象将被移除
            connectivity (int): 连通性 (1=4连通, 2=8连通)
            
        返回：
            cleaned_mask (tensor): 清理后的mask张量 [B, H, W]
        """
        # 确保输入mask张量的格式正确 [B, H, W]
        if mask.dim() != 3:
            raise ValueError("输入mask张量必须是 3 维的 [B, H, W]")
        
        batch_size, height, width = mask.shape
        
        # 处理每张mask
        cleaned_masks = []
        
        for i in range(batch_size):
            # 获取单张mask [H, W]
            single_mask = mask[i].cpu().numpy()
            
            # 转换为二值图像
            binary_mask = (single_mask > 0.5).astype(np.uint8)
            
            # 使用连通组件分析
            connectivity_cv = 4 if connectivity == 1 else 8
            num_labels, labels = cv2.connectedComponents(binary_mask, connectivity=connectivity_cv)
            
            # 创建清理后的mask
            cleaned_binary = np.zeros_like(binary_mask)
            
            removed_objects = 0
            kept_objects = 0
            
            # 检查每个连通组件
            for label in range(1, num_labels):  # 跳过背景标签0
                component_mask = (labels == label)
                component_size = np.sum(component_mask)
                
                if component_size >= min_size:
                    # 保留足够大的对象
                    cleaned_binary[component_mask] = 1
                    kept_objects += 1
                else:
                    # 移除太小的对象
                    removed_objects += 1
            
            print(f"🧹 第 {i+1} 张mask: 保留 {kept_objects} 个对象，移除 {removed_objects} 个小对象")
            
            # 转换回浮点数格式
            cleaned_mask_float = cleaned_binary.astype(np.float32)
            
            # 转换回张量格式
            cleaned_tensor = torch.from_numpy(cleaned_mask_float)
            cleaned_masks.append(cleaned_tensor)
        
        # 堆叠所有处理后的mask
        result_masks = torch.stack(cleaned_masks, dim=0)
        
        print(f"🎯 批处理完成: 共处理 {batch_size} 张mask")
        
        return (result_masks,)

# 节点注册
NODE_CLASS_MAPPINGS = {
    "PD_MaskFillHoles": PD_MaskFillHoles,
    "PD_MaskRemoveSmallObjects": PD_MaskRemoveSmallObjects
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_MaskFillHoles": "PD:Mask Fill Holes",
    "PD_MaskRemoveSmallObjects": "PD:Mask Remove Small Objects"
} 