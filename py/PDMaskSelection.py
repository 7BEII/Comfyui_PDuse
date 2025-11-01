import torch
from torchvision import transforms
from PIL import Image
import numpy as np

class PD_MASK_SELECTION:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mask1": ("MASK",),
                "image1": ("IMAGE",),
                "mask2": ("MASK",),
                "image2": ("IMAGE",),
            }
        }

    RETURN_TYPES = ("MASK", "IMAGE")
    RETURN_NAMES = ("Selected Mask", "Selected Image")
    FUNCTION = "mask_selection"
    CATEGORY = "PD_Image/Process"

    def mask_selection(self, mask1, image1, mask2, image2):
        def calculate_mask_area(mask):
            # Convert to numpy if it's a tensor
            if isinstance(mask, torch.Tensor):
                mask_np = mask.cpu().numpy()
            else:
                mask_np = np.array(mask)
            
            # Handle batch dimension if present
            if len(mask_np.shape) == 4:  # [B, H, W, C] or [B, H, W]
                mask_np = mask_np[0]  # Take first in batch
            
            # If still 3D (H,W,C), convert to 2D by taking max across channels
            if len(mask_np.shape) == 3:
                mask_np = mask_np.max(axis=-1)
            
            # Calculate non-zero area
            area = (mask_np > 0).sum()
            return area
        
        # Calculate areas
        area1 = calculate_mask_area(mask1)
        area2 = calculate_mask_area(mask2)
        
        # If both masks are empty (black), return first pair (or could return empty)
        if area1 == 0 and area2 == 0:
            return (mask1, image1)
        
        # Select mask-image pair with smaller non-zero area
        if area1 == 0:  # mask1 is empty, use mask2 pair
            selected_mask = mask2
            selected_image = image2
        elif area2 == 0:  # mask2 is empty, use mask1 pair
            selected_mask = mask1
            selected_image = image1
        else:  # Both have content, choose smaller
            if area1 < area2:
                selected_mask = mask1
                selected_image = image1
            else:
                selected_mask = mask2
                selected_image = image2
        
        return (selected_mask, selected_image)


# Node mappings
NODE_CLASS_MAPPINGS = {
    "PD_MASK_SELECTION": PD_MASK_SELECTION,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_MASK_SELECTION": "PD:MASK SELECTION",
}