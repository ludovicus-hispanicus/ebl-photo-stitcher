import tkinter as tk
from tkinter import ttk

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

        self.gradient_width_fraction = tk.DoubleVar(value=self.settings.get('gradient_width_fraction', 0.5))
        self.background_color_tolerance = tk.IntVar(value=self.settings.get('background_color_tolerance', 40))

        self.gradient_label = None
        self.tolerance_label = None

        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI elements for the Advanced tab"""

        main_frame = ttk.Frame(self.frame, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        blending_frame = ttk.LabelFrame(main_frame, text="Blending Options")
        blending_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(blending_frame, text="Gradient Coverage:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        gradient_frame = ttk.Frame(blending_frame)
        gradient_frame.grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)


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
        
        self.gradient_label = ttk.Label(gradient_frame, text=f"{percentage}%", width=5)
        self.gradient_label.pack(side=tk.LEFT, padx=5)

        ttk.Label(
            blending_frame, 
            text="Controls how much of each intermediate image is covered by the gradient blend",
            font=("", 8),
            foreground="gray"
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=5)

        extraction_frame = ttk.LabelFrame(main_frame, text="Object Extraction Options")
        extraction_frame.pack(fill=tk.X, padx=5, pady=(15, 5))

        ttk.Label(extraction_frame, text="Color Tolerance:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        tolerance_frame = ttk.Frame(extraction_frame)
        tolerance_frame.grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
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
        
        self.tolerance_label = ttk.Label(tolerance_frame, text=str(tolerance), width=5)
        self.tolerance_label.pack(side=tk.LEFT, padx=5)

        self.tolerance_slider.configure(command=self._update_tolerance_label)

        ttk.Label(
            extraction_frame, 
            text="Controls how strictly background colors are identified (higher = more tolerant)",
            font=("", 8),
            foreground="gray"
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=5)
    
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
            'background_color_tolerance': self.background_color_tolerance.get()
        }
    
    def apply_settings(self, settings):
        """
        Apply settings from the dictionary to the UI controls
        
        Args:
            settings: Dictionary containing application settings
        """
        if 'gradient_width_fraction' in settings and hasattr(self, 'gradient_slider'):

            self.gradient_width_fraction.set(settings['gradient_width_fraction'])

            percentage = int(settings['gradient_width_fraction'] * 100)

            self.gradient_slider_var.set(percentage)
            self.gradient_slider.set(percentage)

            if hasattr(self, 'gradient_label') and self.gradient_label:
                self.gradient_label.config(text=f"{percentage}%")
            
        if 'background_color_tolerance' in settings and hasattr(self, 'tolerance_slider'):

            self.background_color_tolerance.set(settings['background_color_tolerance'])

            tolerance = int(settings['background_color_tolerance'])
            self.tolerance_slider.set(tolerance)

            if hasattr(self, 'tolerance_label') and self.tolerance_label:
                self.tolerance_label.config(text=f"{tolerance}")