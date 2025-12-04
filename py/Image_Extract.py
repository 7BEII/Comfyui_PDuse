import torch

class PD_Extract_Image:
    """
    【全局索引提取器】
    无论输入是单个Batch还是多个List，将其视为一个连续的图片序列。
    根据 index 提取其中唯一的一张图片。
    支持负数索引（-1 为最后一张）。
    """
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "image_index": ("INT", {
                    "default": 0, 
                    "min": -10000, # 允许输入负数
                    "max": 10000, 
                    "step": 1,
                    "display": "number"
                }),
            }
        }

    INPUT_IS_LIST = True
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "extract_image"
    CATEGORY = "PD_Image/Processing"

    def extract_image(self, images, image_index):
        # 1. 参数清洗
        target_idx = image_index[0] if isinstance(image_index, list) else image_index
        image_list = images

        # 2. 计算总数
        total_count = 0
        for img in image_list:
            if hasattr(img, 'shape'):
                total_count += img.shape[0]

        if total_count == 0:
            print("Error: 输入图片为空，返回空白图防止报错。")
            return (torch.zeros((1, 64, 64, 3)),)

        # 3. 智能索引修正 (支持负数倒序)
        original_idx = target_idx # 记录原始输入用于打印
        
        if target_idx < 0:
            target_idx = total_count + target_idx

        # 越界钳制
        if target_idx < 0:
            target_idx = 0
            print(f"Warning: Index {original_idx} 超出下限，已自动修正为 0")
        elif target_idx >= total_count:
            target_idx = total_count - 1
            print(f"Warning: Index {original_idx} 超出上限，已自动修正为最后一张")

        # 4. 全局查找逻辑
        current_pointer = 0
        selected_image = None

        for img_batch in image_list:
            batch_size = img_batch.shape[0]
            
            # 判断目标是否在当前 Batch 区间内
            if current_pointer <= target_idx < (current_pointer + batch_size):
                local_index = target_idx - current_pointer
                # 保持 [1, H, W, C] 维度
                selected_image = img_batch[local_index:local_index+1].clone()
                break
            
            current_pointer += batch_size

        # 兜底
        if selected_image is None:
            selected_image = image_list[-1][-1:].clone()

        return (selected_image,)

# 注册节点
NODE_CLASS_MAPPINGS = {
    "PD_Extract_Image": PD_Extract_Image
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_Extract_Image": "PD_Extract Image (Index)"
}