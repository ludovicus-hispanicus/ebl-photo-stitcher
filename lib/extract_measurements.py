import cv2
import numpy as np
import json
import os
from typing import Optional, Tuple, Dict, Any


def calculate_object_measurements(object_image_path: str, pixels_per_cm: float, 
                                file_id: str, gap_pixels: int = 0) -> Optional[Dict[str, Any]]:
    """
    Calculate the width and height of an extracted object in centimeters.
    
    Args:
        object_image_path (str): Path to the _object.tif file
        pixels_per_cm (float): Conversion factor from pixels to centimeters
        file_id (str): The base filename without suffixes
        gap_pixels (int): Number of gap pixels added on sides during extraction
        
    Returns:
        Dict containing measurement data or None if failed
    """
    try:

        img = cv2.imread(object_image_path)
        if img is None:
            print(f"Error: Could not load object image at {object_image_path}")
            return None
            
        height, width, _ = img.shape

        actual_width_pixels = width - (2 * gap_pixels)
        actual_height_pixels = height - (2 * gap_pixels)

        width_cm = actual_width_pixels / pixels_per_cm
        height_cm = actual_height_pixels / pixels_per_cm

        measurement_record = {
            "_id": file_id,
            "width": {
                "value": round(width_cm, 2),
                "note": "(ca.)"
            },
            "length": {
                "value": round(height_cm, 2), 
                "note": "(ca.)"
            },
            "pixels_per_cm": pixels_per_cm,
        }
        
        print(f"Calculated measurements for {file_id}: {width_cm:.2f}cm x {height_cm:.2f}cm")
        return measurement_record
        
    except Exception as e:
        print(f"Error calculating measurements for {file_id}: {e}")
        return None


def save_measurements_to_json(measurements_list: list, output_dir: str = None) -> bool:
    """
    Save measurements list to calculated_measurements.json file.
    
    Args:
        measurements_list (list): List of measurement dictionaries
        output_dir (str): Directory to save the file (defaults to script directory)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if output_dir is None:
            output_dir = os.path.dirname(os.path.abspath(__file__))
            
        json_path = os.path.join(output_dir, "calculated_measurements.json")
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(measurements_list, f, indent=2, ensure_ascii=False)
            
        print(f"Measurements saved to: {json_path}")
        return True
        
    except Exception as e:
        print(f"Error saving measurements to JSON: {e}")
        return False


def load_existing_measurements(output_dir: str = None) -> list:
    """
    Load existing measurements from calculated_measurements.json if it exists.
    
    Args:
        output_dir (str): Directory containing the JSON file
        
    Returns:
        list: Existing measurements or empty list if file doesn't exist
    """
    try:
        if output_dir is None:
            output_dir = os.path.dirname(os.path.abspath(__file__))
            
        json_path = os.path.join(output_dir, "calculated_measurements.json")
        
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return []
            
    except Exception as e:
        print(f"Error loading existing measurements: {e}")
        return []


def add_measurement_record(object_image_path: str, pixels_per_cm: float, 
                          file_id: str, gap_pixels: int = 0, output_dir: str = None) -> bool:
    """
    Calculate measurements for an object and add to the JSON file.
    
    Args:
        object_image_path (str): Path to the _object.tif file
        pixels_per_cm (float): Conversion factor from pixels to centimeters
        file_id (str): The base filename without suffixes
        gap_pixels (int): Number of gap pixels added during extraction
        output_dir (str): Directory to save the JSON file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:

        measurement_record = calculate_object_measurements(
            object_image_path, pixels_per_cm, file_id, gap_pixels)
            
        if measurement_record is None:
            return False

        existing_measurements = load_existing_measurements(output_dir)

        existing_measurements = [m for m in existing_measurements if m.get("_id") != file_id]

        existing_measurements.append(measurement_record)

        return save_measurements_to_json(existing_measurements, output_dir)
        
    except Exception as e:
        print(f"Error adding measurement record for {file_id}: {e}")
        return False