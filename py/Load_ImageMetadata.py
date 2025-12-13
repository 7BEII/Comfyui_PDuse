import os
import json
import torch
import numpy as np
from PIL import Image, ImageOps, ImageSequence
import folder_paths
import node_helpers


class PD_LoadImageMetadata:
    """
    加载图片并提取元数据信息
    支持读取图片中的workflow、prompt、LoRA等参数信息
    """
    
    @classmethod
    def INPUT_TYPES(s):
        input_dir = folder_paths.get_input_directory()
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        files = folder_paths.filter_files_content_types(files, ["image"])
        return {
            "required": {
                "image": (sorted(files), {"image_upload": True})
            },
        }

    CATEGORY = "PD:load image"
    
    RETURN_TYPES = ("IMAGE", "MASK", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("图片", "遮罩", "提示词", "模型信息", "LoRA信息")
    FUNCTION = "load_image_with_metadata"
    
    def extract_metadata(self, image_path):
        """
        提取图片的元数据信息
        
        Args:
            image_path: 图片路径
            
        Returns:
            tuple: (prompt_text, model_info, lora_info)
        """
        try:
            img = Image.open(image_path)
            
            # 初始化返回值
            prompt_text = ""
            model_info = ""
            lora_info = ""
            
            # 尝试从PNG info中提取信息
            if hasattr(img, 'info') and img.info:
                info = img.info
                
                # 调试：打印所有可用的info键
                print(f"📝 PNG Info 键: {list(info.keys())}")
                
                # 优先从prompt字段提取 (ComfyUI格式)
                if 'prompt' in info:
                    try:
                        prompt_data = json.loads(info['prompt'])
                        
                        # 提取各类信息
                        lora_list = []
                        model_list = []
                        prompt_texts = []
                        
                        for node_id, node_data in prompt_data.items():
                            if isinstance(node_data, dict):
                                class_type = node_data.get('class_type', '')
                                inputs = node_data.get('inputs', {})
                                
                                # 提取模型信息
                                if 'CheckpointLoader' in class_type or 'Checkpoint' in class_type:
                                    ckpt_name = inputs.get('ckpt_name', '')
                                    if ckpt_name:
                                        model_list.append(f"[Checkpoint] {ckpt_name}")
                                
                                # 提取LoRA信息
                                if 'lora' in class_type.lower() or 'LoraLoader' in class_type:
                                    lora_name = inputs.get('lora_name', '')
                                    strength_model = inputs.get('strength_model', 1.0)
                                    strength_clip = inputs.get('strength_clip', 1.0)
                                    
                                    if lora_name:
                                        lora_list.append(
                                            f"lora name: {lora_name}\n"
                                            f"strength_model: {strength_model}\n"
                                            f"strength_clip: {strength_clip}"
                                        )
                                
                                # 提取VAE信息
                                if 'VAELoader' in class_type:
                                    vae_name = inputs.get('vae_name', '')
                                    if vae_name:
                                        model_list.append(f"[VAE] {vae_name}")
                                
                                # 提取文本提示词
                                if class_type in ['CLIPTextEncode', 'CLIPTextEncodeSDXL']:
                                    text = inputs.get('text', '')
                                    if text:
                                        prompt_texts.append(text)
                                
                                # Flux系列提示词节点
                                if 'FluxGuidance' in class_type or 'DualCLIPLoader' in class_type:
                                    text = inputs.get('text', '') or inputs.get('guidance', '')
                                    if text:
                                        prompt_texts.append(str(text))
                        
                        # 格式化输出
                        if prompt_texts:
                            prompt_text = "\n\n".join(prompt_texts)
                            print(f"   ✓ 提取到 {len(prompt_texts)} 个提示词")
                        
                        if model_list:
                            model_info = "\n".join(model_list)
                            print(f"   ✓ 提取到 {len(model_list)} 个模型")
                        
                        if lora_list:
                            lora_info = "\n\n".join(lora_list)
                            print(f"   ✓ 提取到 {len(lora_list)} 个LoRA")
                    
                    except json.JSONDecodeError as e:
                        print(f"⚠️  解析prompt JSON失败: {e}")
                
                # 如果prompt字段没有信息，尝试从workflow字段提取
                if not prompt_text and not model_info and 'workflow' in info:
                    try:
                        workflow_data = json.loads(info['workflow'])
                        
                        # 重新初始化列表
                        lora_list = []
                        model_list = []
                        prompt_texts = []
                        
                        # workflow格式通常是 {"nodes": [...], "links": [...]}
                        if 'nodes' in workflow_data:
                            for node in workflow_data['nodes']:
                                if isinstance(node, dict):
                                    node_type = node.get('type', '')
                                    widgets_values = node.get('widgets_values', [])
                                    
                                    # 提取模型信息
                                    if 'CheckpointLoader' in node_type and widgets_values:
                                        model_list.append(f"[Checkpoint] {widgets_values[0]}")
                                    
                                    # 提取LoRA信息
                                    if 'LoraLoader' in node_type and len(widgets_values) >= 3:
                                        lora_name = widgets_values[0]
                                        strength_model = widgets_values[1]
                                        strength_clip = widgets_values[2]
                                        lora_list.append(
                                            f"lora name: {lora_name}\n"
                                            f"strength_model: {strength_model}\n"
                                            f"strength_clip: {strength_clip}"
                                        )
                                    
                                    # 提取提示词
                                    if 'CLIPTextEncode' in node_type and widgets_values:
                                        prompt_texts.append(str(widgets_values[0]))
                        
                        if prompt_texts:
                            prompt_text = "\n\n".join(prompt_texts)
                            print(f"   ✓ 从workflow提取到 {len(prompt_texts)} 个提示词")
                        if model_list:
                            model_info = "\n".join(model_list)
                            print(f"   ✓ 从workflow提取到 {len(model_list)} 个模型")
                        if lora_list:
                            lora_info = "\n\n".join(lora_list)
                            print(f"   ✓ 从workflow提取到 {len(lora_list)} 个LoRA")
                    
                    except json.JSONDecodeError as e:
                        print(f"⚠️  解析workflow JSON失败: {e}")
                
                # 如果ComfyUI格式没有找到，尝试Stable Diffusion WebUI格式
                if not prompt_text and 'parameters' in info:
                    parameters = str(info['parameters'])
                    if parameters:
                        lines = parameters.split('\n')
                        # 提取正向提示词
                        for i, line in enumerate(lines):
                            if line.startswith('Negative prompt:'):
                                prompt_text = '\n'.join(lines[:i]).strip()
                                break
                        if not prompt_text and lines:
                            prompt_text = lines[0]
            
            return prompt_text, model_info, lora_info
            
        except Exception as e:
            print(f"⚠️  提取元数据失败: {e}")
            import traceback
            traceback.print_exc()
            return "", "", ""
    
    def load_image_with_metadata(self, image):
        """
        加载图片并返回图片数据、遮罩、元数据信息
        
        Args:
            image: 图片文件名
            
        Returns:
            tuple: (image_tensor, mask_tensor, prompt_text, model_info, lora_info)
                - image_tensor: 图像张量 (B, H, W, C)
                - mask_tensor: 遮罩张量 (B, H, W)
                - prompt_text: 提示词文本
                - model_info: 模型信息
                - lora_info: LoRA信息
        """
        # 获取图片路径
        image_path = folder_paths.get_annotated_filepath(image)
        
        # 提取元数据
        prompt_text, model_info, lora_info = self.extract_metadata(image_path)
        
        # 打开图片
        img = node_helpers.pillow(Image.open, image_path)

        output_images = []
        output_masks = []
        w, h = None, None

        excluded_formats = ['MPO']

        # 处理多帧图片（如GIF）
        for i in ImageSequence.Iterator(img):
            # 处理EXIF方向信息
            i = node_helpers.pillow(ImageOps.exif_transpose, i)

            # 处理特殊格式
            if i.mode == 'I':
                i = i.point(lambda i: i * (1 / 255))
            image_pil = i.convert("RGB")

            # 检查尺寸一致性
            if len(output_images) == 0:
                w = image_pil.size[0]
                h = image_pil.size[1]

            if image_pil.size[0] != w or image_pil.size[1] != h:
                continue

            # 转换为张量 (H, W, C)
            image_np = np.array(image_pil).astype(np.float32) / 255.0
            image_tensor = torch.from_numpy(image_np)[None,]  # 添加batch维度 (1, H, W, C)
            
            # 处理Alpha通道（遮罩）
            if 'A' in i.getbands():
                # 有Alpha通道，提取遮罩
                mask_np = np.array(i.getchannel('A')).astype(np.float32) / 255.0
                mask = 1. - torch.from_numpy(mask_np)  # 反转遮罩
            elif i.mode == 'P' and 'transparency' in i.info:
                # 调色板模式且有透明度信息
                mask_np = np.array(i.convert('RGBA').getchannel('A')).astype(np.float32) / 255.0
                mask = 1. - torch.from_numpy(mask_np)
            else:
                # 没有Alpha通道，创建全黑遮罩
                mask = torch.zeros((h, w), dtype=torch.float32, device="cpu")
            
            output_images.append(image_tensor)
            output_masks.append(mask.unsqueeze(0))  # 添加batch维度 (1, H, W)

        # 合并多帧或返回单帧
        if len(output_images) > 1 and img.format not in excluded_formats:
            output_image = torch.cat(output_images, dim=0)  # (B, H, W, C)
            output_mask = torch.cat(output_masks, dim=0)    # (B, H, W)
        else:
            output_image = output_images[0]  # (1, H, W, C)
            output_mask = output_masks[0]    # (1, H, W)

        # 打印调试信息
        print(f"✅ PD加载图片(含元数据): {image}")
        print(f"   - 图像张量形状: {output_image.shape}")
        print(f"   - 遮罩张量形状: {output_mask.shape}")
        print(f"   - 提示词长度: {len(prompt_text)} 字符")
        print(f"   - 模型信息: {'已检测到' if model_info else '未检测到'}")
        print(f"   - LoRA信息: {'已检测到' if lora_info else '未检测到'}")

        return (output_image, output_mask, prompt_text, model_info, lora_info)


# 节点注册
NODE_CLASS_MAPPINGS = {
    "PD_LoadImageMetadata": PD_LoadImageMetadata
}

# 节点显示名称映射
NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_LoadImageMetadata": "PD Load Image (LoRA/JSON/Workflow)"
}

# 导出节点信息供ComfyUI使用
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

