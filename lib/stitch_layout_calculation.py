"""
Core layout calculation logic for stitching tablet images.
"""
import cv2
import numpy as np

try:
    from stitch_config import (
        STITCH_VIEW_GAP_PX,
        STITCH_RULER_PADDING_PX
    )
    from stitch_layout_utils import get_image_dimension
    from stitch_intermediates_manager import group_intermediate_images, calculate_row_widths
    from stitch_image_processing import resize_tablet_views_for_layout, create_rotated_images
except ImportError as e:
    print(f"FATAL ERROR: stitch_layout_calculation.py cannot import: {e}")
    STITCH_VIEW_GAP_PX = 10
    STITCH_RULER_PADDING_PX = 20

    def get_image_dimension(*args, **kwargs): return 0
    def group_intermediate_images(*args, **kwargs): return {}
    def calculate_row_widths(*args, **kwargs): return 0, 0, []
    def resize_tablet_views_for_layout(*args, **kwargs): return {}
    def create_rotated_images(*args, **kwargs): return {}


def calculate_stitching_layout(images_dict, view_gap_px=STITCH_VIEW_GAP_PX, ruler_padding_px=STITCH_RULER_PADDING_PX, custom_layout=None, blend_overlap_px=0):
    """
    Calculate the canvas dimensions and coordinates for placing each image or blended sequence.

    Args:
        images_dict: Dictionary of images to stitch
        view_gap_px: Gap between views in pixels
        ruler_padding_px: Padding above ruler in pixels
        custom_layout: Custom layout configuration
        blend_overlap_px: Overlap for blending sequences

    Returns:
        Tuple of (canvas_width, canvas_height, coordinates_dict, modified_images_dict)
    """

    standard_keys = ["obverse", "reverse", "top", "bottom"]

    if len(images_dict) == 4 and not any(key in standard_keys for key in images_dict.keys()):
        print("      Layout: Found exactly 4 images without standard naming. Assigning as obverse, reverse, top, bottom.")

        keys = list(images_dict.keys())
        standard_dict = {}

        for i, std_key in enumerate(standard_keys):
            if i < len(keys):
                standard_dict[std_key] = images_dict[keys[i]]
                print(f"      Renamed '{keys[i]}' to '{std_key}'")

        images_dict = standard_dict

    def get_sequence_primary_axis(view_key_for_seq):
        if "left" in view_key_for_seq.lower() or "right" in view_key_for_seq.lower():

            if "intermediate" in view_key_for_seq.lower() and ("top" in view_key_for_seq.lower() or "bottom" in view_key_for_seq.lower()):
                return 1
            return 0
        return 1

    obv_data = images_dict.get("obverse")
    obv_h = get_image_dimension(obv_data, 0, blend_overlap_px if isinstance(
        obv_data, list) and get_sequence_primary_axis("obverse") == 0 else 0)
    obv_w = get_image_dimension(obv_data, 1, blend_overlap_px if isinstance(
        obv_data, list) and get_sequence_primary_axis("obverse") == 1 else 0)

    if obv_h == 0 or obv_w == 0:
        if custom_layout:
            for key, data in images_dict.items():
                if data is not None and "ruler" not in key:
                    print(
                        f"      Layout: 'obverse' missing/invalid. Using '{key}' as primary for layout ref.")
                    obv_data = data
                    obv_h = get_image_dimension(obv_data, 0, blend_overlap_px if isinstance(
                        obv_data, list) and get_sequence_primary_axis(key) == 0 else 0)
                    obv_w = get_image_dimension(obv_data, 1, blend_overlap_px if isinstance(
                        obv_data, list) and get_sequence_primary_axis(key) == 1 else 0)
                    break
        if obv_h == 0 or obv_w == 0:
            raise ValueError(
                "A primary image (e.g., 'obverse' or other from custom_layout) with valid dimensions is required for layout.")

    l_w = get_image_dimension(images_dict.get("left"), 1, blend_overlap_px if isinstance(
        images_dict.get("left"), list) and get_sequence_primary_axis("left") == 1 else 0)
    r_w = get_image_dimension(images_dict.get("right"), 1, blend_overlap_px if isinstance(
        images_dict.get("right"), list) and get_sequence_primary_axis("right") == 1 else 0)
    l_h = get_image_dimension(images_dict.get("left"), 0, blend_overlap_px if isinstance(
        images_dict.get("left"), list) and get_sequence_primary_axis("left") == 0 else 0)
    r_h = get_image_dimension(images_dict.get("right"), 0, blend_overlap_px if isinstance(
        images_dict.get("right"), list) and get_sequence_primary_axis("right") == 0 else 0)

    b_h = get_image_dimension(images_dict.get("bottom"), 0, blend_overlap_px if isinstance(
        images_dict.get("bottom"), list) and get_sequence_primary_axis("bottom") == 0 else 0)
    b_w = get_image_dimension(images_dict.get("bottom"), 1, blend_overlap_px if isinstance(
        images_dict.get("bottom"), list) and get_sequence_primary_axis("bottom") == 1 else 0)

    rev_h = get_image_dimension(images_dict.get("reverse"), 0, blend_overlap_px if isinstance(
        images_dict.get("reverse"), list) and get_sequence_primary_axis("reverse") == 0 else 0)
    rev_w = get_image_dimension(images_dict.get("reverse"), 1, blend_overlap_px if isinstance(
        images_dict.get("reverse"), list) and get_sequence_primary_axis("reverse") == 1 else 0)

    t_h = get_image_dimension(images_dict.get("top"), 0, blend_overlap_px if isinstance(
        images_dict.get("top"), list) and get_sequence_primary_axis("top") == 0 else 0)
    t_w = get_image_dimension(images_dict.get("top"), 1, blend_overlap_px if isinstance(
        images_dict.get("top"), list) and get_sequence_primary_axis("top") == 1 else 0)

    rul_h = get_image_dimension(images_dict.get("ruler"), 0)
    rul_w = get_image_dimension(images_dict.get("ruler"), 1)

    intermediate_dims = {}
    for key, img_data in images_dict.items():
        if "intermediate" in key and img_data is not None:

            h = get_image_dimension(img_data, 0, blend_overlap_px if isinstance(
                img_data, list) and get_sequence_primary_axis(key) == 0 else 0)
            w = get_image_dimension(img_data, 1, blend_overlap_px if isinstance(
                img_data, list) and get_sequence_primary_axis(key) == 1 else 0)
            if h > 0 and w > 0:
                intermediate_dims[key] = {"h": h, "w": w, "data": img_data}

    grouped_intermediates = group_intermediate_images(intermediate_dims)

    has_left = images_dict.get("left") is not None and l_w > 0
    has_obverse = images_dict.get("obverse") is not None and obv_w > 0
    has_right = images_dict.get("right") is not None and r_w > 0
    has_reverse = images_dict.get("reverse") is not None and rev_w > 0

    obv_row_width, rev_row_width, potential_canvas_widths = calculate_row_widths(
        grouped_intermediates, has_left, has_obverse, has_right, has_reverse,
        l_w, obv_w, r_w, rev_w, view_gap_px
    )

    for top_int in grouped_intermediates["obverse_top"]:
        potential_canvas_widths.append(top_int["dims"]["w"])

    for bottom_int in grouped_intermediates["obverse_bottom"]:
        potential_canvas_widths.append(bottom_int["dims"]["w"])

    for top_int in grouped_intermediates["reverse_top"]:
        potential_canvas_widths.append(top_int["dims"]["w"])

    for bottom_int in grouped_intermediates["reverse_bottom"]:
        potential_canvas_widths.append(bottom_int["dims"]["w"])

    if b_w > 0:
        potential_canvas_widths.append(b_w)
    if t_w > 0:
        potential_canvas_widths.append(t_w)
    if rul_w > 0:
        potential_canvas_widths.append(rul_w)

    canvas_w = max(potential_canvas_widths) if potential_canvas_widths else 800
    canvas_w += 200

    coords = {}
    rotation_flags = {}
    y_curr = 100

    int_obv_l_key = "intermediate_obverse_left"
    int_obv_r_key = "intermediate_obverse_right"
    int_rev_l_key = "intermediate_reverse_left"
    int_rev_r_key = "intermediate_reverse_right"
    int_obv_t_key = "intermediate_obverse_top"
    int_obv_b_key = "intermediate_obverse_bottom"
    int_rev_t_key = "intermediate_reverse_top"
    int_rev_b_key = "intermediate_reverse_bottom"

    has_int_obv_l = int_obv_l_key in intermediate_dims
    has_int_obv_r = int_obv_r_key in intermediate_dims
    has_int_rev_l = int_rev_l_key in intermediate_dims
    has_int_rev_r = int_rev_r_key in intermediate_dims

    obv_x = (canvas_w - obv_row_width) // 2
    if has_left:
        obv_x += l_w + view_gap_px
    if has_int_obv_l:
        obv_x += intermediate_dims[int_obv_l_key]["w"] + view_gap_px

    rev_x = (canvas_w - rev_row_width) // 2
    if has_left:
        rev_x += l_w + view_gap_px
    if has_int_rev_l:
        rev_x += intermediate_dims[int_rev_l_key]["w"] + view_gap_px

    central_column_x = obv_x
    central_column_width = obv_w

    for top_int in grouped_intermediates["obverse_top"]:
        int_key = top_int["key"]
        int_data = top_int["dims"]
        int_x = central_column_x + (central_column_width - int_data["w"]) // 2
        coords[int_key] = (int_x, y_curr)
        y_curr += int_data["h"] + view_gap_px

    obv_row_y = y_curr

    obv_row_width = 0
    obv_row_elements = []

    if has_left:
        obv_row_elements.append({"key": "left", "width": l_w})
        obv_row_width += l_w + view_gap_px

    left_intermediates = grouped_intermediates["obverse_left"]
    left_intermediates.sort(key=lambda x: x["number"], reverse=True)

    for left_int in left_intermediates:
        int_key = left_int["key"]
        int_w = left_int["dims"]["w"]
        obv_row_elements.append({"key": int_key, "width": int_w})
        obv_row_width += int_w + view_gap_px

    if has_obverse:
        obv_row_elements.append({"key": "obverse", "width": obv_w})
        obv_row_width += obv_w + view_gap_px

    right_intermediates = grouped_intermediates["obverse_right"]
    right_intermediates.sort(key=lambda x: x["number"])

    for right_int in right_intermediates:
        int_key = right_int["key"]
        int_w = right_int["dims"]["w"]
        obv_row_elements.append({"key": int_key, "width": int_w})
        obv_row_width += int_w + view_gap_px

    if has_right:
        obv_row_elements.append({"key": "right", "width": r_w})
        obv_row_width += r_w

    if obv_row_width > 0:
        obv_row_width -= view_gap_px

    current_x = (canvas_w - obv_row_width) // 2

    for element in obv_row_elements:
        key = element["key"]
        width = element["width"]

        if key == "obverse":
            coords["obverse"] = (current_x, obv_row_y)
            central_column_x = current_x
            central_column_width = obv_w
        elif "intermediate" in key:
            img_h = intermediate_dims[key]["h"]

            int_y = obv_row_y + (obv_h - img_h) // 2
            coords[key] = (current_x, int_y)
        else:

            coords[key] = (current_x, obv_row_y)
            rotation_flags[key] = False

        current_x += width + view_gap_px

    y_curr += obv_h + view_gap_px

    for bottom_int in grouped_intermediates["obverse_bottom"]:
        int_key = bottom_int["key"]
        int_data = bottom_int["dims"]
        int_x = central_column_x + (central_column_width - int_data["w"]) // 2
        coords[int_key] = (int_x, y_curr)
        y_curr += int_data["h"] + view_gap_px

    if images_dict.get("bottom") is not None and b_h > 0:
        bottom_x = central_column_x + (central_column_width - b_w) // 2
        coords["bottom"] = (bottom_x, y_curr)
        y_curr += b_h + view_gap_px

    for top_int in grouped_intermediates["reverse_top"]:
        int_key = top_int["key"]
        int_data = top_int["dims"]
        int_x = central_column_x + (central_column_width - int_data["w"]) // 2
        coords[int_key] = (int_x, y_curr)
        y_curr += int_data["h"] + view_gap_px

    rev_row_y = y_curr

    reverse_center_offset = 0
    if has_reverse and has_obverse:
        obverse_center = central_column_x + central_column_width // 2
        reverse_center = obverse_center

    rev_row_width = 0
    rev_row_elements = []

    if has_left:
        rev_row_elements.append({"key": "left_rotated", "width": l_w})
        rev_row_width += l_w + view_gap_px

    left_intermediates = grouped_intermediates["reverse_left"]
    left_intermediates.sort(key=lambda x: x["number"], reverse=True)

    for left_int in left_intermediates:
        int_key = left_int["key"]
        int_w = left_int["dims"]["w"]
        rev_row_elements.append({"key": int_key, "width": int_w})
        rev_row_width += int_w + view_gap_px

    if has_reverse:
        rev_row_elements.append({"key": "reverse", "width": rev_w})
        rev_row_width += rev_w + view_gap_px

    right_intermediates = grouped_intermediates["reverse_right"]
    right_intermediates.sort(key=lambda x: x["number"])

    for right_int in right_intermediates:
        int_key = right_int["key"]
        int_w = right_int["dims"]["w"]
        rev_row_elements.append({"key": int_key, "width": int_w})
        rev_row_width += int_w + view_gap_px

    if has_right:
        rev_row_elements.append({"key": "right_rotated", "width": r_w})
        rev_row_width += r_w

    if rev_row_width > 0:
        rev_row_width -= view_gap_px

    reverse_row_offset = (canvas_w - rev_row_width) // 2
    if has_reverse and has_obverse:

        reverse_pos = 0
        for idx, elem in enumerate(rev_row_elements):
            if elem["key"] == "reverse":
                reverse_pos = idx
                break

        reverse_x_in_row = reverse_row_offset
        for i in range(reverse_pos):
            reverse_x_in_row += rev_row_elements[i]["width"] + view_gap_px

        reverse_center = reverse_x_in_row + rev_w // 2

        obverse_center = central_column_x + obv_w // 2
        reverse_center_offset = obverse_center - reverse_center

        reverse_row_offset += reverse_center_offset

    current_x = reverse_row_offset
    for element in rev_row_elements:
        key = element["key"]
        width = element["width"]

        if key == "reverse":
            coords["reverse"] = (current_x, rev_row_y)
        elif key == "left_rotated":

            rotated_left_y = rev_row_y + (rev_h - l_h) // 2
            coords["left_rotated"] = (current_x, rotated_left_y)
            rotation_flags["left_rotated"] = True
        elif key == "right_rotated":

            rotated_right_y = rev_row_y + (rev_h - r_h) // 2
            coords["right_rotated"] = (current_x, rotated_right_y)
            rotation_flags["right_rotated"] = True
        else:
            img_h = intermediate_dims[key]["h"]

            int_y = rev_row_y + (rev_h - img_h) // 2
            coords[key] = (current_x, int_y)

        current_x += width + view_gap_px

    y_curr += rev_h + view_gap_px

    for bottom_int in grouped_intermediates["reverse_bottom"]:
        int_key = bottom_int["key"]
        int_data = bottom_int["dims"]
        int_x = central_column_x + (central_column_width - int_data["w"]) // 2
        coords[int_key] = (int_x, y_curr)
        y_curr += int_data["h"] + view_gap_px

    if images_dict.get("top") is not None and t_h > 0:
        top_x = central_column_x + (central_column_width - t_w) // 2
        coords["top"] = (top_x, y_curr)
        y_curr += t_h + view_gap_px

    if images_dict.get("ruler") is not None and rul_h > 0:
        y_curr += ruler_padding_px - view_gap_px
        ruler_x = central_column_x + (central_column_width - rul_w) // 2
        coords["ruler"] = (ruler_x, y_curr)
        y_curr += rul_h

    canvas_h = y_curr + 100

    modified_images_dict = create_rotated_images(images_dict)

    for key, data in intermediate_dims.items():
        if key in coords:
            modified_images_dict[key] = data["data"]

    return int(canvas_w), int(canvas_h), coords, modified_images_dict
