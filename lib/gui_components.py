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
                               enable_hdr_var, script_directory, debug_callback):
        """Create main options UI (measurements and HDR)."""

        options_frame = ttk.LabelFrame(parent, text="Options")
        options_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        measurements_checkbox = ttk.Checkbutton(
            options_frame,
            text="Use measurements from database",
            variable=use_measurements_var
        )
        measurements_checkbox.pack(anchor=tk.W, padx=10, pady=5)

        if not measurements_loaded:
            measurements_checkbox.config(state=tk.DISABLED)

            debug_btn = ttk.Button(
                options_frame,
                text="Debug measurements loading",
                command=debug_callback,
                style="Small.TButton"
            )
            debug_btn.pack(anchor=tk.W, padx=20, pady=(0, 5))

        hdr_checkbox = ttk.Checkbutton(
            options_frame,
            text="Enable HDR Processing",
            variable=enable_hdr_var
        )
        hdr_checkbox.pack(anchor=tk.W, padx=10, pady=5)

        hdr_description = ttk.Label(
            options_frame,
            text="HDR processing combines sets of bracketed exposure images into optimized composites",
            font=("", 8),
            foreground="gray"
        )
        hdr_description.pack(anchor=tk.W, padx=30, pady=(0, 5))

        return options_frame, measurements_checkbox, hdr_checkbox

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
        """Create log area UI component."""
        frame = ttk.LabelFrame(parent, text="Log", padding="10")
        frame.pack(fill=tk.BOTH, expand=True, pady=5)

        log_text = tk.Text(
            frame,
            height=15,
            wrap=tk.WORD,
            relief=tk.SUNKEN,
            borderwidth=1,
            state=tk.DISABLED
        )
        log_text.pack(fill=tk.BOTH, expand=True)

        sys.stdout = text_redirector_class(log_text, "stdout")
        sys.stderr = text_redirector_class(log_text, "stderr")

        return frame, log_text
