import cv2
import numpy as np
import os
import math

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
        "consistency_threshold": 0.7,
        "canny_low_threshold": 10,
        "canny_high_threshold": 40,
        "roi_height_fraction": 0.55
    }
    if museum_selection == "Iraq Museum (Sippar Library)":
        base_params.update({
            "hough_min_line_length": 15,
            "hough_max_line_gap": 30,
            "hough_threshold": 60,
            "tick_max_width": 20,
            "tick_min_width": 1,
            "tick_min_height": 30,
            "max_tick_thickness_px": 30,
            "min_ticks_required": 11,
            "num_ticks_for_1cm": 11,
            "consistency_threshold": 0.7,
            "canny_low_threshold": 5,
            "canny_high_threshold": 30,
            "roi_height_fraction": 0.60
        })
    return base_params

def find_ruler_text_location(roi, debug_path=None):
    if roi is None or roi.size == 0:
        return None
    if len(roi.shape) == 3 and roi.shape[2] == 3:
        roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    elif len(roi.shape) == 2:
        roi_gray = roi
    else:
        return None
    template_height = 40
    template_width = 80
    font_scale = 0.8
    thickness = 2
    ruler_texts = ["0 cm", "1 cm"]
    best_detection = None
    for text in ruler_texts:
        template = np.zeros((template_height, template_width), dtype=np.uint8)
        text_size, _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
        text_x = (template_width - text_size[0]) // 2
        text_y = (template_height + text_size[1]) // 2
        cv2.putText(template, text, (text_x, text_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, font_scale, 255, thickness, cv2.LINE_AA)
        methods = [cv2.TM_CCOEFF_NORMED, cv2.TM_CCORR_NORMED, cv2.TM_SQDIFF_NORMED]
        for method in methods:
            try:
                result = cv2.matchTemplate(roi_gray, template, method)
                if method == cv2.TM_SQDIFF_NORMED:
                    min_val, _, min_loc, _ = cv2.minMaxLoc(result)
                    confidence = 1.0 - min_val
                    match_loc = min_loc
                else:
                    _, max_val, _, max_loc = cv2.minMaxLoc(result)
                    confidence = max_val
                    match_loc = max_loc
                confidence_threshold = 0.6
                if confidence > confidence_threshold:
                    if best_detection is None or confidence > best_detection['confidence']:
                        text_center_x = match_loc[0] + template_width // 2
                        text_center_y = match_loc[1] + template_height // 2
                        best_detection = {
                            'location': (text_center_x, text_center_y),
                            'text': text,
                            'confidence': confidence,
                            'bbox': (match_loc[0], match_loc[1], template_width, template_height),
                            'method': method
                        }
            except cv2.error:
                continue
    return best_detection

def _extract_roi_around_text(roi, text_detection, expansion_factor=3):
    x, y, w, h = text_detection['bbox']
    expand_w = w * expansion_factor
    expand_h = h * expansion_factor
    new_x = max(0, x - expand_w // 2)
    new_y = max(0, y - expand_h // 2)
    new_w = min(roi.shape[1] - new_x, expand_w)
    new_h = min(roi.shape[0] - new_y, expand_h)
    return roi[int(new_y):int(new_y + new_h), int(new_x):int(new_x + new_w)]

def _calculate_text_distance(detection1, detection2):
    x1, y1 = detection1['location']
    x2, y2 = detection2['location']
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def detect_1cm_distance_iraq(image_path, museum_selection="Iraq Museum", roi_height_fraction=None):
    params = get_detection_parameters(museum_selection)
    if roi_height_fraction is not None:
        params['roi_height_fraction'] = roi_height_fraction

    image = cv2.imread(image_path)
    if image is None:
        return None

    height, width = image.shape[:2]
    roi_height = int(height * params['roi_height_fraction'])
    roi = image[height - roi_height:, :]

    # Try text-based detection first
    text_detection = find_ruler_text_location(roi)
    if text_detection and text_detection['text'] == "1 cm":
        roi_around_text = _extract_roi_around_text(roi, text_detection)
        zero_cm_detection = find_ruler_text_location(roi_around_text)
        if zero_cm_detection and zero_cm_detection['text'] == "0 cm":
            distance = _calculate_text_distance(text_detection, zero_cm_detection)
            if distance > 0:
                return distance

    # Fallback: line-based detection using all parameters
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, params['canny_low_threshold'], params['canny_high_threshold'])
    lines = cv2.HoughLinesP(
        edges, 1, np.pi/180,
        threshold=params['hough_threshold'],
        minLineLength=params['hough_min_line_length'],
        maxLineGap=params['hough_max_line_gap']
    )
    if lines is None:
        return None
    vertical_lines = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        line_width = abs(x2 - x1)
        line_height = abs(y2 - y1)
        if line_width < params['tick_min_width'] or line_width > params['tick_max_width']:
            continue
        if line_height < params['tick_min_height']:
            continue
        if x2 - x1 != 0:
            angle = abs(np.arctan((y2 - y1) / (x2 - x1)) * 180 / np.pi)
        else:
            angle = 90
        if 80 <= angle <= 90:
            avg_x = (x1 + x2) / 2.0
            vertical_lines.append(avg_x)
    if len(vertical_lines) < 2:
        return None
    vertical_lines.sort()
    # Merge lines that are close together (max_tick_thickness_px)
    merged_lines = []
    i = 0
    while i < len(vertical_lines):
        group = [vertical_lines[i]]
        j = i + 1
        while j < len(vertical_lines) and abs(vertical_lines[j] - vertical_lines[i]) < params['max_tick_thickness_px']:
            group.append(vertical_lines[j])
            j += 1
        merged_lines.append(np.mean(group))
        i = j
    if len(merged_lines) < params['min_ticks_required']:
        return None
    # Find 1cm segment using num_ticks_for_1cm and consistency_threshold
    num_ticks = params['num_ticks_for_1cm']
    candidate_1cm_distances = []
    for i in range(len(merged_lines) - num_ticks + 1):
        segment = merged_lines[i:i+num_ticks]
        span = segment[-1] - segment[0]
        if span <= 0:
            continue
        spacings = np.diff(segment)
        if len(spacings) != num_ticks - 1:
            continue
        median_spacing = np.median(spacings)
        if median_spacing <= 0:
            continue
        stddev = np.std(spacings)
        if stddev < median_spacing * params['consistency_threshold']:
            candidate_1cm_distances.append(span)
    if not candidate_1cm_distances:
        return None
    return float(np.median(candidate_1cm_distances))