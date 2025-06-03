import tkinter as tk
from tkinter import ttk, filedialog


class AdvancedTab:
    def __init__(self, parent, settings):
        """
        Initialize the Advanced tab with controls for advanced settings.

        Args:
            parent: The parent notebook widget
            settings: Dictionary containing application settings
        """
        self.parent = parent
        self.settings = settings

        self.frame = ttk.Frame(parent)
        parent.add(self.frame, text="Advanced")

        self.gradient_width_fraction = tk.DoubleVar(
            value=self.settings.get('gradient_width_fraction', 0.5))
        self.background_color_tolerance = tk.IntVar(
            value=self.settings.get('background_color_tolerance', 40))

        self.add_logo_var = tk.BooleanVar(
            value=self.settings.get('add_logo', False))
        self.logo_path_var = tk.StringVar(
            value=self.settings.get('logo_path', ''))

        self.gradient_label = None
        self.tolerance_label = None

        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI elements for the Advanced tab"""

        main_frame = ttk.Frame(self.frame, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        blending_frame = ttk.LabelFrame(main_frame, text="Blending Options")
        blending_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(blending_frame, text="Gradient Coverage:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5)

        gradient_frame = ttk.Frame(blending_frame)
        gradient_frame.grid(
            row=0, column=1, sticky=tk.W + tk.E, padx=5, pady=5)

        self.gradient_slider_var = tk.DoubleVar()
        percentage = int(self.gradient_width_fraction.get() * 100)
        self.gradient_slider_var.set(percentage)

        self.gradient_slider = ttk.Scale(
            gradient_frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            variable=self.gradient_slider_var,
            command=self._update_gradient_label
        )
        self.gradient_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.gradient_label = ttk.Label(
            gradient_frame, text=f"{percentage}%", width=5)
        self.gradient_label.pack(side=tk.LEFT, padx=5)

        ttk.Label(
            blending_frame,
            text="Controls how much of each intermediate image is covered by the gradient blend",
            font=("", 8),
            foreground="gray"
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=5)

        extraction_frame = ttk.LabelFrame(
            main_frame, text="Object Extraction Options")
        extraction_frame.pack(fill=tk.X, padx=5, pady=(15, 5))

        ttk.Label(extraction_frame, text="Color Tolerance:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5)

        tolerance_frame = ttk.Frame(extraction_frame)
        tolerance_frame.grid(
            row=0, column=1, sticky=tk.W + tk.E, padx=5, pady=5)

        self.tolerance_slider = ttk.Scale(
            tolerance_frame,
            from_=1,
            to=100,
            orient=tk.HORIZONTAL,
            variable=self.background_color_tolerance
        )
        self.tolerance_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tolerance = int(self.background_color_tolerance.get())
        self.tolerance_slider.set(tolerance)

        self.tolerance_label = ttk.Label(
            tolerance_frame, text=str(tolerance), width=5)
        self.tolerance_label.pack(side=tk.LEFT, padx=5)

        self.tolerance_slider.configure(command=self._update_tolerance_label)

        ttk.Label(
            extraction_frame,
            text="Controls how strictly background colors are identified (higher = more tolerant)",
            font=("", 8),
            foreground="gray"
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=5)

        logo_frame = ttk.LabelFrame(main_frame, text="Logo Options")
        logo_frame.pack(fill=tk.X, padx=5, pady=(15, 5))

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
        self.logo_path_entry.pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))

        self.browse_logo_btn = ttk.Button(
            logo_path_frame,
            text="Browse...",
            command=self._browse_logo_file
        )
        self.browse_logo_btn.pack(side=tk.RIGHT)

        self._toggle_logo_path_entry()

    def _toggle_logo_path_entry(self):
        """Toggle logo path entry enabled/disabled state."""
        if self.add_logo_var.get():
            self.logo_path_entry.config(state=tk.NORMAL)
            self.browse_logo_btn.config(state=tk.NORMAL)
        else:
            self.logo_path_entry.config(state=tk.DISABLED)
            self.browse_logo_btn.config(state=tk.DISABLED)

    def _browse_logo_file(self):
        """Browse for a logo file."""
        file_path = filedialog.askopenfilename(
            title="Select Logo File",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff *.tif"),
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.logo_path_var.set(file_path)

    def _update_gradient_label(self, *args):
        """Update the label showing the current gradient percentage"""
        if hasattr(self, 'gradient_label') and self.gradient_label:
            percentage = int(float(self.gradient_slider_var.get()))
            self.gradient_label.config(text=f"{percentage}%")
            self.gradient_width_fraction.set(percentage / 100)

    def _update_tolerance_label(self, *args):
        """Update the label showing the current color tolerance"""
        if hasattr(self, 'tolerance_label') and self.tolerance_label:
            tolerance = int(float(self.tolerance_slider.get()))
            self.tolerance_label.config(text=str(tolerance))
            self.background_color_tolerance.set(tolerance)

    def get_settings(self):
        """
        Get all settings from this tab

        Returns:
            Dictionary with advanced settings
        """
        return {
            'gradient_width_fraction': self.gradient_width_fraction.get(),
            'background_color_tolerance': self.background_color_tolerance.get(),
            'add_logo': self.add_logo_var.get(),
            'logo_path': self.logo_path_var.get()
        }

    def apply_settings(self, settings):
        """
        Apply settings from the dictionary to the UI controls

        Args:
            settings: Dictionary containing application settings
        """
        if 'gradient_width_fraction' in settings and hasattr(self, 'gradient_slider'):
            self.gradient_width_fraction.set(
                settings['gradient_width_fraction'])
            percentage = int(settings['gradient_width_fraction'] * 100)
            self.gradient_slider_var.set(percentage)
            self.gradient_slider.set(percentage)
            if hasattr(self, 'gradient_label') and self.gradient_label:
                self.gradient_label.config(text=f"{percentage}%")

        if 'background_color_tolerance' in settings and hasattr(self, 'tolerance_slider'):
            self.background_color_tolerance.set(
                settings['background_color_tolerance'])
            tolerance = int(settings['background_color_tolerance'])
            self.tolerance_slider.set(tolerance)
            if hasattr(self, 'tolerance_label') and self.tolerance_label:
                self.tolerance_label.config(text=f"{tolerance}")

        if 'add_logo' in settings:
            self.add_logo_var.set(settings['add_logo'])
            self._toggle_logo_path_entry()

        if 'logo_path' in settings:
            self.logo_path_var.set(settings['logo_path'])
