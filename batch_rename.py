#!/usr/bin/env python3
"""
批量重命名脚本 - 统一所有节点文件名
"""

import os
import shutil

py_dir = r"e:\Area\conda-qibei\ComfyUI\custom_nodes\Comfyui_PDuse\py"

# 重命名映射表
rename_map = {
    # 已完成
    # "PD_ImageListForSort.py": "image_list_sort.py",  # 已完成
    
    # 去掉空格
    "banana imagesize by ratio.py": "imagesize_by_ratio.py",
    "Image Blend and White.py": "image_blend_white.py",
    "PD empty ratio latent.py": "empty_ratio_latent.py",
    "PD_Text Overlay Node.py": "text_overlay_node.py",
    "random prompt_v1.py": "random_prompt_v1.py",
    
    # 统一首字母小写
    "Fill_mask.py": "fill_mask.py",
    "Mask_selector.py": "mask_selector.py",
    "Mask_selector_by_area_left.py": "mask_selector_by_area_left.py",
    
    # 去掉PD_前缀，统一命名
    "gif_PD_ImageFengMianWipe.py": "image_fengmian_wipe.py",
    "PD_CropBorder.py": "crop_border.py",
    "PD_image_crop_v2.py": "image_crop_v2.py",
    "PD_image_ratiosize.py": "image_ratiosize.py",
    "PD_Image_Rotate_v1.py": "image_rotate_v1.py",
    "PD_RemoveWhiteBorder.py": "remove_white_border.py",
    
    # 去掉PD前缀
    "PDimage_corp_v1.py": "image_crop_v1.py",
    "PDimage_corp_v2.py": "image_crop_v2_alt.py",
    "PDimage_dual_batch_v1.py": "image_dual_batch_v1.py",
    "PDimage.py": "pd_image.py",
    "PDMaskSelection.py": "mask_selection.py",
    "PDTEXT_SAVE_PATH.py": "text_save_path.py",
    
    # 统一V大小写
    "image_ratio_V1.py": "image_ratio_v1.py",
    "image_text_V1.py": "image_text_v1.py",
    "imageconcante_V1.py": "image_concatenate_v1.py",
}

def main():
    print("=" * 60)
    print("开始批量重命名文件...")
    print("=" * 60)
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for old_name, new_name in rename_map.items():
        old_path = os.path.join(py_dir, old_name)
        new_path = os.path.join(py_dir, new_name)
        
        if os.path.exists(old_path):
            try:
                # 检查新文件名是否已存在
                if os.path.exists(new_path):
                    print(f"[SKIP] {old_name} -> {new_name} (target exists)")
                    skip_count += 1
                else:
                    shutil.move(old_path, new_path)
                    print(f"[OK] {old_name} -> {new_name}")
                    success_count += 1
            except Exception as e:
                print(f"[ERROR] {old_name} - {e}")
                error_count += 1
        else:
            print(f"[NOT FOUND] {old_name}")
            skip_count += 1
    
    print("")
    print("=" * 60)
    print("Rename completed!")
    print("=" * 60)
    print(f"Success: {success_count} files")
    print(f"Skipped: {skip_count} files")
    print(f"Failed: {error_count} files")
    print("=" * 60)

if __name__ == "__main__":
    main()

