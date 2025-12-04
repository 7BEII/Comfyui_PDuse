import os
import json

class PDJSON_Group:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "directory_path": ("STRING", {"default": r"A:\path\to\json_files"}),
                "color_choice": (["Blue", "DeepGray", "Yellow", "Green", "None"], {"default": "None"}),
                "modify_size": (["enable", "disable"], {"default": "disable"}),
                "font_size": ("INT", {"default": 14, "min": 8, "max": 72, "step": 1}),
                "target_title": ("STRING", {"default": ""}),
                "output_folder": ("STRING", {"default": ""}),
                "new_filename": ("STRING", {"default": "_fix01"}),  # 改为后缀模式
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("Result",)
    FUNCTION = "process_json_files"
    CATEGORY = "PD Custom Nodes"

    def process_json_files(self, directory_path, color_choice, modify_size, font_size, target_title, output_folder, new_filename):
        try:
            # 规范化路径
            directory_path = os.path.normpath(directory_path)
            output_folder = os.path.normpath(output_folder) if output_folder else directory_path
            
            # 颜色映射
            color_map = {
                "Blue": "#3f789e",
                "DeepGray": "#444",
                "Yellow": "#c09430",
                "Green": "#3c763d",
                "None": None
            }
            target_color = color_map.get(color_choice)

            # 检查输入文件夹
            if not os.path.exists(directory_path):
                return (f"错误：输入文件夹不存在: {directory_path}",)
            
            # 创建输出文件夹（如果需要）
            if output_folder != directory_path and not os.path.exists(output_folder):
                os.makedirs(output_folder)

            # 获取所有JSON文件
            json_files = [f for f in os.listdir(directory_path) if f.lower().endswith(".json")]
            if not json_files:
                return (f"错误：没有找到JSON文件: {directory_path}",)

            processed_files = []
            
            for filename in json_files:
                input_path = os.path.join(directory_path, filename)
                
                # 生成新文件名（在原始文件名后添加后缀）
                base_name, ext = os.path.splitext(filename)
                new_base_name = f"{base_name}{new_filename}"
                output_name = f"{new_base_name}{ext}"  # 保留原扩展名
                output_path = os.path.join(output_folder, output_name)

                # 读取JSON文件
                try:
                    with open(input_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except Exception as e:
                    print(f"读取JSON文件失败 {input_path}: {e}")
                    continue

                # 修改数据
                modified = False
                for group in data.get("groups", []):
                    # 修改颜色
                    if target_color is not None:
                        group["color"] = target_color
                        modified = True
                    
                    # 修改字体大小
                    if modify_size == "enable":
                        should_modify = not target_title or group.get("title") == target_title
                        if should_modify and "font_size" in group:
                            old_size = group["font_size"]
                            group["font_size"] = font_size
                            print(f"修改组 '{group.get('title')}': 字体大小 {old_size} → {font_size}")
                            modified = True

                # 保存修改
                if modified:
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)
                    processed_files.append(output_path)
                    print(f"已处理文件: {output_path}")
                else:
                    print(f"无需修改: {input_path}")

            result_msg = f"处理完成！已修改 {len(processed_files)} 个文件"
            if output_folder != directory_path:
                result_msg += f"\n输出目录: {output_folder}"
            
            if color_choice != "None":
                result_msg += f"\n颜色修改为: {color_choice} ({target_color})"
            
            if modify_size == "enable":
                result_msg += f"\n字体大小修改为: {font_size} (目标标题: '{target_title}' if specified)"
            
            return (result_msg,)

        except Exception as e:
            return (f"处理出错: {str(e)}",)

class BatchJsonIncremental:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "input_folder": ("STRING", {"default": r"A:\1_area\area_python\pojie"}),  # 输入文件夹路径
                "output_folder": ("STRING", {"default": r"A:\1_area\area_python\output"}),  # 输出文件夹路径
                "start_x": ("INT", {"default": 0}),  # 起始坐标 X
                "start_y": ("INT", {"default": 0}),  # 起始坐标 Y
                "increment": ("INT", {"default": 20}),  # 坐标递增步长
                "file_prefix": ("STRING", {"default": "Modified"}),  # 输出文件前缀
            },
        }

    CATEGORY = "image/PD_jsonincremental"  # 节点类别

    RETURN_TYPES = ("STRING",)  # 输出类型为字符串
    RETURN_NAMES = ("result_message",)  # 返回的结果名称
    FUNCTION = "arrange_nodes_batch"

    def arrange_nodes_batch(self, input_folder, output_folder, start_x, start_y, increment, file_prefix):
        try:
            # 自动规范路径
            input_folder = os.path.normpath(input_folder)
            output_folder = os.path.normpath(output_folder)

            # 打印输入输出文件夹信息
            print(f"Input folder: {input_folder}")
            print(f"Output folder: {output_folder}")

            # 检查输入文件夹是否存在
            if not os.path.exists(input_folder):
                error_msg = f"Error: 输入文件夹不存在: {input_folder}"
                print(error_msg)
                return (error_msg,)

            # 如果输出文件夹不存在，创建它
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
                print(f"Output folder created: {output_folder}")

            # 获取输入文件夹中所有 JSON 文件
            json_files = [f for f in os.listdir(input_folder) if f.endswith(".json")]
            print(f"Found JSON files: {json_files}")

            if not json_files:
                error_msg = f"Error: 输入文件夹中没有找到 JSON 文件: {input_folder}"
                print(error_msg)
                return (error_msg,)

            processed_files = []  # 用于记录已处理的文件列表

            # 遍历所有 JSON 文件
            for idx, json_file in enumerate(json_files):
                input_file = os.path.join(input_folder, json_file)
                output_file = os.path.join(output_folder, f"{file_prefix}_{idx + 1}.json")

                print(f"Processing file: {input_file}")

                # 读取 JSON 文件
                try:
                    with open(input_file, "r", encoding="utf-8") as file:
                        data = json.load(file)
                    print(f"Successfully loaded JSON: {input_file}")
                except json.JSONDecodeError as e:
                    error_msg = f"Error decoding JSON file {input_file}: {e}"
                    print(error_msg)
                    continue

                # 提取节点列表
                nodes = data.get("nodes", [])

                if not nodes:
                    print(f"No nodes found in file: {input_file}")
                    continue

                print(f"Found {len(nodes)} nodes in file: {input_file}")

                # 按照 `id` 字段从小到大排序
                nodes.sort(key=lambda x: x.get("id", 0))
                print(f"Nodes sorted by ID for file: {input_file}")

                # 更新每个节点的 `pos` 和 `xy`
                for i, node in enumerate(nodes):
                    new_x = start_x + i * increment
                    new_y = start_y + i * increment
                    node["pos"] = [new_x, new_y]
                    node["xy"] = [new_x, new_y]
                    print(f"Updated node {i} position to pos: {node['pos']}")

                # 将修改后的节点写回数据
                data["nodes"] = nodes

                # 保存到新的 JSON 文件
                with open(output_file, "w", encoding="utf-8") as file:
                    json.dump(data, file, ensure_ascii=False, indent=4)

                print(f"File saved to: {output_file}")
                processed_files.append(output_file)

            # 返回结果信息
            result_msg = (
                f"批量处理完成！已处理 {len(processed_files)} 个文件，全部按照编号递增节点处理。\n"
                f"文件保存在目录：{output_folder}\n文件列表：\n" + "\n".join(processed_files)
            )
            print(result_msg)
            return (result_msg,)
        except Exception as e:
            # 返回错误信息
            error_msg = f"Error: {str(e)}"
            print(error_msg)
            return (error_msg,)



# 将节点类映射到 ComfyUI 节点
NODE_CLASS_MAPPINGS = {
    "PDJSON_BatchJsonIncremental": BatchJsonIncremental,  # 节点内部名称
    "PDJSON_Group": PDJSON_Group,   
}

# 可选：为节点增加更友好的名称
NODE_DISPLAY_NAME_MAPPINGS = {
    "PDJSON_BatchJsonIncremental": "PDJSON_incrementalnumber",  # 节点显示名称
    "PDJSON_Group": "PDJSON_Group",
}
