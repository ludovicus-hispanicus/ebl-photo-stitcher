import os
import sys
import cv2
import tkinter as tk
import re
import traceback
import time

from workflow_imports import (
    organize_project_subfolders, determine_ruler_image_for_scaling,
    process_tablet_subfolder, get_extended_intermediate_suffixes,
    MUSEUM_CONFIGS, DEFAULT_BACKGROUND_DETECTION_COLOR_TOLERANCE,
    convert_raw_image_to_tiff
)
from workflow_scale_detection import determine_pixels_per_cm
from workflow_object_processing import (
    extract_object_and_detect_background, extract_ruler_contour,
    process_other_views, process_intermediate_images
)
from workflow_ruler_generation import (
    select_ruler_template, generate_digital_ruler, prepare_other_views_list
)
from workflow_cleanup import cleanup_intermediate_files, cleanup_temp_files

def run_complete_image_processing_workflow(
    source_folder_path,
    ruler_position,
    photographer_name,
    object_extraction_bg_mode,
    add_logo,
    logo_path,
    raw_ext_config,
    image_extensions_config,
    ruler_template_1cm_asset_path,
    ruler_template_2cm_asset_path,
    ruler_template_5cm_asset_path,
    view_file_patterns_config,
    temp_ruler_filename,
    object_artifact_suffix_config,
    progress_callback,
    finished_callback,
    museum_selection="British Museum",
    app_root_window=None,
    background_color_tolerance=None,
    use_measurements_from_database=False,
    measurements_dict=None,
    gradient_width_fraction=0.5
):
    """Main workflow orchestration function."""
    start_time = time.time()
    total_objects_processed = 0
    failed_objects = []
    
    if background_color_tolerance is None:
        background_color_tolerance = DEFAULT_BACKGROUND_DETECTION_COLOR_TOLERANCE

    temp_extracted_ruler_filename_config = temp_ruler_filename
    
    print(f"Workflow started for folder: {source_folder_path}")
    progress_callback(2)

    image_extensions_tuple = tuple(ext.lower() for ext in image_extensions_config) + \
        ((raw_ext_config.lower(),) if isinstance(raw_ext_config, str)
         else tuple(r_ext.lower() for r_ext in raw_ext_config))

    try:
        processed_subfolders = organize_project_subfolders(
            source_folder_path, image_extensions_tuple, lambda x: [])
    except Exception as e_org:
        print(f"   Workflow halted due to error during file organization: {e_org}")
        progress_callback(100)
        finished_callback()
        return

    num_folders = len(processed_subfolders)
    print(f"File organization complete. Targeting {num_folders} subfolder(s).")
    progress_callback(10)
    print("-" * 50)

    if num_folders == 0:
        print("No image sets to process.")
        progress_callback(100)
        finished_callback()
        return

    total_ok, total_err, cr2_conv_total = 0, 0, 0
    prog_per_folder = 85.0 / num_folders if num_folders > 0 else 0

    for i, subfolder_path_item in enumerate(processed_subfolders):
        subfolder_name_item = os.path.basename(subfolder_path_item)
        print(f"Processing Subfolder {i+1}/{num_folders}: {subfolder_name_item}")

        current_prog_base = 10 + i * prog_per_folder
        progress_callback(current_prog_base)

        try:

            result = process_single_subfolder(
                subfolder_path_item, subfolder_name_item, image_extensions_tuple,
                view_file_patterns_config, object_artifact_suffix_config,
                temp_extracted_ruler_filename_config, raw_ext_config,
                ruler_position, museum_selection, use_measurements_from_database,
                measurements_dict, background_color_tolerance, object_extraction_bg_mode,
                ruler_template_1cm_asset_path, ruler_template_2cm_asset_path,
                ruler_template_5cm_asset_path, gradient_width_fraction,
                source_folder_path, photographer_name, add_logo, logo_path,
                current_prog_base, prog_per_folder, progress_callback
            )
            
            if result['success']:
                total_ok += 1
                cr2_conv_total += result['cr2_conversions']
            else:
                failed_objects.append(subfolder_name_item)
                total_err += 1
                
        except Exception as e:
            print(f"   ERROR processing set '{subfolder_name_item}': {e}")
            traceback.print_exc()
            failed_objects.append(subfolder_name_item)
            total_err += 1

    print_final_statistics(start_time, total_ok, total_err, cr2_conv_total, failed_objects)

    if total_ok > 0:
        cleanup_intermediate_files(processed_subfolders, object_artifact_suffix_config)

    progress_callback(100)
    finished_callback()

def process_single_subfolder(subfolder_path_item, subfolder_name_item, image_extensions_tuple,
                           view_file_patterns_config, object_artifact_suffix_config,
                           temp_extracted_ruler_filename_config, raw_ext_config,
                           ruler_position, museum_selection, use_measurements_from_database,
                           measurements_dict, background_color_tolerance, object_extraction_bg_mode,
                           ruler_template_1cm_asset_path, ruler_template_2cm_asset_path,
                           ruler_template_5cm_asset_path, gradient_width_fraction,
                           source_folder_path, photographer_name, add_logo, logo_path,
                           current_prog_base, prog_per_folder, progress_callback):
    """Process a single subfolder."""
    
    result = {'success': False, 'cr2_conversions': 0}

    sub_steps_alloc = {
        "layout_dialog": 0.05, "scale": 0.15, "ruler_art": 0.1, 
        "ruler_part_extract": 0.05, "digital_ruler_choice": 0.05, 
        "digital_ruler_resize": 0.1, "other_obj": 0.25, "stitch": 0.25
    }
    accumulated_sub_progress = 0.0

    all_files_in_subfolder = [f for f in os.listdir(subfolder_path_item) 
                             if os.path.isfile(os.path.join(subfolder_path_item, f))]

    ruler_for_scale_fp, orig_views_fps = find_ruler_and_views(
        subfolder_path_item, subfolder_name_item, all_files_in_subfolder,
        image_extensions_tuple, view_file_patterns_config, object_artifact_suffix_config
    )

    if not ruler_for_scale_fp:
        print(f"   No ruler image found for {subfolder_name_item}. Skip.")
        return result

    accumulated_sub_progress += sub_steps_alloc["layout_dialog"] * prog_per_folder
    progress_callback(current_prog_base + accumulated_sub_progress)

    px_cm_val, measurements_used, cr2_conv_scale = determine_pixels_per_cm(
        subfolder_path_item, subfolder_name_item, ruler_for_scale_fp,
        raw_ext_config, museum_selection, ruler_position,
        use_measurements_from_database, measurements_dict, background_color_tolerance
    )
    result['cr2_conversions'] += cr2_conv_scale

    if px_cm_val is None:
        print(f"   ERROR: Could not determine ruler scale for {subfolder_name_item}. Skip.")
        return result

    accumulated_sub_progress += sub_steps_alloc["scale"] * prog_per_folder
    progress_callback(current_prog_base + accumulated_sub_progress)

    path_ruler_extract_img, tmp_ruler_extract_conv_file = prepare_ruler_image(
        ruler_for_scale_fp, subfolder_path_item, raw_ext_config)
    
    if tmp_ruler_extract_conv_file:
        result['cr2_conversions'] += 1

    art_fp, art_cont, detected_bg_color, output_bg_color = extract_object_and_detect_background(
        path_ruler_extract_img, object_extraction_bg_mode,
        object_artifact_suffix_config, museum_selection
    )

    accumulated_sub_progress += sub_steps_alloc["ruler_art"] * prog_per_folder
    progress_callback(current_prog_base + accumulated_sub_progress)

    tmp_iso_ruler_fp = extract_ruler_contour(
        path_ruler_extract_img, detected_bg_color, art_cont,
        background_color_tolerance, temp_extracted_ruler_filename_config,
        subfolder_path_item
    )

    cleanup_temp_files(tmp_ruler_extract_conv_file)

    accumulated_sub_progress += sub_steps_alloc["ruler_part_extract"] * prog_per_folder
    progress_callback(current_prog_base + accumulated_sub_progress)

    chosen_ruler_tpl, custom_ruler_size_cm = select_ruler_template(
        museum_selection, art_fp, px_cm_val, ruler_template_1cm_asset_path,
        ruler_template_2cm_asset_path, ruler_template_5cm_asset_path
    )

    accumulated_sub_progress += sub_steps_alloc["digital_ruler_choice"] * prog_per_folder
    progress_callback(current_prog_base + accumulated_sub_progress)

    generate_digital_ruler(px_cm_val, chosen_ruler_tpl, subfolder_name_item,
                          subfolder_path_item, custom_ruler_size_cm)

    cleanup_temp_files(tmp_iso_ruler_fp)

    accumulated_sub_progress += sub_steps_alloc["digital_ruler_resize"] * prog_per_folder
    progress_callback(current_prog_base + accumulated_sub_progress)

    other_views_to_process_list = prepare_other_views_list(
        None, orig_views_fps, ruler_for_scale_fp
    )

    cr2_conv_other = process_other_views(
        other_views_to_process_list, subfolder_path_item, raw_ext_config,
        object_extraction_bg_mode, output_bg_color,
        object_artifact_suffix_config, museum_selection
    )
    result['cr2_conversions'] += cr2_conv_other

    cr2_conv_intermediate = process_intermediate_images(
        all_files_in_subfolder, subfolder_path_item, subfolder_name_item,
        image_extensions_tuple, object_artifact_suffix_config,
        other_views_to_process_list, ruler_for_scale_fp, raw_ext_config,
        object_extraction_bg_mode, output_bg_color, museum_selection,
        gradient_width_fraction
    )
    result['cr2_conversions'] += cr2_conv_intermediate

    accumulated_sub_progress += sub_steps_alloc["other_obj"] * prog_per_folder

    stitched_output_bg_color = MUSEUM_CONFIGS.get(
        museum_selection, {}).get("background_color", (0, 0, 0))
    if museum_selection == "British Museum":
        stitched_output_bg_color = output_bg_color

    process_tablet_subfolder(
        subfolder_path=subfolder_path_item,
        ruler_position=ruler_position,
        main_input_folder_path=source_folder_path,
        output_base_name=subfolder_name_item,
        pixels_per_cm=px_cm_val,
        photographer_name=photographer_name,
        ruler_image_for_scale_path=ruler_for_scale_fp,
        add_logo=add_logo,
        logo_path=logo_path if add_logo else None,
        object_extraction_background_mode=object_extraction_bg_mode,
        stitched_bg_color=stitched_output_bg_color,
        custom_layout=None
    )

    result['success'] = True
    return result

def find_ruler_and_views(subfolder_path_item, subfolder_name_item, all_files_in_subfolder,
                        image_extensions_tuple, view_file_patterns_config, object_artifact_suffix_config):
    """Find ruler image and identify other views."""
    
    image_files_for_layout = []
    for f_name in all_files_in_subfolder:
        if f_name.lower().endswith(image_extensions_tuple):
            image_files_for_layout.append(os.path.join(subfolder_path_item, f_name))

    intermediate_suffix_patterns = get_extended_intermediate_suffixes()
    if len(image_files_for_layout) > 6:
        print(f"   Subfolder {subfolder_name_item} has {len(image_files_for_layout)} images.")
        print(f"   Using automatic suffix detection for intermediate images (looking for: {list(intermediate_suffix_patterns.keys())})")
        print(f"   Images exceeding 6 without suffix patterns will be ignored.")

    view_original_suffix_patterns_config = view_file_patterns_config if view_file_patterns_config else {}
    
    rel_count = 0
    pr02_reverse, pr03_top, pr04_bottom = None, None, None
    orig_views_fps = {}

    for fn in all_files_in_subfolder:
        fn_low = fn.lower()
        full_fp = os.path.join(subfolder_path_item, fn)
        
        if fn_low.endswith(image_extensions_tuple):
            if (object_artifact_suffix_config not in fn and 
                "_scaled_ruler." not in fn and 
                "temp_isolated_ruler" not in fn and 
                not fn_low.endswith("_rawscale.tif")):
                rel_count += 1

            if "reverse" in view_original_suffix_patterns_config and view_original_suffix_patterns_config["reverse"] in fn_low:
                pr02_reverse = full_fp
            if "top" in view_original_suffix_patterns_config and view_original_suffix_patterns_config["top"] in fn_low:
                pr03_top = full_fp
            if "bottom" in view_original_suffix_patterns_config and view_original_suffix_patterns_config["bottom"] in fn_low:
                pr04_bottom = full_fp

            for vk, sp_pattern_suffix in view_original_suffix_patterns_config.items():
                if not sp_pattern_suffix:
                    continue
                core_pattern = os.path.splitext(sp_pattern_suffix)[0]
                expected_prefix_in_filename = subfolder_name_item + core_pattern

                if fn_low.startswith(expected_prefix_in_filename.lower()):
                    orig_views_fps[vk] = full_fp

    ruler_for_scale_fp = determine_ruler_image_for_scaling(
        None, orig_views_fps, image_files_for_layout,
        pr02_reverse, pr03_top, pr04_bottom, rel_count
    )

    return ruler_for_scale_fp, orig_views_fps

def prepare_ruler_image(ruler_for_scale_fp, subfolder_path_item, raw_ext_config):
    """Prepare ruler image, converting from RAW if needed."""
    path_ruler_extract_img, tmp_ruler_extract_conv_file = ruler_for_scale_fp, None
    
    if path_ruler_extract_img.lower().endswith(raw_ext_config):
        tmp_ruler_extract_conv_file = os.path.join(
            subfolder_path_item, 
            f"{os.path.splitext(os.path.basename(path_ruler_extract_img))[0]}.tif"
        )
        if not os.path.exists(tmp_ruler_extract_conv_file):
            convert_raw_image_to_tiff(path_ruler_extract_img, tmp_ruler_extract_conv_file)
        path_ruler_extract_img = tmp_ruler_extract_conv_file
    
    return path_ruler_extract_img, tmp_ruler_extract_conv_file

def print_final_statistics(start_time, total_ok, total_err, cr2_conv_total, failed_objects):
    """Print final processing statistics."""
    print(f"\n--- Processing Complete ---\nRAW converted: {cr2_conv_total}\nSets OK: {total_ok}\nSets Error: {total_err}\n")

    end_time = time.time()
    elapsed_seconds = end_time - start_time
    minutes, seconds = divmod(elapsed_seconds, 60)

    avg_seconds = elapsed_seconds / total_ok if total_ok > 0 else 0
    avg_minutes, avg_seconds = divmod(avg_seconds, 60)

    print(f"\n--- Processing Statistics ---")
    print(f"Time elapsed: {int(minutes):02d} m {int(seconds):02d} s")
    print(f"Objects processed: {total_ok}")

    if total_err > 0:
        cleaned_failed_objects = []
        for obj in failed_objects:
            base_name = re.sub(r'_\d+$', '', obj)
            if base_name not in cleaned_failed_objects:
                cleaned_failed_objects.append(base_name)
        
        print(f"Objects that could not be processed ({total_err}):")
        for obj_name in cleaned_failed_objects:
            print(f"  - {obj_name}")
    
    print(f"Average time per object: {int(avg_minutes):02d} m {int(avg_seconds):02d} s")
