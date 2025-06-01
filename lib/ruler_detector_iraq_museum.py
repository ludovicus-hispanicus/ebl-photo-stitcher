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


def detect_1cm_distance_iraq(image_path):
    """
    Detects the pixel distance corresponding to 1 cm on a ruler in an image,
    specifically for the Iraq Museum style ruler (lower-left corner, vertical ticks, "1 cm" text).

    Args:
        image_path (str): Path to the image containing the ruler.

    Returns:
        float: Pixel distance representing 1 cm, or None if not found.
    """
    debug_filename = os.path.splitext(os.path.basename(image_path))[
        0] + "_debugging.jpg"
    debug_path = os.path.join(os.path.dirname(image_path), debug_filename)

    try:

        img = cv2.imread(image_path)
        if img is None:
            print(f"Error: Could not load image at {image_path}")
            return None
        height, width, _ = img.shape

        roi_width = width // 3
        roi_height = height // 2
        roi_x = 0
        roi_y = height - roi_height
        initial_roi = img[roi_y:height, roi_x:roi_x + roi_width]

        roi = initial_roi

        roi_temp_path = os.path.join(os.path.dirname(image_path), "_temp_roi.jpg")
        cv2.imwrite(roi_temp_path, roi)

        try:

            print("Applying AI-based background removal...")
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
                print("AI background removal applied successfully")
            else:
                print("Warning: Could not load AI-processed image, using original ROI")

            if os.path.exists(roi_temp_path):
                os.remove(roi_temp_path)
            if os.path.exists(bg_removed_path):
                os.remove(bg_removed_path)

        except Exception as e:
            print(f"AI background removal failed: {e}, using original ROI")

            if os.path.exists(roi_temp_path):
                os.remove(roi_temp_path)

        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blurred_roi = cv2.GaussianBlur(gray_roi, (3, 3), 0)

        contrast_factor = 10
        lookup_table = np.array([
            255 / (1 + math.exp(-contrast_factor * (i - 128) / 255))
            for i in np.arange(0, 256)
        ]).astype("uint8")
        linear_contrast_roi = cv2.LUT(blurred_roi, lookup_table)
        height, width = linear_contrast_roi.shape[:2]
        left_margin = int(width * 0.10)
        right_margin = int(width * 0.90)
        bottom_margin = int(height * 0.50)
        top_margin = int(height * 0.10)

        trimmed_roi = linear_contrast_roi[top_margin:bottom_margin,
                                          left_margin:right_margin]

        alpha_contrast = 1.0
        beta_brightness = 0
        contrast_adjusted_roi = cv2.convertScaleAbs(
            trimmed_roi, alpha=alpha_contrast, beta=beta_brightness)

        cv2.imwrite(os.path.join(os.path.dirname(image_path),
                    "_contrast.jpg"), contrast_adjusted_roi)

        edges_roi = cv2.Canny(contrast_adjusted_roi, 40, 60)

        lines_roi = cv2.HoughLinesP(edges_roi, 1, np.pi / 180,
                                    60, minLineLength=30, maxLineGap=10)

        if lines_roi is None or len(lines_roi) < 2:
            print("Error: Could not detect enough lines in the ROI.")
            cv2.imwrite(debug_path, roi)
            return None

        potential_ticks_props = []
        for line in lines_roi:
            x1, y1, x2, y2 = line[0]
            line_height = abs(y2 - y1)
            line_width = abs(x2 - x1)

            if line_width < 20 and line_height > 20:
                avg_x = (x1 + x2) / 2.0
                potential_ticks_props.append({'x': avg_x, 'y1': min(
                    y1, y2), 'y2': max(y1, y2), 'h': line_height})

        if not potential_ticks_props:
            print("Error: No potential tick lines found after initial filtering.")
            cv2.imwrite(debug_path, roi)
            return None

        potential_ticks_props.sort(key=lambda tick: tick['x'])

        merged_tick_x_values = []
        if not potential_ticks_props:
            return None

        MAX_TICK_THICKNESS_PX = 30

        i = 0
        while i < len(potential_ticks_props):
            current_group_ticks_x = [potential_ticks_props[i]['x']]
            group_scan_idx = i

            for j in range(i + 1, len(potential_ticks_props)):
                if (potential_ticks_props[j]['x'] - potential_ticks_props[i]['x']) < MAX_TICK_THICKNESS_PX:
                    current_group_ticks_x.append(potential_ticks_props[j]['x'])
                    group_scan_idx = j
                else:
                    break

            merged_x = np.mean(current_group_ticks_x)
            merged_tick_x_values.append(merged_x)

            i = group_scan_idx + 1

        if len(merged_tick_x_values) < 11:
            print(
                f"Error: Not enough merged tick marks found ({len(merged_tick_x_values)}). Need at least 11.")
            cv2.imwrite(debug_path, roi)
            return None

        tick_x_coords = merged_tick_x_values

        num_ticks_for_1cm = 11
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
                relative_std_dev_threshold = 0.6
                consistency_threshold = median_internal_spacing * relative_std_dev_threshold

                if std_dev_internal_spacing < consistency_threshold:
                    candidate_1cm_distances.append(current_span_distance)

        if not candidate_1cm_distances:
            print("Error: Could not find any suitable 1cm segments after consistency checks.")
            cv2.imwrite(debug_path, roi)
            return None

        one_cm_distance = np.median(candidate_1cm_distances)

        if one_cm_distance <= 0:
            print(
                f"Error: Calculated 1cm distance ({one_cm_distance:.2f}px) is not positive.")
            cv2.imwrite(debug_path, roi)
            return None

        one_cm_text_info = find_1cm_text_location(roi)
        if one_cm_text_info is not None:

            pass
        else:

            pass

        return one_cm_distance

    except Exception as e:
        print(f"An error occurred in detect_1cm_distance_iraq: {e}")
        cv2.imwrite(debug_path, roi)
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
        cv2.imwrite(debug_path, roi)
        return None

    if len(roi.shape) == 3 and roi.shape[2] == 3:
        roi_gray_for_match = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    elif len(roi.shape) == 2:
        roi_gray_for_match = roi
    else:
        print(f"Error: ROI has unexpected shape {roi.shape} for template matching.")
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
