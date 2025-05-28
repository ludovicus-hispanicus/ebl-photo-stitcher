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
        if axis_index == 0: # Vertical blending - sum of heights minus overlaps, width is min width
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
        else: # Horizontal blending - sum of widths minus overlaps, height is min height
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
        "left": {"axis": 0, "match_dim": obv_h},   # Match obverse height
        "right": {"axis": 0, "match_dim": obv_h},  # Match obverse height
        "top": {"axis": 1, "match_dim": obv_w},    # Match obverse width
        "bottom": {"axis": 1, "match_dim": obv_w}, # Match obverse width
        "reverse": {"axis": 1, "match_dim": obv_w} # Match obverse width
        # Intermediate sequences will also be resized based on these rules if their keys match.
        # E.g., "obverse_top_intermediate_sequence" would align with "top" rule if not explicitly handled.
    }

    output_resized_images = {}
    for view_key, image_data in loaded_images_dictionary.items():
        if view_key == "obverse": # Obverse is the reference, already handled
            output_resized_images[view_key] = obverse_image_data
            continue

        params = None
        # Find matching resize rule (e.g. "obverse_top_intermediate" uses "top" rule)
        for r_key, r_params in resize_config.items():
            if r_key in view_key: # Simple substring match, might need refinement
                params = r_params
                break
        if not params and "ruler" not in view_key: # Ruler is not typically resized relative to obverse
             # If no specific rule, and not obverse or ruler, decide a default or skip.
             # For now, keep original if no rule applies (e.g. for custom arbitrary view names)
            print(f"      Resize: No specific resize rule for '{view_key}'. Keeping original.")
            output_resized_images[view_key] = image_data
            continue
        elif "ruler" in view_key:
            output_resized_images[view_key] = image_data # Keep ruler as is
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
                    resized_sequence.append(None) # Keep placeholder for failed loads
            output_resized_images[view_key] = [rs for rs in resized_sequence if rs is not None] if any(rs is not None for rs in resized_sequence) else None
        elif image_data is not None: # Was loaded, but not array or list (should not happen)
            output_resized_images[view_key] = None
            print(f"      Warn: Resize - Unexpected data type for {view_key}: {type(image_data)}")
        else:
            output_resized_images[view_key] = None # Was None initially
            
    return output_resized_images

def calculate_stitching_layout(images_dict, view_gap_px=STITCH_VIEW_GAP_PX, ruler_padding_px=STITCH_RULER_PADDING_PX, custom_layout=None, blend_overlap_px=0):
    """
    Calculate the canvas dimensions and coordinates for placing each image or blended sequence.
    Returns canvas dimensions, coordinate map, and the input images_dict.
    MODIFIED to handle sequences and use their post-blending dimensions for layout.
    The layout logic is still based on a standard 6-view + ruler concept but uses actual
    dimensions from images_dict (which could be single images or blended sequences).
    
    Also adds rotated left and right views next to the reverse view.
    NOW INCLUDES INTERMEDIATE IMAGES.
    """
    
    # Helper to determine which dimension is primary for a sequence based on key naming
    def get_sequence_primary_axis(view_key_for_seq):
        if "left" in view_key_for_seq.lower() or "right" in view_key_for_seq.lower():
            # This rule might need adjustment if intermediate keys like "intermediate_obverse_left"
            # are intended to be blended horizontally. For now, assume side pieces are vertically blended if sequences.
            # Typically, intermediates are single images after processing.
            if "intermediate" in view_key_for_seq.lower() and ("top" in view_key_for_seq.lower() or "bottom" in view_key_for_seq.lower()):
                 return 1 # intermediate_obverse_top/bottom are likely horizontal strips
            return 0 # Vertical blending for main left/right, primary dimension is height
        return 1 # Horizontal blending for top/bottom/obverse/reverse, primary dimension is width

    # Get dimensions of main tablet views, considering they might be sequences
    obv_data = images_dict.get("obverse")
    obv_h = get_image_dimension(obv_data, 0, blend_overlap_px if isinstance(obv_data, list) and get_sequence_primary_axis("obverse") == 0 else 0)
    obv_w = get_image_dimension(obv_data, 1, blend_overlap_px if isinstance(obv_data, list) and get_sequence_primary_axis("obverse") == 1 else 0)

    if obv_h == 0 or obv_w == 0:
        if custom_layout:
            for key, data in images_dict.items():
                if data is not None and "ruler" not in key: # Found an alternative primary image
                    print(f"      Layout: 'obverse' missing/invalid. Using '{key}' as primary for layout ref.")
                    obv_data = data
                    obv_h = get_image_dimension(obv_data, 0, blend_overlap_px if isinstance(obv_data, list) and get_sequence_primary_axis(key) == 0 else 0)
                    obv_w = get_image_dimension(obv_data, 1, blend_overlap_px if isinstance(obv_data, list) and get_sequence_primary_axis(key) == 1 else 0)
                    break
        if obv_h == 0 or obv_w == 0: 
            raise ValueError("A primary image (e.g., 'obverse' or other from custom_layout) with valid dimensions is required for layout.")

    l_w = get_image_dimension(images_dict.get("left"), 1, blend_overlap_px if isinstance(images_dict.get("left"), list) and get_sequence_primary_axis("left") == 1 else 0)
    r_w = get_image_dimension(images_dict.get("right"), 1, blend_overlap_px if isinstance(images_dict.get("right"), list) and get_sequence_primary_axis("right") == 1 else 0)
    b_h = get_image_dimension(images_dict.get("bottom"), 0, blend_overlap_px if isinstance(images_dict.get("bottom"), list) and get_sequence_primary_axis("bottom") == 0 else 0)
    rev_h = get_image_dimension(images_dict.get("reverse"), 0, blend_overlap_px if isinstance(images_dict.get("reverse"), list) and get_sequence_primary_axis("reverse") == 0 else 0)
    t_h = get_image_dimension(images_dict.get("top"), 0, blend_overlap_px if isinstance(images_dict.get("top"), list) and get_sequence_primary_axis("top") == 0 else 0)
    
    # Get left and right heights for vertical alignment with reverse
    l_h = get_image_dimension(images_dict.get("left"), 0, blend_overlap_px if isinstance(images_dict.get("left"), list) and get_sequence_primary_axis("left") == 0 else 0)
    r_h = get_image_dimension(images_dict.get("right"), 0, blend_overlap_px if isinstance(images_dict.get("right"), list) and get_sequence_primary_axis("right") == 0 else 0)
    
    rul_h = get_image_dimension(images_dict.get("ruler"), 0) # Ruler is assumed to be a single image
    rul_w = get_image_dimension(images_dict.get("ruler"), 1)

    # Get dimensions of intermediate images
    intermediate_dims = {}
    for key, img_data in images_dict.items():
        if "intermediate" in key and img_data is not None: # Process only existing intermediates
            # Assuming intermediates are single images or already blended if they were sequences.
            # The get_sequence_primary_axis might need refinement for intermediates if they can be sequences.
            h = get_image_dimension(img_data, 0, blend_overlap_px if isinstance(img_data, list) and get_sequence_primary_axis(key) == 0 else 0)
            w = get_image_dimension(img_data, 1, blend_overlap_px if isinstance(img_data, list) and get_sequence_primary_axis(key) == 1 else 0)
            if h > 0 and w > 0:
                intermediate_dims[key] = {"h": h, "w": w, "data": img_data}

    # Calculate first row width (left + int_obv_l + obverse + int_obv_r + right)
    row1_elements_widths = []
    if images_dict.get("left") is not None: row1_elements_widths.append(l_w)
    
    int_obv_l_key = "intermediate_obverse_left"
    if int_obv_l_key in intermediate_dims and images_dict.get("obverse") is not None: # Place if obverse exists
        row1_elements_widths.append(intermediate_dims[int_obv_l_key]["w"])
        
    if images_dict.get("obverse") is not None: row1_elements_widths.append(obv_w)
    
    int_obv_r_key = "intermediate_obverse_right"
    if int_obv_r_key in intermediate_dims and images_dict.get("obverse") is not None: # Place if obverse exists
        row1_elements_widths.append(intermediate_dims[int_obv_r_key]["w"])

    if images_dict.get("right") is not None: row1_elements_widths.append(r_w)
    
    row1_w = sum(row1_elements_widths)
    if len(row1_elements_widths) > 1:
        row1_w += view_gap_px * (len(row1_elements_widths) - 1)
    elif not row1_elements_widths and obv_w > 0: row1_w = obv_w
    elif not row1_elements_widths: row1_w = 0


    bottom_w = get_image_dimension(images_dict.get("bottom"), 1, blend_overlap_px if isinstance(images_dict.get("bottom"), list) and get_sequence_primary_axis("bottom") == 1 else 0)
    reverse_w = get_image_dimension(images_dict.get("reverse"), 1, blend_overlap_px if isinstance(images_dict.get("reverse"), list) and get_sequence_primary_axis("reverse") == 1 else 0)
    top_w = get_image_dimension(images_dict.get("top"), 1, blend_overlap_px if isinstance(images_dict.get("top"), list) and get_sequence_primary_axis("top") == 1 else 0)

    # Calculate reverse row width (left_rotated + int_rev_l_rot + reverse + int_rev_r_rot + right_rotated)
    rev_row_elements_widths = []
    if images_dict.get("left") is not None: rev_row_elements_widths.append(l_w) # Rotated width is original left's width

    # Example keys for intermediates around reverse (these might need to match actual generated keys)
    int_rev_l_rot_key = "intermediate_reverse_left_rotated" 
    if int_rev_l_rot_key in intermediate_dims and images_dict.get("reverse") is not None:
        rev_row_elements_widths.append(intermediate_dims[int_rev_l_rot_key]["w"])

    if images_dict.get("reverse") is not None: rev_row_elements_widths.append(reverse_w)

    int_rev_r_rot_key = "intermediate_reverse_right_rotated"
    if int_rev_r_rot_key in intermediate_dims and images_dict.get("reverse") is not None:
        rev_row_elements_widths.append(intermediate_dims[int_rev_r_rot_key]["w"])

    if images_dict.get("right") is not None: rev_row_elements_widths.append(r_w) # Rotated width is original right's width
    
    rev_row_w = sum(rev_row_elements_widths)
    if len(rev_row_elements_widths) > 1:
        rev_row_w += view_gap_px * (len(rev_row_elements_widths) - 1)
    elif not rev_row_elements_widths and reverse_w > 0: rev_row_w = reverse_w
    elif not rev_row_elements_widths: rev_row_w = 0
    
    potential_canvas_widths = [row1_w, rev_row_w]
    # Add widths of single views that are centered (obverse, bottom, top, ruler)
    # Obverse width is part of row1_w.
    if bottom_w > 0: potential_canvas_widths.append(bottom_w)
    if top_w > 0: potential_canvas_widths.append(top_w)
    if rul_w > 0: potential_canvas_widths.append(rul_w)
    # Add widths of vertical intermediates if they are wider than obverse
    int_obv_t_key = "intermediate_obverse_top"
    if int_obv_t_key in intermediate_dims: potential_canvas_widths.append(intermediate_dims[int_obv_t_key]["w"])
    int_obv_b_key = "intermediate_obverse_bottom"
    if int_obv_b_key in intermediate_dims: potential_canvas_widths.append(intermediate_dims[int_obv_b_key]["w"])

    canvas_w = 0
    if potential_canvas_widths:
        canvas_w = max(w for w in potential_canvas_widths if w is not None) # Filter out None before max
    if canvas_w == 0 and obv_w > 0: canvas_w = obv_w # Fallback
    canvas_w += 200  # Add margins

    coords = {}
    rotation_flags = {} 
    y_curr = 100  # Starting Y margin
    
    obverse_x_start_for_centering = 0
    obverse_actual_width_for_centering = obv_w # Default to obverse's own width

    # --- ROW 1: Left - Intermediate_Obv_Left - Obverse - Intermediate_Obv_Right - Right ---
    start_x_row1 = (canvas_w - row1_w) // 2 if row1_w > 0 else (canvas_w - obv_w) // 2 # Fallback for centering obverse if row1_w is 0
    current_x_in_row1 = start_x_row1

    if images_dict.get("left") is not None:
        coords["left"] = (current_x_in_row1, y_curr)
        rotation_flags["left"] = False
        current_x_in_row1 += l_w + view_gap_px
    
    if int_obv_l_key in intermediate_dims and images_dict.get("obverse") is not None:
        int_data = intermediate_dims[int_obv_l_key]
        # Assuming intermediate is resized to match obverse height (obv_h)
        coords[int_obv_l_key] = (current_x_in_row1, y_curr + (obv_h - int_data["h"]) // 2) # Vertically center against obv_h
        current_x_in_row1 += int_data["w"] + view_gap_px

    # Position Obverse
    # If obverse is the first element in the conceptual row (no left, no int_obv_l)
    obv_x_final = current_x_in_row1
    if images_dict.get("left") is None and not (int_obv_l_key in intermediate_dims and images_dict.get("obverse") is not None):
        obv_x_final = start_x_row1
        
    if images_dict.get("obverse") is not None:
        coords["obverse"] = (obv_x_final, y_curr)
        obverse_x_start_for_centering = obv_x_final 
        obverse_actual_width_for_centering = obv_w
        current_x_in_row1 = obv_x_final + obv_w + view_gap_px
    else: # Fallback if obverse is missing (should be caught by earlier checks)
        obverse_x_start_for_centering = (canvas_w - 0) // 2 
        current_x_in_row1 = obverse_x_start_for_centering

    if int_obv_r_key in intermediate_dims and images_dict.get("obverse") is not None:
        int_data = intermediate_dims[int_obv_r_key]
        coords[int_obv_r_key] = (current_x_in_row1, y_curr + (obv_h - int_data["h"]) // 2) # Vertically center against obv_h
        current_x_in_row1 += int_data["w"] + view_gap_px
            
    if images_dict.get("right") is not None:
        # If right is the first element after obverse (no int_obv_r)
        # current_x_in_row1 should already be correctly positioned by obverse or int_obv_r
        coords["right"] = (current_x_in_row1, y_curr)
        rotation_flags["right"] = False
        
    y_curr += obv_h # Advance Y position past the main row (using obverse height as reference for the row)
    
    # --- Intermediate Obverse Bottom ---
    if int_obv_b_key in intermediate_dims:
        y_curr += view_gap_px
        int_data = intermediate_dims[int_obv_b_key]
        # Center under the obverse view's footprint
        int_x = obverse_x_start_for_centering + (obverse_actual_width_for_centering - int_data["w"]) // 2
        coords[int_obv_b_key] = (int_x, y_curr)
        y_curr += int_data["h"]

    # --- Bottom View ---
    if images_dict.get("bottom") is not None and b_h > 0:
        y_curr += view_gap_px
        bottom_x_pos = obverse_x_start_for_centering + (obverse_actual_width_for_centering - bottom_w) // 2 
        coords["bottom"] = (bottom_x_pos, y_curr)
        y_curr += b_h
    
    # --- Reverse Row: Rotated Left - Int_Rev_L_Rot - Reverse - Int_Rev_R_Rot - Rotated Right ---
    reverse_row_y_start = 0
    if images_dict.get("reverse") is not None and rev_h > 0: # Check if reverse itself exists for the row
        y_curr += view_gap_px
        reverse_row_y_start = y_curr
        
        rev_row_start_x = (canvas_w - rev_row_w) // 2 if rev_row_w > 0 else (canvas_w - reverse_w) // 2
        current_x_in_rev_row = rev_row_start_x
        
        if images_dict.get("left") is not None: # Rotated left
            # Vertically center rotated left (height l_h) with reverse view (height rev_h)
            coords["left_rotated"] = (current_x_in_rev_row, reverse_row_y_start + (rev_h - l_h) // 2)
            rotation_flags["left_rotated"] = True
            current_x_in_rev_row += l_w + view_gap_px # l_w is original width
        
        if int_rev_l_rot_key in intermediate_dims and images_dict.get("reverse") is not None:
            int_data = intermediate_dims[int_rev_l_rot_key]
            coords[int_rev_l_rot_key] = (current_x_in_rev_row, reverse_row_y_start + (rev_h - int_data["h"]) // 2)
            current_x_in_rev_row += int_data["w"] + view_gap_px

        # Position Reverse
        rev_x_final = current_x_in_rev_row
        if images_dict.get("left") is None and not (int_rev_l_rot_key in intermediate_dims and images_dict.get("reverse") is not None):
             rev_x_final = rev_row_start_x

        if images_dict.get("reverse") is not None: # Ensure reverse is placed if it's the primary part of this row
            coords["reverse"] = (rev_x_final, reverse_row_y_start)
            current_x_in_rev_row = rev_x_final + reverse_w + view_gap_px
        
        if int_rev_r_rot_key in intermediate_dims and images_dict.get("reverse") is not None:
            int_data = intermediate_dims[int_rev_r_rot_key]
            coords[int_rev_r_rot_key] = (current_x_in_rev_row, reverse_row_y_start + (rev_h - int_data["h"]) // 2)
            current_x_in_rev_row += int_data["w"] + view_gap_px
        
        if images_dict.get("right") is not None: # Rotated right
            coords["right_rotated"] = (current_x_in_rev_row, reverse_row_y_start + (rev_h - r_h) // 2)
            rotation_flags["right_rotated"] = True
        
        y_curr += rev_h # Advance Y past the reverse row height
    
    # --- Intermediate Obverse Top ---
    # Placed after Reverse row and before Top view, centered under obverse.
    if int_obv_t_key in intermediate_dims:
        y_curr += view_gap_px
        int_data = intermediate_dims[int_obv_t_key]
        int_x = obverse_x_start_for_centering + (obverse_actual_width_for_centering - int_data["w"]) // 2
        coords[int_obv_t_key] = (int_x, y_curr)
        y_curr += int_data["h"]
            
    # --- Top View ---
    if images_dict.get("top") is not None and t_h > 0:
        y_curr += view_gap_px
        top_x_pos = obverse_x_start_for_centering + (obverse_actual_width_for_centering - top_w) // 2
        coords["top"] = (top_x_pos, y_curr)
        y_curr += t_h
            
    # --- Ruler View ---
    if images_dict.get("ruler") is not None and rul_h > 0:
        y_curr += ruler_padding_px
        ruler_x_pos = obverse_x_start_for_centering + (obverse_actual_width_for_centering - rul_w) // 2
        coords["ruler"] = (ruler_x_pos, y_curr)
        y_curr += rul_h

    canvas_h = y_curr + 100 # Final canvas height with bottom margin

    modified_images_dict = dict(images_dict) # Start with all original/resized images
    
    if images_dict.get("left") is not None and "left_rotated" in coords: # Check if it's actually placed
        left_img_data = images_dict["left"]
        if isinstance(left_img_data, np.ndarray) and left_img_data.size > 0:
            modified_images_dict["left_rotated"] = cv2.rotate(left_img_data, cv2.ROTATE_180)
        elif isinstance(left_img_data, list) and left_img_data: # If left is a sequence
             # Rotation of sequences needs careful handling: rotate each, or blend then rotate.
             # Assuming for now 'left' for rotation is a single image.
             # If it's a blended sequence, it should be a single ndarray by this point.
            print("      Warn: 'left' is a list, rotation for 'left_rotated' might be unexpected.")


    if images_dict.get("right") is not None and "right_rotated" in coords: # Check if it's actually placed
        right_img_data = images_dict["right"]
        if isinstance(right_img_data, np.ndarray) and right_img_data.size > 0:
            modified_images_dict["right_rotated"] = cv2.rotate(right_img_data, cv2.ROTATE_180)
        elif isinstance(right_img_data, list) and right_img_data:
            print("      Warn: 'right' is a list, rotation for 'right_rotated' might be unexpected.")
            
    # Add intermediate images to modified_images_dict if they are not already effectively there
    # (images_dict already contains them, so this is more about ensuring they are considered by the caller)
    for key, data in intermediate_dims.items():
        if key in coords: # Only include intermediates that were actually placed
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