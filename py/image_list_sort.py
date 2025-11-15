import re
import torch
from typing import List, Tuple, Any

class PD_ImageListForSort:
    """
    A simplified ComfyUI node for sorting image batches with intelligent auto-detection.
    Handles tensor batches (B,H,W,C) format used by ComfyUI.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),  # Input image tensor batch
                "sort_method": (["number", "alphabet", "natural"],),  # Sorting method
                "reverse_order": ("BOOLEAN", {"default": False}),  # Whether to reverse the order
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("sorted_images",)
    FUNCTION = "sort_images"
    CATEGORY = "PDuse/Image"
    
    def extract_first_number(self, text):
        """
        Extract the first number from text with intelligent zero-padding detection.
        Returns tuple: (number_value, padding_length, original_string)
        """
        number_match = re.search(r'\d+', str(text))
        if number_match:
            number_str = number_match.group()
            number_value = int(number_str)
            
            # Detect zero padding
            has_padding = len(number_str) > 1 and number_str.startswith('0')
            padding_length = len(number_str) if has_padding else 0
            
            return (number_value, padding_length, number_str)
        
        return (0, 0, "0")
    
    def extract_first_letter(self, text):
        """
        Extract the first alphabetic sequence from text.
        """
        letter_match = re.search(r'[a-zA-Z]+', str(text))
        if letter_match:
            return letter_match.group().lower()
        return "zzzzz"
    
    def natural_sort_key(self, text):
        """
        Create a natural sorting key for mixed alphanumeric content.
        """
        def convert(part):
            if part.isdigit():
                return int(part)
            return part.lower()
        
        parts = re.split(r'(\d+)', str(text))
        return [convert(part) for part in parts if part]
    
    def create_sort_key(self, index, sort_method, metadata=None):
        """
        Create sorting key based on index and available metadata.
        """
        # Use metadata if available, otherwise use index
        if metadata and hasattr(metadata, 'get'):
            filename = metadata.get('filename', f'image_{index:04d}')
        else:
            filename = f'image_{index:04d}'
        
        if sort_method == "number":
            number_value, padding_length, number_str = self.extract_first_number(filename)
            # Sort by: padding_length (desc), then number_value (asc)
            # This ensures 001 comes before 1, but 1 comes before 2
            return (padding_length, number_value)
            
        elif sort_method == "alphabet":
            return self.extract_first_letter(filename)
            
        else:  # natural
            return self.natural_sort_key(filename)
    
    def sort_images(self, images, sort_method, reverse_order):
        """
        Sort the image tensor batch based on the specified method and order.
        
        Args:
            images: Image tensor batch in format (B,H,W,C)
            sort_method: "number", "alphabet", or "natural" sorting method
            reverse_order: Boolean to reverse the final order
        
        Returns:
            Tuple containing the sorted image tensor batch
        """
        # Validate input tensor format
        if not isinstance(images, torch.Tensor):
            raise ValueError("Input must be a torch tensor")
        
        if len(images.shape) != 4:
            raise ValueError("Input tensor must have 4 dimensions (B,H,W,C)")
        
        batch_size = images.shape[0]
        
        # Create indexed list for sorting
        indexed_images = []
        
        for i in range(batch_size):
            try:
                # Create sort key based on index (since we don't have metadata)
                sort_key = self.create_sort_key(i, sort_method)
                indexed_images.append((images[i:i+1], sort_key, i))
            except Exception as e:
                print(f"Warning: Failed to create sort key for image {i}: {e}")
                # Fallback to original index
                indexed_images.append((images[i:i+1], i, i))
        
        # Sort based on the sort key
        try:
            if sort_method == "number":
                # For number sorting, sort by (padding_length desc, number_value asc)
                sorted_pairs = sorted(indexed_images, key=lambda x: (-x[1][0], x[1][1], x[2]))
            else:
                # For other methods, normal sorting
                sorted_pairs = sorted(indexed_images, key=lambda x: (x[1], x[2]))
        except Exception as e:
            print(f"Warning: Sorting failed, returning original order: {e}")
            sorted_pairs = indexed_images
        
        # Apply reverse if needed
        if reverse_order:
            sorted_pairs.reverse()
        
        # Extract sorted image tensors and concatenate
        sorted_image_tensors = [pair[0] for pair in sorted_pairs]
        result = torch.cat(sorted_image_tensors, dim=0)
        
        return (result,)


# Extended version that can work with metadata if available
class PD_ImageListForSortWithMetadata:
    """
    Enhanced version that can utilize image metadata when available.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "sort_method": (["number", "alphabet", "natural"],),
                "reverse_order": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "filenames": ("STRING", {"default": "", "multiline": True}),  # Optional filename list
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("sorted_images",)
    FUNCTION = "sort_images_with_metadata"
    CATEGORY = "PDuse/Image"
    
    def parse_filenames(self, filenames_str):
        """
        Parse filename string into list.
        """
        if not filenames_str or not filenames_str.strip():
            return []
        
        # Split by lines or commas
        filenames = []
        for line in filenames_str.strip().split('\n'):
            line = line.strip()
            if line:
                # Split by comma if multiple filenames in one line
                filenames.extend([f.strip() for f in line.split(',') if f.strip()])
        
        return filenames
    
    def sort_images_with_metadata(self, images, sort_method, reverse_order, filenames=""):
        """
        Sort images with optional filename metadata.
        """
        if not isinstance(images, torch.Tensor) or len(images.shape) != 4:
            raise ValueError("Input must be a 4D tensor (B,H,W,C)")
        
        batch_size = images.shape[0]
        filename_list = self.parse_filenames(filenames)
        
        # Create indexed list for sorting
        indexed_images = []
        
        for i in range(batch_size):
            # Use provided filename or generate one
            if i < len(filename_list):
                filename = filename_list[i]
            else:
                filename = f"image_{i:04d}"
            
            try:
                if sort_method == "number":
                    number_match = re.search(r'\d+', filename)
                    if number_match:
                        num_str = number_match.group()
                        num_val = int(num_str)
                        padding = len(num_str) if num_str.startswith('0') and len(num_str) > 1 else 0
                        sort_key = (padding, num_val)
                    else:
                        sort_key = (0, i)
                        
                elif sort_method == "alphabet":
                    letter_match = re.search(r'[a-zA-Z]+', filename)
                    sort_key = letter_match.group().lower() if letter_match else f"zzz_{i:04d}"
                    
                else:  # natural
                    def convert(text):
                        return int(text) if text.isdigit() else text.lower()
                    sort_key = [convert(c) for c in re.split(r'(\d+)', filename)]
                
                indexed_images.append((images[i:i+1], sort_key, i))
                
            except Exception as e:
                print(f"Warning: Failed to process image {i} with filename '{filename}': {e}")
                indexed_images.append((images[i:i+1], i, i))
        
        # Sort the images
        try:
            if sort_method == "number":
                sorted_pairs = sorted(indexed_images, key=lambda x: (-x[1][0], x[1][1], x[2]))
            else:
                sorted_pairs = sorted(indexed_images, key=lambda x: (x[1], x[2]))
        except Exception as e:
            print(f"Warning: Sorting failed: {e}")
            sorted_pairs = indexed_images
        
        if reverse_order:
            sorted_pairs.reverse()
        
        # Concatenate sorted tensors
        sorted_tensors = [pair[0] for pair in sorted_pairs]
        result = torch.cat(sorted_tensors, dim=0)
        
        return (result,)


# ComfyUI node registration
NODE_CLASS_MAPPINGS = {
    "PD_ImageListForSort": PD_ImageListForSort,
    "PD_ImageListForSortWithMetadata": PD_ImageListForSortWithMetadata
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_ImageListForSort": "PD Image List Sort",
    "PD_ImageListForSortWithMetadata": "PD Image List Sort (With Metadata)"
}

