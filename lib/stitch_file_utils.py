import os
import cv2
try:
    from image_utils import convert_to_bgr_if_needed
except ImportError:
    print("FATAL ERROR: stitch_file_utils.py cannot import from image_utils.py")
    def convert_to_bgr_if_needed(img): return img
from stitch_config import (
    OBJECT_FILE_SUFFIX, 
    SCALED_RULER_FILE_SUFFIX,
    INTERMEDIATE_SUFFIX_BASE,
    INTERMEDIATE_SUFFIX_FOR_OBJECTS
)

def find_processed_image_file(subfolder_path, base_name, view_specific_part, general_suffix):
    target_filename = f"{base_name}{view_specific_part}{general_suffix}"
    path = os.path.join(subfolder_path, target_filename)
    if os.path.exists(path): return path
    if view_specific_part.startswith("_0") and len(view_specific_part) == 3:
        alt_part = "_" + view_specific_part[2]
        alt_filename = f"{base_name}{alt_part}{general_suffix}"
        alt_path = os.path.join(subfolder_path, alt_filename)
        if os.path.exists(alt_path): return alt_path
    return None

def load_images_for_stitching_process(subfolder_path, image_base_name, view_patterns, include_intermediates=True, intermediate_suffix_patterns=None):
    """
    Load all images needed for the stitching process.
    
    Args:
        subfolder_path: Path to the folder containing the images
        image_base_name: Base name of the tablet images
        view_patterns: Dictionary mapping view names to file patterns
        include_intermediates: Whether to include intermediate images
        intermediate_suffix_patterns: Dictionary mapping suffix codes to position names
        
    Returns:
        Dictionary of loaded images for each view
    """
    loaded_image_arrays = {}
    
    # Load main views (obverse, reverse, etc.)
    for view_key, pattern_part in view_patterns.items():
        if view_key == "ruler":
            fp = find_processed_image_file(subfolder_path, image_base_name, "", SCALED_RULER_FILE_SUFFIX)
        else:
            fp = find_processed_image_file(subfolder_path, image_base_name, pattern_part, OBJECT_FILE_SUFFIX)
        
        if fp:
            try:
                img_array = cv2.imread(fp, cv2.IMREAD_UNCHANGED)
                if img_array is None:
                    print(f"      Warn: Stitch - Failed to load {view_key} from {fp}")
                    continue
                    
                img_array = convert_to_bgr_if_needed(img_array)
                print(f"      Stitch - Loaded {view_key} from {os.path.basename(fp)}")
                loaded_image_arrays[view_key] = img_array
            except Exception as e:
                print(f"      Error loading {view_key}: {e}")
    
    # Load intermediate images if requested
    if include_intermediates:
        # Use provided suffix patterns or default to INTERMEDIATE_SUFFIX_BASE
        suffix_patterns_to_use = intermediate_suffix_patterns or INTERMEDIATE_SUFFIX_BASE
        
        intermediate_images = detect_intermediate_images(
            subfolder_path,
            image_base_name,
            suffix_patterns_to_use,
            INTERMEDIATE_SUFFIX_FOR_OBJECTS
        )
        # Add detected intermediates to the loaded images dictionary
        loaded_image_arrays.update(intermediate_images)
    
    return loaded_image_arrays

def detect_intermediate_images(subfolder_path, base_name, intermediate_suffix_base, intermediate_suffix_for_objects):
    """
    Automatically detect images with intermediate position suffixes.
    
    Args:
        subfolder_path: Path to the folder containing the images
        base_name: Base name of the images
        intermediate_suffix_base: Dictionary mapping suffix codes to position names
        intermediate_suffix_for_objects: Dictionary mapping suffix codes to object file patterns
        
    Returns:
        Dictionary mapping positions to file paths
    """
    detected_images = {}
    all_files = os.listdir(subfolder_path)
    
    # Look for processed object files first
    for suffix_code, position in intermediate_suffix_base.items():
        # Look for processed object files (e.g., _ol_object.tif)
        object_pattern = intermediate_suffix_for_objects[suffix_code]
        
        for filename in all_files:
            if object_pattern.lower() in filename.lower() and filename.startswith(base_name):
                file_path = os.path.join(subfolder_path, filename)
                detected_images[position] = file_path
                print(f"      Detected processed intermediate image: {position} from {filename}")
                break
    
    # Process the detections to load the actual images
    loaded_intermediates = {}
    for position, file_path in detected_images.items():
        try:
            if not os.path.exists(file_path):
                print(f"      Warn: {position} file not found: {file_path}")
                continue
                
            img_array = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
            if img_array is None:
                print(f"      Warn: Failed to load {position} from {file_path}")
                continue
                
            img_array = convert_to_bgr_if_needed(img_array)
            print(f"      Stitch - Loaded {position} from {os.path.basename(file_path)}")
            loaded_intermediates[position] = img_array
        except Exception as e:
            print(f"      Error loading {position}: {e}")
    
    return loaded_intermediates
