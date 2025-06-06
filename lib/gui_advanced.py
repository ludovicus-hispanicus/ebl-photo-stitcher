import tkinter as tk
from tkinter import ttk, filedialog
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
            'roi_vertical_start': self.roi_vertical_start_var.get(),
            'roi_vertical_end': self.roi_vertical_end_var.get(),
            'roi_horizontal_start': self.roi_horizontal_start_var.get(),
            'roi_horizontal_end': self.roi_horizontal_end_var.get(),
            'analysis_scanline_count': self.analysis_scanline_count_var.get(),
            'mark_binarization_threshold': self.mark_binarization_threshold_var.get(),
            'min_mark_width_fraction': self.min_mark_width_fraction_var.get(),
            'max_mark_width_fraction': self.max_mark_width_fraction_var.get(),
            'mark_width_tolerance': self.mark_width_tolerance_var.get(),
            'min_alternating_marks': self.min_alternating_marks_var.get()
        }
        
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
