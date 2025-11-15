#!/usr/bin/env python3
"""
修复大小写重命名（Windows兼容）
使用两步法：旧名 -> 临时名 -> 新名
"""

import os
import shutil

py_dir = r"e:\Area\conda-qibei\ComfyUI\custom_nodes\Comfyui_PDuse\py"

# 需要修复大小写的文件
case_fixes = {
    "Fill_mask.py": "fill_mask.py",
    "Mask_selector.py": "mask_selector.py",
    "Mask_selector_by_area_left.py": "mask_selector_by_area_left.py",
    "image_ratio_V1.py": "image_ratio_v1.py",
    "image_text_V1.py": "image_text_v1.py",
}

def main():
    print("=" * 60)
    print("Fixing case-sensitive renames...")
    print("=" * 60)
    
    for old_name, new_name in case_fixes.items():
        old_path = os.path.join(py_dir, old_name)
        new_path = os.path.join(py_dir, new_name)
        temp_path = os.path.join(py_dir, f"_temp_{new_name}")
        
        if os.path.exists(old_path):
            try:
                # Step 1: 重命名到临时文件
                shutil.move(old_path, temp_path)
                # Step 2: 从临时文件重命名到最终文件
                shutil.move(temp_path, new_path)
                print(f"[OK] {old_name} -> {new_name}")
            except Exception as e:
                print(f"[ERROR] {old_name} - {e}")
                # 尝试恢复
                if os.path.exists(temp_path):
                    try:
                        shutil.move(temp_path, old_path)
                    except:
                        pass
        else:
            print(f"[SKIP] {old_name} (not found or already renamed)")
    
    print("=" * 60)
    print("Case fix completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()

