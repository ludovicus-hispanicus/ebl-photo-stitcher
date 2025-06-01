import cv2
import numpy as np
import re
try:
    from image_utils import resize_image_maintain_aspect, convert_to_bgr_if_needed
    from stitch_config import (
        STITCH_VIEW_GAP_PX,
        STITCH_RULER_PADDING_PX,
        get_extended_intermediate_suffixes  # Add this import
    )
    from blending_mask_applier import generate_position_patterns
except ImportError as e:
    print(f"FATAL ERROR: stitch_layout_manager.py cannot import: {e}")
    def resize_image_maintain_aspect(*args): raise ImportError("resize_image_maintain_aspect missing")
    def convert_to_bgr_if_needed(img): return img
    # Mock the function we need
    def get_extended_intermediate_suffixes(): return {}
    def generate_position_patterns(): return [r'_([a-z]{2}\d*)_', r'intermediate_[^_]+_([^_\.]+)(?:_\d+)?']

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
    - Intermediate Obverse Top (_ot, _ot2, _ot3...)
    - Obverse (_01)
    - Intermediate Obverse Bottom (_ob, _ob2, _ob3...)
    - Bottom (_04)
    - Intermediate Reverse Top (_rt, _rt2, _rt3...)
    - Reverse (_02)
    - Intermediate Reverse Bottom (_rb, _rb2, _rb3...)
    - Top (_03)
    - Ruler
    
    Horizontal arrangement follows the pattern:
    ol3 → ol2 → ol → obverse → or → or2 → or3
    rl3 → rl2 → rl → reverse → rr → rr2 → rr3
    
    If exactly 4 images are provided without standard naming, they will be interpreted as:
    obverse, reverse, top, and bottom views in order of appearance.
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

    # Get all possible intermediate positions from our centralized function
    extended_intermediate_positions = get_extended_intermediate_suffixes()
    
    # Group intermediates by their base position (ignoring numbers)
    grouped_intermediates = {
        "obverse_top": [],    # ot, ot2, ot3...
        "obverse_bottom": [], # ob, ob2, ob3...
        "obverse_left": [],   # ol, ol2, ol3...
        "obverse_right": [],  # or, or2, or3...
        "reverse_top": [],    # rt, rt2, rt3...
        "reverse_bottom": [], # rb, rb2, rb3...
        "reverse_left": [],   # rl, rl2, rl3...
        "reverse_right": [],  # rr, rr2, rr3...
    }
    
    # Process all intermediates and group them
    for key in intermediate_dims:
        position_found = False
        suffix_number = 1  # Default for unnumbered (base) intermediates
        
        # Try to detect position from the key using centralized patterns
        matched_position = None
        
        position_patterns = generate_position_patterns()
        for pattern in position_patterns:
            match = re.search(pattern, key.lower())
            if match:
                matched_position = match.group(1)
                
                # Check if this is a numbered variant
                if len(matched_position) > 2 and matched_position[-1].isdigit():
                    # Extract the suffix number from the matched position
                    suffix_match = re.search(r'([a-z]{2})(\d+)', matched_position)
                    if suffix_match:
                        base_code = suffix_match.group(1)  # e.g., "ol"
                        suffix_number = int(suffix_match.group(2))  # e.g., 2
                        matched_position = base_code
                
                # Map the short code to a position group
                for position_name in grouped_intermediates.keys():
                    if position_name.endswith(matched_position.replace("l", "_left").replace("r", "_right").replace("t", "_top").replace("b", "_bottom")):
                        grouped_intermediates[position_name].append({
                            "key": key,
                            "number": suffix_number,
                            "dims": intermediate_dims[key]
                        })
                        position_found = True
                        break
                    
                    # Also try direct full name matching
                    if position_name == matched_position:
                        grouped_intermediates[position_name].append({
                            "key": key,
                            "number": suffix_number,
                            "dims": intermediate_dims[key]
                        })
                        position_found = True
                        break
                
                if position_found:
                    break
        
        # If still not matched through patterns, try a more direct approach
        if not position_found:
            # First try exact position names (for base intermediates without numbers)
            for position_name in grouped_intermediates.keys():
                full_position_name = f"intermediate_{position_name}"
                if key == full_position_name:
                    # Found a base intermediate (e.g. intermediate_obverse_left)
                    grouped_intermediates[position_name].append({
                        "key": key,
                        "number": suffix_number,
                        "dims": intermediate_dims[key]
                    })
                    position_found = True
                    break
            
            if not position_found:
                # Then try numbered variants with explicit pattern
                match = re.match(r'intermediate_([a-z]+_[a-z]+)_(\d+)', key)
                if match:
                    position_part = match.group(1)  # e.g. "obverse_left", "reverse_right"
                    suffix_number = int(match.group(2))  # e.g. 2, 3
                    
                    if position_part in grouped_intermediates:
                        grouped_intermediates[position_part].append({
                            "key": key,
                            "number": suffix_number,
                            "dims": intermediate_dims[key]
                        })
                        position_found = True
                
        # If still not matched, use a fallback approach
        if not position_found:
            print(f"      Layout: Trying fallback detection for: {key}")
            # Try to extract meaningful position data
            for position_name in grouped_intermediates.keys():
                if position_name in key:
                    print(f"      Layout: Found intermediate with non-standard naming: {key}")
                    grouped_intermediates[position_name].append({
                        "key": key,
                        "number": 99,  # Use high number to place it at outer edge
                        "dims": intermediate_dims[key]
                    })
                    position_found = True
                    break
    
    # Sort each group by number (higher numbers should be farther from the main view)
    for group_key in grouped_intermediates:
        grouped_intermediates[group_key].sort(key=lambda x: x["number"])
    
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
    
    # Calculate canvas width by considering all possible row widths
    potential_canvas_widths = []

    # Calculate obverse row width with ALL intermediates
    obv_row_full_width = 0
    if has_left:
        obv_row_full_width += l_w + view_gap_px

    # Add ALL intermediate_obverse_left variants (ol, ol2, ol3)
    for left_int in grouped_intermediates["obverse_left"]:
        int_w = left_int["dims"]["w"]
        obv_row_full_width += int_w + view_gap_px

    if has_obverse:
        obv_row_full_width += obv_w + view_gap_px

    # Add ALL intermediate_obverse_right variants (or, or2, or3)
    for right_int in grouped_intermediates["obverse_right"]:
        int_w = right_int["dims"]["w"]
        obv_row_full_width += int_w + view_gap_px

    if has_right:
        obv_row_full_width += r_w

    # Subtract extra gap if there are any elements
    if obv_row_full_width > 0 and (has_left or has_obverse or has_right or grouped_intermediates["obverse_left"] or grouped_intermediates["obverse_right"]):
        obv_row_full_width -= view_gap_px

    potential_canvas_widths.append(obv_row_full_width)

    # Calculate reverse row width with ALL intermediates
    rev_row_full_width = 0
    if has_left:
        rev_row_full_width += l_w + view_gap_px

    # Add ALL intermediate_reverse_left variants (rl, rl2, rl3)
    for left_int in grouped_intermediates["reverse_left"]:
        int_w = left_int["dims"]["w"]
        rev_row_full_width += int_w + view_gap_px

    if has_reverse:
        rev_row_full_width += rev_w + view_gap_px

    # Add ALL intermediate_reverse_right variants (rr, rr2, rr3)
    for right_int in grouped_intermediates["reverse_right"]:
        int_w = right_int["dims"]["w"]
        rev_row_full_width += int_w + view_gap_px

    if has_right:
        rev_row_full_width += r_w

    # Subtract extra gap if there are any elements
    if rev_row_full_width > 0 and (has_left or has_reverse or has_right or grouped_intermediates["reverse_left"] or grouped_intermediates["reverse_right"]):
        rev_row_full_width -= view_gap_px

    potential_canvas_widths.append(rev_row_full_width)

    # Add widths of other centered elements
    # Top intermediates (ot, ot2, ot3)
    for top_int in grouped_intermediates["obverse_top"]:
        potential_canvas_widths.append(top_int["dims"]["w"])

    # Bottom intermediates (ob, ob2, ob3)  
    for bottom_int in grouped_intermediates["obverse_bottom"]:
        potential_canvas_widths.append(bottom_int["dims"]["w"])

    # Reverse top intermediates (rt, rt2, rt3)
    for top_int in grouped_intermediates["reverse_top"]:
        potential_canvas_widths.append(top_int["dims"]["w"])

    # Reverse bottom intermediates (rb, rb2, rb3)
    for bottom_int in grouped_intermediates["reverse_bottom"]:
        potential_canvas_widths.append(bottom_int["dims"]["w"])

    if b_w > 0: potential_canvas_widths.append(b_w)
    if t_w > 0: potential_canvas_widths.append(t_w)
    if rul_w > 0: potential_canvas_widths.append(rul_w)

    canvas_w = max(potential_canvas_widths) if potential_canvas_widths else 800
    canvas_w += 200  # Add some padding
    
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
    
    # --- Step 2: Place Obverse Row with all intermediates in order ---
    obv_row_y = y_curr
    
    # Calculate total width of all elements in the obverse row
    # Including all intermediate_obverse_left_X and intermediate_obverse_right_X variants
    obv_row_width = 0
    obv_row_elements = []
    
    # Add left side
    if has_left:
        obv_row_elements.append({"key": "left", "width": l_w})
        obv_row_width += l_w + view_gap_px
    
    # Add all intermediate_obverse_left variants in reverse order (ol3, ol2, ol)
    left_intermediates = grouped_intermediates["obverse_left"]
    left_intermediates.sort(key=lambda x: x["number"], reverse=True)  # Highest number first
    
    for left_int in left_intermediates:
        int_key = left_int["key"]
        int_w = left_int["dims"]["w"]
        obv_row_elements.append({"key": int_key, "width": int_w})
        obv_row_width += int_w + view_gap_px
    
    # Add obverse
    if has_obverse:
        obv_row_elements.append({"key": "obverse", "width": obv_w})
        obv_row_width += obv_w + view_gap_px
    
    # Add all intermediate_obverse_right variants in order (or, or2, or3)
    right_intermediates = grouped_intermediates["obverse_right"]
    right_intermediates.sort(key=lambda x: x["number"])  # Lowest number first
    
    for right_int in right_intermediates:
        int_key = right_int["key"]
        int_w = right_int["dims"]["w"]
        obv_row_elements.append({"key": int_key, "width": int_w})
        obv_row_width += int_w + view_gap_px
    
    # Add right side
    if has_right:
        obv_row_elements.append({"key": "right", "width": r_w})
        obv_row_width += r_w
    
    # Subtract extra gap
    if obv_row_width > 0:
        obv_row_width -= view_gap_px
    
    # Calculate starting position for the obverse row
    current_x = (canvas_w - obv_row_width) // 2
    
    # Place all elements in the obverse row
    for element in obv_row_elements:
        key = element["key"]
        width = element["width"]
        
        if key == "obverse":
            coords["obverse"] = (current_x, obv_row_y)
            central_column_x = current_x  # Save the central column position
            central_column_width = obv_w
        elif "intermediate" in key:
            img_h = intermediate_dims[key]["h"]
            # Vertically center against obverse height
            int_y = obv_row_y + (obv_h - img_h) // 2
            coords[key] = (current_x, int_y)
        else:
            # Left or right
            coords[key] = (current_x, obv_row_y)
            rotation_flags[key] = False
        
        current_x += width + view_gap_px
    
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
    
    # --- Step 6: Place Reverse Row with all intermediates in order ---
    rev_row_y = y_curr
    
    # Calculate the alignment offset to center reverse under obverse
    reverse_center_offset = 0
    if has_reverse and has_obverse:
        obverse_center = central_column_x + central_column_width // 2
        reverse_center = obverse_center  # We want to align reverse center with obverse center
    
    # Calculate total width of all elements in the reverse row
    rev_row_width = 0
    rev_row_elements = []
    
    # Add left side
    if has_left:
        rev_row_elements.append({"key": "left_rotated", "width": l_w})
        rev_row_width += l_w + view_gap_px
    
    # Add all intermediate_reverse_left variants in reverse order (rl3, rl2, rl)
    left_intermediates = grouped_intermediates["reverse_left"]
    left_intermediates.sort(key=lambda x: x["number"], reverse=True)  # Highest number first
    
    for left_int in left_intermediates:
        int_key = left_int["key"]
        int_w = left_int["dims"]["w"]
        rev_row_elements.append({"key": int_key, "width": int_w})
        rev_row_width += int_w + view_gap_px
    
    # Add reverse
    if has_reverse:
        rev_row_elements.append({"key": "reverse", "width": rev_w})
        rev_row_width += rev_w + view_gap_px
    
    # Add all intermediate_reverse_right variants in order (rr, rr2, rr3)
    right_intermediates = grouped_intermediates["reverse_right"]
    right_intermediates.sort(key=lambda x: x["number"])  # Lowest number first
    
    for right_int in right_intermediates:
        int_key = right_int["key"]
        int_w = right_int["dims"]["w"]
        rev_row_elements.append({"key": int_key, "width": int_w})
        rev_row_width += int_w + view_gap_px
    
    # Add right side
    if has_right:
        rev_row_elements.append({"key": "right_rotated", "width": r_w})
        rev_row_width += r_w
    
    # Subtract extra gap
    if rev_row_width > 0:
        rev_row_width -= view_gap_px
        
    # Calculate offset to center the reverse row under the obverse
    reverse_row_offset = (canvas_w - rev_row_width) // 2
    if has_reverse and has_obverse:
        # Find the position of reverse in the row
        reverse_pos = 0
        for idx, elem in enumerate(rev_row_elements):
            if elem["key"] == "reverse":
                reverse_pos = idx
                break
        
        # Calculate the x position where reverse would be
        reverse_x_in_row = reverse_row_offset
        for i in range(reverse_pos):
            reverse_x_in_row += rev_row_elements[i]["width"] + view_gap_px
        
        # Calculate center of reverse if placed at this position
        reverse_center = reverse_x_in_row + rev_w // 2
        
        # Calculate adjustment to align with obverse center
        obverse_center = central_column_x + obv_w // 2
        reverse_center_offset = obverse_center - reverse_center
        
        reverse_row_offset += reverse_center_offset
    
    # Place all elements in the reverse row
    current_x = reverse_row_offset
    for element in rev_row_elements:
        key = element["key"]
        width = element["width"]
        
        if key == "reverse":
            coords["reverse"] = (current_x, rev_row_y)
        elif key == "left_rotated":
            # Rotated left aligned with reverse row
            rotated_left_y = rev_row_y + (rev_h - l_h) // 2
            coords["left_rotated"] = (current_x, rotated_left_y)
            rotation_flags["left_rotated"] = True
        elif key == "right_rotated":
            # Rotated right aligned with reverse row
            rotated_right_y = rev_row_y + (rev_h - r_h) // 2
            coords["right_rotated"] = (current_x, rotated_right_y)
            rotation_flags["right_rotated"] = True
        else:  # Intermediate images
            img_h = intermediate_dims[key]["h"]
            # Vertically center against reverse height
            int_y = rev_row_y + (rev_h - img_h) // 2
            coords[key] = (current_x, int_y)
        
        current_x += width + view_gap_px
    
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