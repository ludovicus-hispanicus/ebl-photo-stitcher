import os
import sys
import re
import tkinter as tk
from tkinter import ttk

APP_NAME_FOR_CONFIG = "eBLImageProcessor"

# Pattern to detect subfolder processing lines
_SUBFOLDER_PATTERN = re.compile(r'^Processing Subfolder \d+/\d+: .+')
_ERROR_PATTERN = re.compile(r'ERROR|Error processing')
_SUCCESS_PATTERN = re.compile(r'Finished processing and stitching for tablet:')


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(sys.argv[0]))
    return os.path.join(base_path, relative_path)


def get_persistent_config_dir_path():
    home_dir = os.path.expanduser("~")
    if sys.platform == "win32":
        app_data_env = os.getenv("APPDATA", os.path.join(
            home_dir, "AppData", "Roaming"))
    elif sys.platform == "darwin":
        app_data_env = os.path.join(home_dir, "Library", "Application Support")
    else:
        app_data_env = os.getenv("XDG_CONFIG_HOME", os.path.join(home_dir, ".config"))

    config_directory = os.path.join(app_data_env, APP_NAME_FOR_CONFIG)

    if not os.path.exists(config_directory):
        try:
            os.makedirs(config_directory, exist_ok=True)
        except OSError:
            print(f"Warning: Could not create config directory {config_directory}.")
            if getattr(sys, 'frozen', False):
                return os.path.dirname(sys.executable)
            return os.path.abspath(os.path.dirname(sys.argv[0]))
    return config_directory


class TextRedirector:
    """Redirects stdout to a tk.Text widget with visual markers for subfolders."""

    def __init__(self, text_widget, log_panel=None, tag_name="stdout"):
        self.widget = text_widget
        self.tag = tag_name
        self.log_panel = log_panel
        self._line_buffer = ""

        # Configure text tags for visual markers
        self.widget.tag_configure("subfolder_marker",
                                  background="#2563eb",
                                  foreground="white",
                                  font=("Consolas", 10, "bold"),
                                  spacing1=12,
                                  spacing3=4,
                                  lmargin1=4,
                                  lmargin2=4,
                                  rmargin=4)
        self.widget.tag_configure("error_line",
                                  foreground="#dc2626",
                                  font=("Consolas", 9, "bold"))
        self.widget.tag_configure("success_line",
                                  foreground="#16a34a",
                                  font=("Consolas", 9, "bold"))
        self.widget.tag_configure("search_highlight",
                                  background="#facc15",
                                  foreground="black")
        self.widget.tag_configure("search_current",
                                  background="#f97316",
                                  foreground="white")

    def write(self, string_to_write):
        self.widget.configure(state=tk.NORMAL)

        # Buffer partial lines (no newline yet)
        self._line_buffer += string_to_write

        # Process complete lines
        while "\n" in self._line_buffer:
            line, self._line_buffer = self._line_buffer.split("\n", 1)
            full_line = line + "\n"
            self._insert_tagged_line(full_line)

        # If buffer has content but no newline, insert it (e.g. progress updates)
        if self._line_buffer and "\n" not in string_to_write:
            # Flush partial line for immediate display
            self._insert_tagged_line(self._line_buffer)
            self._line_buffer = ""

        self.widget.see(tk.END)
        self.widget.configure(state=tk.DISABLED)
        self.widget.update_idletasks()

    def _insert_tagged_line(self, line):
        stripped = line.strip()
        if _SUBFOLDER_PATTERN.match(stripped):
            # Insert a visual separator before the marker
            self.widget.insert(tk.END, "\n", (self.tag,))
            # Add a bookmark mark for navigation
            mark_name = f"subfolder_{self.widget.index(tk.END).split('.')[0]}"
            self.widget.mark_set(mark_name, tk.END)
            self.widget.mark_gravity(mark_name, tk.LEFT)
            self.widget.insert(tk.END, line, ("subfolder_marker",))
            # Notify log panel of new subfolder
            if self.log_panel:
                self.log_panel._on_subfolder_detected(stripped, mark_name)
        elif _ERROR_PATTERN.search(stripped):
            self.widget.insert(tk.END, line, ("error_line",))
        elif _SUCCESS_PATTERN.search(stripped):
            self.widget.insert(tk.END, line, ("success_line",))
        else:
            self.widget.insert(tk.END, line, (self.tag,))

    def flush(self):
        pass


class LogPanel(ttk.Frame):
    """Right-side log panel with search and subfolder navigation."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._subfolder_marks = []  # list of (display_text, mark_name)
        self._search_matches = []
        self._current_match_idx = -1

        self._create_widgets()

    def _create_widgets(self):
        # --- Header with title ---
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=4, pady=(4, 0))

        ttk.Label(header, text="Processing Log",
                  font=("Helvetica", 11, "bold")).pack(side=tk.LEFT)

        # --- Subfolder navigation dropdown ---
        nav_frame = ttk.Frame(self)
        nav_frame.pack(fill=tk.X, padx=4, pady=(4, 0))

        ttk.Label(nav_frame, text="Go to:",
                  font=("Helvetica", 9)).pack(side=tk.LEFT, padx=(0, 4))

        self._nav_var = tk.StringVar(value="")
        self._nav_combo = ttk.Combobox(nav_frame, textvariable=self._nav_var,
                                        state="readonly", width=30,
                                        font=("Consolas", 9))
        self._nav_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._nav_combo.bind("<<ComboboxSelected>>", self._on_nav_selected)

        # --- Search bar ---
        search_frame = ttk.Frame(self)
        search_frame.pack(fill=tk.X, padx=4, pady=(4, 2))

        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", self._on_search_changed)

        self._search_entry = ttk.Entry(search_frame,
                                        textvariable=self._search_var,
                                        font=("Consolas", 9))
        self._search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        self._search_entry.bind("<Return>", lambda e: self._search_next())
        self._search_entry.bind("<Shift-Return>", lambda e: self._search_prev())

        self._match_label = ttk.Label(search_frame, text="",
                                       font=("Helvetica", 8), width=10)
        self._match_label.pack(side=tk.LEFT, padx=(0, 2))

        btn_prev = ttk.Button(search_frame, text="\u25B2", width=3,
                              command=self._search_prev, style="Small.TButton")
        btn_prev.pack(side=tk.LEFT, padx=1)

        btn_next = ttk.Button(search_frame, text="\u25BC", width=3,
                              command=self._search_next, style="Small.TButton")
        btn_next.pack(side=tk.LEFT, padx=1)

        btn_clear = ttk.Button(search_frame, text="X", width=3,
                               command=self._clear_search, style="Small.TButton")
        btn_clear.pack(side=tk.LEFT, padx=1)

        # --- Log text area ---
        text_frame = ttk.Frame(self)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=(2, 4))

        self.log_text = tk.Text(text_frame, wrap=tk.WORD, state=tk.DISABLED,
                                bg="#1e1e1e", fg="#d4d4d4",
                                font=("Consolas", 9),
                                insertbackground="white",
                                selectbackground="#264f78",
                                selectforeground="white",
                                relief=tk.FLAT, borderwidth=2,
                                padx=8, pady=8)

        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL,
                                   command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind Ctrl+F to focus search
        self.winfo_toplevel().bind("<Control-f>", self._focus_search)

    def get_text_widget(self):
        return self.log_text

    def _on_subfolder_detected(self, display_text, mark_name):
        """Called by TextRedirector when a subfolder marker is inserted."""
        self._subfolder_marks.append((display_text, mark_name))
        values = [item[0] for item in self._subfolder_marks]
        self._nav_combo["values"] = values
        # Auto-select the latest subfolder
        self._nav_var.set(display_text)

    def _on_nav_selected(self, event=None):
        """Jump to the selected subfolder in the log."""
        selected = self._nav_var.get()
        for display_text, mark_name in self._subfolder_marks:
            if display_text == selected:
                try:
                    self.log_text.see(mark_name)
                    # Briefly highlight the line
                    line_start = self.log_text.index(mark_name)
                    line_end = f"{line_start} lineend"
                    self.log_text.tag_add("search_current", line_start, line_end)
                    self.log_text.after(1500, lambda: self.log_text.tag_remove(
                        "search_current", "1.0", tk.END))
                except tk.TclError:
                    pass
                break

    def _focus_search(self, event=None):
        """Focus the search entry."""
        self._search_entry.focus_set()
        self._search_entry.select_range(0, tk.END)
        return "break"

    def _on_search_changed(self, *args):
        """Live search as the user types."""
        self._perform_search()

    def _perform_search(self):
        """Find all matches and highlight them."""
        self.log_text.tag_remove("search_highlight", "1.0", tk.END)
        self.log_text.tag_remove("search_current", "1.0", tk.END)
        self._search_matches = []
        self._current_match_idx = -1

        query = self._search_var.get().strip()
        if not query:
            self._match_label.config(text="")
            return

        start = "1.0"
        while True:
            pos = self.log_text.search(query, start, stopindex=tk.END, nocase=True)
            if not pos:
                break
            end = f"{pos}+{len(query)}c"
            self.log_text.tag_add("search_highlight", pos, end)
            self._search_matches.append(pos)
            start = end

        count = len(self._search_matches)
        if count > 0:
            self._current_match_idx = 0
            self._highlight_current_match()
            self._match_label.config(text=f"1/{count}")
        else:
            self._match_label.config(text="0/0")

    def _highlight_current_match(self):
        """Highlight the current match distinctly and scroll to it."""
        self.log_text.tag_remove("search_current", "1.0", tk.END)
        if 0 <= self._current_match_idx < len(self._search_matches):
            pos = self._search_matches[self._current_match_idx]
            query = self._search_var.get().strip()
            end = f"{pos}+{len(query)}c"
            self.log_text.tag_add("search_current", pos, end)
            self.log_text.see(pos)

    def _search_next(self):
        """Move to the next search match."""
        if not self._search_matches:
            return
        self._current_match_idx = (self._current_match_idx + 1) % len(self._search_matches)
        self._highlight_current_match()
        self._match_label.config(
            text=f"{self._current_match_idx + 1}/{len(self._search_matches)}")

    def _search_prev(self):
        """Move to the previous search match."""
        if not self._search_matches:
            return
        self._current_match_idx = (self._current_match_idx - 1) % len(self._search_matches)
        self._highlight_current_match()
        self._match_label.config(
            text=f"{self._current_match_idx + 1}/{len(self._search_matches)}")

    def _clear_search(self):
        """Clear the search."""
        self._search_var.set("")
        self.log_text.tag_remove("search_highlight", "1.0", tk.END)
        self.log_text.tag_remove("search_current", "1.0", tk.END)
        self._search_matches = []
        self._current_match_idx = -1
        self._match_label.config(text="")

    def clear_log(self):
        """Clear all log content and subfolder bookmarks."""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)
        self._subfolder_marks = []
        self._nav_combo["values"] = []
        self._nav_var.set("")
        self._clear_search()
