"""Configuration tab for managing processing projects.

A project is a named bundle of settings (ruler file, background color,
metadata, logo, etc.) that determines how a batch is processed. Built-in
projects ship with the app; users can create, save, and delete their own.
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, colorchooser, messagebox, simpledialog

import project_manager


RULER_POSITIONS = ["top", "bottom", "left", "right", "bottom-left-fixed"]
DETECTION_METHODS = [("General", "general"),
                     ("Iraq Museum (text + ticks)", "iraq_museum")]
RULER_MODES = [("Single file", "single"),
               ("Adaptive set (1/2/5 cm by tablet size)", "adaptive_set")]


class ProjectConfigTab:
    """UI for creating, editing, and saving processing projects."""

    def __init__(self, notebook, on_project_changed=None):
        self.notebook = notebook
        self.on_project_changed = on_project_changed  # callback(project_dict)
        self._current_project = None
        self._suppress_dirty = False
        self._dirty = False

        self.main_frame = ttk.Frame(notebook)
        notebook.add(self.main_frame, text="Configuration")

        self._build_ui()
        self.refresh_project_list()

    # -- UI construction ---------------------------------------------------
    def _build_ui(self):
        # Scrollable container so the form fits small windows
        container = ttk.Frame(self.main_frame)
        container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(container, borderwidth=0, highlightthickness=0)
        vsb = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)

        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        body = ttk.Frame(canvas)
        body_id = canvas.create_window((0, 0), window=body, anchor="nw")

        def _on_body_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        body.bind("<Configure>", _on_body_configure)

        def _on_canvas_configure(event):
            canvas.itemconfigure(body_id, width=event.width)
        canvas.bind("<Configure>", _on_canvas_configure)

        # Mouse wheel / two-finger trackpad scrolling
        def _on_mousewheel(event):
            if event.delta:
                canvas.yview_scroll(int(-event.delta / 120), "units")
            return "break"

        def _on_linux_scroll_up(event):
            canvas.yview_scroll(-3, "units")
            return "break"

        def _on_linux_scroll_down(event):
            canvas.yview_scroll(3, "units")
            return "break"

        def _bind_wheel(_e=None):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            canvas.bind_all("<Button-4>", _on_linux_scroll_up)
            canvas.bind_all("<Button-5>", _on_linux_scroll_down)

        def _unbind_wheel(_e=None):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        self.main_frame.bind("<Enter>", _bind_wheel)
        self.main_frame.bind("<Leave>", _unbind_wheel)

        # Project selector row
        selector_frame = ttk.LabelFrame(body, text="Project", padding="8")
        selector_frame.pack(fill=tk.X, padx=8, pady=(8, 4))

        top_row = ttk.Frame(selector_frame)
        top_row.pack(fill=tk.X)
        ttk.Label(top_row, text="Active project:").pack(side=tk.LEFT, padx=(0, 6))

        self.project_var = tk.StringVar()
        self.project_combo = ttk.Combobox(top_row, textvariable=self.project_var,
                                           state="readonly", width=32)
        self.project_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.project_combo.bind("<<ComboboxSelected>>", self._on_project_selected)

        btn_row = ttk.Frame(selector_frame)
        btn_row.pack(fill=tk.X, pady=(6, 0))
        ttk.Button(btn_row, text="New", command=self._new_project).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(btn_row, text="Duplicate", command=self._duplicate_project).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(btn_row, text="Save", command=self._save_project).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(btn_row, text="Delete", command=self._delete_project).pack(side=tk.LEFT, padx=(0, 4))

        self.status_label = ttk.Label(selector_frame, text="", foreground="gray")
        self.status_label.pack(anchor=tk.W, pady=(4, 0))

        # --- Background color ---
        bg_frame = ttk.LabelFrame(body, text="Background", padding="8")
        bg_frame.pack(fill=tk.X, padx=8, pady=4)

        bg_row = ttk.Frame(bg_frame)
        bg_row.pack(fill=tk.X)
        ttk.Label(bg_row, text="Color:").pack(side=tk.LEFT, padx=(0, 6))

        self.bg_color_var = tk.StringVar(value="(0, 0, 0)")
        self.bg_color_entry = ttk.Entry(bg_row, textvariable=self.bg_color_var, width=16)
        self.bg_color_entry.pack(side=tk.LEFT, padx=(0, 6))
        self.bg_color_entry.bind("<FocusOut>", lambda e: self._mark_dirty())

        self.bg_swatch = tk.Label(bg_row, text="  ", bg="#000000", width=3,
                                   relief=tk.SUNKEN, borderwidth=2)
        self.bg_swatch.pack(side=tk.LEFT, padx=(0, 6))

        ttk.Button(bg_row, text="Pick...",
                   command=self._pick_bg_color).pack(side=tk.LEFT)
        ttk.Button(bg_row, text="Black",
                   command=lambda: self._set_bg_color((0, 0, 0))).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(bg_row, text="White",
                   command=lambda: self._set_bg_color((255, 255, 255))).pack(side=tk.LEFT, padx=(6, 0))

        # --- Ruler ---
        ruler_frame = ttk.LabelFrame(body, text="Ruler", padding="8")
        ruler_frame.pack(fill=tk.X, padx=8, pady=4)

        mode_row = ttk.Frame(ruler_frame)
        mode_row.pack(fill=tk.X)
        ttk.Label(mode_row, text="Mode:").pack(side=tk.LEFT, padx=(0, 6))
        self.ruler_mode_var = tk.StringVar(value="single")
        for label, value in RULER_MODES:
            ttk.Radiobutton(mode_row, text=label, variable=self.ruler_mode_var,
                            value=value, command=self._on_ruler_mode_changed).pack(side=tk.LEFT, padx=(0, 10))

        # Single-file ruler row
        self.single_frame = ttk.Frame(ruler_frame)
        self.single_frame.pack(fill=tk.X, pady=(6, 0))

        file_row = ttk.Frame(self.single_frame)
        file_row.pack(fill=tk.X)
        ttk.Label(file_row, text="Ruler file:", width=12).pack(side=tk.LEFT)
        self.ruler_file_var = tk.StringVar()
        ttk.Entry(file_row, textvariable=self.ruler_file_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        ttk.Button(file_row, text="Browse...",
                   command=self._browse_ruler_file).pack(side=tk.LEFT)
        self.ruler_file_var.trace_add("write", lambda *a: self._mark_dirty())

        size_row = ttk.Frame(self.single_frame)
        size_row.pack(fill=tk.X, pady=(4, 0))
        ttk.Label(size_row, text="Size (cm):", width=12).pack(side=tk.LEFT)
        self.ruler_size_var = tk.StringVar(value="5.0")
        ttk.Entry(size_row, textvariable=self.ruler_size_var, width=10).pack(side=tk.LEFT)
        self.ruler_size_var.trace_add("write", lambda *a: self._mark_dirty())

        # Adaptive set ruler rows
        self.adaptive_frame = ttk.Frame(ruler_frame)
        self.adaptive_vars = {}
        for key in ("1cm", "2cm", "5cm"):
            row = ttk.Frame(self.adaptive_frame)
            row.pack(fill=tk.X, pady=(4, 0))
            ttk.Label(row, text=f"{key} file:", width=12).pack(side=tk.LEFT)
            file_var = tk.StringVar()
            ttk.Entry(row, textvariable=file_var).pack(
                side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
            ttk.Button(row, text="Browse...",
                       command=lambda k=key: self._browse_adaptive_ruler(k)).pack(side=tk.LEFT, padx=(0, 4))
            ttk.Label(row, text="cm:", width=4).pack(side=tk.LEFT)
            size_var = tk.StringVar(value="0.0")
            ttk.Entry(row, textvariable=size_var, width=8).pack(side=tk.LEFT)
            file_var.trace_add("write", lambda *a: self._mark_dirty())
            size_var.trace_add("write", lambda *a: self._mark_dirty())
            self.adaptive_vars[key] = (file_var, size_var)

        # Ruler preview
        self.ruler_preview_frame = ttk.Frame(ruler_frame)
        self.ruler_preview_frame.pack(fill=tk.X, pady=(8, 0))
        self.ruler_preview_label = ttk.Label(self.ruler_preview_frame)
        self.ruler_preview_label.pack(anchor=tk.W)
        self._ruler_preview_photo = None  # keep reference to prevent GC

        # Update preview when ruler file changes
        self.ruler_file_var.trace_add("write", lambda *a: self._update_ruler_preview())
        for key, (f_var, _) in self.adaptive_vars.items():
            f_var.trace_add("write", lambda *a: self._update_ruler_preview())

        # --- Ruler Position (visual selector) ---
        pos_frame = ttk.LabelFrame(body, text="Ruler Position in Final Image", padding="8")
        pos_frame.pack(fill=tk.X, padx=8, pady=4)

        ttk.Label(pos_frame, text="Click to set ruler location:").pack(anchor=tk.W)

        canvas_size = 140
        padding = 12
        band_thickness = 28

        self.ruler_pos_canvas = tk.Canvas(
            pos_frame, width=canvas_size, height=canvas_size,
            bg="lightgray", relief=tk.SUNKEN, borderwidth=1
        )
        self.ruler_pos_canvas.pack(pady=5)
        self.ruler_pos_canvas.bind("<Button-1>", self._on_ruler_pos_click)

        self._ruler_pos_params = {
            'size': canvas_size,
            'padding': padding,
            'band_thickness': band_thickness
        }

        self.position_lock_var = tk.BooleanVar(value=False)
        self.fixed_position_var = tk.StringVar(value="top")
        self.ruler_position_var = tk.StringVar(value="top")

        # --- Detection method ---
        det_frame = ttk.LabelFrame(body, text="Scale Detection", padding="8")
        det_frame.pack(fill=tk.X, padx=8, pady=4)

        self.detection_var = tk.StringVar(value="general")
        for label, value in DETECTION_METHODS:
            ttk.Radiobutton(det_frame, text=label, variable=self.detection_var,
                            value=value, command=self._mark_dirty).pack(anchor=tk.W)

        # --- Metadata ---
        meta_frame = ttk.LabelFrame(body, text="Metadata", padding="8")
        meta_frame.pack(fill=tk.X, padx=8, pady=4)

        photo_row = ttk.Frame(meta_frame)
        photo_row.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(photo_row, text="Photographer:", width=14).pack(side=tk.LEFT)
        self.photographer_var = tk.StringVar()
        ttk.Entry(photo_row, textvariable=self.photographer_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.photographer_var.trace_add("write", lambda *a: self._mark_dirty())

        ttk.Label(meta_frame, text="Institution:").pack(anchor=tk.W)
        self.institution_var = tk.StringVar()
        ttk.Entry(meta_frame, textvariable=self.institution_var).pack(fill=tk.X, pady=(2, 6))
        self.institution_var.trace_add("write", lambda *a: self._mark_dirty())

        ttk.Label(meta_frame, text="Credit line:").pack(anchor=tk.W)
        self.credit_text = tk.Text(meta_frame, height=3, wrap=tk.WORD)
        self.credit_text.pack(fill=tk.X, pady=(2, 0))
        self.credit_text.bind("<<Modified>>", self._on_credit_modified)

        # --- Logo ---
        logo_frame = ttk.LabelFrame(body, text="Logo", padding="8")
        logo_frame.pack(fill=tk.X, padx=8, pady=4)

        self.logo_enabled_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(logo_frame, text="Add logo to final image",
                        variable=self.logo_enabled_var,
                        command=self._mark_dirty).pack(anchor=tk.W)

        logo_row = ttk.Frame(logo_frame)
        logo_row.pack(fill=tk.X, pady=(4, 0))
        ttk.Label(logo_row, text="Logo file:", width=12).pack(side=tk.LEFT)
        self.logo_path_var = tk.StringVar()
        ttk.Entry(logo_row, textvariable=self.logo_path_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        ttk.Button(logo_row, text="Browse...",
                   command=self._browse_logo_file).pack(side=tk.LEFT)
        self.logo_path_var.trace_add("write", lambda *a: self._mark_dirty())

        # --- Measurements ---
        meas_frame = ttk.LabelFrame(body, text="Measurements Database", padding="8")
        meas_frame.pack(fill=tk.X, padx=8, pady=(4, 12))

        meas_row = ttk.Frame(meas_frame)
        meas_row.pack(fill=tk.X)
        ttk.Label(meas_row, text="File:", width=12).pack(side=tk.LEFT)
        self.measurements_file_var = tk.StringVar()
        ttk.Entry(meas_row, textvariable=self.measurements_file_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        ttk.Button(meas_row, text="Browse...",
                   command=self._browse_measurements_file).pack(side=tk.LEFT)
        self.measurements_file_var.trace_add("write", lambda *a: self._mark_dirty())

        ttk.Label(meas_frame, text="Leave empty if this project has no measurements database.",
                  foreground="gray").pack(anchor=tk.W, pady=(4, 0))

        self._on_ruler_mode_changed()

    # -- Project list management -------------------------------------------
    def refresh_project_list(self, select_name=None):
        projects = project_manager.list_projects()
        names = [p["name"] for p in projects]
        self.project_combo["values"] = names
        if select_name and select_name in names:
            self.project_var.set(select_name)
        elif names and not self.project_var.get():
            self.project_var.set(names[0])
        if self.project_var.get():
            self._load_project(self.project_var.get())

    def get_active_project(self):
        return self._current_project

    def get_project_names(self):
        return [p["name"] for p in project_manager.list_projects()]

    def set_active_project_by_name(self, name):
        """Called externally (e.g. from the Main tab selector) to switch projects."""
        if self.project_var.get() == name:
            return
        self.project_var.set(name)
        self._load_project(name)

    # -- Event handlers -----------------------------------------------------
    def _on_project_selected(self, event=None):
        self._load_project(self.project_var.get())

    def _load_project(self, name):
        project = project_manager.get_project_by_name(name)
        if project is None:
            return
        self._current_project = project
        self._populate_form(project)
        self._dirty = False
        builtin_tag = " (built-in)" if project.get("builtin") else ""
        self.status_label.config(
            text=f"Loaded: {project['name']}{builtin_tag}", foreground="gray")
        project_manager.set_active_project(project)
        if self.on_project_changed:
            try:
                self.on_project_changed(project)
            except Exception as e:
                print(f"Project change callback failed: {e}")

    def _populate_form(self, project):
        self._suppress_dirty = True
        try:
            bg = project.get("background_color", [0, 0, 0])
            self._set_bg_color(tuple(bg), mark_dirty=False)

            mode = project.get("ruler_mode", "single")
            self.ruler_mode_var.set(mode)

            self.ruler_file_var.set(project.get("ruler_file", ""))
            self.ruler_size_var.set(str(project.get("ruler_size_cm", 5.0)))

            files = project.get("ruler_files", {}) or {}
            sizes = project.get("ruler_sizes_cm", {}) or {}
            for key, (f_var, s_var) in self.adaptive_vars.items():
                f_var.set(files.get(key, ""))
                s_var.set(str(sizes.get(key, 0.0)))

            self.detection_var.set(project.get("detection_method", "general"))

            self.position_lock_var.set(bool(project.get("ruler_position_locked")))
            fixed_pos = project.get("fixed_ruler_position", "top")
            self.fixed_position_var.set(fixed_pos)
            self.ruler_position_var.set(fixed_pos)
            self._draw_ruler_position()

            self.photographer_var.set(project.get("photographer", "") or "")
            self.institution_var.set(project.get("institution", "") or "")

            self.credit_text.delete("1.0", tk.END)
            self.credit_text.insert("1.0", project.get("credit_line", "") or "")
            self.credit_text.edit_modified(False)

            self.logo_enabled_var.set(bool(project.get("logo_enabled")))
            self.logo_path_var.set(project.get("logo_path", "") or "")
            self.measurements_file_var.set(project.get("measurements_file", "") or "")

            self._on_ruler_mode_changed()
        finally:
            self._suppress_dirty = False

    def _collect_form(self):
        """Gather form values into a project dict."""
        try:
            bg_tuple = self._parse_bg_color(self.bg_color_var.get())
        except ValueError:
            raise ValueError("Background color must be three integers 0-255, e.g. (0, 0, 0)")

        mode = self.ruler_mode_var.get()
        project = {
            "name": self.project_var.get().strip(),
            "builtin": False,
            "background_color": list(bg_tuple),
            "ruler_mode": mode,
            "detection_method": self.detection_var.get(),
            "ruler_position_locked": True,
            "fixed_ruler_position": self.ruler_position_var.get(),
            "photographer": self.photographer_var.get().strip(),
            "institution": self.institution_var.get().strip(),
            "credit_line": self.credit_text.get("1.0", tk.END).strip(),
            "logo_enabled": bool(self.logo_enabled_var.get()),
            "logo_path": self.logo_path_var.get().strip(),
            "measurements_file": self.measurements_file_var.get().strip(),
        }

        if mode == "single":
            project["ruler_file"] = self.ruler_file_var.get().strip()
            try:
                project["ruler_size_cm"] = float(self.ruler_size_var.get())
            except ValueError:
                raise ValueError("Ruler size must be a number")
        else:
            files = {}
            sizes = {}
            for key, (f_var, s_var) in self.adaptive_vars.items():
                files[key] = f_var.get().strip()
                try:
                    sizes[key] = float(s_var.get() or 0)
                except ValueError:
                    raise ValueError(f"{key} ruler size must be a number")
            project["ruler_files"] = files
            project["ruler_sizes_cm"] = sizes

        return project

    # -- Actions ------------------------------------------------------------
    def _new_project(self):
        name = simpledialog.askstring("New Project", "Project name:",
                                       parent=self.main_frame)
        if not name:
            return
        if project_manager.get_project_by_name(name):
            messagebox.showerror("Name exists", f"A project named '{name}' already exists.")
            return
        project = project_manager.default_new_project(name)
        project_manager.save_user_project(project)
        self.refresh_project_list(select_name=name)

    def _duplicate_project(self):
        source = self._current_project
        if not source:
            return
        name = simpledialog.askstring(
            "Duplicate Project",
            f"New name (copy of '{source['name']}'):",
            initialvalue=f"{source['name']} (copy)",
            parent=self.main_frame)
        if not name:
            return
        if project_manager.get_project_by_name(name):
            messagebox.showerror("Name exists", f"A project named '{name}' already exists.")
            return
        project_manager.duplicate_project(source, name)
        self.refresh_project_list(select_name=name)

    def _save_project(self):
        if not self._current_project:
            return
        try:
            project = self._collect_form()
        except ValueError as e:
            messagebox.showerror("Invalid value", str(e))
            return

        # Built-in projects cannot be saved in place; offer to duplicate
        if self._current_project.get("builtin"):
            if not messagebox.askyesno(
                "Built-in project",
                "Built-in projects can't be edited. Save a copy as a new user project?"):
                return
            self._duplicate_project()
            return

        project_manager.save_user_project(project)
        self._dirty = False
        self.status_label.config(
            text=f"Saved: {project['name']}", foreground="green")
        self.refresh_project_list(select_name=project["name"])

    def _delete_project(self):
        if not self._current_project:
            return
        if self._current_project.get("builtin"):
            messagebox.showinfo("Built-in project", "Built-in projects cannot be deleted.")
            return
        name = self._current_project["name"]
        if not messagebox.askyesno("Delete project", f"Delete project '{name}'?"):
            return
        project_manager.delete_user_project(name)
        self._current_project = None
        self.refresh_project_list()

    # -- Browsers -----------------------------------------------------------
    def _browse_ruler_file(self):
        filename = filedialog.askopenfilename(
            title="Select Ruler File",
            filetypes=[("Ruler images", "*.svg *.png *.tif *.tiff *.jpg"),
                       ("All files", "*.*")])
        if filename:
            self.ruler_file_var.set(filename)

    def _browse_adaptive_ruler(self, key):
        filename = filedialog.askopenfilename(
            title=f"Select {key} Ruler File",
            filetypes=[("Ruler images", "*.svg *.png *.tif *.tiff *.jpg"),
                       ("All files", "*.*")])
        if filename:
            self.adaptive_vars[key][0].set(filename)

    def _browse_logo_file(self):
        filename = filedialog.askopenfilename(
            title="Select Logo File",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff"),
                       ("All files", "*.*")])
        if filename:
            self.logo_path_var.set(filename)

    def _browse_measurements_file(self):
        filename = filedialog.askopenfilename(
            title="Select Measurements File",
            filetypes=[("Measurements", "*.json *.xlsx *.xls"),
                       ("All files", "*.*")])
        if filename:
            self.measurements_file_var.set(filename)

    # -- Background color helpers ------------------------------------------
    def _pick_bg_color(self):
        current = self._parse_bg_color(self.bg_color_var.get(), default=(0, 0, 0))
        result = colorchooser.askcolor(
            color="#%02x%02x%02x" % current, title="Background color")
        if result and result[0]:
            r, g, b = (int(c) for c in result[0])
            self._set_bg_color((r, g, b))

    def _set_bg_color(self, rgb, mark_dirty=True):
        self.bg_color_var.set(f"({rgb[0]}, {rgb[1]}, {rgb[2]})")
        try:
            self.bg_swatch.config(bg="#%02x%02x%02x" % rgb)
        except tk.TclError:
            pass
        if mark_dirty:
            self._mark_dirty()

    @staticmethod
    def _parse_bg_color(text, default=None):
        cleaned = text.strip().strip("()[]")
        parts = [p.strip() for p in cleaned.split(",")]
        if len(parts) != 3:
            if default is not None:
                return default
            raise ValueError("Expected three values")
        try:
            rgb = tuple(max(0, min(255, int(p))) for p in parts)
        except ValueError:
            if default is not None:
                return default
            raise
        return rgb

    # -- State helpers ------------------------------------------------------
    def _on_ruler_mode_changed(self, *args):
        mode = self.ruler_mode_var.get()
        if mode == "single":
            self.single_frame.pack(fill=tk.X, pady=(6, 0))
            self.adaptive_frame.pack_forget()
        else:
            self.single_frame.pack_forget()
            self.adaptive_frame.pack(fill=tk.X, pady=(6, 0))
        self._mark_dirty()

    def _load_ruler_image(self, filename):
        """Load a ruler image, handling SVG→PNG fallback. Returns PIL Image or None."""
        from PIL import Image

        ruler_path = project_manager.resolve_asset_path(filename)
        if not ruler_path or not os.path.exists(ruler_path):
            return None

        ext = os.path.splitext(ruler_path)[1].lower()
        if ext == '.svg':
            png_path = os.path.splitext(ruler_path)[0] + '.png'
            if os.path.exists(png_path):
                return Image.open(png_path)
            return None
        else:
            return Image.open(ruler_path)

    def _update_ruler_preview(self):
        """Show a preview of the selected ruler file(s)."""
        self.ruler_preview_label.config(image='', text='')
        self._ruler_preview_photo = None

        mode = self.ruler_mode_var.get()

        try:
            from PIL import Image, ImageTk, ImageDraw, ImageFont

            if mode == "single":
                ruler_filename = self.ruler_file_var.get().strip()
                if not ruler_filename:
                    return
                img = self._load_ruler_image(ruler_filename)
                if not img:
                    self.ruler_preview_label.config(text=f"(ruler not found: {ruler_filename})", foreground="gray")
                    return

                max_w = 300
                w, h = img.size
                if w > max_w:
                    ratio = max_w / w
                    img = img.resize((max_w, int(h * ratio)), Image.LANCZOS)

                self._ruler_preview_photo = ImageTk.PhotoImage(img)
                self.ruler_preview_label.config(image=self._ruler_preview_photo, text='')

            else:
                # Adaptive: show all rulers stacked vertically with labels
                images = []
                labels = []
                for key in ("1cm", "2cm", "5cm"):
                    f_var, _ = self.adaptive_vars.get(key, (None, None))
                    if f_var and f_var.get().strip():
                        img = self._load_ruler_image(f_var.get().strip())
                        if img:
                            images.append(img)
                            labels.append(key)

                if not images:
                    return

                # Resize all to same width
                max_w = 300
                resized = []
                for img in images:
                    w, h = img.size
                    if w > max_w:
                        ratio = max_w / w
                        img = img.resize((max_w, int(h * ratio)), Image.LANCZOS)
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    resized.append(img)

                # Stack vertically with labels
                label_height = 18
                gap = 4
                total_h = sum(r.height + label_height + gap for r in resized)
                canvas_w = max(r.width for r in resized)
                composite = Image.new('RGBA', (canvas_w, total_h), (240, 240, 240, 255))

                draw = ImageDraw.Draw(composite)
                y = 0
                for i, (img, label) in enumerate(zip(resized, labels)):
                    draw.text((4, y + 2), label, fill=(80, 80, 80, 255))
                    y += label_height
                    composite.paste(img, (0, y), img if img.mode == 'RGBA' else None)
                    y += img.height + gap

                self._ruler_preview_photo = ImageTk.PhotoImage(composite)
                self.ruler_preview_label.config(image=self._ruler_preview_photo, text='')

        except Exception as e:
            self.ruler_preview_label.config(text=f"(preview error: {e})", foreground="gray")

    def _on_ruler_pos_click(self, event):
        """Handle click on the ruler position canvas using the original handler."""
        from gui_events import EventHandlers
        museum_var = tk.StringVar(value=self._current_project.get("name", "") if self._current_project else "")
        EventHandlers.handle_ruler_canvas_click(
            event, self._ruler_pos_params, self.ruler_position_var,
            museum_var, self._draw_ruler_position
        )
        self._mark_dirty()

    def _draw_ruler_position(self):
        """Draw the ruler position indicator using the original detailed drawing."""
        from gui_layout import LayoutManager
        pos = self.ruler_position_var.get()
        museum = self._current_project.get("name", "") if self._current_project else ""
        LayoutManager.draw_ruler_selector(
            self.ruler_pos_canvas, pos, museum, self._ruler_pos_params
        )

    def _on_credit_modified(self, event=None):
        if self.credit_text.edit_modified():
            self.credit_text.edit_modified(False)
            self._mark_dirty()

    def _mark_dirty(self):
        if self._suppress_dirty:
            return
        self._dirty = True
        if self._current_project and not self._current_project.get("builtin"):
            self.status_label.config(text="Unsaved changes", foreground="#b45309")
