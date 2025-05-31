import cv2
import numpy as np
import os
import re

def apply_blending_mask_to_intermediate(
    image_array,
    intermediate_position,
    background_color=(0, 0, 0),
    gradient_width_fraction=0.8
):
    """
    Apply a gradient blending mask to an intermediate image based on its position.
    
    Args:
        image_array: The BGR image array to apply the mask to
        intermediate_position: String indicating the position (e.g., "intermediate_obverse_left", "ol", etc.)
        background_color: BGR tuple for the background color
        gradient_width_fraction: How much of the image should be covered by the gradient (0.0-1.0)
        
    Returns:
        The image with gradient mask applied
    """
    if image_array is None or image_array.size == 0:
        return image_array
        
    h, w = image_array.shape[:2]
    if h == 0 or w == 0:
        return image_array
    
    # Normalize the position name to a standard format
    position = _normalize_position_name(intermediate_position)
    
    # Create mask for gradient blending
    mask = np.ones((h, w), dtype=np.float32)
    
    # Calculate the gradient size
    gradient_size_px = {
        "left": int(w * gradient_width_fraction),
        "right": int(w * gradient_width_fraction),
        "top": int(h * gradient_width_fraction),
        "bottom": int(h * gradient_width_fraction)
    }
    
    # Apply gradient based on position
    if "right" in position:
        # Blend from left side (towards the object's right side)
        for x in range(min(gradient_size_px["right"], w)):
            alpha = x / gradient_size_px["right"]
            mask[:, x] = alpha
            
    elif "left" in position:
        # Blend from right side (towards the object's left side)
        for x in range(min(gradient_size_px["left"], w)):
            alpha = x / gradient_size_px["left"]
            mask[:, w-x-1] = alpha
            
    elif "top" in position:
        # Blend from bottom side (towards the object's top)
        for y in range(min(gradient_size_px["top"], h)):
            alpha = y / gradient_size_px["top"]
            mask[h-y-1, :] = alpha
            
    elif "bottom" in position:
        # Blend from top side (towards the object's bottom)
        for y in range(min(gradient_size_px["bottom"], h)):
            alpha = y / gradient_size_px["bottom"]
            mask[y, :] = alpha
    
    # Create background canvas
    background = np.full_like(image_array, background_color, dtype=np.uint8)
    
    # Apply the mask (3-channel)
    mask_3ch = np.stack([mask] * 3, axis=2)
    blended = cv2.convertScaleAbs(
        image_array * mask_3ch + background * (1 - mask_3ch)
    )
    
    return blended

def _normalize_position_name(position):
    """Normalize various position name formats to a standard form"""
    position = position.lower()
    
    # Handle shorthand codes like 'ol', 'or', etc.
    if position == 'ol' or position == 'rl' or position == '07':
        return 'left'
    elif position == 'or' or position == 'rr' or position == '08':
        return 'right'
    elif position == 'ot' or position == 'rt':
        return 'top'
    elif position == 'ob' or position == 'rb':
        return 'bottom'
    
    # Handle full names
    if 'left' in position:
        return 'left'
    elif 'right' in position:
        return 'right'
    elif 'top' in position:
        return 'top'
    elif 'bottom' in position:
        return 'bottom'
    
    # Default if we can't determine
    return position

def process_intermediate_image_with_mask(
    input_image_path,
    background_color=(0, 0, 0),
    gradient_width_fraction=0.5
):
    """
    Load an intermediate image, apply the appropriate blending mask, and save it back.
    
    Args:
        input_image_path: Path to the intermediate image (must contain position indicator)
        background_color: BGR tuple for the background color
        gradient_width_fraction: How much of the image should be covered by the gradient (0.0-1.0)
        
    Returns:
        Path to the processed image (same as input path)
    """
    # Detect the intermediate position from filename
    basename = os.path.basename(input_image_path)
    
    # Try to detect position from filename using patterns:
    # 1. _ot_object.tif, _ob_object.tif, etc. (short position codes)
    # 2. intermediate_obverse_top, etc. (full position names)
    position = None
    position_patterns = [
        r'_([or0][rltb78])_',
        r'intermediate_[^_]+_([^_\.]+)'
    ]
    
    for pattern in position_patterns:
        match = re.search(pattern, basename.lower())
        if match:
            position = match.group(1)
            break
    
    if not position:
        print(f"  Warning: Could not detect intermediate position from {basename}")
        return input_image_path
    
    print(f"  Applying blending mask to intermediate image: {basename} (position: {position})")
    
    # Load the image
    image = cv2.imread(input_image_path, cv2.IMREAD_UNCHANGED)
    if image is None:
        print(f"  Error: Failed to load intermediate image: {input_image_path}")
        return input_image_path
    
    # Apply the blending mask
    blended_image = apply_blending_mask_to_intermediate(
        image, position, background_color, gradient_width_fraction
    )
    
    # Save the blended image, overwriting the original
    if not cv2.imwrite(input_image_path, blended_image):
        print(f"  Error: Failed to save blended intermediate image: {input_image_path}")
    
    return input_image_path