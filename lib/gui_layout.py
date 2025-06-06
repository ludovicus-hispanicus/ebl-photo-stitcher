"""Layout and styling functions for the eBL Photo Stitcher application."""

import tkinter as tk
from tkinter import ttk


class LayoutManager:
    """Helper class for UI layout and styling."""

    @staticmethod
    def setup_styles(root):
        """Set up ttk styles for the application."""
        style = ttk.Style()

        style.configure("TLabel", padding=5, font=('Helvetica', 10))
        style.configure("TButton", padding=5, font=('Helvetica', 10))
        style.configure("TFrame", padding=10)

        style.configure("Link.TLabel", foreground="blue",
                        font=('Helvetica', 10, 'underline'))

        style.configure("Link.TButton",
                        foreground="blue",
                        font=('Helvetica', 10, 'underline'),
                        background=root.cget('bg'),
                        relief="flat",
                        padding=2,
                        borderwidth=0)
        style.map("Link.TButton",
                  background=[("active", root.cget('bg'))],
                  relief=[("active", "flat")])

        style.configure("Small.TButton", padding=2, font=('Helvetica', 8))

        return style

    @staticmethod
    def create_tabs(parent_frame):
        """Create notebook with tabs."""
        header_frame = ttk.Frame(parent_frame, padding=0)
        header_frame.pack(fill=tk.X, pady=(0, 5))

        header_frame.columnconfigure(0, weight=1)
        header_frame.columnconfigure(1, weight=0)

        notebook = ttk.Notebook(header_frame)
        notebook.grid(row=0, column=0, sticky="w")

        buttons_frame = ttk.Frame(header_frame)
        buttons_frame.grid(row=0, column=0, sticky="ne")

        return header_frame, notebook, buttons_frame

    @staticmethod
    def _create_link_button(parent_frame, text, command_callback):
        """Create a styled link button (shared styling for help and version buttons)."""
        try:
            bg_color = parent_frame.winfo_toplevel().cget('bg')
        except:
            bg_color = 'SystemButtonFace'

        button = tk.Button(
            parent_frame,
            text=text,
            fg="blue",
            cursor="hand2",
            font=('Helvetica', 10, 'underline'),
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0,
            bg=bg_color,
            activebackground=bg_color,
            command=command_callback
        )
        return button

    @staticmethod
    def create_version_button(buttons_frame, command_callback):
        """Create version button in header."""
        version_button = LayoutManager._create_link_button(
            buttons_frame, "Checking...", command_callback
        )

        version_button.config(
            fg="gray",
            cursor="arrow",
            font=('Helvetica', 10)
        )

        version_button.pack(side=tk.LEFT, padx=(0, 15))
        return version_button

    @staticmethod
    def update_version_button(version_button, latest_version, is_newer_available, get_current_version_func):
        """Update version button based on check results."""
        if version_button is None:
            print("Version button not yet created - skipping update")
            return

        if latest_version is None:

            version_button.config(
                text=f"Latest Version ({get_current_version_func()})",
                fg="gray",
                cursor="arrow",
                font=('Helvetica', 10),
                state="disabled"
            )
        elif is_newer_available:

            version_button.config(
                text="Update Available",
                fg="blue",
                cursor="hand2",
                font=('Helvetica', 10, 'underline'),
                state="normal"
            )
        else:

            version_button.config(
                text=f"Latest Version ({get_current_version_func()})",
                fg="gray",
                cursor="arrow",
                font=('Helvetica', 10),
                state="disabled"
            )

    @staticmethod
    def create_help_link(buttons_frame, help_url):
        """Create help link in header."""
        import webbrowser
        
        help_button = LayoutManager._create_link_button(
            buttons_frame,
            "Help", 
            lambda: webbrowser.open_new(help_url)
        )

        help_button.pack(side=tk.LEFT)
        return help_button

    @staticmethod
    def draw_ruler_selector(canvas, ruler_position, museum_selection, canvas_params):
        """Draw the ruler selector canvas."""

        s = canvas_params['size']
        p = canvas_params['padding']
        bt = canvas_params['band_thickness']

        canvas.delete("all")

        ox1, oy1, ox2, oy2 = p + bt, p + bt, s - p - bt, s - p - bt

        canvas.create_rectangle(
            ox1, oy1, ox2, oy2, outline="gray", fill="whitesmoke", dash=(2, 2))
        canvas.create_text(s / 2, s / 2, text="Object",
                           font=('Helvetica', 9, 'italic'), fill="gray")

        is_iraq_museum = (museum_selection == "Iraq Museum")

        active_fill_color = "lightblue"
        selected_fill_color = "blue"
        disabled_fill_color = "#e0e0e0"
        iraq_fixed_fill_color = selected_fill_color
        text_color = "black"
        nd = 4
        lh, lv = ox2 - ox1, oy2 - oy1

        top_fill = disabled_fill_color if is_iraq_museum else (
            selected_fill_color if ruler_position == "top" else active_fill_color)
        bottom_fill = disabled_fill_color if is_iraq_museum else (
            selected_fill_color if ruler_position == "bottom" else active_fill_color)
        left_fill = disabled_fill_color if is_iraq_museum else (
            selected_fill_color if ruler_position == "left" else active_fill_color)
        right_fill = disabled_fill_color if is_iraq_museum else (
            selected_fill_color if ruler_position == "right" else active_fill_color)

        canvas.create_rectangle(ox1, p, ox2, p + bt, fill=top_fill,
                                outline=text_color, tags="top_zone")
        if not is_iraq_museum:
            for i in range(nd + 1):
                x = ox1 + i * (lh / nd)
                canvas.create_line(x, p, x, p + bt * .6, fill=text_color)

        canvas.create_rectangle(ox1, oy2, ox2, oy2 + bt,
                                fill=bottom_fill, outline=text_color, tags="bottom_zone")
        if not is_iraq_museum:
            for i in range(nd + 1):
                x = ox1 + i * (lh / nd)
                canvas.create_line(x, oy2, x, oy2 + bt * .6, fill=text_color)

        canvas.create_rectangle(p, oy1, p + bt, oy2, fill=left_fill,
                                outline=text_color, tags="left_zone")
        if not is_iraq_museum:
            for i in range(nd + 1):
                y = oy1 + i * (lv / nd)
                canvas.create_line(p, y, p + bt * .6, y, fill=text_color)

        canvas.create_rectangle(ox2, oy1, ox2 + bt, oy2,
                                fill=right_fill, outline=text_color, tags="right_zone")
        if not is_iraq_museum:
            for i in range(nd + 1):
                y = oy1 + i * (lv / nd)
                canvas.create_line(ox2, y, ox2 + bt * .6, y, fill=text_color)

        if is_iraq_museum:
            cs_x1 = p
            cs_y1 = oy2
            cs_x2 = p + bt
            cs_y2 = oy2 + bt
            canvas.create_rectangle(cs_x1, cs_y1, cs_x2, cs_y2,
                                    fill=iraq_fixed_fill_color, outline=text_color,
                                    tags="iraq_fixed_pos")

            canvas.create_text(p + bt / 2, oy2 + bt / 2, text="IM",
                               font=('Helvetica', 7, 'bold'), fill="white")
