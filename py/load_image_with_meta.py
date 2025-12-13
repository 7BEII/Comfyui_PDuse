import os
import json
import torch
import numpy as np
from PIL import Image, ImageOps, ImageSequence
import folder_paths

class LoadImageWithMetadata:
    @classmethod
    def INPUT_TYPES(s):
        input_dir = folder_paths.get_input_directory()
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        files = folder_paths.filter_files_content_types(files, ["image"])
        return {"required":
                    {"image": (sorted(files), {"image_upload": True})},
                }

    CATEGORY = "CustomTools/ImageLoader"
    
    # 修改：移除了 MASK 和 raw_prompt，只保留 image, formatted_list, raw_workflow
    RETURN_TYPES = ("IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("image", "formatted_list", "raw_workflow")
    FUNCTION = "load_image_with_metadata"

    def format_node_data(self, prompt_data):
        """
        格式化逻辑：保持你喜欢的 [ID] Type Value Link 格式
        """
        output_lines = []

        try:
            if isinstance(prompt_data, str):
                prompt_data = json.loads(prompt_data)
            
            # 按 Node ID 排序
            sorted_items = sorted(prompt_data.items(), key=lambda x: int(x[0]) if x[0].isdigit() else x[0])

            for node_id, node_data in sorted_items:
                class_type = node_data.get("class_type", "Unknown")
                inputs = node_data.get("inputs", {})

                # 1. Node ID
                output_lines.append(f"█ [ID: {node_id}]") 
                
                # 2. Type
                output_lines.append(f"   Type: {class_type}")
                
                params = []
                links = []

                for k, v in inputs.items():
                    # 判断是否为连线 [node_id, slot_index]
                    if isinstance(v, list) and len(v) == 2:
                        links.append(f"   ► Link ({k}): -> Node [{v[0]}]")
                    else:
                        str_v = str(v)
                        # 截断超长内容，避免文本框卡顿
                        if len(str_v) > 100:
                            str_v = str_v[:100] + "...(truncated)"
                        params.append(f"   • {k}: {str_v}")

                # 3. Values
                if params:
                    output_lines.append("   [Values]:")
                    output_lines.extend(params)
                
                # 4. Links
                if links:
                    output_lines.append("   [Links]:")
                    output_lines.extend(links)

                output_lines.append("-" * 30)

        except Exception as e:
            return f"Error parsing metadata: {str(e)}"

        return "\n".join(output_lines)

    def load_image_with_metadata(self, image):
        image_path = folder_paths.get_annotated_filepath(image)
        img = Image.open(image_path)
        
        # --- 元数据处理 ---
        formatted_text = "No Metadata Found"
        raw_workflow_str = "{}"

        # 1. 提取 Prompt 信息用于生成 Formatted List
        if "prompt" in img.info:
            raw_prompt_content = img.info["prompt"]
            formatted_text = self.format_node_data(raw_prompt_content)
        
        # 2. 提取 Workflow (完整的初始 JSON 信息)
        if "workflow" in img.info:
            raw_workflow_str = img.info["workflow"]
            # 确保输出是 String 格式
            if not isinstance(raw_workflow_str, str):
                raw_workflow_str = json.dumps(raw_workflow_str, indent=2)
        # ------------------

        # --- 图片处理 (移除了 Mask 输出逻辑) ---
        output_images = []
        w, h = None, None
        excluded_formats = ['MPO']

        for i in ImageSequence.Iterator(img):
            i = ImageOps.exif_transpose(i)
            if i.mode == 'I':
                i = i.point(lambda i: i * (1 / 255))
            image = i.convert("RGB")
            
            if len(output_images) == 0:
                w = image.size[0]
                h = image.size[1]
            if image.size[0] != w or image.size[1] != h:
                continue
            
            image = np.array(image).astype(np.float32) / 255.0
            image = torch.from_numpy(image)[None,]
            
            output_images.append(image)

        if len(output_images) > 1 and img.format not in excluded_formats:
            output_image = torch.cat(output_images, dim=0)
        else:
            output_image = output_images[0]

        return (output_image, formatted_text, raw_workflow_str)

# 注册节点
NODE_CLASS_MAPPINGS = {
    "PD_LoadImageWithMeta": LoadImageWithMetadata
}

# 节点显示名称
NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_LoadImageWithMeta": "PD:Load Image + Metadata"
}