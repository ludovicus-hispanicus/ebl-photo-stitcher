import tkinter as tk
from tkinter import ttk, filedialog

class AdvancedTab:
    def __init__(self, notebook):
        self.notebook = notebook
        self.main_frame = ttk.Frame(notebook)
        notebook.add(self.main_frame, text="Advanced")

        self.gradient_width_var = tk.DoubleVar(value=0.5)
        self.bg_tolerance_var = tk.IntVar(value=40)
        self.rotation_var = tk.StringVar(value="0")

        self.create_widgets()

    def create_widgets(self):
        """Create basic advanced settings widgets."""

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

        self.bg_tolerance_label = ttk.Label(tolerance_frame, text="40.0", width=6)
        self.bg_tolerance_label.pack(side="right", padx=(10, 0))

        processing_frame = ttk.LabelFrame(
            self.main_frame, text="Gradient Mask for Intermediate Views", padding="10")
        processing_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(processing_frame, text="Gradient Width Fraction:").pack(anchor="w")

        gradient_scale_frame = ttk.Frame(processing_frame)
        gradient_scale_frame.pack(fill="x", pady=(5, 0))

        gradient_scale = ttk.Scale(gradient_scale_frame, from_=0.1, to=1.0,
                                   variable=self.gradient_width_var, orient="horizontal",
                                   command=self._update_gradient_label)
        gradient_scale.pack(side="left", fill="x", expand=True)

        self.gradient_label = ttk.Label(gradient_scale_frame, text="0.50", width=6)
        self.gradient_label.pack(side="right", padx=(10, 0))

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

    def get_settings(self):
        """Get basic advanced settings as a dictionary."""
        return {
            'gradient_width_fraction': self.gradient_width_var.get(),
            'background_color_tolerance': self.bg_tolerance_var.get(),
            'rotation_angle': int(self.rotation_var.get())
        }

    def set_settings(self, settings_dict):
        """Set basic advanced settings from a dictionary."""
        if 'gradient_width_fraction' in settings_dict:
            self.gradient_width_var.set(settings_dict['gradient_width_fraction'])
        if 'background_color_tolerance' in settings_dict:
            self.bg_tolerance_var.set(settings_dict['background_color_tolerance'])
        if 'rotation_angle' in settings_dict:
            self.rotation_var.set(str(settings_dict['rotation_angle']))

        self._update_bg_tolerance_label(str(self.bg_tolerance_var.get()))
        self._update_gradient_label(str(self.gradient_width_var.get()))

    def _update_bg_tolerance_label(self, value):
        """Update background tolerance label."""
        self.bg_tolerance_label.config(text=f"{float(value):.1f}")

    def _update_gradient_label(self, value):
        """Update gradient label."""
        self.gradient_label.config(text=f"{float(value):.2f}")


class AdvancedRulerTab:
    def __init__(self, notebook):
        self.notebook = notebook
        self.main_frame = ttk.Frame(notebook)
        notebook.add(self.main_frame, text="Advanced (Ruler)")

        self.canvas = tk.Canvas(self.main_frame)
        self.scrollbar = ttk.Scrollbar(
            self.main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

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

    def create_widgets(self):
        """Create ruler detection widgets."""

        presets_frame = ttk.LabelFrame(
            self.scrollable_frame, text="Quick Presets", padding="10")
        presets_frame.pack(fill="x", pady=(0, 10))

        preset_buttons_frame = ttk.Frame(presets_frame)
        preset_buttons_frame.pack(fill="x")

        ttk.Button(preset_buttons_frame, text="Wide Coverage",
                   command=self.apply_wide_coverage_preset).pack(side="left", padx=(0, 5))
        ttk.Button(preset_buttons_frame, text="Standard",
                   command=self.apply_standard_preset).pack(side="left", padx=(0, 5))
        ttk.Button(preset_buttons_frame, text="Precise",
                   command=self.apply_precise_preset).pack(side="left", padx=(0, 5))
        ttk.Button(preset_buttons_frame, text="Fine Detail",
                   command=self.apply_fine_detail_preset).pack(side="left")

        roi_frame = ttk.LabelFrame(self.scrollable_frame,
                                   text="Region of Interest", padding="10")
        roi_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(roi_frame, text="Vertical ROI:").pack(anchor="w", pady=(0, 5))
        roi_v_frame = ttk.Frame(roi_frame)
        roi_v_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(roi_v_frame, text="Start:", width=8).pack(side="left")
        ttk.Scale(roi_v_frame, from_=0.0, to=1.0, variable=self.roi_vertical_start_var,
                  orient="horizontal").pack(side="left", fill="x", expand=True, padx=(5, 10))
        ttk.Label(roi_v_frame, text="End:", width=8).pack(side="left")
        ttk.Scale(roi_v_frame, from_=0.0, to=1.0, variable=self.roi_vertical_end_var,
                  orient="horizontal").pack(side="left", fill="x", expand=True, padx=(5, 0))

        ttk.Label(roi_frame, text="Horizontal ROI:").pack(anchor="w", pady=(0, 5))
        roi_h_frame = ttk.Frame(roi_frame)
        roi_h_frame.pack(fill="x")

        ttk.Label(roi_h_frame, text="Start:", width=8).pack(side="left")
        ttk.Scale(roi_h_frame, from_=0.0, to=1.0, variable=self.roi_horizontal_start_var,
                  orient="horizontal").pack(side="left", fill="x", expand=True, padx=(5, 10))
        ttk.Label(roi_h_frame, text="End:", width=8).pack(side="left")
        ttk.Scale(roi_h_frame, from_=0.0, to=1.0, variable=self.roi_horizontal_end_var,
                  orient="horizontal").pack(side="left", fill="x", expand=True, padx=(5, 0))

        analysis_frame = ttk.LabelFrame(
            self.scrollable_frame, text="Analysis Parameters", padding="10")
        analysis_frame.pack(fill="x", pady=(0, 10))

        scanline_frame = ttk.Frame(analysis_frame)
        scanline_frame.pack(fill="x", pady=(0, 5))
        ttk.Label(scanline_frame, text="Scanline Count:", width=20).pack(side="left")
        ttk.Scale(scanline_frame, from_=10, to=200, variable=self.analysis_scanline_count_var,
                  orient="horizontal").pack(side="left", fill="x", expand=True, padx=(5, 0))

        threshold_frame = ttk.Frame(analysis_frame)
        threshold_frame.pack(fill="x", pady=(0, 5))
        ttk.Label(threshold_frame, text="Binarization Threshold:",
                  width=20).pack(side="left")
        ttk.Scale(threshold_frame, from_=50, to=255, variable=self.mark_binarization_threshold_var,
                  orient="horizontal").pack(side="left", fill="x", expand=True, padx=(5, 0))

        width_frame = ttk.LabelFrame(
            self.scrollable_frame, text="Mark Width Detection", padding="10")
        width_frame.pack(fill="x", pady=(0, 10))

        min_width_frame = ttk.Frame(width_frame)
        min_width_frame.pack(fill="x", pady=(0, 5))
        ttk.Label(min_width_frame, text="Min Mark Width:", width=20).pack(side="left")
        ttk.Scale(min_width_frame, from_=0.01, to=0.2, variable=self.min_mark_width_fraction_var,
                  orient="horizontal").pack(side="left", fill="x", expand=True, padx=(5, 0))

        max_width_frame = ttk.Frame(width_frame)
        max_width_frame.pack(fill="x", pady=(0, 5))
        ttk.Label(max_width_frame, text="Max Mark Width:", width=20).pack(side="left")
        ttk.Scale(max_width_frame, from_=0.2, to=1.0, variable=self.max_mark_width_fraction_var,
                  orient="horizontal").pack(side="left", fill="x", expand=True, padx=(5, 0))

        tolerance_frame = ttk.Frame(width_frame)
        tolerance_frame.pack(fill="x", pady=(0, 5))
        ttk.Label(tolerance_frame, text="Width Tolerance:", width=20).pack(side="left")
        ttk.Scale(tolerance_frame, from_=0.1, to=2.0, variable=self.mark_width_tolerance_var,
                  orient="horizontal").pack(side="left", fill="x", expand=True, padx=(5, 0))

        min_marks_frame = ttk.Frame(width_frame)
        min_marks_frame.pack(fill="x")
        ttk.Label(min_marks_frame, text="Min Alternating Marks:",
                  width=20).pack(side="left")
        ttk.Scale(min_marks_frame, from_=3, to=20, variable=self.min_alternating_marks_var,
                  orient="horizontal").pack(side="left", fill="x", expand=True, padx=(5, 0))

    def apply_wide_coverage_preset(self):
        """Apply wide coverage preset."""
        self.roi_vertical_start_var.set(0.01)
        self.roi_vertical_end_var.set(0.50)
        self.roi_horizontal_start_var.set(0.01)
        self.roi_horizontal_end_var.set(0.50)
        self.analysis_scanline_count_var.set(30)
        self.mark_binarization_threshold_var.set(120)
        self.min_mark_width_fraction_var.set(0.02)
        self.max_mark_width_fraction_var.set(0.60)
        self.mark_width_tolerance_var.set(0.8)
        self.min_alternating_marks_var.set(6)

    def apply_standard_preset(self):
        """Apply standard preset."""
        self.roi_vertical_start_var.set(0.02)
        self.roi_vertical_end_var.set(0.30)
        self.roi_horizontal_start_var.set(0.02)
        self.roi_horizontal_end_var.set(0.30)
        self.analysis_scanline_count_var.set(50)
        self.mark_binarization_threshold_var.set(150)
        self.min_mark_width_fraction_var.set(0.040)
        self.max_mark_width_fraction_var.set(0.40)
        self.mark_width_tolerance_var.set(0.5)
        self.min_alternating_marks_var.set(8)

    def apply_precise_preset(self):
        """Apply precise preset."""
        self.roi_vertical_start_var.set(0.05)
        self.roi_vertical_end_var.set(0.25)
        self.roi_horizontal_start_var.set(0.05)
        self.roi_horizontal_end_var.set(0.25)
        self.analysis_scanline_count_var.set(80)
        self.mark_binarization_threshold_var.set(170)
        self.min_mark_width_fraction_var.set(0.050)
        self.max_mark_width_fraction_var.set(0.30)
        self.mark_width_tolerance_var.set(0.3)
        self.min_alternating_marks_var.set(10)

    def apply_fine_detail_preset(self):
        """Apply fine detail preset."""
        self.roi_vertical_start_var.set(0.10)
        self.roi_vertical_end_var.set(0.20)
        self.roi_horizontal_start_var.set(0.10)
        self.roi_horizontal_end_var.set(0.20)
        self.analysis_scanline_count_var.set(100)
        self.mark_binarization_threshold_var.set(180)
        self.min_mark_width_fraction_var.set(0.060)
        self.max_mark_width_fraction_var.set(0.25)
        self.mark_width_tolerance_var.set(0.2)
        self.min_alternating_marks_var.set(12)

    def get_settings(self):
        """Get ruler detection settings as a dictionary."""
        return {
=======
from ruler_presets import get_preset_by_name, apply_settings_to_vars


class AdvancedTab:
    def __init__(self, parent_notebook):
        # Create the tab frame
        self.tab_frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.tab_frame, text="Advanced")
        
        # Create main frame (no scrolling as requested)
        self.frame = ttk.Frame(self.tab_frame, padding="10")
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Initialize variables
        self.bg_tolerance_var = tk.DoubleVar(value=40.0)
        self.gradient_var = tk.DoubleVar(value=0.5)
        self.add_logo_var = tk.BooleanVar(value=False)
        self.logo_path_var = tk.StringVar(value='')  # Fix: change value('') to value=''
        
        # Initialize ruler detection variables
        self._init_ruler_detection_vars()
        
        # Create widgets
        self._create_widgets()
        
    def _init_ruler_detection_vars(self):
        """Initialize ruler detection variables"""
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
        
    def _create_widgets(self):
        # Background Color Tolerance as slider (as requested)
        bg_tolerance_frame = ttk.LabelFrame(self.frame, text="Background Color Tolerance", padding="5")
        bg_tolerance_frame.pack(fill=tk.X, pady=5)
        
        self.bg_tolerance_scale = ttk.Scale(
            bg_tolerance_frame, 
            from_=10.0, 
            to=100.0, 
            variable=self.bg_tolerance_var,
            orient=tk.HORIZONTAL,
            command=self._update_bg_tolerance_label
        )
        self.bg_tolerance_scale.pack(fill=tk.X, padx=5, pady=5)
        
        self.bg_tolerance_label = ttk.Label(bg_tolerance_frame, text="40.0")
        self.bg_tolerance_label.pack()
        
        # Gradient Width Fraction as slider (as requested)
        gradient_frame = ttk.LabelFrame(self.frame, text="Gradient Width Fraction", padding="5")
        gradient_frame.pack(fill=tk.X, pady=5)
        
        self.gradient_scale = ttk.Scale(
            gradient_frame,
            from_=0.1,
            to=1.0,
            variable=self.gradient_var,
            orient=tk.HORIZONTAL,
            command=self._update_gradient_label
        )
        self.gradient_scale.pack(fill=tk.X, padx=5, pady=5)
        
        self.gradient_label = ttk.Label(gradient_frame, text="0.5")
        self.gradient_label.pack()
        
        # Ruler Detection Presets
        presets_frame = ttk.LabelFrame(self.frame, text="Ruler Detection Presets", padding="5")
        presets_frame.pack(fill=tk.X, pady=5)
        
        preset_buttons_frame = ttk.Frame(presets_frame)
        preset_buttons_frame.pack(fill=tk.X, pady=5)
        
        # Create preset buttons
        ttk.Button(
            preset_buttons_frame,
            text="Default Settings",
            command=lambda: self._apply_preset("Default Settings")
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            preset_buttons_frame,
            text="Fine Graduation Ruler",
            command=lambda: self._apply_preset("Fine Graduation Ruler")
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            preset_buttons_frame,
            text="Wide Coverage",
            command=lambda: self._apply_preset("Wide Coverage")
        ).pack(side=tk.LEFT, padx=5)
        
        # Ruler Detection Settings (detailed controls)
        ruler_frame = ttk.LabelFrame(self.frame, text="Ruler Detection Settings", padding="5")
        ruler_frame.pack(fill=tk.X, pady=5)
        
        # ROI settings
        roi_frame = ttk.Frame(ruler_frame)
        roi_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(roi_frame, text="ROI Vertical (Start/End):").pack(anchor=tk.W)
        roi_v_frame = ttk.Frame(roi_frame)
        roi_v_frame.pack(fill=tk.X, pady=2)
        
        ttk.Scale(roi_v_frame, from_=0.0, to=1.0, variable=self.roi_vertical_start_var, 
                 orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        ttk.Scale(roi_v_frame, from_=0.0, to=1.0, variable=self.roi_vertical_end_var, 
                 orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(roi_frame, text="ROI Horizontal (Start/End):").pack(anchor=tk.W, pady=(5,0))
        roi_h_frame = ttk.Frame(roi_frame)
        roi_h_frame.pack(fill=tk.X, pady=2)
        
        ttk.Scale(roi_h_frame, from_=0.0, to=1.0, variable=self.roi_horizontal_start_var, 
                 orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        ttk.Scale(roi_h_frame, from_=0.0, to=1.0, variable=self.roi_horizontal_end_var, 
                 orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Other ruler settings
        ttk.Label(ruler_frame, text="Mark Binarization Threshold:").pack(anchor=tk.W, pady=(5,0))
        ttk.Scale(ruler_frame, from_=50, to=255, variable=self.mark_binarization_threshold_var, 
                 orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(ruler_frame, text="Mark Width Tolerance:").pack(anchor=tk.W)
        ttk.Scale(ruler_frame, from_=0.1, to=1.0, variable=self.mark_width_tolerance_var, 
                 orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5, pady=2)
        
        # Logo settings
        logo_frame = ttk.LabelFrame(self.frame, text="Logo Settings", padding="5")
        logo_frame.pack(fill=tk.X, pady=5)
        
        self.add_logo_checkbox = ttk.Checkbutton(
            logo_frame,
            text="Add Logo",
            variable=self.add_logo_var,
            command=self._toggle_logo_path_entry
        )
        self.add_logo_checkbox.pack(anchor=tk.W, pady=2)
        
        # Logo path entry
        logo_path_frame = ttk.Frame(logo_frame)
        logo_path_frame.pack(fill=tk.X, pady=2)
        
        self.logo_path_entry = ttk.Entry(
            logo_path_frame,
            textvariable=self.logo_path_var,
            state='disabled'
        )
        self.logo_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.browse_logo_btn = ttk.Button(
            logo_path_frame,
            text="Browse",
            command=self._browse_logo_file,
            state='disabled'
        )
        self.browse_logo_btn.pack(side=tk.RIGHT)
        
    def _apply_preset(self, preset_name):
        """Apply a ruler detection preset"""
        preset_settings = get_preset_by_name(preset_name)
        
        # Create variable mapping for apply_settings_to_vars
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
        
    def _update_bg_tolerance_label(self, value):
        """Update background tolerance label."""
        self.bg_tolerance_label.config(text=f"{float(value):.1f}")
        
    def _update_gradient_label(self, value):
        """Update gradient label."""
        self.gradient_label.config(text=f"{float(value):.2f}")
        
    def _update_ruler_sensitivity_label(self, value):
        """Update ruler sensitivity label."""
        self.ruler_sensitivity_label.config(text=f"{float(value):.2f}")
        
    def _update_ruler_min_area_label(self, value):
        """Update ruler minimum area label."""
        self.ruler_min_area_label.config(text=f"{float(value):.3f}")
        
    def _browse_logo_file(self):
        """Browse for logo file."""
        filename = filedialog.askopenfilename(
            title="Select Logo File",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff")]
        )
        if filename:
            self.logo_path_var.set(filename)
            
    def _toggle_logo_path_entry(self):
        """Toggle logo path entry state."""
        if self.add_logo_var.get():
            self.logo_path_entry.config(state='normal')
            self.browse_logo_btn.config(state='normal')
        else:
            self.logo_path_entry.config(state='disabled')
            self.browse_logo_btn.config(state='disabled')
            
    def get_settings(self):
        """Get current settings from the advanced tab."""
        return {
            'background_color_tolerance': self.bg_tolerance_var.get(),
            'gradient_width_fraction': self.gradient_var.get(),
            'add_logo': self.add_logo_var.get(),
            'logo_path': self.logo_path_var.get(),

    def set_settings(self, settings_dict):
        """Set ruler detection settings from a dictionary."""
        if 'roi_vertical_start' in settings_dict:
            self.roi_vertical_start_var.set(settings_dict['roi_vertical_start'])
        if 'roi_vertical_end' in settings_dict:
            self.roi_vertical_end_var.set(settings_dict['roi_vertical_end'])
        if 'roi_horizontal_start' in settings_dict:
            self.roi_horizontal_start_var.set(settings_dict['roi_horizontal_start'])
        if 'roi_horizontal_end' in settings_dict:
            self.roi_horizontal_end_var.set(settings_dict['roi_horizontal_end'])
        if 'analysis_scanline_count' in settings_dict:
            self.analysis_scanline_count_var.set(
                settings_dict['analysis_scanline_count'])
        if 'mark_binarization_threshold' in settings_dict:
            self.mark_binarization_threshold_var.set(
                settings_dict['mark_binarization_threshold'])
        if 'min_mark_width_fraction' in settings_dict:
            self.min_mark_width_fraction_var.set(
                settings_dict['min_mark_width_fraction'])
        if 'max_mark_width_fraction' in settings_dict:
            self.max_mark_width_fraction_var.set(
                settings_dict['max_mark_width_fraction'])
        if 'mark_width_tolerance' in settings_dict:
            self.mark_width_tolerance_var.set(settings_dict['mark_width_tolerance'])
        if 'min_alternating_marks' in settings_dict:
            self.min_alternating_marks_var.set(settings_dict['min_alternating_marks'])


class AdvancedLogoTab:
    def __init__(self, notebook):
        self.notebook = notebook
        self.main_frame = ttk.Frame(notebook)
        notebook.add(self.main_frame, text="Advanced (Logo)")

        self.add_logo_var = tk.BooleanVar(value=False)
        self.logo_path_var = tk.StringVar(value="")

        self.create_widgets()

    def create_widgets(self):
        """Create logo settings widgets."""

        logo_frame = ttk.LabelFrame(self.main_frame, text="Logo Settings", padding="10")
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

        info_frame = ttk.LabelFrame(
            self.main_frame, text="Logo Information", padding="10")
        info_frame.pack(fill="x", pady=(0, 10))

        info_text = """
The logo will be added to the final stitched image. Supported formats:
• PNG (recommended for transparency)
• JPG/JPEG
• GIF
• BMP
• TIFF

The logo will be automatically resized to fit the image layout.
        """

        ttk.Label(info_frame, text=info_text.strip(),
                  font=("TkDefaultFont", 8),
                  foreground="gray", justify="left").pack(anchor="w")

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
            title="Select Logo File",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.logo_path_var.set(filename)
        
    def apply_settings(self, settings):
        """Apply settings to the advanced tab widgets."""
        self.bg_tolerance_var.set(settings.get('background_color_tolerance', 40.0))
        self.gradient_var.set(settings.get('gradient_width_fraction', 0.5))
        self.add_logo_var.set(settings.get('add_logo', False))
        self.logo_path_var.set(settings.get('logo_path', ''))
        
        # Apply ruler detection settings with defaults
        if hasattr(self, 'ruler_sensitivity_var'):
            self.ruler_sensitivity_var.set(settings.get('ruler_sensitivity', 0.5))
        if hasattr(self, 'ruler_min_area_var'):
            self.ruler_min_area_var.set(settings.get('ruler_min_area', 0.01))
        if hasattr(self, 'ruler_fallback_enabled_var'):
            self.ruler_fallback_enabled_var.set(settings.get('ruler_fallback_enabled', True))
        
        # Update labels
        self._update_bg_tolerance_label(str(self.bg_tolerance_var.get()))
        self._update_gradient_label(str(self.gradient_var.get()))
        if hasattr(self, 'ruler_sensitivity_label'):
            self._update_ruler_sensitivity_label(str(self.ruler_sensitivity_var.get()))
        if hasattr(self, 'ruler_min_area_label'):
            self._update_ruler_min_area_label(str(self.ruler_min_area_var.get()))
        
        # Update toggle state
        self._toggle_logo_path_entry()
