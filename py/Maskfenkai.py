import cv2
import numpy as np
import torch


class PD_Maskfenkai:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "mask": ("MASK",),
                "min_area": ("INT", {"default": 10, "min": 1, "max": 999999}),
                "row_tolerance": ("INT", {"default": 50, "min": 1, "max": 2048}),
                "split_iterations": ("INT", {"default": 0, "min": 0, "max": 20}),
                "bbox_padding": ("INT", {"default": 8, "min": 0, "max": 512}),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("images", "masks")
    OUTPUT_IS_LIST = (True, True)

    FUNCTION = "split_objects"
    CATEGORY = "Custom/PD"

    def split_objects(
        self,
        image,
        mask,
        min_area=10,
        row_tolerance=50,
        split_iterations=0,
        bbox_padding=8,
    ):
        """
        Split one ComfyUI image/mask pair into multiple cropped image/mask pairs.

        Output order is stable: top-to-bottom, then left-to-right.
        """
        if image is None or mask is None:
            return ([], [])

        # ComfyUI tensors are usually batched. We only split the first item here.
        img_np = image[0].detach().cpu().numpy().astype(np.float32, copy=False)
        mask_np = mask[0].detach().cpu().numpy().astype(np.float32, copy=False)

        # Normalize mask to 2D [H, W].
        if mask_np.ndim == 3 and mask_np.shape[-1] == 1:
            mask_np = mask_np[..., 0]
        else:
            mask_np = np.squeeze(mask_np)

        if mask_np.ndim != 2:
            raise ValueError(f"MASK must be 2D after squeeze, got shape {mask_np.shape}")

        # Your masks are black foreground on white background, so treat dark
        # pixels as the object region directly.
        binary_mask = (mask_np < 0.5).astype(np.uint8)
        if not np.any(binary_mask):
            original_img = torch.from_numpy(np.ascontiguousarray(img_np)).unsqueeze(0)
            original_mask = torch.from_numpy(np.ascontiguousarray(mask_np)).unsqueeze(0)
            return ([original_img], [original_mask])

        # Erode a little first so tiny bridges or antialiasing do not merge
        # nearby stickers into one giant component.
        split_mask = binary_mask
        if split_iterations > 0:
            kernel = np.ones((3, 3), dtype=np.uint8)
            split_mask = cv2.erode(split_mask, kernel, iterations=split_iterations)
            if not np.any(split_mask):
                split_mask = binary_mask

        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(split_mask, connectivity=8)

        components = []
        for component_id in range(1, num_labels):
            area = int(stats[component_id, cv2.CC_STAT_AREA])
            if area < min_area:
                continue

            x = int(stats[component_id, cv2.CC_STAT_LEFT])
            y = int(stats[component_id, cv2.CC_STAT_TOP])
            w = int(stats[component_id, cv2.CC_STAT_WIDTH])
            h = int(stats[component_id, cv2.CC_STAT_HEIGHT])

            x0 = max(0, x - bbox_padding)
            y0 = max(0, y - bbox_padding)
            x1 = min(img_np.shape[1], x + w + bbox_padding)
            y1 = min(img_np.shape[0], y + h + bbox_padding)

            components.append(
                {
                    "id": component_id,
                    "x": x0,
                    "y": y0,
                    "w": x1 - x0,
                    "h": y1 - y0,
                }
            )

        # First sort by top-left, then regroup by row tolerance so the order
        # stays stable for 2x3 / multi-row sticker sheets.
        components.sort(key=lambda c: (c["y"], c["x"]))

        rows = []
        for comp in components:
            placed = False
            cy = comp["y"] + comp["h"] * 0.5

            for row in rows:
                if abs(cy - row["avg_cy"]) <= row_tolerance:
                    row["items"].append(comp)
                    row["avg_cy"] = sum(
                        item["y"] + item["h"] * 0.5 for item in row["items"]
                    ) / len(row["items"])
                    placed = True
                    break

            if not placed:
                rows.append({"avg_cy": cy, "items": [comp]})

        rows.sort(key=lambda row: row["avg_cy"])
        ordered_components = []
        for row in rows:
            row["items"].sort(key=lambda c: c["x"])
            ordered_components.extend(row["items"])

        out_images = []
        out_masks = []

        for comp in ordered_components:
            comp_id = comp["id"]
            x, y, w, h = comp["x"], comp["y"], comp["w"], comp["h"]

            crop_img = img_np[y : y + h, x : x + w].copy()
            crop_labels = labels[y : y + h, x : x + w]

            # Start from the eroded seed, then grow it back a bit while staying
            # inside the original foreground. This keeps the full sticker/head
            # without re-merging neighboring stickers.
            seed_mask = (crop_labels == comp_id).astype(np.uint8)
            if split_iterations > 0:
                kernel = np.ones((3, 3), dtype=np.uint8)
                grown_mask = cv2.dilate(seed_mask, kernel, iterations=split_iterations)
            else:
                grown_mask = seed_mask

            precise_mask = np.logical_and(grown_mask > 0, binary_mask[y : y + h, x : x + w] > 0).astype(np.float32)

            # Keep the image crop intact. The mask carries the exact object shape.
            crop_img = np.ascontiguousarray(crop_img, dtype=np.float32)
            precise_mask = np.ascontiguousarray(precise_mask, dtype=np.float32)

            tensor_img = torch.from_numpy(crop_img).unsqueeze(0)
            tensor_mask = torch.from_numpy(precise_mask).unsqueeze(0)

            out_images.append(tensor_img)
            out_masks.append(tensor_mask)

        if not out_images:
            original_img = torch.from_numpy(np.ascontiguousarray(img_np)).unsqueeze(0)
            original_mask = torch.from_numpy(np.ascontiguousarray(mask_np)).unsqueeze(0)
            return ([original_img], [original_mask])

        return (out_images, out_masks)


NODE_CLASS_MAPPINGS = {
    "PD_Maskfenkai": PD_Maskfenkai
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_Maskfenkai": "PD Mask Split to List"
}
