import os
import cv2
from workflow_imports import resize_ruler
from resize_ruler import resize_and_save_ruler_template

def select_ruler_template(museum_selection, art_fp, px_cm_val, ruler_template_1cm_asset_path,
                          ruler_template_2cm_asset_path, ruler_template_5cm_asset_path):
    """
    Select appropriate ruler template based on museum and artifact size.

    Returns:
        tuple: (chosen_ruler_tpl, custom_ruler_size_cm)
    """
    chosen_ruler_tpl = ruler_template_5cm_asset_path
    custom_ruler_size_cm = None

    if museum_selection == "British Museum":
        art_img_chk = cv2.imread(art_fp)
        if art_img_chk is not None and px_cm_val > 0:
            art_w_cm_val = art_img_chk.shape[1] / px_cm_val
            if art_w_cm_val > 0:
                t1 = resize_ruler.RULER_TARGET_PHYSICAL_WIDTHS_CM["1cm"]
                t2 = resize_ruler.RULER_TARGET_PHYSICAL_WIDTHS_CM["2cm"]
                if art_w_cm_val < t1:
                    chosen_ruler_tpl = ruler_template_1cm_asset_path
                elif art_w_cm_val < t2:
                    chosen_ruler_tpl = ruler_template_2cm_asset_path

    elif museum_selection == "Iraq Museum":
        chosen_ruler_tpl = os.path.join(
            os.path.dirname(ruler_template_1cm_asset_path), "IM_photo_ruler.svg")
        custom_ruler_size_cm = 4.599
        print(f"Using Iraq Museum ruler: {chosen_ruler_tpl}")

    elif museum_selection == "eBL Ruler (CBS)":
        chosen_ruler_tpl = os.path.join(
            os.path.dirname(ruler_template_1cm_asset_path), "General_eBL_photo_ruler.svg")
        custom_ruler_size_cm = 4.317
        print(f"Using eBL Ruler (CBS): {chosen_ruler_tpl}")

    elif museum_selection == "Non-eBL Ruler (VAM)":
        chosen_ruler_tpl = os.path.join(
            os.path.dirname(ruler_template_1cm_asset_path), "General_External_photo_ruler.svg")
        custom_ruler_size_cm = 3.248
        print(f"Using Non-eBL Ruler (VAM): {chosen_ruler_tpl}")

    return chosen_ruler_tpl, custom_ruler_size_cm


def generate_digital_ruler(px_cm_val, chosen_ruler_tpl, subfolder_name_item,
                           subfolder_path_item, custom_ruler_size_cm=None):
    """
    Generate and save the digital ruler template.

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        resize_and_save_ruler_template(
            px_cm_val,
            chosen_ruler_tpl,
            subfolder_name_item,
            subfolder_path_item,
            custom_ruler_size_cm=custom_ruler_size_cm
        )
        print(
            f"    Successfully generated/resized digital ruler: {chosen_ruler_tpl} for {subfolder_name_item}.")
        return True
    except Exception as e_ruler_gen:
        print(f"    ERROR during digital ruler generation/resizing: {e_ruler_gen}")
        return False


def prepare_other_views_list(custom_layout_config, orig_views_fps, ruler_for_scale_fp):
    """
    Prepare list of other views to process (excluding the ruler image).

    Returns:
        list: List of file paths to process
    """
    other_views_to_process_list = []

    if custom_layout_config:
        all_custom_assigned_paths = set()
        for key, value in custom_layout_config.items():
            if isinstance(value, str) and value:
                all_custom_assigned_paths.add(value)
            elif isinstance(value, list):
                for item_path in value:
                    if item_path:
                        all_custom_assigned_paths.add(item_path)

        other_views_to_process_list = [
            p for p in all_custom_assigned_paths if p != ruler_for_scale_fp]
    else:
        other_views_to_process_list = [
            fp_other for fp_other in orig_views_fps.values() if fp_other != ruler_for_scale_fp]

    return other_views_to_process_list
