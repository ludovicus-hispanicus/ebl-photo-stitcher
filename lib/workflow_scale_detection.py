import os
from workflow_imports import (
    ruler_detector, ruler_detector_iraq_museum, convert_raw_image_to_tiff,
    get_tablet_width_from_measurements, determine_pixels_per_cm_from_measurement,
    DEFAULT_BACKGROUND_DETECTION_COLOR_TOLERANCE
)

def detect_scale_from_ruler(ruler_for_scale_fp, subfolder_path_item, raw_ext_config, 
                          museum_selection, ruler_position, progress_callback=None):
    """
    Detect scale from ruler image using appropriate detector based on museum.
    
    Returns:
        tuple: (px_cm_val, cr2_conv_count, temp_file_created)
    """
    curr_scale_fp, is_temp_s_file = ruler_for_scale_fp, False
    cr2_conv_count = 0

    if curr_scale_fp.lower().endswith(raw_ext_config):
        tmp_s_fp = os.path.join(
            subfolder_path_item, 
            f"{os.path.splitext(os.path.basename(curr_scale_fp))[0]}_rawscale.tif"
        )
        convert_raw_image_to_tiff(curr_scale_fp, tmp_s_fp)
        curr_scale_fp, is_temp_s_file = tmp_s_fp, True
        cr2_conv_count = 1

    if museum_selection == "Iraq Museum":
        print(f"   Using Iraq Museum specific ruler detector for {os.path.basename(curr_scale_fp)}...")
        px_cm_val = ruler_detector_iraq_museum.detect_1cm_distance_iraq(curr_scale_fp)
        if px_cm_val is None or px_cm_val <= 0:
            raise ValueError("Iraq Museum ruler detection failed to return a valid pixels/cm value.")
        print(f"     Iraq Museum ruler detector returned px/cm: {px_cm_val}")
    else:
        px_cm_val = ruler_detector.estimate_pixels_per_centimeter_from_ruler(
            curr_scale_fp, ruler_position=ruler_position)

    if is_temp_s_file and os.path.exists(curr_scale_fp):
        os.remove(curr_scale_fp)
    
    return px_cm_val, cr2_conv_count

def get_scale_from_measurements(subfolder_path_item, measurements_dict, ruler_for_scale_fp, 
                              background_color_tolerance=None):
    """
    Get scale from measurements database.
    
    Returns:
        tuple: (px_cm_val, measurements_used)
    """
    if background_color_tolerance is None:
        background_color_tolerance = DEFAULT_BACKGROUND_DETECTION_COLOR_TOLERANCE
        
    tablet_width_cm = get_tablet_width_from_measurements(subfolder_path_item, measurements_dict)
    if tablet_width_cm is None or tablet_width_cm <= 0:
        return None, False
        
    try:
        px_cm_val = determine_pixels_per_cm_from_measurement(
            ruler_for_scale_fp,
            tablet_width_cm,
            should_extract_object=True,
            bg_color_tolerance=background_color_tolerance
        )
        print(f"   Using measurement from database: {tablet_width_cm} cm, calculated {px_cm_val:.2f} px/cm")
        return px_cm_val, True
    except Exception as e:
        print(f"   Error using measurement from database: {e}")
        return None, False

def determine_pixels_per_cm(subfolder_path_item, subfolder_name_item, ruler_for_scale_fp, 
                           raw_ext_config, museum_selection, ruler_position,
                           use_measurements_from_database, measurements_dict, 
                           background_color_tolerance=None):
    """
    Determine pixels per cm using measurements or ruler detection.
    
    Returns:
        tuple: (px_cm_val, measurements_used, cr2_conv_count)
    """
    px_cm_val = None
    measurements_used = False
    cr2_conv_count = 0

    if use_measurements_from_database and measurements_dict:
        px_cm_val, measurements_used = get_scale_from_measurements(
            subfolder_path_item, measurements_dict, ruler_for_scale_fp, background_color_tolerance)

    if px_cm_val is None:
        try:
            px_cm_val, cr2_conv_count = detect_scale_from_ruler(
                ruler_for_scale_fp, subfolder_path_item, raw_ext_config,
                museum_selection, ruler_position)
        except Exception as e:
            print(f"   Error during ruler scale detection: {e}")

            if not measurements_used and measurements_dict:
                px_cm_val, measurements_used = get_scale_from_measurements(
                    subfolder_path_item, measurements_dict, ruler_for_scale_fp, background_color_tolerance)
                if px_cm_val is not None:
                    print(f"   FALLBACK: Using measurement from database")
                else:
                    print(f"   No measurement found in database for this tablet")
    
    return px_cm_val, measurements_used, cr2_conv_count