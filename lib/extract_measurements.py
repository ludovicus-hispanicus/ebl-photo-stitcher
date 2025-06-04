import cv2
import numpy as np
import json
import os
from typing import Optional, Tuple, Dict, Any, List
import pandas as pd

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


def load_sippar_reference_data() -> Dict[str, Dict]:
    """
    Load reference measurements from assets/sippar.json.

    Returns:
        Dictionary mapping object IDs to their reference measurements
    """
    try:
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sippar_path = os.path.join(script_dir, "assets", "sippar.json")

        print(f"DEBUG: Looking for sippar.json at: {sippar_path}")
        print(f"DEBUG: File exists: {os.path.exists(sippar_path)}")

        if not os.path.exists(sippar_path):
            print(f"Warning: sippar.json not found at {sippar_path}")
            return {}

        with open(sippar_path, 'r', encoding='utf-8') as f:
            sippar_list = json.load(f)

        print(f"DEBUG: Loaded JSON type: {type(sippar_list)}")
        print(f"DEBUG: JSON length: {len(sippar_list) if isinstance(sippar_list, list) else 'Not a list'}")

        sippar_dict = {}
        items_processed = 0
        items_with_id = 0
        
        for item in sippar_list:
            items_processed += 1
            if isinstance(item, dict) and "_id" in item:
                items_with_id += 1
                object_id = item["_id"]
                sippar_dict[object_id] = item
                print(f"DEBUG: Added object {object_id}: width={item.get('width', 'N/A')}, length={item.get('length', 'N/A')}")

        print(f"DEBUG: Processed {items_processed} items, {items_with_id} had '_id' field")
        print(f"DEBUG: Available object IDs: {list(sippar_dict.keys())[:10]}...")
        print(f"Loaded {len(sippar_dict)} reference measurements from sippar.json")

        if "BM.58103" in sippar_dict:
            print(f"DEBUG: Found BM.58103 in sippar data: {sippar_dict['BM.58103']}")
        else:
            print("DEBUG: BM.58103 NOT found in sippar data")
            
        return sippar_dict

    except Exception as e:
        print(f"Error loading sippar.json: {e}")
        import traceback
        traceback.print_exc()
        return {}


def calculate_deviation_percentage(reference_value: float, calculated_value: float) -> float:
    """
    Calculate percentage deviation between reference and calculated values.

    Args:
        reference_value: Value from database
        calculated_value: Value calculated from photograph

    Returns:
        Percentage deviation (calculated - reference) / reference * 100
    """
    if reference_value == 0:
        return float('inf') if calculated_value != 0 else 0.0

    return ((calculated_value - reference_value) / reference_value) * 100


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

        calc_width = calculated_measurements.get("width", {}).get("value", 0)
        calc_length = calculated_measurements.get("length", {}).get("value", 0)

        ref_width = reference_measurements.get("width", 0)
        ref_length = reference_measurements.get("length", 0)

        width_deviation = calculate_deviation_percentage(ref_width, calc_width)
        length_deviation = calculate_deviation_percentage(
            ref_length, calc_length)

        if width_deviation != float('inf') and length_deviation != float('inf'):
            global_deviation = (abs(width_deviation) +
                                abs(length_deviation)) / 2
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


def create_comparison_excel(output_dir: str = None) -> bool:
    """
    Create Excel file with fallback measurement comparisons.

    Args:
        output_dir: Directory to save the Excel file

    Returns:
        True if Excel file was created successfully, False otherwise
    """
    global _fallback_comparisons

    if not _fallback_comparisons:
        print("No fallback comparisons to export to Excel")
        return False

    try:
        if output_dir is None:
            output_dir = os.path.dirname(os.path.abspath(__file__))

        excel_path = os.path.join(output_dir, "measurement_comparison.xlsx")

        df = pd.DataFrame(_fallback_comparisons)
        df.to_excel(excel_path, index=False,
                    sheet_name="Measurement Comparison")

        print(f"Excel comparison file created: {excel_path}")
        print(
            f"Exported {len(_fallback_comparisons)} fallback measurement comparisons")

        return True

    except ImportError:
        print("Error: pandas and openpyxl are required for Excel export")
        print("Install with: pip install pandas openpyxl")
        return False
    except Exception as e:
        print(f"Error creating Excel comparison file: {e}")
        return False


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
        print(f"DEBUG: add_measurement_record called with file_id='{file_id}', was_fallback={was_fallback_measurement}")
        
        measurement_record = calculate_object_measurements(
            object_image_path, pixels_per_cm, file_id, gap_pixels)

        if measurement_record is None:
            print(f"DEBUG: measurement_record is None for {file_id}")
            return False

        # Check if this object should be tracked for comparison
        if was_fallback_measurement:
            print(f"DEBUG: Processing fallback measurement for {file_id}")
            sippar_data = load_sippar_reference_data()
            print(f"DEBUG: Checking if '{file_id}' is in sippar_data keys")
            
            if file_id in sippar_data:
                print(f"DEBUG: Found {file_id} in sippar data, tracking comparison")
                track_fallback_comparison(
                    file_id, measurement_record, sippar_data[file_id], was_fallback=True)
            else:
                print(f"DEBUG: {file_id} NOT found in sippar data")
                # Show what keys are available for debugging
                available_keys = list(sippar_data.keys())[:5]  # First 5 keys
                print(f"DEBUG: Available keys (first 5): {available_keys}")

        existing_measurements = load_existing_measurements(output_dir)

        # Remove any existing record for this object
        existing_measurements = [m for m in existing_measurements if m.get("_id") != file_id]

        existing_measurements.append(measurement_record)

        return save_measurements_to_json(existing_measurements, output_dir)

    except Exception as e:
        print(f"Error adding measurement record for {file_id}: {e}")
        import traceback
        traceback.print_exc()
        return False


def finalize_measurements_with_comparison(output_dir: str = None) -> bool:
    """
    Finalize the measurements process by creating both JSON and Excel outputs.
    Call this at the end of your processing workflow.

    Args:
        output_dir: Directory to save output files

    Returns:
        True if successful, False otherwise
    """
    try:

        excel_created = create_comparison_excel(output_dir)

        if excel_created:
            print("Measurement comparison workflow completed successfully")
        else:
            print("No fallback measurements to compare - Excel file not created")

        return True

    except Exception as e:
        print(f"Error finalizing measurements: {e}")
        return False
