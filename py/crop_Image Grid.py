import torch

class ImageGridSplitter:
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "columns": ("INT", {"default": 3, "min": 1, "max": 100, "step": 1}),
                "rows": ("INT", {"default": 3, "min": 1, "max": 100, "step": 1}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "split_image"
    CATEGORY = "Image/Process"

    def split_image(self, image, columns, rows):
        # image 形状是 [B, H, W, C]
        B, H, W, C = image.shape
        
        # 计算每一格的大小
        cell_h = H // rows
        cell_w = W // columns
        
        output_images = []

        for r in range(rows):
            for c in range(columns):
                # 计算切片边界
                start_h = r * cell_h
                end_h = (r + 1) * cell_h
                start_w = c * cell_w
                end_w = (c + 1) * cell_w
                
                # 执行切片 [Batch, Height, Width, Channels]
                rect = image[:, start_h:end_h, start_w:end_w, :]
                output_images.append(rect)

        # 将所有切好的图拼接成一个新的 Batch 维度
        # 这样在 ComfyUI 中后续节点可以一次性处理这 9 张图
        combined_output = torch.cat(output_images, dim=0)
        
        return (combined_output,)

# 注册节点名称
NODE_CLASS_MAPPINGS = {
    "ImageGridSplitter": ImageGridSplitter
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageGridSplitter": "PDcrop: Image Grid"
}
