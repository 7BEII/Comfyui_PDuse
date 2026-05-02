import nodes


class PD_lora_loader(nodes.LoraLoaderModelOnly):
    @classmethod
    def INPUT_TYPES(cls):
        return nodes.LoraLoaderModelOnly.INPUT_TYPES()

    RETURN_TYPES = ("MODEL", "STRING", "STRING")
    RETURN_NAMES = ("MODEL", "name", "strength")
    FUNCTION = "load_pd_lora"
    CATEGORY = "PD_Nodes"

    def load_pd_lora(self, model, lora_name, strength_model):
        strength_text = f"{strength_model:.2f}"
        print(f"PD_lora_loader: name={lora_name}, strength={strength_text}")
        model_lora = self.load_lora(model, None, lora_name, strength_model, 0)[0]
        return (model_lora, str(lora_name), strength_text)


NODE_CLASS_MAPPINGS = {
    "PD_lora_loader": PD_lora_loader,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_lora_loader": "PD_lora_loader",
}
