import shutil
import os
from pathlib import Path

class PD_TensorTraining:
    """
    Tensor数据预处理节点 v4：
    修复了逻辑，增加了运行模式选择。
    可以选择只处理特定格式，也可以选择整库复制。
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        # 定义格式下拉菜单选项
        ext_list = ["All", ".jpg", ".png", ".txt"]
        
        return {
            "required": {
                "input_path": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "输入文件夹路径"
                }),
                "output_path": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "输出路径 (会自动创建)"
                }),
                
                # --- 新增：运行模式 ---
                "operation_mode": (["Copy All (Dataset Safe)", "Strict Filter (Rules Only)"], {
                    "default": "Copy All (Dataset Safe)"
                }),
                
                # --- 第一组规则 ---
                "find_1": ("STRING", {
                    "default": "R",
                    "placeholder": "查找词1"
                }),
                "replace_1": ("STRING", {
                    "default": "star", 
                    "placeholder": "替换词1"
                }),
                "ext_1": (ext_list, {"default": ".jpg"}),

                # --- 第二组规则 ---
                "find_2": ("STRING", {
                    "default": "T",
                    "placeholder": "查找词2"
                }),
                "replace_2": ("STRING", {
                    "default": "end",
                    "placeholder": "替换词2"
                }),
                "ext_2": (ext_list, {"default": ".jpg"}),

                # --- 第三组规则 ---
                "find_3": ("STRING", {
                    "default": "T",
                    "placeholder": "查找词3"
                }),
                "replace_3": ("STRING", {
                    "default": "",
                    "placeholder": "替换词3"
                }),
                "ext_3": (ext_list, {"default": ".txt"}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("message",)
    FUNCTION = "process_dataset"
    CATEGORY = "PandyTool/File"
    DESCRIPTION = "批量复制并重命名，支持严格过滤模式"

    def process_dataset(self, input_path, output_path, operation_mode,
                       find_1, replace_1, ext_1,
                       find_2, replace_2, ext_2,
                       find_3, replace_3, ext_3):
        
        VALID_EXTS = {'.jpg', '.png', '.txt'}

        try:
            # 1. 路径校验
            if not input_path.strip(): return ("❌ 错误：未输入源路径",)
            if not output_path.strip(): return ("❌ 错误：未输入目标路径",)
                
            in_dir = Path(input_path.strip())
            out_dir = Path(output_path.strip())

            if not in_dir.exists(): return (f"❌ 错误：输入文件夹不存在: {input_path}",)

            # 2. 自动创建输出目录
            try:
                out_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return (f"❌ 错误：无法创建输出目录 - {e}",)

            # 3. 统计数据
            stats = {
                "total": 0, "renamed": 0, "copied": 0, "errors": 0, "skipped": 0, "logs": []
            }

            # 4. 获取文件
            files = [f for f in in_dir.iterdir() if f.is_file() and f.suffix.lower() in VALID_EXTS]
            
            if not files:
                return (f"⚠️ 警告：目录中没有支持的文件 (jpg/png/txt)",)

            # 5. 核心处理循环
            for f in files:
                try:
                    original_name = f.name
                    current_ext = f.suffix.lower() 
                    new_name = original_name
                    
                    # 标记该文件是否被规则命中
                    matched_rule = False

                    # --- 规则处理 (增加 .strip() 防止空字符串误判) ---
                    
                    # 规则 1
                    if find_1 and find_1.strip():
                        if (ext_1 == "All" or ext_1 == current_ext):
                            if find_1 in new_name:
                                new_name = new_name.replace(find_1, replace_1)
                                matched_rule = True # 命中了内容修改
                            elif operation_mode == "Strict Filter (Rules Only)":
                                # 在严格模式下，如果后缀匹配了规则（比如是txt），但没包含关键词
                                # 我们通常认为它属于"该类文件"，允许通过，但如果你希望严格到"只有包含关键词才复制"，逻辑需更严
                                # 这里保持宽容：只要后缀对应且规则非空，就视为命中了关注范围
                                matched_rule = True

                    # 规则 2
                    if find_2 and find_2.strip():
                        if (ext_2 == "All" or ext_2 == current_ext):
                            if find_2 in new_name:
                                new_name = new_name.replace(find_2, replace_2)
                                matched_rule = True
                            elif operation_mode == "Strict Filter (Rules Only)":
                                matched_rule = True

                    # 规则 3
                    if find_3 and find_3.strip():
                        if (ext_3 == "All" or ext_3 == current_ext):
                            if find_3 in new_name:
                                new_name = new_name.replace(find_3, replace_3)
                                matched_rule = True
                            elif operation_mode == "Strict Filter (Rules Only)":
                                matched_rule = True

                    # --- 决策：是否复制/处理 ---
                    
                    should_process = True
                    
                    # 如果是严格模式，且没有命中任何有效规则的后缀范围，则跳过
                    if operation_mode == "Strict Filter (Rules Only)":
                        # 检查当前文件是否属于任何一个由于设置了find而生效的ext范围
                        active_scope = False
                        
                        # 检查规则1是否激活且覆盖当前后缀
                        if find_1.strip() and (ext_1 == "All" or ext_1 == current_ext): active_scope = True
                        # 检查规则2
                        if find_2.strip() and (ext_2 == "All" or ext_2 == current_ext): active_scope = True
                        # 检查规则3
                        if find_3.strip() and (ext_3 == "All" or ext_3 == current_ext): active_scope = True
                        
                        if not active_scope:
                            should_process = False

                    if not should_process:
                        stats["skipped"] += 1
                        continue

                    # --- 执行操作 ---
                    stats["total"] += 1
                    
                    # 判断是否发生了重命名
                    is_renamed = (new_name != original_name)
                    
                    # 目标路径处理
                    dest_path = out_dir / new_name
                    dest_path = self._get_unique_path(dest_path)

                    shutil.copy2(str(f), str(dest_path))

                    if is_renamed:
                        stats["renamed"] += 1
                        stats["logs"].append(f"🔄 [{current_ext}] {original_name} -> {dest_path.name}")
                    else:
                        stats["copied"] += 1
                        stats["logs"].append(f"📄 [{current_ext}] {original_name}")

                except Exception as e:
                    stats["errors"] += 1
                    stats["logs"].append(f"❌ {f.name}: {str(e)}")

            return (self._make_report(out_dir, stats),)

        except Exception as e:
            return (f"❌ 严重错误: {str(e)}",)

    def _get_unique_path(self, path: Path) -> Path:
        if not path.exists(): return path
        stem = path.stem
        suffix = path.suffix
        parent = path.parent
        counter = 1
        while path.exists():
            path = parent / f"{stem}_{counter}{suffix}"
            counter += 1
        return path

    def _make_report(self, out_dir, stats):
        msg = []
        msg.append("✅ Tensor 数据集处理完成")
        msg.append(f"📂 输出: {out_dir}")
        msg.append(f"📊 统计: 处理 {stats['total']} | 改名 {stats['renamed']} | 原样 {stats['copied']} | 忽略 {stats['skipped']}")
        msg.append("\n📝 详情 (Top 20):")
        msg.extend(stats["logs"][:20])
        if len(stats["logs"]) > 20:
            msg.append(f"... 剩余 {len(stats['logs']) - 20} 条")
        return "\n".join(msg)

NODE_CLASS_MAPPINGS = {
    "PD_TensorTraining": PD_TensorTraining
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_TensorTraining": "PD: Tensor Dataset Prepare"
}