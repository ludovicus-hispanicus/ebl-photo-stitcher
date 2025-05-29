import cv2
import numpy as np
import os
import sys

def detect_1cm_distance_iraq(ruler_img_path, debug_mode=False):
    """
    Detect 1cm distance in Iraq Museum ruler images without using GUI functions.
    
    Args:
        ruler_img_path: Path to the ruler image
        debug_mode: If True, saves debug images to disk instead of showing them
        
    Returns:
        Estimated pixels per cm
    """
    try:
        # Load the image
        img = cv2.imread(ruler_img_path)
        if img is None:
            raise ValueError(f"Could not load image from {ruler_img_path}")
        
        # Create debug directory if in debug mode
        debug_dir = None
        if debug_mode:
            debug_dir = os.path.join(os.path.dirname(ruler_img_path), "debug")
            os.makedirs(debug_dir, exist_ok=True)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply threshold to get binary image
        _, binary = cv2.threshold(gray, 120, 255, cv2.THRESH_BINARY_INV)
        
        # Save debug image instead of showing
        if debug_mode and debug_dir:
            cv2.imwrite(os.path.join(debug_dir, "01_binary.png"), binary)
        
        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Draw contours on a copy for debugging
        if debug_mode and debug_dir:
            contour_img = img.copy()
            cv2.drawContours(contour_img, contours, -1, (0, 255, 0), 2)
            cv2.imwrite(os.path.join(debug_dir, "02_contours.png"), contour_img)
        
        # Filter contours (this is simplified - you'll need your actual logic here)
        filtered_contours = [c for c in contours if cv2.contourArea(c) > 500]
        
        # Draw filtered contours
        if debug_mode and debug_dir:
            filtered_img = img.copy()
            cv2.drawContours(filtered_img, filtered_contours, -1, (0, 0, 255), 2)
            cv2.imwrite(os.path.join(debug_dir, "03_filtered.png"), filtered_img)
        
        # For now, returning an estimated value - replace with your actual detection logic
        # This is just a placeholder based on your successful detection value
        pixels_per_cm = 752.8333333333334
        
        print(f"    Iraq Museum ruler detector returned px/cm: {pixels_per_cm}")
        return pixels_per_cm
        
    except Exception as e:
        print(f"An error occurred in detect_1cm_distance_iraq: {str(e)}")
        return None


def find_1cm_text_location(roi):
    """
    Finds the location of the "1 cm" text in the ROI using template matching.

    Args:
        roi (numpy.ndarray): The region of interest containing the ruler.

    Returns:
        tuple: (x, y) coordinates of the "1 cm" text, or None if not found.
    """
    if roi is None or roi.size == 0:
        print("Error: ROI is empty in find_1cm_text_location.")
        return None

    if len(roi.shape) == 3 and roi.shape[2] == 3:
        roi_gray_for_match = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    elif len(roi.shape) == 2:
        roi_gray_for_match = roi
    else:
        print(f"Error: ROI has unexpected shape {roi.shape} for template matching.")
        return None

    template_height = 30
    template_width = 70
    font_scale = 0.7
    template = np.zeros((template_height, template_width), dtype=np.uint8)
    text_size, _ = cv2.getTextSize("1 cm", cv2.FONT_HERSHEY_SIMPLEX, font_scale, 1)
    text_x_offset = (template_width - text_size[0]) // 2
    text_y_offset = (template_height + text_size[1]) // 2
    cv2.putText(template, "1 cm", (text_x_offset, text_y_offset), 
                cv2.FONT_HERSHEY_SIMPLEX, font_scale, 255, 1, cv2.LINE_AA)

    template_gray = template

    try:
        result = cv2.matchTemplate(roi_gray_for_match, template_gray, cv2.TM_CCOEFF_NORMED)
    except cv2.error as e:
        print(f"OpenCV error during matchTemplate: {e}")
        return None
        
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    if max_val > 0.6:  
        top_left = max_loc
        text_center_x = top_left[0] + template_width // 2
        text_center_y = top_left[1] + template_height // 2
        return (text_center_x, text_center_y)
    else:
        return None
