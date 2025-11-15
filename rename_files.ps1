# 统一重命名脚本 - 将所有节点文件名标准化
# 规则：小写+下划线，去掉PD_前缀，去掉空格

$pyDir = "e:\Area\conda-qibei\ComfyUI\custom_nodes\Comfyui_PDuse\py"

# 重命名映射表
$renameMap = @{
    # 去掉空格
    "banana imagesize by ratio.py" = "imagesize_by_ratio.py"
    "Image Blend and White.py" = "image_blend_white.py"
    "PD empty ratio latent.py" = "empty_ratio_latent.py"
    "PD_Text Overlay Node.py" = "text_overlay_node.py"
    "random prompt_v1.py" = "random_prompt_v1.py"
    
    # 统一首字母小写
    "Fill_mask.py" = "fill_mask.py"
    "Mask_selector.py" = "mask_selector.py"
    "Mask_selector_by_area_left.py" = "mask_selector_by_area_left.py"
    
    # 去掉PD_前缀，统一命名
    "gif_PD_ImageFengMianWipe.py" = "image_fengmian_wipe.py"
    "PD_CropBorder.py" = "crop_border.py"
    "PD_image_crop_v2.py" = "image_crop_v2.py"
    "PD_image_ratiosize.py" = "image_ratiosize.py"
    "PD_Image_Rotate_v1.py" = "image_rotate_v1.py"
    "PD_ImageListForSort.py" = "image_list_sort.py"
    "PD_RemoveWhiteBorder.py" = "remove_white_border.py"
    
    # 去掉PD前缀
    "PDimage_corp_v1.py" = "image_crop_v1.py"
    "PDimage_corp_v2.py" = "image_crop_v2_alt.py"
    "PDimage_dual_batch_v1.py" = "image_dual_batch_v1.py"
    "PDimage.py" = "pd_image.py"
    "PDMaskSelection.py" = "mask_selection.py"
    "PDTEXT_SAVE_PATH.py" = "text_save_path.py"
    
    # 统一V大小写
    "image_ratio_V1.py" = "image_ratio_v1.py"
    "image_text_V1.py" = "image_text_v1.py"
    "imageconcante_V1.py" = "image_concatenate_v1.py"
}

Write-Host ("=" * 60)
Write-Host "开始重命名文件..." -ForegroundColor Green
Write-Host ("=" * 60)

$successCount = 0
$skipCount = 0
$errorCount = 0

foreach ($oldName in $renameMap.Keys) {
    $newName = $renameMap[$oldName]
    $oldPath = Join-Path $pyDir $oldName
    $newPath = Join-Path $pyDir $newName
    
    if (Test-Path $oldPath) {
        try {
            # 检查新文件名是否已存在
            if (Test-Path $newPath) {
                Write-Host "⚠️  跳过: $oldName -> $newName (目标文件已存在)" -ForegroundColor Yellow
                $skipCount++
            } else {
                Rename-Item -Path $oldPath -NewName $newName -ErrorAction Stop
                Write-Host "✅ 重命名: $oldName -> $newName" -ForegroundColor Green
                $successCount++
            }
        } catch {
            Write-Host "❌ 失败: $oldName - $_" -ForegroundColor Red
            $errorCount++
        }
    } else {
        Write-Host "⚠️  文件不存在: $oldName" -ForegroundColor Yellow
        $skipCount++
    }
}

Write-Host ""
Write-Host ("=" * 60)
Write-Host "重命名完成!" -ForegroundColor Green
Write-Host ("=" * 60)
Write-Host "✅ 成功: $successCount 个文件" -ForegroundColor Green
Write-Host "⚠️  跳过: $skipCount 个文件" -ForegroundColor Yellow
Write-Host "❌ 失败: $errorCount 个文件" -ForegroundColor Red
Write-Host ("=" * 60)

