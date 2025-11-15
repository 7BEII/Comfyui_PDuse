from PIL import Image, ImageDraw, ImageFont
import numpy as np
import torch

def pil2tensor(image):
    """Convert PIL image to tensor in the correct format"""
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)

class SimpleResolutionNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "max_dimension": ("INT", {
                    "default": 1024, 
                    "min": 256, 
                    "max": 4096, 
                    "step": 8
                }),
                "aspect_ratio": ([
                    "3:4 (Portrait)",
                    "4:3 (Landscape)", 
                    "1:1 (Square)"
                ], {"default": "1:1 (Square)"}),
                "divisible_by": (["8", "16", "32", "64"], {"default": "64"}),
            }
        }

    RETURN_TYPES = ("INT", "INT", "STRING", "IMAGE")
    RETURN_NAMES = ("width", "height", "resolution", "preview")
    FUNCTION = "calculate_dimensions"
    CATEGORY = "PDuse/Image"
    OUTPUT_NODE = True

    def create_preview_image(self, width, height, resolution, ratio_display):
        # 1024x1024 preview size
        preview_size = (1024, 1024)
        image = Image.new('RGB', preview_size, (0, 0, 0))  # Black background
        draw = ImageDraw.Draw(image)

        # Draw grid with grey lines
        grid_color = '#333333'  # Dark grey for grid
        grid_spacing = 50
        for x in range(0, preview_size[0], grid_spacing):
            draw.line([(x, 0), (x, preview_size[1])], fill=grid_color)
        for y in range(0, preview_size[1], grid_spacing):
            draw.line([(0, y), (preview_size[0], y)], fill=grid_color)

        # Calculate preview box dimensions
        preview_width = 800
        preview_height = int(preview_width * (height / width))
      
        # Adjust if height is too tall
        if preview_height > 800:
            preview_height = 800
            preview_width = int(preview_height * (width / height))

        # Calculate center position
        x_offset = (preview_size[0] - preview_width) // 2
        y_offset = (preview_size[1] - preview_height) // 2

        # Draw the aspect ratio box
        draw.rectangle(
            [(x_offset, y_offset), (x_offset + preview_width, y_offset + preview_height)],
            outline='red',
            width=4
        )

        # Add text
        try:
            # Draw text (centered)
            text_y = y_offset + preview_height//2
          
            # Resolution text in red
            draw.text((preview_size[0]//2, text_y), 
                     f"{width}x{height}", 
                     fill='red', 
                     anchor="mm",
                     font=ImageFont.truetype("arial.ttf", 48))
          
            # Aspect ratio text in red
            draw.text((preview_size[0]//2, text_y + 60),
                     f"({ratio_display})",
                     fill='red',
                     anchor="mm",
                     font=ImageFont.truetype("arial.ttf", 36))
          
            # Resolution text at bottom in white
            draw.text((preview_size[0]//2, y_offset + preview_height + 60),
                     f"Resolution: {resolution}",
                     fill='white',
                     anchor="mm",
                     font=ImageFont.truetype("arial.ttf", 32))
          
        except:
            # Fallback if font loading fails
            draw.text((preview_size[0]//2, text_y), f"{width}x{height}", fill='red', anchor="mm")
            draw.text((preview_size[0]//2, text_y + 60), f"({ratio_display})", fill='red', anchor="mm")
            draw.text((preview_size[0]//2, y_offset + preview_height + 60), f"Resolution: {resolution}", fill='white', anchor="mm")

        # Convert to tensor
        return pil2tensor(image)

    def calculate_dimensions(self, max_dimension, aspect_ratio, divisible_by):
        round_to = int(divisible_by)
      
        # Extract numeric ratio from selection
        numeric_ratio = aspect_ratio.split(' ')[0]
        ratio_display = numeric_ratio
      
        width_ratio, height_ratio = map(int, numeric_ratio.split(':'))
      
        # Calculate dimensions based on max_dimension
        if width_ratio >= height_ratio:
            # Landscape or square - width is the longer side
            width = max_dimension
            height = int(max_dimension * height_ratio / width_ratio)
        else:
            # Portrait - height is the longer side
            height = max_dimension
            width = int(max_dimension * width_ratio / height_ratio)

        # Round to divisible by selected value
        width = round(width / round_to) * round_to
        height = round(height / round_to) * round_to

        resolution = f"{width} x {height}"
      
        # Generate preview image
        preview = self.create_preview_image(width, height, resolution, ratio_display)
      
        return width, height, resolution, preview

# Node registration
NODE_CLASS_MAPPINGS = {
    "SimpleResolutionNode": SimpleResolutionNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SimpleResolutionNode": "PD_image ratiosize",
} 