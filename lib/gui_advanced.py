import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from ruler_presets import (
    get_default_ruler_settings, 
    get_fine_ruler_preset_settings, 
    get_wide_coverage_preset_settings,
    apply_settings_to_vars
)

class AdvancedTab:
    def __init__(self, parent_notebook):
        self.parent = parent_notebook

        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text="Advanced")

        self.gradient_width_fraction_var = tk.DoubleVar(value=0.5)
        self.background_color_tolerance_var = tk.IntVar(value=15)
        self.add_logo_var = tk.BooleanVar(value=False)
        self.logo_path_var = tk.StringVar(value="")

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
        
        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI elements for the Advanced tab"""

        canvas = tk.Canvas(self.frame)
        scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        main_frame = scrollable_frame

        processing_frame = ttk.LabelFrame(main_frame, text="Processing Settings")
        processing_frame.pack(fill=tk.X, padx=5, pady=5)

        gradient_frame = ttk.Frame(processing_frame)
        gradient_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(gradient_frame, text="Gradient Width Fraction:").pack(side=tk.LEFT)
        gradient_spinbox = ttk.Spinbox(
            gradient_frame, from_=0.1, to=1.0, increment=0.1,
            textvariable=self.gradient_width_fraction_var, width=10
        )
        gradient_spinbox.pack(side=tk.RIGHT)

        tolerance_frame = ttk.Frame(processing_frame)
        tolerance_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(tolerance_frame, text="Background Color Tolerance:").pack(side=tk.LEFT)
        tolerance_spinbox = ttk.Spinbox(
            tolerance_frame, from_=1, to=100, increment=1,
            textvariable=self.background_color_tolerance_var, width=10
        )
        tolerance_spinbox.pack(side=tk.RIGHT)

        logo_frame = ttk.LabelFrame(main_frame, text="Logo Options")
        logo_frame.pack(fill=tk.X, padx=5, pady=5)

        self.logo_checkbox = ttk.Checkbutton(
            logo_frame,
            text="Add Logo to Output",
            variable=self.add_logo_var,
            command=self._toggle_logo_path_entry
        )
        self.logo_checkbox.pack(anchor=tk.W, padx=5, pady=5)

        logo_path_frame = ttk.Frame(logo_frame)
        logo_path_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        ttk.Label(logo_path_frame, text="Logo File:").pack(side=tk.LEFT)
        self.logo_path_entry = ttk.Entry(
            logo_path_frame, 
            textvariable=self.logo_path_var,
            width=40
        )
        self.logo_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))

        self.browse_logo_btn = ttk.Button(
            logo_path_frame,
            text="Browse...",
            command=self._browse_logo_file
        )
        self.browse_logo_btn.pack(side=tk.RIGHT)

        logo_description = ttk.Label(
            logo_frame,
            text="Logo will be automatically resized to 1800px width while maintaining aspect ratio",
            font=("", 8),
            foreground="gray"
        )
        logo_description.pack(anchor=tk.W, padx=30, pady=(0, 5))

        ruler_frame = ttk.LabelFrame(main_frame, text="Ruler Detection Settings")
        ruler_frame.pack(fill=tk.X, padx=5, pady=5)

        roi_subframe = ttk.LabelFrame(ruler_frame, text="Region of Interest (ROI)")
        roi_subframe.pack(fill=tk.X, padx=5, pady=5)

        roi_v_start_frame = ttk.Frame(roi_subframe)
        roi_v_start_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(roi_v_start_frame, text="Vertical Start Fraction:").pack(side=tk.LEFT)
        ttk.Spinbox(
            roi_v_start_frame, from_=0.0, to=1.0, increment=0.01,
            textvariable=self.roi_vertical_start_var, width=10, format="%.2f"
        ).pack(side=tk.RIGHT)

        roi_v_end_frame = ttk.Frame(roi_subframe)
        roi_v_end_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(roi_v_end_frame, text="Vertical End Fraction:").pack(side=tk.LEFT)
        ttk.Spinbox(
            roi_v_end_frame, from_=0.0, to=1.0, increment=0.01,
            textvariable=self.roi_vertical_end_var, width=10, format="%.2f"
        ).pack(side=tk.RIGHT)

        roi_h_start_frame = ttk.Frame(roi_subframe)
        roi_h_start_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(roi_h_start_frame, text="Horizontal Start Fraction:").pack(side=tk.LEFT)
        ttk.Spinbox(
            roi_h_start_frame, from_=0.0, to=1.0, increment=0.01,
            textvariable=self.roi_horizontal_start_var, width=10, format="%.2f"
        ).pack(side=tk.RIGHT)

        roi_h_end_frame = ttk.Frame(roi_subframe)
        roi_h_end_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(roi_h_end_frame, text="Horizontal End Fraction:").pack(side=tk.LEFT)
        ttk.Spinbox(
            roi_h_end_frame, from_=0.0, to=1.0, increment=0.01,
            textvariable=self.roi_horizontal_end_var, width=10, format="%.2f"
        ).pack(side=tk.RIGHT)

        analysis_subframe = ttk.LabelFrame(ruler_frame, text="Analysis Parameters")
        analysis_subframe.pack(fill=tk.X, padx=5, pady=5)

        scanline_frame = ttk.Frame(analysis_subframe)
        scanline_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(scanline_frame, text="Analysis Scanline Count:").pack(side=tk.LEFT)
        ttk.Spinbox(
            scanline_frame, from_=1, to=20, increment=1,
            textvariable=self.analysis_scanline_count_var, width=10
        ).pack(side=tk.RIGHT)

        threshold_frame = ttk.Frame(analysis_subframe)
        threshold_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(threshold_frame, text="Mark Binarization Threshold:").pack(side=tk.LEFT)
        ttk.Spinbox(
            threshold_frame, from_=50, to=255, increment=5,
            textvariable=self.mark_binarization_threshold_var, width=10
        ).pack(side=tk.RIGHT)

        mark_subframe = ttk.LabelFrame(ruler_frame, text="Mark Detection Parameters")
        mark_subframe.pack(fill=tk.X, padx=5, pady=5)

        min_width_frame = ttk.Frame(mark_subframe)
        min_width_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(min_width_frame, text="Min Mark Width Fraction:").pack(side=tk.LEFT)
        ttk.Spinbox(
            min_width_frame, from_=0.001, to=0.5, increment=0.001,
            textvariable=self.min_mark_width_fraction_var, width=10, format="%.3f"
        ).pack(side=tk.RIGHT)

        max_width_frame = ttk.Frame(mark_subframe)
        max_width_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(max_width_frame, text="Max Mark Width Fraction:").pack(side=tk.LEFT)
        ttk.Spinbox(
            max_width_frame, from_=0.1, to=1.0, increment=0.05,
            textvariable=self.max_mark_width_fraction_var, width=10, format="%.2f"
        ).pack(side=tk.RIGHT)

        tolerance_width_frame = ttk.Frame(mark_subframe)
        tolerance_width_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(tolerance_width_frame, text="Mark Width Tolerance:").pack(side=tk.LEFT)
        ttk.Spinbox(
            tolerance_width_frame, from_=0.1, to=1.0, increment=0.05,
            textvariable=self.mark_width_tolerance_var, width=10, format="%.2f"
        ).pack(side=tk.RIGHT)

        alt_marks_frame = ttk.Frame(mark_subframe)
        alt_marks_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(alt_marks_frame, text="Min Alternating Marks:").pack(side=tk.LEFT)
        ttk.Spinbox(
            alt_marks_frame, from_=2, to=10, increment=1,
            textvariable=self.min_alternating_marks_var, width=10
        ).pack(side=tk.RIGHT)

        presets_frame = ttk.LabelFrame(ruler_frame, text="Quick Presets")
        presets_frame.pack(fill=tk.X, padx=5, pady=5)

        preset_buttons_frame = ttk.Frame(presets_frame)
        preset_buttons_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(
            preset_buttons_frame, text="Default Settings",
            command=self._apply_default_ruler_preset
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            preset_buttons_frame, text="Fine Graduation Ruler",
            command=self._apply_fine_ruler_preset
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            preset_buttons_frame, text="Wide Coverage",
            command=self._apply_wide_coverage_preset
        ).pack(side=tk.LEFT, padx=5)

        self._toggle_logo_path_entry()

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", _on_mousewheel)

    def _apply_default_ruler_preset(self):
        """Apply default ruler detection settings"""
        settings = get_default_ruler_settings()
        self._apply_ruler_settings(settings)

    def _apply_fine_ruler_preset(self):
        """Apply settings optimized for fine graduation rulers"""
        settings = get_fine_ruler_preset_settings()
        self._apply_ruler_settings(settings)

    def _apply_wide_coverage_preset(self):
        """Apply settings for maximum ruler coverage"""
        settings = get_wide_coverage_preset_settings()
        self._apply_ruler_settings(settings)

    def _apply_ruler_settings(self, settings):
        """Apply ruler settings to the UI variables"""
        var_mapping = {
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
        
        apply_settings_to_vars(settings, var_mapping)
        print(f"Applied ruler preset with settings: {settings}")

    def _toggle_logo_path_entry(self):
        """Toggle logo path entry based on checkbox state"""
        if self.add_logo_var.get():
            self.logo_path_entry.config(state='normal')
            self.browse_logo_btn.config(state='normal')
        else:
            self.logo_path_entry.config(state='disabled')
            self.browse_logo_btn.config(state='disabled')

    def _browse_logo_file(self):
        """Browse for logo file"""
        file_types = [
            ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff"),
            ("PNG files", "*.png"),
            ("JPEG files", "*.jpg *.jpeg"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Select Logo File",
            filetypes=file_types
        )
        
        if filename:
            self.logo_path_var.set(filename)

    def get_settings(self):
        """Get all advanced settings"""
        return {
            'gradient_width_fraction': self.gradient_width_fraction_var.get(),
            'background_color_tolerance': self.background_color_tolerance_var.get(),
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
        """Apply settings from dictionary"""
        self.gradient_width_fraction_var.set(settings.get('gradient_width_fraction', 0.5))
        self.background_color_tolerance_var.set(settings.get('background_color_tolerance', 15))
        self.add_logo_var.set(settings.get('add_logo', False))
        self.logo_path_var.set(settings.get('logo_path', ''))

        self.roi_vertical_start_var.set(settings.get('roi_vertical_start', 0.02))
        self.roi_vertical_end_var.set(settings.get('roi_vertical_end', 0.30))
        self.roi_horizontal_start_var.set(settings.get('roi_horizontal_start', 0.02))
        self.roi_horizontal_end_var.set(settings.get('roi_horizontal_end', 0.30))
        self.analysis_scanline_count_var.set(settings.get('analysis_scanline_count', 7))
        self.mark_binarization_threshold_var.set(settings.get('mark_binarization_threshold', 150))
        self.min_mark_width_fraction_var.set(settings.get('min_mark_width_fraction', 0.04))
        self.max_mark_width_fraction_var.set(settings.get('max_mark_width_fraction', 0.40))
        self.mark_width_tolerance_var.set(settings.get('mark_width_tolerance', 0.40))
        self.min_alternating_marks_var.set(settings.get('min_alternating_marks', 2))
        
        self._toggle_logo_path_entry()

    def apply_recommended_preset(self, preset_name):
        """Apply a recommended preset based on workflow results"""
        from ruler_presets import get_preset_by_name
        
        settings = get_preset_by_name(preset_name)
        self._apply_ruler_settings(settings)
        print(f"Applied recommended preset: {preset_name}")
