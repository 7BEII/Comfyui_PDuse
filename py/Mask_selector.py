import torch
import numpy as np
import cv2

class PD_MaskSelector:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "mask": ("MASK",),
                "select": (["mask1", "mask2", "mask3", "mask4"],),  # 新增 mask4
                "sort_by": (["left_to_right", "area_desc"],),
                "min_area": ("INT", {"default": 100, "min": 0, "max": 100000, "step": 10}),
                "padding": ("INT", {"default": 10, "min": 0, "max": 200, "step": 1}),
                "output_mode": (["crop", "full_canvas"],),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    FUNCTION = "select_region"
    CATEGORY = "mask"

    def _connected_regions(self, mask_uint8, min_area=100):
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            mask_uint8, connectivity=8
        )
        regions = []
        for i in range(1, num_labels):  # 跳过背景
            area = int(stats[i, cv2.CC_STAT_AREA])
            if area >= min_area:
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
        if is_image:
            H, W, C = arr.shape
            out = np.zeros((target_h, target_w, C), dtype=arr.dtype)
            out[:H, :W, :] = arr
        else:
            H, W = arr.shape
            out = np.zeros((target_h, target_w), dtype=arr.dtype)
            out[:H, :W] = arr
        return out

    def select_region(self, image, mask, select="mask1", sort_by="left_to_right",
                      min_area=100, padding=10, output_mode="crop"):
        bsz = image.shape[0]
        select_idx = {"mask1": 0, "mask2": 1, "mask3": 2, "mask4": 3}[select]

        crops_img = []
        crops_msk = []

        for b in range(bsz):
            img = image[b].cpu().numpy()
            msk = mask[b].cpu().numpy()

            H, W = msk.shape[:2]
            mask_uint8 = (msk > 0.5).astype(np.uint8) * 255

            regions, labels = self._connected_regions(mask_uint8, min_area=min_area)

            if sort_by == "left_to_right":
                regions.sort(key=lambda r: r["cx"])
            else:
                regions.sort(key=lambda r: r["area"], reverse=True)

            if select_idx >= len(regions):
                if output_mode == "full_canvas":
                    sel_img = np.zeros_like(img, dtype=img.dtype)
                    sel_msk = np.zeros((H, W), dtype=np.float32)
                else:
                    sel_img = np.zeros((1, 1, img.shape[2]), dtype=img.dtype)
                    sel_msk = np.zeros((1, 1), dtype=np.float32)
            else:
                region = regions[select_idx]
                single_mask = (labels == region["label"]).astype(np.float32)

                if output_mode == "full_canvas":
                    sel_msk = single_mask
                    sel_img = img * sel_msk[..., None]
                else:
                    x, y, w, h = region["x"], region["y"], region["w"], region["h"]
                    x1 = max(0, x - padding)
                    y1 = max(0, y - padding)
                    x2 = min(W, x + w + padding)
                    y2 = min(H, y + h + padding)
                    sel_img = img[y1:y2, x1:x2, :]
                    sel_msk = single_mask[y1:y2, x1:x2]

            crops_img.append(sel_img)
            crops_msk.append(sel_msk)

        if output_mode == "crop":
            max_h = max(ci.shape[0] for ci in crops_img)
            max_w = max(ci.shape[1] for ci in crops_img)
            crops_img = [self._pad_to(ci, max_h, max_w, is_image=True) for ci in crops_img]
            crops_msk = [self._pad_to(cm, max_h, max_w, is_image=False) for cm in crops_msk]

        out_img = torch.from_numpy(np.stack(crops_img, axis=0)).float()
        out_msk = torch.from_numpy(np.stack(crops_msk, axis=0)).float()

        return (out_img, out_msk)


NODE_CLASS_MAPPINGS = {
    "PD_Mask Selector": PD_MaskSelector
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_Mask Selector": "PD_Mask Selector"
}
