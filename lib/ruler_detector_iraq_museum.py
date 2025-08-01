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
    base_params = {
        "hough_min_line_length": 30,
        "hough_max_line_gap": 10,
        "hough_threshold": 60,
        "tick_max_width": 20,
        "tick_min_width": 1,
        "tick_min_height": 20,
        "max_tick_thickness_px": 30,
        "min_ticks_required": 11,
        "num_ticks_for_1cm": 11,
        "consistency_threshold": 0.7
    }
    
    if museum_selection == "Iraq Museum (Sippar Library)":
        base_params.update({
            "hough_min_line_length": 8,  # Reduced for shorter ticks
            "hough_max_line_gap": 20,    # Increased to bridge small gaps
            "hough_threshold": 60,       # Can be adjusted based on edge detection
            "tick_max_width": 10,        # Adjusted for thinner lines
            "tick_min_width": 1,         # Adjusted for thinner lines
            "tick_min_height": 10,       # Adjusted for shorter ticks
            "min_ticks_required": 8,     # Reduced as 1cm might have fewer clear ticks
            "num_ticks_for_1cm": 10,     # Standard for Sippar Library rulers
            "consistency_threshold": 5,# Increased flexibility for spacing
        })
    
    return base_params


def detect_1cm_distance_iraq(image_path, museum_selection="Iraq Museum"):
    base_filename = os.path.splitext(os.path.basename(image_path))[0]
    debug_filename = f"{base_filename}_debugging.jpg"
    debug_path = os.path.join(os.path.dirname(image_path), debug_filename)
    
    params = get_detection_parameters(museum_selection)

    try:
        img = cv2.imread(image_path)
        if img is None:
            print(f"Error: Could not load image at {image_path}")
            return None
        height, width, _ = img.shape

        # Define ROI
        if museum_selection == "Iraq Museum (Sippar Library)":
            # Wider ROI for Sippar Library - full width, bottom 40-50%
            roi_width = width
            roi_x = 0
            roi_height = int(height * 0.45)  # Adjusted roi_height
            roi_y = height - roi_height
        else:
            roi_width = width // 3
            roi_x = 0
            roi_height = height // 2
            roi_y = height - roi_height
        initial_roi = img[roi_y:height, roi_x:roi_x + roi_width]

        roi = initial_roi.copy() # Make a copy to avoid modifying original roi_temp_path for debugging

        # Skip background removal for Sippar Library
        if museum_selection != "Iraq Museum (Sippar Library)":
            roi_temp_path = os.path.join(os.path.dirname(image_path), f"{base_filename}_temp_roi.jpg")
            cv2.imwrite(roi_temp_path, roi)
            try:
                bg_removed_path, _ = extract_and_save_center_object(
                    roi_temp_path,
                    output_image_background_color=(255, 255, 255),
                    output_filename_suffix="_bg_removed.tif",
                    feather_radius_px=5,
                    min_object_area_as_image_fraction=0.01
                )

                bg_removed_img = cv2.imread(bg_removed_path)
                if bg_removed_img is not None:
                    roi = bg_removed_img

                if os.path.exists(roi_temp_path):
                    os.remove(roi_temp_path)
                if os.path.exists(bg_removed_path):
                    os.remove(bg_removed_path)

            except Exception as e:
                print(f"Error during background removal: {e}")
                if os.path.exists(roi_temp_path):
                    os.remove(roi_temp_path)
        # else: for Sippar, we directly use 'roi' as 'initial_roi'
        
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        processed_roi = gray_roi.copy()

        if museum_selection == "Iraq Museum (Sippar Library)":
            # Apply trimming for Sippar Library after minimal processing
            height_p, width_p = processed_roi.shape[:2]
            left_margin = int(width_p * 0.05)   # Less aggressive trimming
            right_margin = int(width_p * 0.95)
            bottom_margin = int(height_p * 0.80)
            top_margin = int(height_p * 0.20)
            
            trimmed_roi = processed_roi[top_margin:bottom_margin,
                                        left_margin:right_margin]
            
            # Very light contrast adjustment
            alpha_contrast = 1.1
            beta_brightness = 0
            contrast_adjusted_roi = cv2.convertScaleAbs(
                trimmed_roi, alpha=alpha_contrast, beta=beta_brightness)

            # Sharpening - use a more pronounced sharpening
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            sharpened = cv2.filter2D(contrast_adjusted_roi, -1, kernel)
            
            # Use morphological operations to enhance vertical lines
            # Close operation with a slightly larger vertical kernel to connect more gaps
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 7)) # Increased kernel height
            enhanced = cv2.morphologyEx(sharpened, cv2.MORPH_CLOSE, vertical_kernel)
            
            # Apply a binary threshold to make lines stark black/white before Canny
            # This is a critical step for consistent edge detection on subtle lines
            _, processed_roi_for_edges = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)


        else: # Original preprocessing for other museum specimens
            blurred_roi = cv2.GaussianBlur(gray_roi, (3, 3), 0)

            contrast_factor = 10
            lookup_table = np.array([
                255 / (1 + math.exp(-contrast_factor * (i - 128) / 255))
                for i in np.arange(0, 256)
            ]).astype("uint8")
            linear_contrast_roi = cv2.LUT(blurred_roi, lookup_table)
            height_p, width_p = linear_contrast_roi.shape[:2]
            left_margin = int(width_p * 0.10)
            right_margin = int(width_p * 0.90)
            bottom_margin = int(height_p * 0.50)
            top_margin = int(height_p * 0.10)

            trimmed_roi = linear_contrast_roi[top_margin:bottom_margin,
                                            left_margin:right_margin]

            alpha_contrast = 1.5
            beta_brightness = -1
            processed_roi_for_edges = cv2.convertScaleAbs(
                trimmed_roi, alpha=alpha_contrast, beta=beta_brightness)
        
        # Canny Edge Detection
        if museum_selection == "Iraq Museum (Sippar Library)":
            # Significantly lowered Canny thresholds
            edges_roi = cv2.Canny(processed_roi_for_edges, 5, 20) # Even more sensitive
        else:
            edges_roi = cv2.Canny(processed_roi_for_edges, 40, 60)

        # For debugging purposes, save the processed ROI and edges
        cv2.imwrite(debug_path, roi) # Save the initial ROI
        cv2.imwrite(os.path.join(os.path.dirname(image_path), f"{base_filename}_processed_roi.jpg"), processed_roi_for_edges)
        cv2.imwrite(os.path.join(os.path.dirname(image_path), f"{base_filename}_edges.jpg"), edges_roi)

        lines_roi = cv2.HoughLinesP(
            edges_roi, 
            1, 
            np.pi / 180,
            params['hough_threshold'], 
            minLineLength=params['hough_min_line_length'], 
            maxLineGap=params['hough_max_line_gap']
        )

        if lines_roi is None or len(lines_roi) < 2:
            print("No sufficient lines detected.")
            # Before returning, draw the ROI and its edges on the debug image
            debug_img_with_lines = initial_roi.copy()
            cv2.putText(debug_img_with_lines, "No sufficient lines detected", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.imwrite(debug_path, debug_img_with_lines)
            return None

        potential_ticks_props = []
        # Drawing lines on a copy for debugging
        debug_img_with_lines = initial_roi.copy()
        for line in lines_roi:
            x1, y1, x2, y2 = line[0]
            line_height = abs(y2 - y1)
            line_width = abs(x2 - x1)

            if (line_width >= params['tick_min_width'] and 
                line_width <= params['tick_max_width'] and 
                line_height >= params['tick_min_height']):
                avg_x = (x1 + x2) / 2.0
                potential_ticks_props.append({'x': avg_x, 'y1': min(
                    y1, y2), 'y2': max(y1, y2), 'h': line_height, 'w': line_width})
                cv2.line(debug_img_with_lines, (x1, y1), (x2, y2), (0, 255, 0), 2) # Draw green lines

        cv2.imwrite(debug_path, debug_img_with_lines) # Save the debug image with detected lines

        if not potential_ticks_props:
            print("No potential ticks found after filtering.")
            return None

        potential_ticks_props.sort(key=lambda tick: tick['x'])

        merged_tick_x_values = []
        if not potential_ticks_props:
            return None

        i = 0
        while i < len(potential_ticks_props):
            current_group_ticks_x = [potential_ticks_props[i]['x']]
            group_scan_idx = i

            for j in range(i + 1, len(potential_ticks_props)):
                if (potential_ticks_props[j]['x'] - potential_ticks_props[i]['x']) < params['max_tick_thickness_px']:
                    current_group_ticks_x.append(potential_ticks_props[j]['x'])
                    group_scan_idx = j
                else:
                    break

            merged_x = np.mean(current_group_ticks_x)
            merged_tick_x_values.append(merged_x)

            i = group_scan_idx + 1

        if len(merged_tick_x_values) < params['min_ticks_required']:
            print(f"Not enough merged ticks found: {len(merged_tick_x_values)} vs required {params['min_ticks_required']}")
            return None

        tick_x_coords = merged_tick_x_values

        num_ticks_for_1cm = params['num_ticks_for_1cm']
        candidate_1cm_distances = []

        if len(tick_x_coords) >= num_ticks_for_1cm:
            for i in range(len(tick_x_coords) - num_ticks_for_1cm + 1):
                current_tick_segment = tick_x_coords[i: i + num_ticks_for_1cm]
                span_start_x = current_tick_segment[0]
                span_end_x = current_tick_segment[-1]
                current_span_distance = span_end_x - span_start_x

                if current_span_distance <= 0:
                    continue

                internal_spacings = np.diff(current_tick_segment)

                if internal_spacings.size != (num_ticks_for_1cm - 1):
                    continue

                median_internal_spacing = np.median(internal_spacings)
                if median_internal_spacing <= 0:
                    continue

                std_dev_internal_spacing = np.std(internal_spacings)
                consistency_threshold = median_internal_spacing * params['consistency_threshold']

                if std_dev_internal_spacing < consistency_threshold:
                    candidate_1cm_distances.append(current_span_distance)

        if not candidate_1cm_distances:
            print("No consistent 1cm candidates found.")
            return None

        one_cm_distance = np.median(candidate_1cm_distances)

        if one_cm_distance <= 0:
            print("Calculated 1cm distance is zero or negative.")
            return None

        one_cm_text_info = find_1cm_text_location(roi, debug_path) # Pass roi to find_1cm_text_location for text detection

        return one_cm_distance

    except Exception as e:
        print(f"An error occurred: {e}")
        # Save the current state of roi for debugging if an error occurs
        if 'roi' in locals() and roi is not None:
            cv2.imwrite(debug_path, roi)
        return None


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