import os
import sys
import json
import tkinter as tk
from tkinter import messagebox, ttk
import webbrowser

script_directory = os.path.dirname(os.path.abspath(__file__))
lib_directory = os.path.join(script_directory, "lib")
if lib_directory not in sys.path:
    sys.path.insert(0, lib_directory)

try:
    from gui_utils import resource_path, get_persistent_config_dir_path, TextRedirector
    from gui_config_manager import (
        DEFAULT_PHOTOGRAPHER,
    )
    from version_checker import CURRENT_VERSION, VersionChecker, get_current_version
    from gui_workflow_runner import run_complete_image_processing_workflow
    from workflow_imports import (
        resize_ruler, ruler_detector, extract_and_save_center_object,
        extract_specific_contour_to_image_array, DEFAULT_BACKGROUND_DETECTION_COLOR_TOLERANCE,
        create_foreground_mask, select_contour_closest_to_image_center,
        select_ruler_like_contour
    )
    from object_extractor import DEFAULT_EXTRACTED_OBJECT_FILENAME_SUFFIX as OBJECT_ARTIFACT_SUFFIX
    from raw_processor import convert_raw_image_to_tiff
    from stitch_images import process_tablet_subfolder
    import stitch_config
    from stitch_config import (
        STITCH_VIEW_PATTERNS_BASE,
        STITCH_VIEW_PATTERNS_WITH_EXT,
        INTERMEDIATE_SUFFIX_WITH_EXT,
    )
    from put_images_in_subfolders import group_and_move_files_to_subfolders as organize_to_subfolders
    from measurements_utils import load_measurements_from_json
    from gui_advanced import AdvancedTab, AdvancedRulerTab, AdvancedLogoTab

    from gui_components import UIComponents
    from gui_layout import LayoutManager
    update_version_button = LayoutManager.update_version_button
    from gui_events import EventHandlers
    from gui_config_handlers import ConfigManager
    from gui_museum_options import MuseumOptionsManager

except ImportError as e:

    expected_lib_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "lib")

    try:
        root_err_tk = tk.Tk()
        root_err_tk.withdraw()
        messagebox.showerror(
            "Startup Error", f"Critical library module import failed: {e}\nAttempted to load from 'lib' package. Ensure 'lib' directory exists at '{expected_lib_path}' and contains all required modules and an __init__.py file.")
    except Exception:
        print(
            f"ERROR: Critical library module import failed: {e}\nAttempted to load from 'lib' package. Ensure 'lib' directory exists at '{expected_lib_path}' and contains all required modules and an __init__.py file.")
    sys.exit(1)

ASSETS_SUBFOLDER = "assets"
ICON_FILENAME_ONLY = "eBL_logo.png"
RULER_1CM_FILENAME_ONLY = "BM_1cm_scale.tif"
RULER_2CM_FILENAME_ONLY = "BM_2cm_scale.tif"
RULER_5CM_FILENAME_ONLY = "BM_5cm_scale.tif"
ICON_FILE_ASSET_PATH = resource_path(
    os.path.join(ASSETS_SUBFOLDER, ICON_FILENAME_ONLY))
RULER_TEMPLATE_1CM_PATH_ASSET = resource_path(
    os.path.join(ASSETS_SUBFOLDER, RULER_1CM_FILENAME_ONLY))
RULER_TEMPLATE_2CM_PATH_ASSET = resource_path(
    os.path.join(ASSETS_SUBFOLDER, RULER_2CM_FILENAME_ONLY))
RULER_TEMPLATE_5CM_PATH_ASSET = resource_path(
    os.path.join(ASSETS_SUBFOLDER, RULER_5CM_FILENAME_ONLY))
VALID_IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.tif', '.tiff', '.bmp')
RAW_IMAGE_EXTENSION = '.cr2'
TEMP_EXTRACTED_RULER_FOR_SCALING_FILENAME = "temp_isolated_ruler.tif"
HELP_URL = "https://github.com/ElectronicBabylonianLiterature/ebl-photo-stitcher?tab=readme-ov-file#usage-gui"

_ORIG_STITCH_CREDIT = stitch_config.STITCH_CREDIT_LINE
_ORIG_STITCH_INSTITUTION = stitch_config.STITCH_INSTITUTION


class ImageProcessorApp:
    def __init__(self, root_window):

        self.RAW_IMAGE_EXTENSION = RAW_IMAGE_EXTENSION
        self.VALID_IMAGE_EXTENSIONS = VALID_IMAGE_EXTENSIONS
        self.RULER_TEMPLATE_1CM_PATH_ASSET = RULER_TEMPLATE_1CM_PATH_ASSET
        self.RULER_TEMPLATE_2CM_PATH_ASSET = RULER_TEMPLATE_2CM_PATH_ASSET
        self.RULER_TEMPLATE_5CM_PATH_ASSET = RULER_TEMPLATE_5CM_PATH_ASSET
        self.STITCH_VIEW_PATTERNS_WITH_EXT = STITCH_VIEW_PATTERNS_WITH_EXT
        self.TEMP_EXTRACTED_RULER_FOR_SCALING_FILENAME = TEMP_EXTRACTED_RULER_FOR_SCALING_FILENAME
        self.OBJECT_ARTIFACT_SUFFIX = OBJECT_ARTIFACT_SUFFIX
        self.HELP_URL = HELP_URL
        self.DEFAULT_BACKGROUND_DETECTION_COLOR_TOLERANCE = DEFAULT_BACKGROUND_DETECTION_COLOR_TOLERANCE

        self.root = root_window
        self.root.title(f"eBL Photo Stitcher {CURRENT_VERSION}")
        self.root.geometry("600x950")

        self.config_file_path = os.path.join(
            get_persistent_config_dir_path(), "gui_config.json")

        self.input_folder_var = tk.StringVar()
        self.ruler_position_var = tk.StringVar()
        self.photographer_var = tk.StringVar()
        self.museum_var = tk.StringVar()
        self.progress_var = tk.DoubleVar(value=0.0)
        self.use_measurements_var = tk.BooleanVar(value=False)
        self.enable_hdr_processing = tk.BooleanVar(value=False)
        self.use_first_photo_measurements_var = tk.BooleanVar(value=False)
        self.gradient_width_fraction = 0.5

        self.measurements_loaded = False
        self.measurements_dict = {}
        measurements_file = resource_path(
            os.path.join(ASSETS_SUBFOLDER, "sippar.json"))
        if os.path.exists(measurements_file):
            self.measurements_dict = load_measurements_from_json(
                measurements_file)
            self.measurements_loaded = len(self.measurements_dict) > 0

        self.version_checker = VersionChecker(callback=self._on_version_check_complete)
        self.version_button = None
        self.version_check_timeout_id = None

        self._setup_icon()
        self._setup_styles()
        self._create_widgets()
        self.load_config()
        self.on_museum_changed(None)

        self.root.after(1000, self._start_version_check)
        self.version_check_timeout_id = self.root.after(
            8000, self._on_version_check_timeout)

    def _setup_icon(self):
        """Set up application icon."""
        try:
            if os.path.exists(ICON_FILE_ASSET_PATH):
                self.root.iconphoto(False, tk.PhotoImage(
                    file=ICON_FILE_ASSET_PATH))
        except Exception:

            pass

    def _setup_styles(self):
        """Set up ttk styles for the application."""
        self.style = LayoutManager.setup_styles(self.root)

        self.style.configure("Link.TButton",
                             foreground="blue",
                             relief="flat",
                             borderwidth=0)
        self.style.map("Link.TButton",
                       foreground=[('active', 'darkblue')])

    def _create_widgets(self):
        """Create all UI widgets."""
        mf = ttk.Frame(self.root, padding="10")
        mf.pack(expand=True, fill=tk.BOTH)

        self.header_frame, self.notebook, buttons_frame = LayoutManager.create_tabs(mf)

        self.version_button = LayoutManager.create_version_button(
            buttons_frame, self._on_version_button_click)

        self.help_btn = LayoutManager.create_help_link(
            buttons_frame, self.HELP_URL)

        self.main_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.main_tab, text="Main")

        self.folder_frame, self.fe = UIComponents.create_folder_selection_ui(
            self.main_tab, self.input_folder_var, self.browse_folder)

        self.metadata_frame, self.pe = UIComponents.create_photographer_ui(
            self.main_tab, self.photographer_var)

        self.ruler_frame, self.rc, self.canvas_params, self.museum_combo = UIComponents.create_ruler_pos_ui(
            self.main_tab, self.museum_var, self.ruler_position_var,
            self.on_museum_changed, self.on_ruler_canvas_click)

        self.options_frame, self.measurements_checkbox, self.hdr_checkbox, self.first_photo_measurements_checkbox = UIComponents.create_main_options_ui(
            self.main_tab, self.use_measurements_var, self.measurements_loaded,
            self.enable_hdr_processing, self.use_first_photo_measurements_var,
            script_directory, self.debug_measurements_loading)

        self.prb = UIComponents.create_process_button_ui(
            self.main_tab, self.start_processing_thread)

        self.progress_frame, self.progress_bar, self.progress_var = UIComponents.create_progress_bar_ui(
            self.main_tab)

        self.log_frame = ttk.LabelFrame(
            self.main_tab, text="Processing Log", padding="5")
        self.log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        text_frame = ttk.Frame(self.log_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self.lt = tk.Text(text_frame, height=10, wrap=tk.WORD, state=tk.DISABLED,
                          bg="#f0f0f0", font=("Consolas", 9))

        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.lt.yview)

        self.lt.configure(yscrollcommand=scrollbar.set)

        self.lt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        sys.stdout = TextRedirector(self.lt)

        self.advanced_tab = AdvancedTab(self.notebook)
        self.advanced_ruler_tab = AdvancedRulerTab(self.notebook)
        self.advanced_logo_tab = AdvancedLogoTab(self.notebook)

        settings = {
            'gradient_width_fraction': self.gradient_width_fraction,
            'background_color_tolerance': self.DEFAULT_BACKGROUND_DETECTION_COLOR_TOLERANCE,
            'add_logo': False,
            'logo_path': ''
        }
        self.advanced_tab.set_settings(settings)

    def draw_ruler_selector(self):
        """Draw the ruler selector canvas."""
        LayoutManager.draw_ruler_selector(
            self.rc, self.ruler_position_var.get(),
            self.museum_var.get(), self.canvas_params)

    def on_ruler_canvas_click(self, event):
        """Handle clicks on the ruler canvas."""
        EventHandlers.handle_ruler_canvas_click(
            event, self.canvas_params, self.ruler_position_var,
            self.museum_var, self.draw_ruler_selector)

    def on_museum_changed(self, event):
        """Handle museum selection changes."""
        EventHandlers.handle_museum_change(
            event, self.museum_var, self.ruler_position_var,
            self.measurements_checkbox, self.measurements_loaded,
            self.draw_ruler_selector, self.save_config)

    def browse_folder(self):
        """Browse for input folder."""
        EventHandlers.browse_input_folder(self.input_folder_var)

    def save_config(self):
        """Save application configuration."""
        advanced_settings = {}
        try:
            if hasattr(self, 'advanced_tab'):
                advanced_settings = self.advanced_tab.get_settings()
        except:
            pass
            
        config_data = {
            'input_folder': self.input_folder_var.get(),
            'ruler_position': self.ruler_position_var.get(),
            'photographer': self.photographer_var.get(),
            'museum': self.museum_var.get(),
            'use_measurements': self.use_measurements_var.get(),
            'enable_hdr_processing': self.enable_hdr_processing.get(),
            'advanced_settings': advanced_settings  # Save advanced settings including rotation
        }
        try:
            with open(self.config_file_path, 'w') as f:
                json.dump(config_data, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def load_config(self):
        """Load application configuration."""
        config_data = None
        try:
            if os.path.exists(self.config_file_path):
                with open(self.config_file_path, 'r') as f:
                    config_data = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load config: {e}")
            config_data = None

        if config_data:
            self.input_folder_var.set(config_data.get('input_folder', ''))
            self.ruler_position_var.set(config_data.get('ruler_position', 'top'))
            self.photographer_var.set(config_data.get('photographer', DEFAULT_PHOTOGRAPHER))
            self.museum_var.set(config_data.get('museum', 'British Museum'))
            self.use_measurements_var.set(config_data.get('use_measurements', False))
            self.enable_hdr_processing.set(config_data.get('enable_hdr_processing', False))

            if hasattr(self, 'advanced_tab') and 'advanced_settings' in config_data:
                try:
                    self.advanced_tab.set_settings(config_data['advanced_settings'])
                except Exception as e:
                    print(f"Warning: Could not load advanced settings: {e}")

        self.use_first_photo_measurements_var.set(False)

    def update_progress_bar(self, value):
        """Update the progress bar value."""
        self.progress_var.set(value)
        self.root.update_idletasks()

    def processing_finished_ui_update(self):
        """Update UI after processing is finished."""
        self.prb.config(state=tk.NORMAL)
        messagebox.showinfo("Processing Complete", "Workflow finished.")
        self.update_progress_bar(0)

    def configure_museum_settings(self, museum_selection):
        """Configure museum-specific settings."""
        MuseumOptionsManager.configure_museum_settings(
            museum_selection, stitch_config,
            _ORIG_STITCH_CREDIT, _ORIG_STITCH_INSTITUTION)

    def start_processing_thread(self):
        """Start the processing thread with current settings."""
        advanced_settings = self.advanced_tab.get_settings()
        logo_settings = self.advanced_logo_tab.get_settings()
        ruler_settings = self.advanced_ruler_tab.get_settings()
        
        combined_settings = {**advanced_settings, **logo_settings, **ruler_settings}

        workflow_args = [
            self.input_folder_var.get(),
            self.ruler_position_var.get(),
            self.photographer_var.get(),
            'rembg',
            logo_settings['add_logo'],
            logo_settings['logo_path'],
            self.RAW_IMAGE_EXTENSION,
            self.VALID_IMAGE_EXTENSIONS,
            self.RULER_TEMPLATE_1CM_PATH_ASSET,
            self.RULER_TEMPLATE_2CM_PATH_ASSET,
            self.RULER_TEMPLATE_5CM_PATH_ASSET,
            self.STITCH_VIEW_PATTERNS_WITH_EXT,
            self.TEMP_EXTRACTED_RULER_FOR_SCALING_FILENAME,
            self.OBJECT_ARTIFACT_SUFFIX,
            self.update_progress_bar,
            self.processing_finished_ui_update,
        ]

        workflow_kwargs = {
            'museum_selection': self.museum_var.get(),
            'app_root_window': self,
            'background_color_tolerance': advanced_settings['background_color_tolerance'],
            'use_measurements_from_database': self.use_measurements_var.get(),
            'measurements_dict': self.measurements_dict,
            'gradient_width_fraction': advanced_settings['gradient_width_fraction'],
            'enable_hdr_processing': self.enable_hdr_processing.get(),
            'use_first_photo_measurements': self.use_first_photo_measurements_var.get()
        }

        self.configure_museum_settings(self.museum_var.get())
        self.prb.config(state=tk.DISABLED)

        import threading
        workflow_thread = threading.Thread(
            target=run_complete_image_processing_workflow,
            args=workflow_args,
            kwargs=workflow_kwargs
        )
        workflow_thread.daemon = True
        workflow_thread.start()

    def debug_measurements_loading(self):
        """Debug function to test loading the measurements file."""
        EventHandlers.debug_measurements_loading(self, ASSETS_SUBFOLDER)

    def _start_version_check(self):
        """Start the background version check."""
        print("Checking for updates...")
        self.version_checker.check_for_updates_async()

    def _on_version_check_timeout(self):
        """Called if version check takes too long."""
        if not self.version_checker.check_completed:
            print("Version check timed out - showing current version")
            self.root.after(0, self._handle_version_update, None, False)

    def _on_version_check_complete(self, latest_version, is_newer_available):
        """Called when version check completes."""
        if self.version_check_timeout_id:
            self.root.after_cancel(self.version_check_timeout_id)

        self.root.after(0, self._handle_version_update,
                        latest_version, is_newer_available)

    def _handle_version_update(self, latest_version, is_newer_available):
        """Handle version update on main thread."""

        update_version_button(
            self.version_button,
            latest_version,
            is_newer_available,
            get_current_version
        )

        if latest_version is None:
            print("Version check failed - showing current version")
        elif is_newer_available:
            print(f"Update available: {latest_version}")
        else:
            print("Application is up to date")

    def _on_version_button_click(self):
        """Handle version button click (only works when update is available)."""
        if self.version_checker.is_newer_available:
            self.version_checker.open_releases_page()


if __name__ == "__main__":

    try:

        modules_to_check = {
            "resize_ruler_module": resize_ruler,
            "ruler_detector_module": ruler_detector,
            "stitch_images.process_tablet_subfolder": process_tablet_subfolder if 'stitch_images' in sys.modules and hasattr(sys.modules['stitch_images'], 'process_tablet_subfolder') else None,
            "object_extractor.extract_and_save_center_object": extract_and_save_center_object if 'object_extractor' in sys.modules and hasattr(sys.modules['object_extractor'], 'extract_and_save_center_object') else None,
            "object_extractor.extract_specific_contour_to_image_array": extract_specific_contour_to_image_array if 'object_extractor' in sys.modules and hasattr(sys.modules['object_extractor'], 'extract_specific_contour_to_image_array') else None,
            "remove_background.create_foreground_mask": create_foreground_mask if 'remove_background' in sys.modules and hasattr(sys.modules['remove_background'], 'create_foreground_mask_from_background') else None,
            "remove_background.select_contour_closest_to_image_center": select_contour_closest_to_image_center if 'remove_background' in sys.modules and hasattr(sys.modules['remove_background'], 'select_contour_closest_to_image_center') else None,
            "remove_background.select_ruler_like_contour": select_ruler_like_contour if 'remove_background' in sys.modules and hasattr(sys.modules['remove_background'], 'select_ruler_like_contour_from_list') else None,
            "raw_processor.convert_raw_image_to_tiff": convert_raw_image_to_tiff if 'raw_processor' in sys.modules and hasattr(sys.modules['raw_processor'], 'convert_raw_image_to_tiff') else None,
            "put_images_in_subfolders.organize_files": organize_to_subfolders,
            "gui_utils.resource_path": resource_path,
            "gui_utils.get_persistent_config_dir_path": get_persistent_config_dir_path,
            "gui_utils.TextRedirector_class": TextRedirector,
            "gui_workflow_runner.run_complete_image_processing_workflow": run_complete_image_processing_workflow if 'gui_workflow_runner' in sys.modules and hasattr(sys.modules['gui_workflow_runner'], 'run_complete_image_processing_workflow') else None
        }

        missing = [name for name, mod_or_func in modules_to_check.items()
                   if mod_or_func is None]

        root = tk.Tk()

        if missing:
            msg = "ERROR: Critical components missing:\n" + "\n".join(missing) + \
                "\nEnsure all .py files are in the same directory/Python path and error-free."

            error_frame = ttk.Frame(root, padding=20)
            error_frame.pack(fill=tk.BOTH, expand=True)

            ttk.Label(error_frame, text="Application Error", font=(
                "Helvetica", 14, "bold")).pack(pady=(0, 10))

            error_text = tk.Text(error_frame, height=15,
                                 width=60, wrap=tk.WORD)
            error_text.pack(fill=tk.BOTH, expand=True, pady=5)
            error_text.insert(tk.END, msg)
            error_text.config(state=tk.DISABLED)

            scrollbar = ttk.Scrollbar(error_text, command=error_text.yview)
            error_text.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            ttk.Button(error_frame, text="Close Application",
                       command=root.destroy).pack(pady=10)

            print(msg)
        else:

            app = ImageProcessorApp(root)

        root.mainloop()

    except Exception as e:

        try:
            import traceback
            root = tk.Tk()
            root.title("Unexpected Error")

            error_frame = ttk.Frame(root, padding=20)
            error_frame.pack(fill=tk.BOTH, expand=True)

            ttk.Label(error_frame, text="Unexpected Error", font=(
                "Helvetica", 14, "bold")).pack(pady=(0, 10))

            error_text = tk.Text(error_frame, height=15,
                                 width=60, wrap=tk.WORD)
            error_text.pack(fill=tk.BOTH, expand=True, pady=5)

            error_trace = f"An unexpected error occurred:\n{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            error_text.insert(tk.END, error_trace)
            error_text.config(state=tk.DISABLED)

            scrollbar = ttk.Scrollbar(error_text, command=error_text.yview)
            error_text.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            ttk.Button(error_frame, text="Close Application",
                       command=root.destroy).pack(pady=10)

            print(error_trace)
            root.mainloop()
        except:

            import traceback
            print("CRITICAL ERROR: Application failed to start")
            print(traceback.format_exc())
            input("Press Enter to close...")
