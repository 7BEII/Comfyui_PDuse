import torch
import numpy as np
import cv2

class PD_MaskSelectorByAreaLeft:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "mask": ("MASK",),
                "select": (["mask1", "mask2", "mask3", "mask4"],),
                "padding": ("INT", {"default": 10, "min": 0, "max": 200, "step": 1}),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK", "INT", "INT")
    RETURN_NAMES = ("image", "mask", "x", "y")
    FUNCTION = "select_region"
    CATEGORY = "PDuse/Mask"

    def _connected_regions(self, mask_uint8):
        """检测所有连通区域"""
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            mask_uint8, connectivity=8
        )
        regions = []
        for i in range(1, num_labels):  # 跳过背景
            area = int(stats[i, cv2.CC_STAT_AREA])
            x = int(stats[i, cv2.CC_STAT_LEFT])
            y = int(stats[i, cv2.CC_STAT_TOP])
            w = int(stats[i, cv2.CC_STAT_WIDTH])
            h = int(stats[i, cv2.CC_STAT_HEIGHT])
            cx = float(centroids[i][0])
            cy = float(centroids[i][1])
            regions.append({
                "label": i, "area": area,
                "x": x, "y": y, "w": w, "h": h,
                "cx": cx, "cy": cy
            })
        return regions, labels

    def _pad_to(self, arr, target_h, target_w, is_image=True):
        """填充到目标尺寸"""
        if is_image:
            H, W, C = arr.shape
            out = np.zeros((target_h, target_w, C), dtype=arr.dtype)
            out[:H, :W, :] = arr
        else:
            H, W = arr.shape
            out = np.zeros((target_h, target_w), dtype=arr.dtype)
            out[:H, :W] = arr
        return out

    def select_region(self, image, mask, select="mask1", padding=10):
        bsz = image.shape[0]
        select_idx = {"mask1": 0, "mask2": 1, "mask3": 2, "mask4": 3}[select]

        crops_img = []
        crops_msk = []
        x_coords = []
        y_coords = []

        for b in range(bsz):
            img = image[b].cpu().numpy()
            msk = mask[b].cpu().numpy()

            H, W = msk.shape[:2]
            mask_uint8 = (msk > 0.5).astype(np.uint8) * 255

            # 检测所有连通区域
            regions, labels = self._connected_regions(mask_uint8)

            # 步骤1: 按面积从大到小排序，取前4个
            regions.sort(key=lambda r: r["area"], reverse=True)
            top_regions = regions[:4]  # 取最大的4个区域

            # 步骤2: 对这4个大区域按从左到右排序
            top_regions.sort(key=lambda r: r["cx"])

            # 步骤3: 根据 select 参数选择
            if select_idx >= len(top_regions):
                # 如果选择的索引超出范围，返回空白
                sel_img = np.zeros((1, 1, img.shape[2]), dtype=img.dtype)
                sel_msk = np.zeros((1, 1), dtype=np.float32)
                crop_x = 0
                crop_y = 0
            else:
                region = top_regions[select_idx]
                single_mask = (labels == region["label"]).astype(np.float32)

                # 裁切模式（固定）
                x, y, w, h = region["x"], region["y"], region["w"], region["h"]
                x1 = max(0, x - padding)
                y1 = max(0, y - padding)
                x2 = min(W, x + w + padding)
                y2 = min(H, y + h + padding)
                
                sel_img = img[y1:y2, x1:x2, :]
                sel_msk = single_mask[y1:y2, x1:x2]
                
                # 记录裁切位置
                crop_x = x1
                crop_y = y1

            crops_img.append(sel_img)
            crops_msk.append(sel_msk)
            x_coords.append(crop_x)
            y_coords.append(crop_y)

        # 填充到统一尺寸
        max_h = max(ci.shape[0] for ci in crops_img)
        max_w = max(ci.shape[1] for ci in crops_img)
        crops_img = [self._pad_to(ci, max_h, max_w, is_image=True) for ci in crops_img]
        crops_msk = [self._pad_to(cm, max_h, max_w, is_image=False) for cm in crops_msk]

        out_img = torch.from_numpy(np.stack(crops_img, axis=0)).float()
        out_msk = torch.from_numpy(np.stack(crops_msk, axis=0)).float()
        
        # 输出第一个batch的坐标（如果有多个batch，可以根据需要调整）
        out_x = x_coords[0]
        out_y = y_coords[0]

        return (out_img, out_msk, out_x, out_y)


NODE_CLASS_MAPPINGS = {
    "PD_Mask Selector By Area Left": PD_MaskSelectorByAreaLeft
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_Mask Selector By Area Left": "PD_Mask Selector By Area Left"
}

