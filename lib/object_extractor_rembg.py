import cv2
import numpy as np
import os
from rembg import remove
from PIL import Image, ImageOps
import time
import shutil
from object_extractor import DEFAULT_BACKGROUND_DETECTION_COLOR_TOLERANCE
import sys

def _ensure_local_model():
    """
    Ensures the U2NET model exists in the expected location by copying from assets.
    This prevents rembg from attempting to download the model.
    """
    # Determine user home directory for model location
    user_home = os.path.expanduser("~")
    model_dir = os.path.join(user_home, ".u2net")
    model_path = os.path.join(model_dir, "u2net.onnx")
    
    # Skip if model already exists
    if os.path.exists(model_path):
        return
    
    # Create directory if it doesn't exist
    os.makedirs(model_dir, exist_ok=True)
    
    # Determine assets directory - handle both normal run and packaged versions
    if getattr(sys, 'frozen', False):
        # Running in a PyInstaller bundle
        base_dir = os.path.dirname(sys.executable)
    else:
        # Running in normal Python environment
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    assets_model_path = os.path.join(base_dir, "assets", "u2net.onnx")
    
    # Copy the model if the asset exists
    if os.path.exists(assets_model_path):
        print(f"  Copying U2NET model from local assets instead of downloading")
        shutil.copy2(assets_model_path, model_path)
    else:
        print(f"  Warning: Local model not found at {assets_model_path}")
        # The program will still attempt to download in this case

def extract_and_save_center_object(
    input_image_filepath,
    source_background_detection_mode="auto", # Kept for compatibility 
    output_image_background_color=(0, 0, 0),
    feather_radius_px=10, # Kept for compatibility
    output_filename_suffix="_object.tif",
    min_object_area_as_image_fraction=0.01, # Kept for compatibility
    object_contour_smoothing_kernel_size=3, # Kept for compatibility
    museum_selection=None # Kept for compatibility
):
    """
    Extract the object closest to the center among the two largest objects.
    
    Args:
        input_image_filepath: Path to the input image
        output_image_background_color: BGR tuple for background color (OpenCV format)
        output_filename_suffix: Suffix for the output filename
        
    Returns:
        Tuple of (output_filepath, dummy_contour) for compatibility
    """
    print(f"  Extracting center object from: {os.path.basename(input_image_filepath)} using rembg")
    start_time = time.time()
    
    # Ensure the model exists locally before processing
    _ensure_local_model()
    
    # Load the image using PIL (rembg works with PIL images)
    try:
        input_img = Image.open(input_image_filepath)
    except Exception as e:
        raise FileNotFoundError(f"Could not load image for object extraction: {input_image_filepath} - {e}")
    
    # Remove the background using default settings
    output_img = remove(input_img)
    
    # Get the alpha channel as a binary mask with an appropriate threshold
    alpha = np.array(output_img.getchannel('A'))
    # Use the default threshold value to exclude very faint pixels
    binary_mask = (alpha > DEFAULT_BACKGROUND_DETECTION_COLOR_TOLERANCE / 2).astype(np.uint8) * 255
    
    # Apply morphological operations to clean up the mask
    kernel = np.ones((3, 3), np.uint8)
    binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel)
    
    # Find connected components in the mask (separate objects)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary_mask, connectivity=8)
    
    if num_labels <= 1:
        print("    Warning: No objects detected in the image!")
        bbox = (0, 0, output_img.width, output_img.height)
        # Use the whole image as mask
        selected_object_mask = binary_mask
    else:
        # Calculate image center
        center_x = output_img.width / 2
        center_y = output_img.height / 2
        
        # Skip label 0 (background) and find the two largest areas
        obj_data = []
        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            cx, cy = centroids[i]
            # Calculate distance from center
            distance_to_center = np.sqrt((cx - center_x)**2 + (cy - center_y)**2)
            obj_data.append((i, area, distance_to_center))
        
        # Sort by area (descending)
        obj_data.sort(key=lambda x: x[1], reverse=True)
        
        # Get the two largest objects
        largest_objects = obj_data[:min(2, len(obj_data))]
        print(f"    Found {num_labels-1} separate objects")
        
        # Select the object closest to the center among the two largest
        if len(largest_objects) == 1:
            # Only one object, use it
            selected_label = largest_objects[0][0]
            print(f"    Only one object found - using it")
        else:
            # Compare the two largest objects by distance to center
            if largest_objects[0][2] <= largest_objects[1][2]:
                # First object is closer to center
                selected_label = largest_objects[0][0]
                print(f"    Two largest objects found - selecting the one closer to center")
            else:
                # Second object is closer to center
                selected_label = largest_objects[1][0]
                print(f"    Two largest objects found - selecting the one closer to center")
        
        # Create a mask for only the selected object
        selected_object_mask = np.zeros_like(binary_mask)
        selected_object_mask[labels == selected_label] = 255
        
        # Find the bounding box of the selected object
        y_indices, x_indices = np.where(selected_object_mask > 0)
        if len(y_indices) == 0:
            print("    Warning: No valid objects found!")
            bbox = (0, 0, output_img.width, output_img.height)
        else:
            x_min, x_max = np.min(x_indices), np.max(x_indices)
            y_min, y_max = np.min(y_indices), np.max(y_indices)
            
            # Add padding
            padding = 10
            x_min = max(0, x_min - padding)
            y_min = max(0, y_min - padding)
            x_max = min(output_img.width, x_max + padding)
            y_max = min(output_img.height, y_max + padding)
            
            bbox = (x_min, y_min, x_max, y_max)
    
    # Create PIL mask from numpy array
    selected_mask_pil = Image.fromarray(selected_object_mask)
    
    # Create an alpha composite
    filtered_output = Image.new('RGBA', output_img.size, (0, 0, 0, 0))
    filtered_output.paste(output_img, (0, 0), selected_mask_pil)
    
    # Crop to the bounding box
    cropped_img = filtered_output.crop(bbox)
    
    # Convert output_image_background_color from BGR to RGB for PIL
    bg_color_rgb = (output_image_background_color[2], 
                    output_image_background_color[1], 
                    output_image_background_color[0])
    
    # Create a new image with the specified background color
    bg_img = Image.new('RGB', cropped_img.size, bg_color_rgb)
    
    # Paste the foreground onto the background using the alpha channel as mask
    bg_img.paste(cropped_img, (0, 0), cropped_img)
    
    # Save the image
    base_filepath, _ = os.path.splitext(input_image_filepath)
    output_image_filepath = f"{base_filepath}{output_filename_suffix}"
    
    try:
        # For TIF/JPG, save as RGB
        bg_img.save(output_image_filepath)
        elapsed = time.time() - start_time
        print(f"    Successfully saved extracted artifact: {output_image_filepath} (took {elapsed:.2f}s)")
        
        # Return dummy contour for compatibility
        dummy_contour = np.array([[[0, 0]], [[0, 1]], [[1, 1]], [[1, 0]]], dtype=np.int32)
        
        return output_image_filepath, dummy_contour
    except Exception as e:
        raise IOError(f"Error saving extracted artifact to {output_image_filepath}: {e}")