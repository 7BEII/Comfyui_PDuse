import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image, ImageDraw

import comfy.utils


class PDBingxiangtieBlendV1:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "front_image": ("IMAGE",),
                "front_mask": ("MASK",),
                "medium_image": ("IMAGE",),
                "background": ("IMAGE",),
                "front_scale": ("FLOAT", {"default": 1.0, "min": 0.01, "max": 1.0, "step": 0.01}),
                "medium_X": ("INT", {"default": 0, "min": -8192, "max": 8192, "step": 1}),
                "medium_Y": ("INT", {"default": 0, "min": -8192, "max": 8192, "step": 1}),
                "medium_scale": ("FLOAT", {"default": 1.0, "min": 0.01, "max": 10.0, "step": 0.01}),
                "interpolation": (["lanczos", "bicubic", "bilinear", "area", "nearest-exact"], {"default": "lanczos"}),

            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "blend"
    CATEGORY = "PDuse/Image"

    def blend(self, front_image, front_mask, medium_image, background, medium_X, medium_Y, medium_scale, interpolation, front_scale=1.0):
        front_height, front_width = front_image.shape[1:3]
        canvas_height, canvas_width = front_height, front_width
        fit_scale = front_scale
        scaled_front_width = max(1, round(front_width * fit_scale))
        scaled_front_height = max(1, round(front_height * fit_scale))
        front_x = (canvas_width - scaled_front_width) // 2
        front_y = (canvas_height - scaled_front_height) // 2

        batch_size = max(front_image.shape[0], front_mask.shape[0], medium_image.shape[0], background.shape[0])
        outputs = []

        for index in range(batch_size):
            source_frame = self._batch_item(front_image, index)
            if source_frame.shape[:2] != (scaled_front_height, scaled_front_width):
                source_frame = comfy.utils.common_upscale(
                    source_frame.movedim(-1, 0).unsqueeze(0),
                    scaled_front_width,
                    scaled_front_height,
                    interpolation,
                    "disabled",
                )[0].movedim(0, -1)
            frame = torch.zeros(
                (canvas_height, canvas_width, source_frame.shape[-1]),
                dtype=source_frame.dtype,
                device=source_frame.device,
            )
            frame[front_y:front_y + scaled_front_height, front_x:front_x + scaled_front_width] = source_frame

            source_mask = self._prepare_mask(
                self._batch_item(front_mask, index),
                scaled_front_height,
                scaled_front_width,
            )
            mask = torch.ones((canvas_height, canvas_width), dtype=source_mask.dtype, device=source_mask.device)
            mask[front_y:front_y + scaled_front_height, front_x:front_x + scaled_front_width] = source_mask

            card = self._batch_item(medium_image, index)
            bottom = self._cover_resize(self._batch_item(background, index), canvas_height, canvas_width, interpolation)
            window = self._find_inner_window(mask)

            left, top, right, bottom_edge = self._bounding_box(window)
            window_width = right - left
            window_height = bottom_edge - top
            resize_scale = max(window_width / card.shape[1], window_height / card.shape[0]) * medium_scale
            resized_width = max(1, round(card.shape[1] * resize_scale))
            resized_height = max(1, round(card.shape[0] * resize_scale))
            resized_card = comfy.utils.common_upscale(
                card.movedim(-1, 0).unsqueeze(0),
                resized_width,
                resized_height,
                interpolation,
                "disabled",
            )[0].movedim(0, -1)

            card_x = left + (window_width - resized_width) // 2 + round(medium_X * fit_scale)
            card_y = top + (window_height - resized_height) // 2 + round(medium_Y * fit_scale)
            composed = bottom.clone()
            self._paste_card(composed, resized_card, window, card_x, card_y)

            frame_alpha = (1.0 - mask).clamp(0.0, 1.0).unsqueeze(-1)
            outputs.append(frame * frame_alpha + composed * (1.0 - frame_alpha))

        return (torch.stack(outputs),)

    @staticmethod
    def _batch_item(batch, index):
        return batch[min(index, batch.shape[0] - 1)]

    @staticmethod
    def _cover_resize(image, height, width, interpolation):
        if image.shape[:2] == (height, width):
            return image

        source_height, source_width = image.shape[:2]
        scale = max(width / source_width, height / source_height)
        resized_width = max(width, round(source_width * scale))
        resized_height = max(height, round(source_height * scale))
        resized = comfy.utils.common_upscale(
            image.movedim(-1, 0).unsqueeze(0),
            resized_width,
            resized_height,
            interpolation,
            "disabled",
        )[0].movedim(0, -1)
        left = (resized_width - width) // 2
        top = (resized_height - height) // 2
        return resized[top:top + height, left:left + width]

    @staticmethod
    def _prepare_mask(mask, height, width):
        if mask.shape != (height, width):
            mask = F.interpolate(mask.unsqueeze(0).unsqueeze(0), size=(height, width), mode="nearest")[0, 0]
        return mask

    @staticmethod
    def _find_inner_window(frame_mask):
        transparent = (frame_mask.detach().cpu().numpy() > 0.5).astype(np.uint8) * 255
        image = Image.fromarray(transparent, mode="L").copy()
        pixels = image.load()
        width, height = image.size

        for px in range(width):
            if pixels[px, 0] == 255:
                ImageDraw.floodfill(image, (px, 0), 0)
            if pixels[px, height - 1] == 255:
                ImageDraw.floodfill(image, (px, height - 1), 0)
        for py in range(height):
            if pixels[0, py] == 255:
                ImageDraw.floodfill(image, (0, py), 0)
            if pixels[width - 1, py] == 255:
                ImageDraw.floodfill(image, (width - 1, py), 0)

        enclosed = np.asarray(image) == 255
        points = np.argwhere(enclosed)
        if points.size == 0:
            raise ValueError("没有识别到冰箱贴的透明内框，请连接冰箱贴 PNG 的 MASK 输出")

        center_y = (height - 1) / 2
        center_x = (width - 1) / 2
        nearest = points[np.argmin((points[:, 0] - center_y) ** 2 + (points[:, 1] - center_x) ** 2)]
        ImageDraw.floodfill(image, (int(nearest[1]), int(nearest[0])), 128)
        window = torch.from_numpy(np.asarray(image).copy() == 128)
        return window.to(device=frame_mask.device)


    @staticmethod
    def _bounding_box(mask):
        points = torch.nonzero(mask, as_tuple=False)
        top, left = points.min(dim=0).values.tolist()
        bottom, right = (points.max(dim=0).values + 1).tolist()
        return left, top, right, bottom

    @staticmethod
    def _paste_card(canvas, card, window, x, y):
        canvas_height, canvas_width = canvas.shape[:2]
        card_height, card_width = card.shape[:2]
        dst_left = max(0, x)
        dst_top = max(0, y)
        dst_right = min(canvas_width, x + card_width)
        dst_bottom = min(canvas_height, y + card_height)
        if dst_left >= dst_right or dst_top >= dst_bottom:
            return

        src_left = dst_left - x
        src_top = dst_top - y
        src_right = src_left + dst_right - dst_left
        src_bottom = src_top + dst_bottom - dst_top
        region_mask = window[dst_top:dst_bottom, dst_left:dst_right].unsqueeze(-1)
        destination = canvas[dst_top:dst_bottom, dst_left:dst_right]
        source = card[src_top:src_bottom, src_left:src_right]
        canvas[dst_top:dst_bottom, dst_left:dst_right] = torch.where(region_mask, source, destination)


NODE_CLASS_MAPPINGS = {
    "PD-bingxiangtie-blend-v1": PDBingxiangtieBlendV1,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD-bingxiangtie-blend-v1": "PD-bingxiangtie-blend-v1",
}




