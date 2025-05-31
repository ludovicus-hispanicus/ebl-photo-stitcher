"""Configuration handling for the eBL Photo Stitcher application."""

class ConfigManager:
    """Extended configuration management for the application."""
    
    @staticmethod
    def save_config(app_instance, config_file_path):
        """Save configuration to a file."""
        from gui_config_manager import save_config as save_app_config
        
        # Collect all configuration values
        cfg_data = {
            "last_folder": app_instance.input_folder_var.get(), 
            "last_ruler_position": app_instance.ruler_position_var.get(),
            "last_photographer": app_instance.photographer_var.get(), 
            "last_add_logo": app_instance.add_logo_var.get(),
            "last_logo_path": app_instance.logo_path_var.get(), 
            "last_museum": app_instance.museum_var.get(),
            "last_use_measurements": app_instance.use_measurements_var.get(),
            "gradient_width_fraction": app_instance.advanced_tab.gradient_width_fraction.get(),
            "background_color_tolerance": app_instance.advanced_tab.background_color_tolerance.get(),
        }
        
        # Save to file
        save_app_config(config_file_path, cfg_data)

    @staticmethod
    def load_config(app_instance, config_file_path):
        """Load configuration from a file."""
        from gui_config_manager import load_config as load_app_config, get_default_config_values
        
        # Load config file
        loaded_cfg = load_app_config(config_file_path)
        defaults = get_default_config_values()
        
        # Apply configuration values
        app_instance.input_folder_var.set(loaded_cfg.get("last_folder", defaults["last_folder"]))
        app_instance.ruler_position_var.set(loaded_cfg.get("last_ruler_position", defaults["last_ruler_position"]))
        app_instance.photographer_var.set(loaded_cfg.get("last_photographer", defaults["last_photographer"]))
        app_instance.add_logo_var.set(loaded_cfg.get("last_add_logo", defaults["last_add_logo"]))
        app_instance.logo_path_var.set(loaded_cfg.get("last_logo_path", defaults["last_logo_path"]))
        app_instance.museum_var.set(loaded_cfg.get("last_museum", defaults["last_museum"]))
        
        # Load use measurements setting if available
        if app_instance.measurements_loaded:
            app_instance.use_measurements_var.set(loaded_cfg.get("last_use_measurements", False))
        
        # Load advanced settings
        app_instance.gradient_width_fraction = loaded_cfg.get("gradient_width_fraction", 0.5)
        background_tolerance = loaded_cfg.get(
            "background_color_tolerance", 
            app_instance.DEFAULT_BACKGROUND_DETECTION_COLOR_TOLERANCE
        )
        
        # Apply advanced settings to the advanced tab if it exists
        if hasattr(app_instance, 'advanced_tab'):
            app_instance.advanced_tab.apply_settings({
                'gradient_width_fraction': app_instance.gradient_width_fraction,
                'background_color_tolerance': background_tolerance
            })
        
        # Update UI based on loaded settings
        app_instance.toggle_logo_path_entry()