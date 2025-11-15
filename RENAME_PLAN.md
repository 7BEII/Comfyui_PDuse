# 文件重命名计划

## 重命名规则

1. 去掉 `PD_` 前缀
2. 去掉空格，使用下划线
3. 统一小写命名
4. 修正拼写错误

## 重命名映射表

| 旧文件名 | 新文件名 | 状态 |
|---------|---------|------|
| `PD_ImageListForSort.py` | `image_list_sort.py` | ✅ 完成 |
| `gif_PD_ImageFengMianWipe.py` | `image_fengmian_wipe.py` | 进行中 |
| `banana imagesize by ratio.py` | `imagesize_by_ratio.py` | 待处理 |
| `Image Blend and White.py` | `image_blend_white.py` | 待处理 |
| `PD empty ratio latent.py` | `empty_ratio_latent.py` | 待处理 |
| `PD_Text Overlay Node.py` | `text_overlay_node.py` | 待处理 |
| `random prompt_v1.py` | `random_prompt_v1.py` | 待处理 |
| `Fill_mask.py` | `fill_mask.py` | 待处理 |
| `Mask_selector.py` | `mask_selector.py` | 待处理 |
| `Mask_selector_by_area_left.py` | `mask_selector_by_area_left.py` | 待处理 |
| `PD_CropBorder.py` | `crop_border.py` | 待处理 |
| `PD_image_crop_v2.py` | `image_crop_v2.py` | 待处理 |
| `PD_image_ratiosize.py` | `image_ratiosize.py` | 待处理 |
| `PD_Image_Rotate_v1.py` | `image_rotate_v1.py` | 待处理 |
| `PD_RemoveWhiteBorder.py` | `remove_white_border.py` | 待处理 |
| `PDimage_corp_v1.py` | `image_crop_v1.py` | 待处理 |
| `PDimage_corp_v2.py` | `image_crop_v2_alt.py` | 待处理 |
| `PDimage_dual_batch_v1.py` | `image_dual_batch_v1.py` | 待处理 |
| `PDimage.py` | `pd_image.py` | 待处理 |
| `PDMaskSelection.py` | `mask_selection.py` | 待处理 |
| `PDTEXT_SAVE_PATH.py` | `text_save_path.py` | 待处理 |
| `image_ratio_V1.py` | `image_ratio_v1.py` | 待处理 |
| `image_text_V1.py` | `image_text_v1.py` | 待处理 |
| `imageconcante_V1.py` | `image_concatenate_v1.py` | 待处理 |

## 保持不变的文件

以下文件已经符合命名规范，保持不变：

- `add_label.py`
- `image_resize_v1.py`
- `image_resize_v2.py`
- `image_resize_v3.py`
- `imagebach.py`
- `imageblend_v1.py`
- `imagetoratio_v1.py`
- `logic.py`
- `mask_edge_selector.py`
- `png.py`
- `show.py`
- `string_del_word.py`
- `string_empty_word.py`
- `txt.py`

## 注意事项

所有重命名**不会改变文件内部的类名和函数名**，只改变文件名。ComfyUI的`__init__.py`会自动扫描py目录下的所有模块并加载。

