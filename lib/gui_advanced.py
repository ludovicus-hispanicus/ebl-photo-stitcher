import tkinter as tk
from tkinter import ttk, filedialog
from ruler_presets import get_preset_by_name, apply_settings_to_vars


class AdvancedTab:
    def __init__(self, notebook):
        self.notebook = notebook
        self.main_frame = ttk.Frame(notebook)
        notebook.add(self.main_frame, text="Advanced")

        # Initialize all variables
        self.gradient_width_var = tk.DoubleVar(value=0.5)
        self.bg_tolerance_var = tk.IntVar(value=40)
        self.rotation_var = tk.StringVar(value="0")
        self.add_logo_var = tk.BooleanVar(value=False)
        self.logo_path_var = tk.StringVar(value="")

        # Initialize ruler detection variables
        self.roi_vertical_start_var = tk.DoubleVar(value=0.02)
        self.roi_vertical_end_var = tk.DoubleVar(value=0.30)
        self.roi_horizontal_start_var = tk.DoubleVar(value=0.02)
        self.roi_horizontal_end_var = tk.DoubleVar(value=0.30)
        self.analysis_scanline_count_var = tk.IntVar(value=7)
        self.mark_binarization_threshold_var = tk.IntVar(value=150)
        self.min_mark_width_fraction_var = tk.DoubleVar(value=0.04)
        self.max_mark_width_fraction_var = tk.DoubleVar(value=0.40)
        self.mark_width_tolerance_var = tk.DoubleVar(value=0.40)
        self.min_alternating_marks_var = tk.IntVar(value=2)

        self.create_widgets()

    def create_widgets(self):
        """Create all advanced settings widgets."""

        # Background Detection
        bg_frame = ttk.LabelFrame(
            self.main_frame, text="Background Detection", padding="10")
        bg_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(bg_frame, text="Background Color Tolerance:").pack(anchor="w")
        tolerance_frame = ttk.Frame(bg_frame)
        tolerance_frame.pack(fill="x", pady=(5, 0))

        tolerance_scale = ttk.Scale(tolerance_frame, from_=10, to=100,
                                    variable=self.bg_tolerance_var, orient="horizontal",
                                    command=self._update_bg_tolerance_label)
        tolerance_scale.pack(side="left", fill="x", expand=True)

        self.bg_tolerance_label = ttk.Label(
            tolerance_frame, text="40.0", width=6)
        self.bg_tolerance_label.pack(side="right", padx=(10, 0))

        # Gradient Processing
        processing_frame = ttk.LabelFrame(
            self.main_frame, text="Gradient Mask for Intermediate Views", padding="10")
        processing_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(processing_frame, text="Gradient Width Fraction:").pack(
            anchor="w")
        gradient_scale_frame = ttk.Frame(processing_frame)
        gradient_scale_frame.pack(fill="x", pady=(5, 0))

        gradient_scale = ttk.Scale(gradient_scale_frame, from_=0.1, to=1.0,
                                   variable=self.gradient_width_var, orient="horizontal",
                                   command=self._update_gradient_label)
        gradient_scale.pack(side="left", fill="x", expand=True)

        self.gradient_label = ttk.Label(
            gradient_scale_frame, text="0.50", width=6)
        self.gradient_label.pack(side="right", padx=(10, 0))

        # Image Rotation
        self.create_rotation_section()

    def create_rotation_section(self):
        """Create rotation controls section."""
        rotation_frame = ttk.LabelFrame(
            self.main_frame, text="Image Rotation", padding="10")
        rotation_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(rotation_frame, text="Rotate all images before processing:").pack(
            anchor="w", pady=(0, 5))

        rotation_options_frame = ttk.Frame(rotation_frame)
        rotation_options_frame.pack(fill="x")

        ttk.Radiobutton(rotation_options_frame, text="No rotation (0°)",
                        variable=self.rotation_var, value="0").pack(side="left", padx=(0, 15))
        ttk.Radiobutton(rotation_options_frame, text="90° clockwise",
                        variable=self.rotation_var, value="90").pack(side="left", padx=(0, 15))
        ttk.Radiobutton(rotation_options_frame, text="180°",
                        variable=self.rotation_var, value="180").pack(side="left", padx=(0, 15))
        ttk.Radiobutton(rotation_options_frame, text="270° clockwise",
                        variable=self.rotation_var, value="270").pack(side="left")

    def _apply_preset(self, preset_name):
        """Apply a ruler detection preset."""
        try:
            preset_settings = get_preset_by_name(preset_name)
            var_dict = {
                'roi_vertical_start': self.roi_vertical_start_var,
                'roi_vertical_end': self.roi_vertical_end_var,
                'roi_horizontal_start': self.roi_horizontal_start_var,
                'roi_horizontal_end': self.roi_horizontal_end_var,
                'analysis_scanline_count': self.analysis_scanline_count_var,
                'mark_binarization_threshold': self.mark_binarization_threshold_var,
                'min_mark_width_fraction': self.min_mark_width_fraction_var,
                'max_mark_width_fraction': self.max_mark_width_fraction_var,
                'mark_width_tolerance': self.mark_width_tolerance_var,
                'min_alternating_marks': self.min_alternating_marks_var
            }
            apply_settings_to_vars(preset_settings, var_dict)
            print(f"Applied ruler preset: {preset_name}")
        except Exception as e:
            print(f"Error applying preset {preset_name}: {e}")

    def _update_bg_tolerance_label(self, value):
        """Update background tolerance label."""
        self.bg_tolerance_label.config(text=f"{float(value):.1f}")

    def _update_gradient_label(self, value):
        """Update gradient label."""
        self.gradient_label.config(text=f"{float(value):.2f}")

    def get_settings(self):
        """Get basic advanced settings as a dictionary."""
        return {
            'background_color_tolerance': self.bg_tolerance_var.get(),
            'gradient_width_fraction': self.gradient_width_var.get(),
            'rotation_angle': int(self.rotation_var.get())
        }

    def set_settings(self, settings_dict):
        """Set all advanced settings from a dictionary."""
        if 'gradient_width_fraction' in settings_dict:
            self.gradient_width_var.set(
                settings_dict['gradient_width_fraction'])
        if 'background_color_tolerance' in settings_dict:
            self.bg_tolerance_var.set(
                settings_dict['background_color_tolerance'])
        if 'rotation_angle' in settings_dict:
            self.rotation_var.set(str(settings_dict['rotation_angle']))

        # Apply ruler detection settings
        ruler_settings = ['roi_vertical_start', 'roi_vertical_end', 'roi_horizontal_start',
                          'roi_horizontal_end', 'analysis_scanline_count', 'mark_binarization_threshold',
                          'min_mark_width_fraction', 'max_mark_width_fraction', 'mark_width_tolerance',
                          'min_alternating_marks']

        for setting in ruler_settings:
            if setting in settings_dict:
                getattr(self, f"{setting}_var").set(settings_dict[setting])

        # Update labels
        self._update_bg_tolerance_label(str(self.bg_tolerance_var.get()))
        self._update_gradient_label(str(self.gradient_width_var.get()))

    # Alias methods for compatibility
    def apply_settings(self, settings):
        """Alias for set_settings for compatibility."""
        self.set_settings(settings)


class AdvancedRulerTab:
    def __init__(self, notebook, root_window=None):
        self.root_window = root_window
        self.notebook = notebook
        self.main_frame = ttk.Frame(notebook)
        notebook.add(self.main_frame, text="Advanced (Ruler)")

        # Create scrollable frame
        self.canvas = tk.Canvas(self.main_frame)
        self.scrollbar = ttk.Scrollbar(
            self.main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind("<Configure>",
                                   lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Enable mouse wheel / two-finger trackpad scrolling when pointer is over the tab
        def _on_mousewheel(event):
            # Windows/macOS: event.delta is in units of 120 (or small increments for precise scroll)
            if event.delta:
                self.canvas.yview_scroll(int(-event.delta / 120), "units")
            return "break"

        def _on_linux_scroll_up(event):
            self.canvas.yview_scroll(-3, "units")
            return "break"

        def _on_linux_scroll_down(event):
            self.canvas.yview_scroll(3, "units")
            return "break"

        def _bind_wheel(_e=None):
            self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
            self.canvas.bind_all("<Button-4>", _on_linux_scroll_up)
            self.canvas.bind_all("<Button-5>", _on_linux_scroll_down)

        def _unbind_wheel(_e=None):
            self.canvas.unbind_all("<MouseWheel>")
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")

        # Only capture wheel events when the cursor is over this tab's content
        self.main_frame.bind("<Enter>", _bind_wheel)
        self.main_frame.bind("<Leave>", _unbind_wheel)

        # Initialize variables with default values
        self.roi_vertical_start_var = tk.DoubleVar(value=0.02)
        self.roi_vertical_end_var = tk.DoubleVar(value=0.30)
        self.roi_horizontal_start_var = tk.DoubleVar(value=0.02)
        self.roi_horizontal_end_var = tk.DoubleVar(value=0.30)
        self.analysis_scanline_count_var = tk.IntVar(value=50)
        self.mark_binarization_threshold_var = tk.IntVar(value=150)
        self.min_mark_width_fraction_var = tk.DoubleVar(value=0.040)
        self.max_mark_width_fraction_var = tk.DoubleVar(value=0.40)
        self.mark_width_tolerance_var = tk.DoubleVar(value=0.5)
        self.min_alternating_marks_var = tk.IntVar(value=8)
        
        self.create_widgets()

    def get_settings(self):
        """Get all advanced settings as a dictionary."""
        return {
            'analysis_scanline_count': self.analysis_scanline_count_var.get(),
            'mark_binarization_threshold': self.mark_binarization_threshold_var.get(),
            'mark_width_tolerance': self.mark_width_tolerance_var.get(),
            'max_mark_width_fraction': self.max_mark_width_fraction_var.get(),
            'min_alternating_marks': self.min_alternating_marks_var.get(),
            'min_mark_width_fraction': self.min_mark_width_fraction_var.get(),
            'roi_horizontal_end': self.roi_horizontal_end_var.get(),
            'roi_horizontal_start': self.roi_horizontal_start_var.get(),
            'roi_vertical_end': self.roi_vertical_end_var.get(),
            'roi_vertical_start': self.roi_vertical_start_var.get(),
        }

    def set_settings(self, settings_dict):
        """Set ruler settings from a dictionary."""
        if 'analysis_scanline_count' in settings_dict:
            self.analysis_scanline_count_var.set(
                settings_dict['analysis_scanline_count'])
        if 'mark_binarization_threshold' in settings_dict:
            self.mark_binarization_threshold_var.set(
                settings_dict['mark_binarization_threshold'])
        if 'mark_width_tolerance' in settings_dict:
            self.mark_width_tolerance_var.set(
                settings_dict['mark_width_tolerance'])
        if 'max_mark_width_fraction' in settings_dict:
            self.max_mark_width_fraction_var.set(
                settings_dict['max_mark_width_fraction'])
        if 'min_alternating_marks' in settings_dict:
            self.min_alternating_marks_var.set(
                settings_dict['min_alternating_marks'])
        if 'min_mark_width_fraction' in settings_dict:
            self.min_mark_width_fraction_var.set(
                settings_dict['min_mark_width_fraction'])
        if 'roi_horizontal_end' in settings_dict:
            self.roi_horizontal_end_var.set(
                settings_dict['roi_horizontal_end'])
        if 'roi_horizontal_start' in settings_dict:
            self.roi_horizontal_start_var.set(
                settings_dict['roi_horizontal_start'])
        if 'roi_vertical_end' in settings_dict:
            self.roi_vertical_end_var.set(settings_dict['roi_vertical_end'])
        if 'roi_vertical_start' in settings_dict:
            self.roi_vertical_start_var.set(
                settings_dict['roi_vertical_start'])

    def create_widgets(self):
        """Create detailed ruler detection widgets."""

        # Quick Presets
        presets_frame = ttk.LabelFrame(
            self.scrollable_frame, text="Quick Presets", padding="10")
        presets_frame.pack(fill="x", pady=(0, 10))

        preset_buttons_frame = ttk.Frame(presets_frame)
        preset_buttons_frame.pack(fill="x")

        presets = [("Wide Coverage", self.apply_wide_coverage_preset),
                   ("Standard", self.apply_standard_preset),
                   ("Precise", self.apply_precise_preset),
                   ("Fine Detail", self.apply_fine_detail_preset)]

        for text, command in presets:
            ttk.Button(preset_buttons_frame, text=text,
                       command=command).pack(side="left", padx=(0, 5))

        # Region of Interest
        roi_frame = ttk.LabelFrame(
            self.scrollable_frame, text="Region of Interest", padding="10")
        roi_frame.pack(fill="x", pady=(0, 10))

        # Vertical ROI
        ttk.Label(roi_frame, text="Vertical ROI:").pack(
            anchor="w", pady=(0, 5))
        roi_v_frame = ttk.Frame(roi_frame)
        roi_v_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(roi_v_frame, text="Start:", width=8).pack(side="left")
        ttk.Scale(roi_v_frame, from_=0.0, to=1.0, variable=self.roi_vertical_start_var,
                  orient="horizontal").pack(side="left", fill="x", expand=True, padx=(5, 10))
        ttk.Label(roi_v_frame, text="End:", width=8).pack(side="left")
        ttk.Scale(roi_v_frame, from_=0.0, to=1.0, variable=self.roi_vertical_end_var,
                  orient="horizontal").pack(side="left", fill="x", expand=True, padx=(5, 0))

        # Horizontal ROI
        ttk.Label(roi_frame, text="Horizontal ROI:").pack(
            anchor="w", pady=(0, 5))
        roi_h_frame = ttk.Frame(roi_frame)
        roi_h_frame.pack(fill="x")

        ttk.Label(roi_h_frame, text="Start:", width=8).pack(side="left")
        ttk.Scale(roi_h_frame, from_=0.0, to=1.0, variable=self.roi_horizontal_start_var,
                  orient="horizontal").pack(side="left", fill="x", expand=True, padx=(5, 10))
        ttk.Label(roi_h_frame, text="End:", width=8).pack(side="left")
        ttk.Scale(roi_h_frame, from_=0.0, to=1.0, variable=self.roi_horizontal_end_var,
                  orient="horizontal").pack(side="left", fill="x", expand=True, padx=(5, 0))

        # Analysis Parameters
        analysis_frame = ttk.LabelFrame(
            self.scrollable_frame, text="Analysis Parameters", padding="10")
        analysis_frame.pack(fill="x", pady=(0, 10))

        # Create parameter controls
        params = [
            ("Scanline Count:", self.analysis_scanline_count_var, 10, 200),
            ("Binarization Threshold:", self.mark_binarization_threshold_var, 50, 255)
        ]

        for label_text, var, min_val, max_val in params:
            frame = ttk.Frame(analysis_frame)
            frame.pack(fill="x", pady=(0, 5))
            ttk.Label(frame, text=label_text, width=20).pack(side="left")
            ttk.Scale(frame, from_=min_val, to=max_val, variable=var,
                      orient="horizontal").pack(side="left", fill="x", expand=True, padx=(5, 0))

        # Mark Width Detection
        width_frame = ttk.LabelFrame(
            self.scrollable_frame, text="Mark Width Detection", padding="10")
        width_frame.pack(fill="x", pady=(0, 10))

        width_params = [
            ("Min Mark Width:", self.min_mark_width_fraction_var, 0.01, 0.2),
            ("Max Mark Width:", self.max_mark_width_fraction_var, 0.2, 1.0),
            ("Width Tolerance:", self.mark_width_tolerance_var, 0.1, 2.0),
            ("Min Alternating Marks:", self.min_alternating_marks_var, 3, 20)
        ]

        for label_text, var, min_val, max_val in width_params:
            frame = ttk.Frame(width_frame)
            frame.pack(fill="x", pady=(0, 5))
            ttk.Label(frame, text=label_text, width=20).pack(side="left")
            ttk.Scale(frame, from_=min_val, to=max_val, variable=var,
                      orient="horizontal").pack(side="left", fill="x", expand=True, padx=(5, 0))

    def apply_wide_coverage_preset(self):
        """Apply wide coverage preset."""
        settings = {'roi_vertical_start': 0.01, 'roi_vertical_end': 0.50, 'roi_horizontal_start': 0.01,
                    'roi_horizontal_end': 0.50, 'analysis_scanline_count': 30, 'mark_binarization_threshold': 120,
                    'min_mark_width_fraction': 0.02, 'max_mark_width_fraction': 0.60, 'mark_width_tolerance': 0.8,
                    'min_alternating_marks': 6}
        self._apply_settings(settings)

    def apply_standard_preset(self):
        """Apply standard preset."""
        settings = {'roi_vertical_start': 0.02, 'roi_vertical_end': 0.30, 'roi_horizontal_start': 0.02,
                    'roi_horizontal_end': 0.30, 'analysis_scanline_count': 50, 'mark_binarization_threshold': 150,
                    'min_mark_width_fraction': 0.040, 'max_mark_width_fraction': 0.40, 'mark_width_tolerance': 0.5,
                    'min_alternating_marks': 8}
        self._apply_settings(settings)

    def apply_precise_preset(self):
        """Apply precise preset."""
        settings = {'roi_vertical_start': 0.05, 'roi_vertical_end': 0.25, 'roi_horizontal_start': 0.05,
                    'roi_horizontal_end': 0.25, 'analysis_scanline_count': 80, 'mark_binarization_threshold': 170,
                    'min_mark_width_fraction': 0.050, 'max_mark_width_fraction': 0.30, 'mark_width_tolerance': 0.3,
                    'min_alternating_marks': 10}
        self._apply_settings(settings)

    def apply_fine_detail_preset(self):
        """Apply fine detail preset."""
        settings = {'roi_vertical_start': 0.10, 'roi_vertical_end': 0.20, 'roi_horizontal_start': 0.10,
                    'roi_horizontal_end': 0.20, 'analysis_scanline_count': 100, 'mark_binarization_threshold': 180,
                    'min_mark_width_fraction': 0.060, 'max_mark_width_fraction': 0.25, 'mark_width_tolerance': 0.2,
                    'min_alternating_marks': 12}
        self._apply_settings(settings)

    def _apply_settings(self, settings):
        """Apply settings to variables."""
        for key, value in settings.items():
            if hasattr(self, f"{key}_var"):
                getattr(self, f"{key}_var").set(value)



class AdvancedLogoTab:
    def __init__(self, notebook, root_window=None):
        self.root_window = root_window
        self.notebook = notebook
        self.main_frame = ttk.Frame(notebook)
        notebook.add(self.main_frame, text="Advanced (Logo)")

        self.add_logo_var = tk.BooleanVar(value=False)
        self.logo_path_var = tk.StringVar(value="")

        self.create_widgets()

    def create_widgets(self):
        """Create logo settings widgets."""
        logo_frame = ttk.LabelFrame(
            self.main_frame, text="Logo Settings", padding="10")
        logo_frame.pack(fill="x", pady=(0, 10))

        self.add_logo_cb = ttk.Checkbutton(logo_frame, text="Add logo to final image",
                                           variable=self.add_logo_var,
                                           command=self._toggle_logo_path_entry)
        self.add_logo_cb.pack(anchor="w", pady=(0, 10))

        ttk.Label(logo_frame, text="Logo file path:").pack(anchor="w")

        path_entry_frame = ttk.Frame(logo_frame)
        path_entry_frame.pack(fill="x", pady=(5, 0))

        self.logo_path_entry = ttk.Entry(
            path_entry_frame, textvariable=self.logo_path_var)
        self.logo_path_entry.pack(side="left", fill="x", expand=True)

        self.logo_browse_btn = ttk.Button(path_entry_frame, text="Browse...",
                                          command=self._browse_logo_file)
        self.logo_browse_btn.pack(side="right", padx=(5, 0))

        self._toggle_logo_path_entry()

    def get_settings(self):
        """Get logo settings as a dictionary."""
        return {
            'add_logo': self.add_logo_var.get(),
            'logo_path': self.logo_path_var.get()
        }

    def set_settings(self, settings_dict):
        """Set logo settings from a dictionary."""
        if 'add_logo' in settings_dict:
            self.add_logo_var.set(settings_dict['add_logo'])
        if 'logo_path' in settings_dict:
            self.logo_path_var.set(settings_dict['logo_path'])
        self._toggle_logo_path_entry()

    def _toggle_logo_path_entry(self):
        """Toggle logo path entry state."""
        state = "normal" if self.add_logo_var.get() else "disabled"
        self.logo_path_entry.config(state=state)
        self.logo_browse_btn.config(state=state)

    def _browse_logo_file(self):
        """Browse for logo file."""
        filename = filedialog.askopenfilename(
            parent=self.root_window,
            title="Select Logo File",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff")]
        )
        if filename:
            self.logo_path_var.set(filename)
