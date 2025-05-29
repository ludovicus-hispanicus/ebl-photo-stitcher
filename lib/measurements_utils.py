import json
import os
import re

def load_measurements_from_json(json_path):
    """
    Load measurements data from a JSON file.
    
    Args:
        json_path: Path to the JSON file containing measurements
        
    Returns:
        Dictionary mapping tablet IDs to their measurements, or empty dict if file not found
    """

    if not os.path.exists(json_path):
        return {}
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Create a lookup dictionary mapping _id to measurements
        measurements_dict = {}
        for item in data:
            if "_id" in item and "width" in item:
                measurements_dict[item["_id"]] = item
                
        return measurements_dict
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from measurements file: {e}")
        return {}
    except Exception as e:
        print(f"Error loading measurements file: {e}")
        return {}

def extract_tablet_id_from_path(folder_path):
    """
    Extract tablet ID from folder path.
    
    Args:
        folder_path: Path to the tablet folder
        
    Returns:
        Extracted tablet ID or None if not found
    """
    # Extract the last folder name
    folder_name = os.path.basename(folder_path)
    
    # Look for patterns like "BM_1234" or just "1234"
    # You may need to adjust this regex based on your actual file naming conventions
    match = re.search(r'(?:BM[_\s])?(\d+)', folder_name, re.IGNORECASE)
    if match:
        return match.group(1)  # Return just the number part
    
    return None

def get_tablet_width_from_measurements(folder_path, measurements_dict):
    """
    Get tablet width from measurements based on folder path.
    
    Args:
        folder_path: Path to the tablet folder
        measurements_dict: Dictionary with measurements data
        
    Returns:
        Width in cm if found, None otherwise
    """
    tablet_id = extract_tablet_id_from_path(folder_path)
    if not tablet_id:
        return None
    
    # Try different ID formats (add more as needed based on your data)
    potential_ids = [
        tablet_id,
        f"BM.{tablet_id}",
        f"BM {tablet_id}",
        f"BM_{tablet_id}"
    ]
    
    for id_format in potential_ids:
        if id_format in measurements_dict:
            width_cm = measurements_dict[id_format].get("width")
            if width_cm is not None and isinstance(width_cm, (int, float)) and width_cm > 0:
                print(f"Found measurement for ID {id_format}: {width_cm} cm")
                return width_cm
    
    print(f"No measurement found for tablet ID: {tablet_id}")
    return None

def is_valid_measurements_file(file_path):
    """
    Check if the given file is a valid measurements JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        True if valid, False otherwise
    """
    if not os.path.exists(file_path):
        return False
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if not isinstance(data, list) or len(data) == 0:
            return False
            
        # Check at least the first item has required fields
        return "_id" in data[0] and "width" in data[0]
    except:
        return False