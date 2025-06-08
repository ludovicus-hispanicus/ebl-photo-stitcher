import cv2
import numpy as np
import os
import time
from PIL import Image
from object_extractor_rembg import _ensure_local_model, remove
from object_extractor import DEFAULT_BACKGROUND_DETECTION_COLOR_TOLERANCE

def is_likely_ruler_object(contour_mask, image_shape, ruler_position="bottom"):
    """
    Determine if a detected object is likely a ruler based on shape and position.
    
    Args:
        contour_mask: Binary mask of the object
        image_shape: Shape of the original image (height, width)
        ruler_position: Expected ruler position
        
    Returns:
        bool: True if object is likely a ruler
    """

    y_indices, x_indices = np.where(contour_mask > 0)
    if len(y_indices) == 0:
        return False
        
    x_min, x_max = np.min(x_indices), np.max(x_indices)
    y_min, y_max = np.min(y_indices), np.max(y_indices)
    
    obj_width = x_max - x_min + 1
    obj_height = y_max - y_min + 1
    img_height, img_width = image_shape[:2]

    aspect_ratio = max(obj_width / obj_height, obj_height / obj_width)
    if aspect_ratio < 2.5:  # Not elongated enough to be a ruler
        return False

    obj_area = np.sum(contour_mask > 0)
    img_area = img_height * img_width
    area_fraction = obj_area / img_area

    if area_fraction > 0.3:  # Too large to be a ruler
        return False

    center_x = (x_min + x_max) / 2
    center_y = (y_min + y_max) / 2
    
    if ruler_position == "bottom":

        return center_y > img_height * 0.6
    elif ruler_position == "top":

        return center_y < img_height * 0.4
    elif ruler_position == "left":

        return center_x < img_width * 0.4
    elif ruler_position == "right":

        return center_x > img_width * 0.6
    
    return False

def test_object_for_ruler_patterns(object_mask, original_image, ruler_position="bottom", museum_selection="British Museum"):
    """
    Test if an object contains ruler patterns using existing detection methods.
    
    Args:
        object_mask: Binary mask of the object
        original_image: Original image array
        ruler_position: Expected ruler position
        museum_selection: Museum selection for appropriate detector
        
    Returns:
        bool: True if ruler patterns detected
    """
    try:

        y_indices, x_indices = np.where(object_mask > 0)
        if len(y_indices) == 0:
            return False
            
        x_min, x_max = np.min(x_indices), np.max(x_indices)
        y_min, y_max = np.min(y_indices), np.max(y_indices)

        padding = 10
        x_min = max(0, x_min - padding)
        y_min = max(0, y_min - padding)
        x_max = min(original_image.shape[1], x_max + padding)
        y_max = min(original_image.shape[0], y_max + padding)

        object_region = original_image[y_min:y_max, x_min:x_max]

        temp_path = "temp_ruler_test.tif"
        cv2.imwrite(temp_path, object_region)

        try:
            if museum_selection == "Iraq Museum":
                from ruler_detector_iraq_museum import detect_1cm_distance_iraq
                px_cm = detect_1cm_distance_iraq(temp_path)
                is_ruler = (px_cm is not None)
            else:
                from ruler_detector import estimate_pixels_per_centimeter_from_ruler
                px_cm = estimate_pixels_per_centimeter_from_ruler(temp_path, ruler_position=ruler_position)
                is_ruler = (px_cm is not None and px_cm > 0)
        except:
            is_ruler = False

        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        return is_ruler
        
    except Exception as e:
        print(f"    Warning: Error testing object for ruler patterns: {e}")
        return False

def extract_and_save_multiple_objects(
    input_image_filepath,
    source_background_detection_mode="auto",
    output_image_background_color=(0, 0, 0),
    feather_radius_px=10,
    output_filename_suffix="_object.tif",
    min_object_area_as_image_fraction=0.01,
    object_contour_smoothing_kernel_size=3,
    museum_selection=None,
    ruler_position="bottom"
):
    """
    Extract multiple objects from an image, automatically excluding rulers.
    
    Args:
        input_image_filepath: Path to the input image
        output_image_background_color: BGR tuple for background color (OpenCV format)
        output_filename_suffix: Suffix for the output filename
        ruler_position: Expected ruler position for exclusion
        
    Returns:
        List of tuples: [(output_filepath, dummy_contour), ...] for each non-ruler object
    """
    print(f"  Extracting multiple objects from: {os.path.basename(input_image_filepath)} using rembg")
    start_time = time.time()

    if not _ensure_local_model():
        raise RuntimeError("U2NET model is required but could not be downloaded or found.")

    try:
        input_img = Image.open(input_image_filepath)
        if input_img.mode != 'RGB':
            input_img = input_img.convert('RGB')
    except Exception as e:
        raise FileNotFoundError(f"Could not load image for object extraction: {input_image_filepath} - {e}")

    output_img = remove(input_img)

    alpha = np.array(output_img.getchannel('A'))
    custom_alpha_tolerance = DEFAULT_BACKGROUND_DETECTION_COLOR_TOLERANCE * 2
    binary_mask = (alpha > custom_alpha_tolerance).astype(np.uint8) * 255

    kernel = np.ones((3, 3), np.uint8)
    binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel)

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary_mask, connectivity=8)
    
    if num_labels <= 1:
        print("    Warning: No objects detected in the image!")
        return []

    print(f"    Found {num_labels-1} separate objects")

    valid_objects = []
    original_cv_img = cv2.imread(input_image_filepath)
    
    for i in range(1, num_labels):  # Skip background (label 0)
        area = stats[i, cv2.CC_STAT_AREA]

        total_pixels = output_img.width * output_img.height
        if area < (total_pixels * min_object_area_as_image_fraction):
            print(f"    Skipping object {i}: too small ({area} pixels)")
            continue

        object_mask = (labels == i).astype(np.uint8) * 255

        is_ruler_by_shape = is_likely_ruler_object(object_mask, original_cv_img.shape, ruler_position)
        is_ruler_by_pattern = False
        
        if is_ruler_by_shape:

            is_ruler_by_pattern = test_object_for_ruler_patterns(
                object_mask, original_cv_img, ruler_position, museum_selection)
        
        is_ruler = is_ruler_by_shape or is_ruler_by_pattern
        
        if is_ruler:
            print(f"    Skipping object {i}: identified as ruler")
            continue
            
        print(f"    Object {i}: valid artifact ({area} pixels)")
        valid_objects.append((i, area, object_mask))
    
    if not valid_objects:
        print("    Warning: No valid non-ruler objects found!")
        return []

    valid_objects.sort(key=lambda x: x[1], reverse=True)

    saved_objects = []
    bg_color_rgb = (output_image_background_color[2], output_image_background_color[1], output_image_background_color[0])
    
    for obj_idx, (label, area, object_mask) in enumerate(valid_objects):

        selected_mask_pil = Image.fromarray(object_mask)

        filtered_output = Image.new('RGBA', output_img.size, (0, 0, 0, 0))
        filtered_output.paste(output_img, (0, 0), selected_mask_pil)

        y_indices, x_indices = np.where(object_mask > 0)
        if len(y_indices) == 0:
            continue
            
        x_min, x_max = np.min(x_indices), np.max(x_indices)
        y_min, y_max = np.min(y_indices), np.max(y_indices)

        padding = 10
        x_min = max(0, x_min - padding)
        y_min = max(0, y_min - padding)
        x_max = min(output_img.width, x_max + padding)
        y_max = min(output_img.height, y_max + padding)
        
        bbox = (x_min, y_min, x_max, y_max)

        cropped_img = filtered_output.crop(bbox)

        bg_img = Image.new('RGB', cropped_img.size, bg_color_rgb)
        bg_img.paste(cropped_img, (0, 0), cropped_img)

        base_filepath, ext = os.path.splitext(input_image_filepath)
        if len(valid_objects) == 1:

            output_image_filepath = f"{base_filepath}{output_filename_suffix}"
        else:

            output_image_filepath = f"{base_filepath}_{obj_idx+1:02d}{output_filename_suffix}"
        
        try:
            bg_img.save(output_image_filepath)
            print(f"    Successfully saved object {obj_idx+1}: {os.path.basename(output_image_filepath)}")

            dummy_contour = np.array([[[0, 0]], [[0, 1]], [[1, 1]], [[1, 0]]], dtype=np.int32)
            saved_objects.append((output_image_filepath, dummy_contour))
            
        except Exception as e:
            print(f"    Error saving object {obj_idx+1}: {e}")
            continue
    
    elapsed = time.time() - start_time
    print(f"    Multi-object extraction complete: {len(saved_objects)} objects saved (took {elapsed:.2f}s)")
    
    return saved_objects