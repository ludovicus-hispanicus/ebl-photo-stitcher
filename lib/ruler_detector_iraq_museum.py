import cv2
import numpy as np
import os
import math
from remove_background import (
    detect_dominant_corner_background_color,
    get_museum_background_color,
    create_foreground_mask_from_background,
    select_contour_closest_to_image_center
)
from object_extractor_rembg import extract_and_save_center_object


def get_detection_parameters(museum_selection="Iraq Museum"):
    """
    Get detection parameters based on museum selection.
    
    Args:
        museum_selection (str): The museum/collection selection
        
    Returns:
        dict: Dictionary containing detection parameters
    """
    if museum_selection == "Iraq Museum (Sippar Library)":
        return {
            'hough_threshold': 80,
            'hough_min_line_length': 20,
            'tick_min_height': 25,
            'canny_low_threshold': 15,
            'canny_high_threshold': 45,
            'roi_height_fraction': 0.60  # Default ROI height fraction
        }
    else:
        # Default Iraq Museum parameters
        return {
            'hough_threshold': 60,
            'hough_min_line_length': 15,
            'tick_min_height': 20,
            'canny_low_threshold': 10,
            'canny_high_threshold': 40,
            'roi_height_fraction': 0.55  # Default ROI height fraction
        }


def detect_1cm_distance_iraq(image_path, museum_selection="Iraq Museum", roi_height_fraction=None):
    """
    Detect 1cm distance on a ruler in images from Iraq Museum.
    
    Args:
        image_path (str): Path to the image file
        museum_selection (str): Museum selection for parameter configuration
        roi_height_fraction (float, optional): Fraction of image height to use for ROI (0.0 to 1.0)
                                             If None, uses default from parameter configuration
    
    Returns:
        float: Distance in pixels representing 1cm on the ruler, or None if detection fails
    """
    # Get detection parameters
    params = get_detection_parameters(museum_selection)
    
    # Override roi_height_fraction if provided
    if roi_height_fraction is not None:
        params['roi_height_fraction'] = roi_height_fraction
    
    # Read and preprocess the image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not load image from {image_path}")
        return None
    
    height, width = image.shape[:2]
    
    # Apply ROI using the roi_height_fraction parameter
    roi_height = int(height * params['roi_height_fraction'])
    roi_y_start = height - roi_height
    roi = image[roi_y_start:height, :]
    
    # Convert to grayscale
    gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray_roi, (5, 5), 0)
    
    # Edge detection using Canny
    edges = cv2.Canny(blurred, 
                     params['canny_low_threshold'], 
                     params['canny_high_threshold'])
    
    # Hough Line Transform to detect lines
    lines = cv2.HoughLinesP(edges, 
                           1, 
                           np.pi/180, 
                           threshold=params['hough_threshold'],
                           minLineLength=params['hough_min_line_length'], 
                           maxLineGap=10)
    
    if lines is None:
        return None
    
    # Filter for mostly vertical lines (ruler markings)
    vertical_lines = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        
        # Calculate line angle
        if x2 - x1 != 0:
            angle = abs(np.arctan((y2 - y1) / (x2 - x1)) * 180 / np.pi)
        else:
            angle = 90
        
        # Keep lines that are mostly vertical (80-90 degrees)
        if 80 <= angle <= 90:
            line_length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            if line_length >= params['tick_min_height']:
                vertical_lines.append(line[0])
    
    if len(vertical_lines) < 2:
        return None
    
    # Sort lines by x-coordinate
    vertical_lines.sort(key=lambda line: line[0])
    
    # Calculate distances between consecutive vertical lines
    distances = []
    for i in range(len(vertical_lines) - 1):
        x1 = vertical_lines[i][0]
        x2 = vertical_lines[i + 1][0]
        distance = abs(x2 - x1)
        distances.append(distance)
    
    if not distances:
        return None
    
    # Return the most common distance (mode) as the 1cm measurement
    # This assumes regular spacing of ruler markings
    distances.sort()
    
    # Find the most frequent distance (simple mode calculation)
    distance_counts = {}
    for dist in distances:
        # Group similar distances (within 5 pixels)
        found_group = False
        for key in distance_counts:
            if abs(dist - key) <= 5:
                distance_counts[key] += 1
                found_group = True
                break
        if not found_group:
            distance_counts[dist] = 1
    
    if not distance_counts:
        return None
    
    # Return the distance with the highest count
    most_common_distance = max(distance_counts.keys(), key=lambda k: distance_counts[k])
    
    return float(most_common_distance)

def find_1cm_text_location(roi, debug_path=None):
    if roi is None or roi.size == 0:
        if debug_path:
            cv2.imwrite(debug_path, np.zeros((100, 100, 3), dtype=np.uint8)) # Save a blank image
        return None

    if len(roi.shape) == 3 and roi.shape[2] == 3:
        roi_gray_for_match = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    elif len(roi.shape) == 2:
        roi_gray_for_match = roi
    else:
        if debug_path:
            cv2.imwrite(debug_path, roi)
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
        result = cv2.matchTemplate(
            roi_gray_for_match, template_gray, cv2.TM_CCOEFF_NORMED)
    except cv2.error as e:
        print(f"Error during template matching: {e}")
        return None

    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    if max_val > 0.6: # Confidence threshold for template matching
        top_left = max_loc
        text_center_x = top_left[0] + template_width // 2
        text_center_y = top_left[1] + template_height // 2
        return (text_center_x, text_center_y)
    else:
        return None