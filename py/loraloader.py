import nodes
import folder_paths

class PD_ModelLoraLoader(nodes.LoraLoader):
    """
    PD Universal Lora Loader (V4)
    更新日志:
    1. 【全端口可选】：Model 和 CLIP 都是可选的。
    2. 【纯信息模式】：如果都没连，不加载模型，直接输出 None，但正常输出 LoRA 名字和权重数值。
    3. 【数值优化】：输出权重保留两位小数。
    """
    
    def __init__(self):
        super().__init__()

    @classmethod
    def INPUT_TYPES(s):
        inputs = nodes.LoraLoader.INPUT_TYPES()
        required_inputs = inputs["required"].copy()
        
        # 定义可选输入字典
        optional_inputs = {}

        # 1. 将 'model' 移到可选
        if "model" in required_inputs:
            del required_inputs["model"]
            optional_inputs["model"] = ("MODEL",)

        # 2. 将 'clip' 移到可选
        if "clip" in required_inputs:
            del required_inputs["clip"]
            optional_inputs["clip"] = ("CLIP",)
        
        # 3. 返回新的配置：lora_name 和 strength 还在 required 里，保证菜单存在
        return {
            "required": required_inputs,
            "optional": optional_inputs
        }

    RETURN_TYPES = ("MODEL", "CLIP", "STRING", "FLOAT", "FLOAT")
    RETURN_NAMES = ("MODEL", "CLIP", "lora_name", "strength_model", "strength_clip")
    
    FUNCTION = "load_pd_lora"
    CATEGORY = "PD_Nodes"

    def load_pd_lora(self, lora_name, strength_model, strength_clip, model=None, clip=None):
        # 1. 数值清洗：保留两位小数
        clean_strength_model = round(strength_model, 2)
        clean_strength_clip = round(strength_clip, 2)

        # 2. 逻辑判断
        # 如果连了 Model，我们才执行真正的加载逻辑
        if model is not None:
            # 调用父类加载 (父类能够处理 clip 为 None 的情况)
            model_lora, clip_lora = super().load_lora(model, clip, lora_name, strength_model, strength_clip)
            return (model_lora, clip_lora, lora_name, clean_strength_model, clean_strength_clip)
        
        else:
            # 3. 纯信息模式 (没有连 Model)
            # 这种情况下，我们不能调用 super().load_lora()，因为它会因为 model 是 None 而报错。
            # 所以我们直接返回空的 Model/Clip，但返回正确的字符串和数值。
            return (None, None, lora_name, clean_strength_model, clean_strength_clip)

# 节点注册
NODE_CLASS_MAPPINGS = {
    "PD_ModelLoraLoader": PD_ModelLoraLoader
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_ModelLoraLoader": "PD Universal Lora Loader"
}