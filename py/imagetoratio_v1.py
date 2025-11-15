import torch

class PDImageToRatioV1:
    """
    图片尺寸转比例节点V1
    输入图片，自动获取图片尺寸并转换为比例格式输出（如 16:9）
    """
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("ratio",)
    FUNCTION = "image_to_ratio"
    CATEGORY = "PDuse/Image"

    @classmethod
    def INPUT_TYPES(cls):
        """
        返回节点的输入参数定义。
        @returns {dict} 输入参数定义
        """
        return {
            "required": {
                "image": ("IMAGE",),
            }
        }

    def image_to_ratio(self, image):
        """
        获取图片尺寸并转换为比例格式。
        @param image {Tensor} 输入图片，形状为 (B, H, W, C)
        @returns {tuple} (比例字符串,)
        """
        # 获取图片尺寸
        # image 形状为 (B, H, W, C)
        batch_size, height, width, channels = image.shape
        
        # 使用第一张图片的尺寸
        w = int(width)
        h = int(height)
        
        # 计算最大公约数并简化比例
        gcd = self._gcd(w, h)
        ratio_w = w // gcd
        ratio_h = h // gcd
        
        # 格式化为字符串 宽:高
        ratio_string = f"{ratio_w}:{ratio_h}"
        
        return (ratio_string,)
    
    def _gcd(self, a, b):
        """
        计算两个数的最大公约数（欧几里得算法）。
        @param a {int} 第一个数
        @param b {int} 第二个数
        @returns {int} 最大公约数
        """
        while b:
            a, b = b, a % b
        return a


# 节点注册
NODE_CLASS_MAPPINGS = {
    "PDImageToRatioV1": PDImageToRatioV1,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PDImageToRatioV1": "PD_Image to Ratio V1",
}

