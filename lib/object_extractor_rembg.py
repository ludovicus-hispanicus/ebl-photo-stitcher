import cv2
import numpy as np
import os
import sys
import shutil
import time
from rembg import remove
from PIL import Image, ImageOps
from object_extractor import DEFAULT_BACKGROUND_DETECTION_COLOR_TOLERANCE

def _download_with_progress(url, destination):
    """Download a file with progress reporting."""
    import requests
    from tqdm import tqdm
    
    print(f"  Downloading U2NET model from {url}")
    print(f"  This is a large file (~176MB) and may take several minutes.")
    
    try:

        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))

        temp_destination = destination + ".download"
        
        with open(temp_destination, 'wb') as f, tqdm(
                desc="  Downloading",
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
            for data in response.iter_content(chunk_size=1024*1024):
                if data:
                    size = f.write(data)
                    bar.update(size)

        shutil.move(temp_destination, destination)
        print(f"  Download complete! Model saved to {destination}")
        return True
        
    except Exception as e:
        print(f"  Error downloading model: {e}")

        if os.path.exists(temp_destination):
            os.remove(temp_destination)
        return False

def _ensure_local_model():
    """Ensures the U2NET model exists in the expected location."""
    user_home = os.path.expanduser("~")
    model_dir = os.path.join(user_home, ".u2net")
    model_path = os.path.join(model_dir, "u2net.onnx")

    if os.path.exists(model_path):
        return True

    os.makedirs(model_dir, exist_ok=True)

    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    assets_model_path = os.path.join(base_dir, "assets", "u2net.onnx")

    if os.path.exists(assets_model_path):
        print(f"  Copying U2NET model from local assets")
        try:
            shutil.copy2(assets_model_path, model_path)
            return True
        except Exception as e:
            print(f"  Error copying model: {e}")

    url = "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx"
    success = _download_with_progress(url, model_path)
    
    if not success:
        print("\n================================================================")
        print("  ERROR: Could not download or find the U2NET model.")
        print("  You can download it manually from:")
        print("  https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx")
        print(f"  And save it to: {model_path}")
        print("================================================================\n")
    
    return success

def extract_and_save_center_object(
    input_image_filepath,
    source_background_detection_mode="auto",
    output_image_background_color=(0, 0, 0),
    feather_radius_px=10,
    output_filename_suffix="_object.tif",
    min_object_area_as_image_fraction=0.01,
    object_contour_smoothing_kernel_size=3,
    museum_selection=None
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

    if not _ensure_local_model():
        raise RuntimeError("U2NET model is required but could not be downloaded or found.")

    try:
        input_img = Image.open(input_image_filepath)
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
        bbox = (0, 0, output_img.width, output_img.height)

        selected_object_mask = binary_mask
    else:

        center_x = output_img.width / 2
        center_y = output_img.height / 2

        obj_data = []
        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            cx, cy = centroids[i]

            distance_to_center = np.sqrt((cx - center_x)**2 + (cy - center_y)**2)
            obj_data.append((i, area, distance_to_center))

        obj_data.sort(key=lambda x: x[1], reverse=True)

        largest_objects = obj_data[:min(2, len(obj_data))]
        print(f"    Found {num_labels-1} separate objects")

        if len(largest_objects) == 1:

            selected_label = largest_objects[0][0]
            print(f"    Only one object found - using it")
        else:

            if largest_objects[0][2] <= largest_objects[1][2]:

                selected_label = largest_objects[0][0]
                print(f"    Two largest objects found - selecting the one closer to center")
            else:

                selected_label = largest_objects[1][0]
                print(f"    Two largest objects found - selecting the one closer to center")

        selected_object_mask = np.zeros_like(binary_mask)
        selected_object_mask[labels == selected_label] = 255

        y_indices, x_indices = np.where(selected_object_mask > 0)
        if len(y_indices) == 0:
            print("    Warning: No valid objects found!")
            bbox = (0, 0, output_img.width, output_img.height)
        else:
            x_min, x_max = np.min(x_indices), np.max(x_indices)
            y_min, y_max = np.min(y_indices), np.max(y_indices)

            padding = 10
            x_min = max(0, x_min - padding)
            y_min = max(0, y_min - padding)
            x_max = min(output_img.width, x_max + padding)
            y_max = min(output_img.height, y_max + padding)
            
            bbox = (x_min, y_min, x_max, y_max)

    selected_mask_pil = Image.fromarray(selected_object_mask)

    filtered_output = Image.new('RGBA', output_img.size, (0, 0, 0, 0))
    filtered_output.paste(output_img, (0, 0), selected_mask_pil)

    cropped_img = filtered_output.crop(bbox)

    bg_color_rgb = (output_image_background_color[2], 
                    output_image_background_color[1], 
                    output_image_background_color[0])

    bg_img = Image.new('RGB', cropped_img.size, bg_color_rgb)

    bg_img.paste(cropped_img, (0, 0), cropped_img)

    base_filepath, _ = os.path.splitext(input_image_filepath)
    output_image_filepath = f"{base_filepath}{output_filename_suffix}"
    
    try:

        bg_img.save(output_image_filepath)
        elapsed = time.time() - start_time
        print(f"    Successfully saved extracted artifact: {output_image_filepath} (took {elapsed:.2f}s)")

        dummy_contour = np.array([[[0, 0]], [[0, 1]], [[1, 1]], [[1, 0]]], dtype=np.int32)
        
        return output_image_filepath, dummy_contour
    except Exception as e:
        raise IOError(f"Error saving extracted artifact to {output_image_filepath}: {e}")