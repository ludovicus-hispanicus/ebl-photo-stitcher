"""UI component creation functions for the eBL Photo Stitcher application."""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog


class UIComponents:
    """Helper class for creating UI components."""

    @staticmethod
    def create_folder_selection_ui(parent, input_folder_var, browse_callback):
        """Create folder selection UI component."""
        frame = ttk.LabelFrame(parent, text="Input Folder", padding="10")
        frame.pack(fill=tk.X, pady=5)

        ttk.Label(frame, text="Image Source Folder:").pack(
            side=tk.LEFT, padx=(0, 5))

        entry = ttk.Entry(frame, textvariable=input_folder_var, width=50)
        entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        browse_btn = ttk.Button(frame, text="Browse...",
                                command=browse_callback)
        browse_btn.pack(side=tk.LEFT)

        return frame, entry

    @staticmethod
    def create_photographer_ui(parent, photographer_var):
        """Create photographer input UI component."""
        frame = ttk.LabelFrame(parent, text="Metadata", padding="10")
        frame.pack(fill=tk.X, pady=5)

        ttk.Label(frame, text="Photographer:").pack(side=tk.LEFT, padx=(0, 5))

        entry = ttk.Entry(frame, textvariable=photographer_var, width=40)
        entry.pack(side=tk.LEFT, expand=True, fill=tk.X)

        return frame, entry

    @staticmethod
    def create_ruler_pos_ui(parent, museum_var, ruler_position_var, on_museum_changed, on_ruler_canvas_click):
        """Create ruler position UI component."""
        frame = ttk.LabelFrame(parent, text="Ruler Options", padding="10")
        frame.pack(fill=tk.X, pady=5)

        museum_frame = ttk.Frame(frame)
        museum_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(museum_frame, text="Museum:").pack(side=tk.LEFT, padx=(0, 5))

        museum_combo = ttk.Combobox(
            museum_frame,
            textvariable=museum_var,
            width=20,
            values=["British Museum", "Iraq Museum",
                    "eBL Ruler (CBS)", "Non-eBL Ruler (VAM)"]
        )
        museum_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        museum_combo.bind("<<ComboboxSelected>>", on_museum_changed)

        ttk.Label(frame, text="Click ruler location:").pack(anchor=tk.W)

        canvas_size = 120
        padding = 10
        band_thickness = 25

        ruler_canvas = tk.Canvas(
            frame,
            width=canvas_size,
            height=canvas_size,
            bg="lightgray",
            relief=tk.SUNKEN,
            borderwidth=1
        )
        ruler_canvas.pack(pady=5)
        ruler_canvas.bind("<Button-1>", on_ruler_canvas_click)

        canvas_params = {
            'size': canvas_size,
            'padding': padding,
            'band_thickness': band_thickness
        }

        return frame, ruler_canvas, canvas_params, museum_combo

    @staticmethod
    def create_main_options_ui(parent, use_measurements_var, measurements_loaded,
                          enable_hdr_var, use_first_photo_measurements_var, 
                          script_directory, debug_callback):
        """Create main options UI (measurements, first photo measurements, and HDR)."""

        options_frame = ttk.LabelFrame(parent, text="Options")
        options_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        measurements_checkbox = ttk.Checkbutton(
            options_frame,
            text="Use measurements from database",
            variable=use_measurements_var
        )
        measurements_checkbox.pack(anchor=tk.W, padx=10, pady=0)
        
        measurements_description = ttk.Label(
            options_frame,
            text="Use known tablet dimensions for scale instead of ruler marks",
            font=("", 8),
            foreground="gray"
        )
        measurements_description.pack(anchor=tk.W, padx=30, pady=(0, 5))

        if not measurements_loaded:
            measurements_checkbox.config(state=tk.DISABLED)

            debug_btn = ttk.Button(
                options_frame,
                text="Debug measurements loading",
                command=debug_callback,
                style="Small.TButton"
            )
            debug_btn.pack(anchor=tk.W, padx=20, pady=(0, 0))

        first_photo_measurements_checkbox = ttk.Checkbutton(
            options_frame,
            text="Take measurements from first photograph only",
            variable=use_first_photo_measurements_var
        )
        first_photo_measurements_checkbox.pack(anchor=tk.W, padx=10, pady=(0, 0))

        first_photo_description = ttk.Label(
            options_frame,
            text="Detect ruler only in first image set, apply px/cm ratio to all others",
            font=("", 8),
            foreground="gray"
        )
        first_photo_description.pack(anchor=tk.W, padx=50, pady=(0, 0))

        hdr_checkbox = ttk.Checkbutton(
            options_frame,
            text="Enable HDR Processing",
            variable=enable_hdr_var
        )
        hdr_checkbox.pack(anchor=tk.W, padx=10, pady=0)

        hdr_description = ttk.Label(
            options_frame,
            text="HDR processing combines sets of 3 bracketed exposure images into composites",
            font=("", 8),
            foreground="gray"
        )
        hdr_description.pack(anchor=tk.W, padx=30, pady=(0, 0))

        return options_frame, measurements_checkbox, hdr_checkbox, first_photo_measurements_checkbox

    @staticmethod
    def create_process_button_ui(parent, start_processing_callback):
        """Create processing button UI component."""
        process_btn = ttk.Button(
            parent,
            text="Start Processing",
            command=start_processing_callback
        )
        process_btn.pack(pady=(15, 5), ipadx=10, ipady=5)

        return process_btn

    @staticmethod
    def create_progress_bar_ui(parent):
        """Create progress bar UI component."""
        frame = ttk.Frame(parent, padding="0 0 0 5")
        frame.pack(fill=tk.X)

        progress_var = tk.DoubleVar(value=0.0)
        progress_bar = ttk.Progressbar(
            frame,
            orient="horizontal",
            length=100,
            mode="determinate",
            variable=progress_var
        )
        progress_bar.pack(fill=tk.X, expand=True)

        return frame, progress_bar, progress_var

    @staticmethod
    def create_log_area_ui(parent, text_redirector_class):
        """Create log area UI with scrollbar."""
        log_frame = ttk.LabelFrame(parent, text="Processing Log", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        text_frame = ttk.Frame(log_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        log_text = tk.Text(text_frame, height=10, wrap=tk.WORD, state=tk.DISABLED,
                          bg="#f0f0f0", font=("Consolas", 9))

        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=log_text.yview)

        log_text.configure(yscrollcommand=scrollbar.set)

        log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        sys.stdout = text_redirector_class(log_text)

        return log_frame, log_text
