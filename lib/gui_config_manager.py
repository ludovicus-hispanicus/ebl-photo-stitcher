\
import os
import json

CONFIG_FILENAME_ONLY = "gui_config.json"

DEFAULT_PHOTOGRAPHER = "Ivor Kerslake"

def save_config(config_file_path, config_data):
    """Saves the configuration data to a JSON file."""
    try:
        os.makedirs(os.path.dirname(config_file_path), exist_ok=True)
        with open(config_file_path, "w") as f:
            json.dump(config_data, f, indent=4)
        print(f"Config saved: {config_file_path}")
        return True
    except Exception as e:
        print(f"Error saving config to {config_file_path}: {e}")
        return False

def load_config(config_file_path):
    """Loads configuration data from a JSON file."""
    config_data = {}
    try:
        if os.path.exists(config_file_path):
            with open(config_file_path, "r") as f:
                config_data = json.load(f)
            print(f"Config loaded: {config_file_path}")
    except Exception as e:
        print(f"Warn: Could not load config from {config_file_path}: {e}")

    return config_data

def get_default_config_values():
    """Returns a dictionary of default configuration values."""
    return {
        "last_folder": "",
        "last_ruler_position": "top",
        "last_photographer": DEFAULT_PHOTOGRAPHER,
        "last_add_logo": False,
        "last_logo_path": "",
        "last_museum": "British Museum"
    }
