# Coordinate layout calculation for tablet image components
import cv2
import numpy as np
try:
    from image_utils import resize_image_maintain_aspect, convert_to_bgr_if_needed
except ImportError:
    print("FATAL ERROR: stitch_layout_manager.py cannot import from image_utils.py")
    def resize_image_maintain_aspect(*args): raise ImportError("resize_image_maintain_aspect missing")
    def convert_to_bgr_if_needed(img): return img
    
from stitch_config import (
    STITCH_VIEW_GAP_PX,
    STITCH_RULER_PADDING_PX
    # Assuming INTERMEDIATE_VIEW_RELATIONSHIPS might be defined here,
    # but for now, we'll use common key name patterns.
)

def get_image_dimension(image_or_list, axis_index, blend_overlap_px=0):
    """Get height or width dimension of an image or a list of images (calculating post-blend dimension for lists)."""
    if isinstance(image_or_list, np.ndarray) and image_or_list.ndim >= 2 and image_or_list.size > 0:
        return image_or_list.shape[axis_index]
    elif isinstance(image_or_list, list) and image_or_list:
        if not image_or_list: return 0
        # For a list, calculate the dimension after hypothetical blending.
        # Axis_index: 0 for height, 1 for width.
        if axis_index == 0:
            total_height = 0
            min_common_width = float('inf')
            for i, img in enumerate(image_or_list):
                if not isinstance(img, np.ndarray) or img.size == 0: continue
                total_height += img.shape[0]
                min_common_width = min(min_common_width, img.shape[1])
                if i > 0: total_height -= blend_overlap_px
            # The final width of a vertically blended sequence is min_common_width
            # This function is asked for a single dimension, so if axis_index is 1 (width) for a vertical blend:
            # return min_common_width if min_common_width != float('inf') else 0
            # However, the primary use here is to get the length along the blending axis.
            return total_height
        else:
            total_width = 0
            min_common_height = float('inf')
            for i, img in enumerate(image_or_list):
                if not isinstance(img, np.ndarray) or img.size == 0: continue
                total_width += img.shape[1]
                min_common_height = min(min_common_height, img.shape[0])
                if i > 0: total_width -= blend_overlap_px
            # The final height of a horizontally blended sequence is min_common_height
            # return min_common_height if min_common_height != float('inf') else 0
            return total_width
    return 0

def resize_tablet_views_for_layout(loaded_images_dictionary):
    """
    Resize all tablet views. If obverse is present, other main views are resized relative to it.
    Handles single images and lists of images (sequences).
    """
    obverse_image_data = loaded_images_dictionary.get("obverse")
    
    # Determine obverse dimensions (could be single image or sequence)
    # For sequences, the 'obverse' itself isn't typically a sequence that needs blending for this purpose.
    # We assume 'obverse' if present, is a single image or the primary image of a set.
    # If 'obverse' itself could be a sequence to be blended, its primary image should be used for ref dims.
    obv_h, obv_w = 0, 0
    if isinstance(obverse_image_data, np.ndarray) and obverse_image_data.size > 0:
        obv_h, obv_w = obverse_image_data.shape[:2]
    elif isinstance(obverse_image_data, list) and obverse_image_data and isinstance(obverse_image_data[0], np.ndarray):
        # If obverse is a list (e.g. from custom layout), use the first image for reference dimensions.
        obv_h, obv_w = obverse_image_data[0].shape[:2]
        print("      Resize: 'obverse' is a list, using first image for reference dimensions.")

    if obv_h == 0 or obv_w == 0:
        # If no valid obverse, we cannot do relative resizing. 
        # Images will be used as-is or a default size could be applied.
        # For now, let's print a warning and proceed without relative resizing for other views.
        print("      Warn: Obverse image not valid for relative resizing. Skipping relative resize of other views.")
        # We still need to process lists if they exist, just not relative to obverse.
        # The function should still return the dictionary, possibly with original sizes or individually processed lists.
        # Let's ensure all images in lists are at least processed, even if not resized relative to obverse.
        processed_dict = {}
        for view_key, image_data_item in loaded_images_dictionary.items():
            if isinstance(image_data_item, list):
                processed_list = [img for img in image_data_item if isinstance(img, np.ndarray) and img.size > 0]
                processed_dict[view_key] = processed_list if processed_list else None
            elif isinstance(image_data_item, np.ndarray) and image_data_item.size > 0:
                processed_dict[view_key] = image_data_item
            else:
                processed_dict[view_key] = None
        return processed_dict

    # Standard resize config relative to obverse
    resize_config = {
        # view_key: {axis_to_match_obverse_dim, obverse_dim_to_match}
        "left": {"axis": 0, "match_dim": obv_h},
        "right": {"axis": 0, "match_dim": obv_h},
        "top": {"axis": 1, "match_dim": obv_w},
        "bottom": {"axis": 1, "match_dim": obv_w},
        "reverse": {"axis": 1, "match_dim": obv_w}
        # Intermediate sequences will also be resized based on these rules if their keys match.
        # E.g., "obverse_top_intermediate_sequence" would align with "top" rule if not explicitly handled.
    }

    output_resized_images = {}
    for view_key, image_data in loaded_images_dictionary.items():
        if view_key == "obverse":
            output_resized_images[view_key] = obverse_image_data
            continue

        params = None
        # Find matching resize rule (e.g. "obverse_top_intermediate" uses "top" rule)
        for r_key, r_params in resize_config.items():
            if r_key in view_key:
                params = r_params
                break
        if not params and "ruler" not in view_key:
             # If no specific rule, and not obverse or ruler, decide a default or skip.
             # For now, keep original if no rule applies (e.g. for custom arbitrary view names)
            print(f"      Resize: No specific resize rule for '{view_key}'. Keeping original.")
            output_resized_images[view_key] = image_data
            continue
        elif "ruler" in view_key:
            output_resized_images[view_key] = image_data
            continue

        if isinstance(image_data, np.ndarray) and image_data.size > 0:
            output_resized_images[view_key] = resize_image_maintain_aspect(
                image_data, params["match_dim"], params["axis"]
            )
        elif isinstance(image_data, list):
            resized_sequence = []
            for img_in_seq in image_data:
                if isinstance(img_in_seq, np.ndarray) and img_in_seq.size > 0:
                    resized_img = resize_image_maintain_aspect(
                        img_in_seq, params["match_dim"], params["axis"]
                    )
                    resized_sequence.append(resized_img)
                else:
                    resized_sequence.append(None)
            output_resized_images[view_key] = [rs for rs in resized_sequence if rs is not None] if any(rs is not None for rs in resized_sequence) else None
        elif image_data is not None:
            output_resized_images[view_key] = None
            print(f"      Warn: Resize - Unexpected data type for {view_key}: {type(image_data)}")
        else:
            output_resized_images[view_key] = None
            
    return output_resized_images

def calculate_stitching_layout(images_dict, view_gap_px=STITCH_VIEW_GAP_PX, ruler_padding_px=STITCH_RULER_PADDING_PX, custom_layout=None, blend_overlap_px=0):
    """
    Calculate the canvas dimensions and coordinates for placing each image or blended sequence.
    Returns canvas dimensions, coordinate map, and the input images_dict.
    
    The central column is arranged in this order:
    - Intermediate Obverse Top (_ot)
    - Obverse (_01)
    - Intermediate Obverse Bottom (_ob)
    - Bottom (_04)
    - Intermediate Reverse Top (_rt)
    - Reverse (_02)
    - Intermediate Reverse Bottom (_rb)
    - Top (_03)
    - Ruler
    
    If exactly 4 images are provided without standard naming, they will be interpreted as:
    obverse, reverse, top, and bottom views in order of appearance.
    
    The sides (left, right) are aligned horizontally with obverse/reverse.
    """
    # Auto-detect and assign standard views if exactly 4 images are provided
    standard_keys = ["obverse", "reverse", "top", "bottom"]
    
    # Check if we have exactly 4 images and none of them have standard keys
    if len(images_dict) == 4 and not any(key in standard_keys for key in images_dict.keys()):
        print("      Layout: Found exactly 4 images without standard naming. Assigning as obverse, reverse, top, bottom.")
        
        # Create a new dictionary with standard names
        keys = list(images_dict.keys())
        standard_dict = {}
        
        # Map the 4 images to standard views
        for i, std_key in enumerate(standard_keys):
            if i < len(keys):
                standard_dict[std_key] = images_dict[keys[i]]
                print(f"      Renamed '{keys[i]}' to '{std_key}'")
        
        # Replace the input dictionary with our new standardized one
        images_dict = standard_dict
    
    # Helper to determine which dimension is primary for a sequence based on key naming
    def get_sequence_primary_axis(view_key_for_seq):
        if "left" in view_key_for_seq.lower() or "right" in view_key_for_seq.lower():
            # This rule might need adjustment if intermediate keys like "intermediate_obverse_left"
            # are intended to be blended horizontally. For now, assume side pieces are vertically blended if sequences.
            # Typically, intermediates are single images after processing.
            if "intermediate" in view_key_for_seq.lower() and ("top" in view_key_for_seq.lower() or "bottom" in view_key_for_seq.lower()):
                 return 1
            return 0
        return 1

    # Get dimensions of main tablet views, considering they might be sequences
    obv_data = images_dict.get("obverse")
    obv_h = get_image_dimension(obv_data, 0, blend_overlap_px if isinstance(obv_data, list) and get_sequence_primary_axis("obverse") == 0 else 0)
    obv_w = get_image_dimension(obv_data, 1, blend_overlap_px if isinstance(obv_data, list) and get_sequence_primary_axis("obverse") == 1 else 0)

    if obv_h == 0 or obv_w == 0:
        if custom_layout:
            for key, data in images_dict.items():
                if data is not None and "ruler" not in key:
                    print(f"      Layout: 'obverse' missing/invalid. Using '{key}' as primary for layout ref.")
                    obv_data = data
                    obv_h = get_image_dimension(obv_data, 0, blend_overlap_px if isinstance(obv_data, list) and get_sequence_primary_axis(key) == 0 else 0)
                    obv_w = get_image_dimension(obv_data, 1, blend_overlap_px if isinstance(obv_data, list) and get_sequence_primary_axis(key) == 1 else 0)
                    break
        if obv_h == 0 or obv_w == 0: 
            raise ValueError("A primary image (e.g., 'obverse' or other from custom_layout) with valid dimensions is required for layout.")

    # Get dimensions for all sides
    l_w = get_image_dimension(images_dict.get("left"), 1, blend_overlap_px if isinstance(images_dict.get("left"), list) and get_sequence_primary_axis("left") == 1 else 0)
    r_w = get_image_dimension(images_dict.get("right"), 1, blend_overlap_px if isinstance(images_dict.get("right"), list) and get_sequence_primary_axis("right") == 1 else 0)
    l_h = get_image_dimension(images_dict.get("left"), 0, blend_overlap_px if isinstance(images_dict.get("left"), list) and get_sequence_primary_axis("left") == 0 else 0)
    r_h = get_image_dimension(images_dict.get("right"), 0, blend_overlap_px if isinstance(images_dict.get("right"), list) and get_sequence_primary_axis("right") == 0 else 0)
    
    b_h = get_image_dimension(images_dict.get("bottom"), 0, blend_overlap_px if isinstance(images_dict.get("bottom"), list) and get_sequence_primary_axis("bottom") == 0 else 0)
    b_w = get_image_dimension(images_dict.get("bottom"), 1, blend_overlap_px if isinstance(images_dict.get("bottom"), list) and get_sequence_primary_axis("bottom") == 1 else 0)
    
    rev_h = get_image_dimension(images_dict.get("reverse"), 0, blend_overlap_px if isinstance(images_dict.get("reverse"), list) and get_sequence_primary_axis("reverse") == 0 else 0)
    rev_w = get_image_dimension(images_dict.get("reverse"), 1, blend_overlap_px if isinstance(images_dict.get("reverse"), list) and get_sequence_primary_axis("reverse") == 1 else 0)
    
    t_h = get_image_dimension(images_dict.get("top"), 0, blend_overlap_px if isinstance(images_dict.get("top"), list) and get_sequence_primary_axis("top") == 0 else 0)
    t_w = get_image_dimension(images_dict.get("top"), 1, blend_overlap_px if isinstance(images_dict.get("top"), list) and get_sequence_primary_axis("top") == 1 else 0)
    
    rul_h = get_image_dimension(images_dict.get("ruler"), 0)
    rul_w = get_image_dimension(images_dict.get("ruler"), 1)

    # Get dimensions of intermediate images
    intermediate_dims = {}
    for key, img_data in images_dict.items():
        if "intermediate" in key and img_data is not None:
            # Assuming intermediates are single images or already blended if they were sequences.
            h = get_image_dimension(img_data, 0, blend_overlap_px if isinstance(img_data, list) and get_sequence_primary_axis(key) == 0 else 0)
            w = get_image_dimension(img_data, 1, blend_overlap_px if isinstance(img_data, list) and get_sequence_primary_axis(key) == 1 else 0)
            if h > 0 and w > 0:
                intermediate_dims[key] = {"h": h, "w": w, "data": img_data}

    # Define keys for intermediates
    int_obv_t_key = "intermediate_obverse_top"
    int_obv_b_key = "intermediate_obverse_bottom"
    int_rev_t_key = "intermediate_reverse_top"
    int_rev_b_key = "intermediate_reverse_bottom"
    int_obv_l_key = "intermediate_obverse_left"
    int_obv_r_key = "intermediate_obverse_right"
    int_rev_l_key = "intermediate_reverse_left"
    int_rev_r_key = "intermediate_reverse_right"
    
    # Calculate widths for horizontal rows
    
    # Obverse row: left + int_obv_l + obverse + int_obv_r + right
    obv_row_width = 0
    has_left = images_dict.get("left") is not None and l_w > 0
    has_int_obv_l = int_obv_l_key in intermediate_dims
    has_obverse = images_dict.get("obverse") is not None and obv_w > 0
    has_int_obv_r = int_obv_r_key in intermediate_dims
    has_right = images_dict.get("right") is not None and r_w > 0
    
    obv_row_elements = []
    if has_left: obv_row_elements.append(l_w)
    if has_int_obv_l: obv_row_elements.append(intermediate_dims[int_obv_l_key]["w"])
    if has_obverse: obv_row_elements.append(obv_w)
    if has_int_obv_r: obv_row_elements.append(intermediate_dims[int_obv_r_key]["w"])
    if has_right: obv_row_elements.append(r_w)
    
    obv_row_width = sum(obv_row_elements)
    if len(obv_row_elements) > 1:
        obv_row_width += view_gap_px * (len(obv_row_elements) - 1)
    
    # Reverse row: left + int_rev_l + reverse + int_rev_r + right
    rev_row_width = 0
    has_int_rev_l = int_rev_l_key in intermediate_dims
    has_reverse = images_dict.get("reverse") is not None and rev_w > 0
    has_int_rev_r = int_rev_r_key in intermediate_dims
    
    rev_row_elements = []
    if has_left: rev_row_elements.append(l_w)
    if has_int_rev_l: rev_row_elements.append(intermediate_dims[int_rev_l_key]["w"])
    if has_reverse: rev_row_elements.append(rev_w)
    if has_int_rev_r: rev_row_elements.append(intermediate_dims[int_rev_r_key]["w"])
    if has_right: rev_row_elements.append(r_w)
    
    rev_row_width = sum(rev_row_elements)
    if len(rev_row_elements) > 1:
        rev_row_width += view_gap_px * (len(rev_row_elements) - 1)
    
    # Calculate canvas width
    potential_canvas_widths = [obv_row_width, rev_row_width]
    
    # Add widths of other centered elements
    if has_obverse and int_obv_t_key in intermediate_dims:
        potential_canvas_widths.append(intermediate_dims[int_obv_t_key]["w"])
    if has_obverse and int_obv_b_key in intermediate_dims:
        potential_canvas_widths.append(intermediate_dims[int_obv_b_key]["w"])
    if has_reverse and int_rev_t_key in intermediate_dims:
        potential_canvas_widths.append(intermediate_dims[int_rev_t_key]["w"])
    if has_reverse and int_rev_b_key in intermediate_dims:
        potential_canvas_widths.append(intermediate_dims[int_rev_b_key]["w"])
    if b_w > 0: potential_canvas_widths.append(b_w)
    if t_w > 0: potential_canvas_widths.append(t_w)
    if rul_w > 0: potential_canvas_widths.append(rul_w)
    
    canvas_w = max(potential_canvas_widths) if potential_canvas_widths else 800
    canvas_w += 200
    
    # Layout calculation
    coords = {}
    rotation_flags = {}
    y_curr = 100
    
    # Calculate center positions for the column views
    # The center of the layout is based on the widest row
    # If obverse row is wider, center everything based on obverse position
    # If reverse row is wider, center everything based on reverse position
    
    # Calculate obverse x position in its row
    obv_x = (canvas_w - obv_row_width) // 2
    if has_left:
        obv_x += l_w + view_gap_px
    if has_int_obv_l:
        obv_x += intermediate_dims[int_obv_l_key]["w"] + view_gap_px
    
    # Calculate reverse x position in its row
    rev_x = (canvas_w - rev_row_width) // 2
    if has_left:
        rev_x += l_w + view_gap_px
    if has_int_rev_l:
        rev_x += intermediate_dims[int_rev_l_key]["w"] + view_gap_px
    
    # Determine the central column reference position
    # We want the centers of obverse and reverse to align vertically
    central_column_x = obv_x
    central_column_width = obv_w
    
    # --- Step 1: Place Intermediate Obverse Top (_ot) ---
    if int_obv_t_key in intermediate_dims:
        int_data = intermediate_dims[int_obv_t_key]
        int_x = central_column_x + (central_column_width - int_data["w"]) // 2
        coords[int_obv_t_key] = (int_x, y_curr)
        y_curr += int_data["h"] + view_gap_px
    
    # --- Step 2: Place Obverse Row (Left, Int_Obv_L, Obverse, Int_Obv_R, Right) ---
    obv_row_y = y_curr
    current_x = (canvas_w - obv_row_width) // 2
    
    if has_left:
        coords["left"] = (current_x, obv_row_y)
        rotation_flags["left"] = False
        current_x += l_w + view_gap_px
    
    if has_int_obv_l:
        int_data = intermediate_dims[int_obv_l_key]
        # Vertically center against obverse height
        int_y = obv_row_y + (obv_h - int_data["h"]) // 2
        coords[int_obv_l_key] = (current_x, int_y)
        current_x += int_data["w"] + view_gap_px
    
    if has_obverse:
        coords["obverse"] = (current_x, obv_row_y)
        central_column_x = current_x
        central_column_width = obv_w
        current_x += obv_w + view_gap_px
    
    if has_int_obv_r:
        int_data = intermediate_dims[int_obv_r_key]
        # Vertically center against obverse height
        int_y = obv_row_y + (obv_h - int_data["h"]) // 2
        coords[int_obv_r_key] = (current_x, int_y)
        current_x += int_data["w"] + view_gap_px
    
    if has_right:
        coords["right"] = (current_x, obv_row_y)
        rotation_flags["right"] = False
    
    y_curr += obv_h + view_gap_px
    
    # --- Step 3: Place Intermediate Obverse Bottom (_ob) ---
    if int_obv_b_key in intermediate_dims:
        int_data = intermediate_dims[int_obv_b_key]
        int_x = central_column_x + (central_column_width - int_data["w"]) // 2
        coords[int_obv_b_key] = (int_x, y_curr)
        y_curr += int_data["h"] + view_gap_px
    
    # --- Step 4: Place Bottom ---
    if images_dict.get("bottom") is not None and b_h > 0:
        bottom_x = central_column_x + (central_column_width - b_w) // 2
        coords["bottom"] = (bottom_x, y_curr)
        y_curr += b_h + view_gap_px
    
    # --- Step 5: Place Intermediate Reverse Top (_rt) ---
    if int_rev_t_key in intermediate_dims:
        int_data = intermediate_dims[int_rev_t_key]
        int_x = central_column_x + (central_column_width - int_data["w"]) // 2
        coords[int_rev_t_key] = (int_x, y_curr)
        y_curr += int_data["h"] + view_gap_px
    
    # --- Step 6: Place Reverse Row (Left, Int_Rev_L, Reverse, Int_Rev_R, Right) ---
    rev_row_y = y_curr
    
    # Adjust reverse x position to align its center with obverse's center
    reverse_center_offset = 0
    if has_reverse and has_obverse:
        # Calculate centers of obverse and reverse
        obverse_center = central_column_x + obv_w // 2
        reverse_center = rev_x + rev_w // 2
        reverse_center_offset = obverse_center - reverse_center
    
    current_x = (canvas_w - rev_row_width) // 2 + reverse_center_offset
    
    if has_left:
        # Rotated left aligned with reverse row
        rotated_left_y = rev_row_y + (rev_h - l_h) // 2
        coords["left_rotated"] = (current_x, rotated_left_y)
        rotation_flags["left_rotated"] = True
        current_x += l_w + view_gap_px
    
    if has_int_rev_l:
        int_data = intermediate_dims[int_rev_l_key]
        # Vertically center against reverse height
        int_y = rev_row_y + (rev_h - int_data["h"]) // 2
        coords[int_rev_l_key] = (current_x, int_y)
        current_x += int_data["w"] + view_gap_px
    
    if has_reverse:
        coords["reverse"] = (current_x, rev_row_y)
        current_x += rev_w + view_gap_px
    
    if has_int_rev_r:
        int_data = intermediate_dims[int_rev_r_key]
        # Vertically center against reverse height
        int_y = rev_row_y + (rev_h - int_data["h"]) // 2
        coords[int_rev_r_key] = (current_x, int_y)
        current_x += int_data["w"] + view_gap_px
    
    if has_right:
        # Rotated right aligned with reverse row
        rotated_right_y = rev_row_y + (rev_h - r_h) // 2
        coords["right_rotated"] = (current_x, rotated_right_y)
        rotation_flags["right_rotated"] = True
    
    y_curr += rev_h + view_gap_px
    
    # --- Step 7: Place Intermediate Reverse Bottom (_rb) ---
    if int_rev_b_key in intermediate_dims:
        int_data = intermediate_dims[int_rev_b_key]
        int_x = central_column_x + (central_column_width - int_data["w"]) // 2
        coords[int_rev_b_key] = (int_x, y_curr)
        y_curr += int_data["h"] + view_gap_px
    
    # --- Step 8: Place Top ---
    if images_dict.get("top") is not None and t_h > 0:
        top_x = central_column_x + (central_column_width - t_w) // 2
        coords["top"] = (top_x, y_curr)
        y_curr += t_h + view_gap_px
    
    # --- Step 9: Place Ruler ---
    if images_dict.get("ruler") is not None and rul_h > 0:
        y_curr += ruler_padding_px - view_gap_px
        ruler_x = central_column_x + (central_column_width - rul_w) // 2
        coords["ruler"] = (ruler_x, y_curr)
        y_curr += rul_h
    
    canvas_h = y_curr + 100
    
    # Create rotated versions of left and right for the reverse row
    modified_images_dict = dict(images_dict)
    
    if images_dict.get("left") is not None and "left_rotated" in coords:
        left_img_data = images_dict["left"]
        if isinstance(left_img_data, np.ndarray) and left_img_data.size > 0:
            modified_images_dict["left_rotated"] = cv2.rotate(left_img_data, cv2.ROTATE_180)
        elif isinstance(left_img_data, list) and left_img_data:
            print("      Warn: 'left' is a list, rotation for 'left_rotated' might be unexpected.")
    
    if images_dict.get("right") is not None and "right_rotated" in coords:
        right_img_data = images_dict["right"]
        if isinstance(right_img_data, np.ndarray) and right_img_data.size > 0:
            modified_images_dict["right_rotated"] = cv2.rotate(right_img_data, cv2.ROTATE_180)
        elif isinstance(right_img_data, list) and right_img_data:
            print("      Warn: 'right' is a list, rotation for 'right_rotated' might be unexpected.")
    
    # Add intermediate images to modified_images_dict
    for key, data in intermediate_dims.items():
        if key in coords:
            modified_images_dict[key] = data["data"]
    
    return int(canvas_w), int(canvas_h), coords, modified_images_dict

def get_layout_bounding_box(images_dict, layout_coords):
    """
    Calculate the bounding box that contains all placed images.
    Returns (min_x, min_y, max_x, max_y) if there are valid elements, None otherwise.
    """
    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')
    found_any_placed_element = False
    
    # Find boundaries of all placed images
    for key, (x_coord, y_coord) in layout_coords.items():
        image_array = images_dict.get(key)
        if isinstance(image_array, np.ndarray) and image_array.size > 0:
            found_any_placed_element = True
            h_img, w_img = image_array.shape[:2]
            min_x = min(min_x, x_coord)
            min_y = min(min_y, y_coord)
            max_x = max(max_x, x_coord + w_img)
            max_y = max(max_y, y_coord + h_img)
            
    return (min_x, min_y, max_x, max_y) if found_any_placed_element else None