import cv2
import numpy as np
import json
import os
from typing import Optional, Tuple, Dict, Any, List

_fallback_comparisons = []


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

        print(
            f"Calculated measurements for {file_id}: {width_cm:.2f}cm x {height_cm:.2f}cm")
        return measurement_record

    except Exception as e:
        print(f"Error calculating measurements for {file_id}: {e}")
        return None


def track_fallback_comparison(object_id: str, calculated_measurements: Dict,
                              reference_measurements: Dict, was_fallback: bool = True):
    """
    Track a comparison between calculated and reference measurements for fallback cases.

    Args:
        object_id: The object ID
        calculated_measurements: Measurements calculated from photograph
        reference_measurements: Reference measurements from sippar.json
        was_fallback: True if measurements were used as fallback (not primary)
    """
    global _fallback_comparisons

    if not was_fallback:
        return

    try:
        from extract_measurements_excel import calculate_deviation_percentage

        calc_width = calculated_measurements.get("width", {}).get("value", 0)
        calc_length = calculated_measurements.get("length", {}).get("value", 0)

        ref_width = reference_measurements.get("width", 0)
        ref_length = reference_measurements.get("length", 0)

        width_deviation = calculate_deviation_percentage(ref_width, calc_width)
        length_deviation = calculate_deviation_percentage(ref_length, calc_length)

        if width_deviation != float('inf') and length_deviation != float('inf'):
            global_deviation = (abs(width_deviation) + abs(length_deviation)) / 2
        else:
            global_deviation = float('inf')

        comparison_record = {
            'Object_id': object_id,
            'Width × Length (From database)': f"{ref_width} × {ref_length}",
            'Width × Length (Calculated from photograph)': f"{calc_width} × {calc_length}",
            'Width Deviation (%)': round(width_deviation, 2) if width_deviation != float('inf') else 'N/A',
            'Length Deviation (%)': round(length_deviation, 2) if length_deviation != float('inf') else 'N/A',
            'Global Deviation (%)': round(global_deviation, 2) if global_deviation != float('inf') else 'N/A'
        }

        _fallback_comparisons.append(comparison_record)
        print(
            f"Tracked fallback comparison for {object_id}: Global deviation {comparison_record['Global Deviation (%)']}%")

    except Exception as e:
        print(f"Error tracking fallback comparison for {object_id}: {e}")


def clear_fallback_comparisons():
    """Clear the global fallback comparisons list (useful for new processing runs)."""
    global _fallback_comparisons
    _fallback_comparisons = []
    print("Cleared fallback comparison tracking")


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
                           file_id: str, gap_pixels: int = 0, output_dir: str = None,
                           was_fallback_measurement: bool = False) -> bool:
    """
    Calculate measurements for an object and add to the JSON file.

    Args:
        object_image_path (str): Path to the _object.tif file
        pixels_per_cm (float): Conversion factor from pixels to centimeters
        file_id (str): The base filename without suffixes
        gap_pixels (int): Number of gap pixels added during extraction
        output_dir (str): Directory to save the JSON file
        was_fallback_measurement (bool): True if measurements were used as fallback

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        measurement_record = calculate_object_measurements(
            object_image_path, pixels_per_cm, file_id, gap_pixels)

        if measurement_record is None:
            return False

        if was_fallback_measurement:
            from extract_measurements_excel import load_sippar_reference_data
            
            sippar_data = load_sippar_reference_data()
            
            if file_id in sippar_data:
                track_fallback_comparison(
                    file_id, measurement_record, sippar_data[file_id], was_fallback=True)
            else:
                available_keys = list(sippar_data.keys())[:5]

        existing_measurements = load_existing_measurements(output_dir)

        existing_measurements = [m for m in existing_measurements if m.get("_id") != file_id]

        existing_measurements.append(measurement_record)

        return save_measurements_to_json(existing_measurements, output_dir)

    except Exception as e:
        print(f"Error adding measurement record for {file_id}: {e}")
        import traceback
        traceback.print_exc()
        return False
