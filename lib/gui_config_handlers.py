"""Configuration handling for the eBL Photo Stitcher application."""

import json
import os
from gui_config_manager import DEFAULT_PHOTOGRAPHER


class ConfigManager:
    """Manager for saving and loading application configuration."""

    @staticmethod
    def save_config(app_instance, config_file_path):
        """Save application configuration."""
        try:
            advanced_settings = app_instance.advanced_tab.get_settings()
            ruler_settings = app_instance.advanced_ruler_tab.get_settings()
            logo_settings = app_instance.advanced_logo_tab.get_settings()

            config = {
                'input_folder': app_instance.input_folder_var.get(),
                'ruler_position': app_instance.ruler_position_var.get(),
                'photographer_name': app_instance.photographer_var.get(),
                'museum_selection': app_instance.museum_var.get(),
                'use_measurements': app_instance.use_measurements_var.get(),
                'enable_hdr_processing': app_instance.enable_hdr_processing.get(),
                # Advanced settings
                'gradient_width_fraction': advanced_settings['gradient_width_fraction'],
                'background_color_tolerance': advanced_settings['background_color_tolerance'],
                'rotation_angle': advanced_settings['rotation_angle'],
                'multi_object_detection': advanced_settings['multi_object_detection'],
                # Logo settings
                'add_logo': logo_settings['add_logo'],
                'logo_path': logo_settings['logo_path'],
                # Ruler settings
                'ruler_settings': ruler_settings
            }

            os.makedirs(os.path.dirname(config_file_path), exist_ok=True)

            with open(config_file_path, 'w') as f:
                json.dump(config, f, indent=2)

            print(f"Configuration saved to {config_file_path}")

        except Exception as e:
            print(f"Error saving configuration: {e}")

    @staticmethod
    def load_config(app_instance, config_file_path):
        """Load application configuration."""
        try:
            if not os.path.exists(config_file_path):
                print(f"No configuration file found at {config_file_path}. Using defaults.")
                return

            with open(config_file_path, 'r') as f:
                config = json.load(f)

            app_instance.input_folder_var.set(config.get('input_folder', ''))
            app_instance.ruler_position_var.set(config.get('ruler_position', 'top'))
            app_instance.photographer_var.set(config.get('photographer_name', DEFAULT_PHOTOGRAPHER))
            app_instance.museum_var.set(config.get('museum_selection', 'British Museum'))
            app_instance.use_measurements_var.set(config.get('use_measurements', False))
            app_instance.enable_hdr_processing.set(config.get('enable_hdr_processing', False))

            # Load advanced settings
            advanced_settings = {
                'gradient_width_fraction': config.get('gradient_width_fraction', 0.5),
                'background_color_tolerance': config.get('background_color_tolerance', app_instance.DEFAULT_BACKGROUND_DETECTION_COLOR_TOLERANCE),
                'rotation_angle': config.get('rotation_angle', 0),
                'multi_object_detection': config.get('multi_object_detection', False)
            }
            app_instance.advanced_tab.set_settings(advanced_settings)  # Changed from apply_settings

            # Load logo settings
            logo_settings = {
                'add_logo': config.get('add_logo', False),
                'logo_path': config.get('logo_path', '')
            }
            app_instance.advanced_logo_tab.set_settings(logo_settings)

            # Load ruler settings
            ruler_settings = config.get('ruler_settings', {})
            if ruler_settings:
                app_instance.advanced_ruler_tab.set_settings(ruler_settings)

            print(f"Configuration loaded from {config_file_path}")

        except Exception as e:
            print(f"Error loading configuration: {e}")

            app_instance.ruler_position_var.set('top')
            app_instance.photographer_var.set(DEFAULT_PHOTOGRAPHER)
            app_instance.museum_var.set('British Museum')
            app_instance.use_measurements_var.set(False)
            app_instance.enable_hdr_processing.set(False)
