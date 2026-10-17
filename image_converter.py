import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk

# Register AVIF support through pillow-avif-plugin.
try:
    import pillow_avif  # noqa: F401
except ImportError:
    pass

# Register HEIC/HEIF support through pillow-heif.
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except (ImportError, OSError):
    pass

try:
    import resvg_py
except (ImportError, OSError):
    resvg_py = None
from pathlib import Path
import os
import json
import sys
import subprocess
import importlib

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

SUPPORTED = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".gif", ".avif", ".svg", ".heic", ".heif", ".ico"}

class ImageConverter:
    SETTINGS_FILE = Path.home() / ".image_converter_settings.json"

    def __init__(self, root):
        self.root = root
        self.root.title("Image Converter v4.5 – Modern Dark")
        # Use a more flexible default/minimum size for Linux desktop displays.
        self.root.geometry("1000x700")
        self.root.minsize(700, 500)
        self.files = []
        self.preview_photo = None
        self.last_output_dir = self.load_settings()
        self.build_ui()
        self.apply_theme()

    def apply_theme(self):
        """Apply a polished dark slate theme with teal accents."""
        self.colors = {
            "bg": "#111827",
            "panel": "#1F2937",
            "panel_alt": "#273449",
            "border": "#374151",
            "text": "#F3F4F6",
            "muted": "#9CA3AF",
            "accent": "#14B8A6",
            "accent_active": "#0D9488",
            "input": "#0B1220",
            "selection": "#0F766E",
            "danger": "#F87171",
        }
        c = self.colors
        self.root.configure(bg=c["bg"])

        # Native ttk controls get a matching dark style.
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TCombobox", fieldbackground=c["input"], background=c["panel_alt"],
                        foreground=c["text"], arrowcolor=c["text"], bordercolor=c["border"],
                        lightcolor=c["border"], darkcolor=c["border"], padding=4)
        style.map("TCombobox", fieldbackground=[("readonly", c["input"])],
                  foreground=[("readonly", c["text"])],
                  selectbackground=[("readonly", c["selection"])],
                  selectforeground=[("readonly", c["text"])])
        style.configure("Horizontal.TProgressbar", troughcolor=c["input"],
                        background=c["accent"], bordercolor=c["border"],
                        lightcolor=c["accent"], darkcolor=c["accent"])

        def paint(widget):
            kind = widget.winfo_class()
            parent = widget.master
            parent_kind = parent.winfo_class() if parent else ""
            try:
                panel_bg = parent.cget("bg") if parent is not None else c["bg"]
            except tk.TclError:
                panel_bg = c["bg"]
            try:
                if kind == "Frame":
                    widget.configure(bg=panel_bg, highlightthickness=0)
                elif kind == "Labelframe":
                    widget.configure(bg=c["panel"], fg=c["text"],
                                     highlightbackground=c["border"], bd=1, relief="solid")
                elif kind == "Label":
                    widget.configure(bg=panel_bg, fg=c["text"])
                elif kind == "Listbox":
                    widget.configure(bg=c["input"], fg=c["text"],
                                     selectbackground=c["selection"], selectforeground="white",
                                     highlightbackground=c["border"], highlightcolor=c["accent"],
                                     relief="flat", bd=1, activestyle="none")
                elif kind == "Canvas":
                    widget.configure(bg=c["input"], highlightbackground=c["border"],
                                     highlightcolor=c["accent"], relief="flat", bd=1)
                elif kind == "Button":
                    is_primary = widget.cget("text").strip().upper() == "KONVERTER"
                    bg = c["accent"] if is_primary else c["panel_alt"]
                    fg = "#062A27" if is_primary else c["text"]
                    widget.configure(bg=bg, fg=fg, activebackground=c["accent_active"],
                                     activeforeground="white", relief="flat", bd=0,
                                     cursor="hand2", highlightthickness=0)
                    if is_primary:
                        widget.configure(pady=11)
                elif kind == "Entry":
                    widget.configure(bg=c["input"], fg=c["text"], insertbackground=c["text"],
                                     disabledbackground=c["panel_alt"], disabledforeground=c["muted"],
                                     relief="flat", bd=1, highlightthickness=1,
                                     highlightbackground=c["border"], highlightcolor=c["accent"])
                elif kind == "Checkbutton":
                    widget.configure(bg=c["panel"], fg=c["text"],
                                     activebackground=c["panel"], activeforeground=c["accent"],
                                     selectcolor=c["input"], disabledforeground=c["muted"])
                elif kind == "Scale":
                    widget.configure(bg=c["panel"], fg=c["text"], troughcolor=c["input"],
                                     activebackground=c["accent"], highlightthickness=0, bd=0)
            except tk.TclError:
                pass
            for child in widget.winfo_children():
                paint(child)

        for child in self.root.winfo_children():
            paint(child)

        # Give the drag-and-drop area a subtle accent treatment.
        self.drop_area.configure(bg="#12343A", fg="#99F6E4",
                                 activebackground="#164E55",
                                 highlightbackground=c["accent"], highlightthickness=1,
                                 relief="flat", bd=0)
        self.info_frame.configure(bg=c["panel"])
        self.info_label.configure(bg=c["panel"], fg=c["muted"])
        self.status_label.configure(bg=c["bg"], fg=c["accent"])
        self.output_label.configure(bg=c["bg"], fg=c["muted"])

    def build_ui(self):
        tk.Label(self.root, text="Image Converter", font=("Segoe UI", 24, "bold")).pack(pady=(18, 2))
        tk.Label(
            self.root,
            text="Convert images locally on your PC — no uploads to the internet.",
            font=("Segoe UI", 10)
        ).pack(pady=(0, 12))

        main = tk.Frame(self.root)
        main.pack(fill="both", expand=True, padx=22)

        left = tk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        drop_text = (
            "Drop images here\n\nor\n\nClick “Add Images”"
            if DND_AVAILABLE else
            "Add images using the button below"
        )
        self.drop_area = tk.Label(
            left, text=drop_text, font=("Segoe UI", 12),
            relief="groove", bd=2, padx=20, pady=35
        )
        self.drop_area.pack(fill="x", pady=(0, 10))

        if DND_AVAILABLE:
            self.drop_area.drop_target_register(DND_FILES)
            self.drop_area.dnd_bind("<<Drop>>", self.drop_files)

        self.file_list = tk.Listbox(left, selectmode=tk.EXTENDED, font=("Segoe UI", 10))
        self.file_list.pack(fill="both", expand=True)
        self.file_list.bind("<<ListboxSelect>>", self.preview_selected)

        buttons = tk.Frame(left)
        buttons.pack(fill="x", pady=10)
        tk.Button(buttons, text="Add Images", command=self.choose_files,
                  font=("Segoe UI", 10), padx=15, pady=7).pack(side="left")
        tk.Button(buttons, text="Remove Selected", command=self.remove_selected,
                  font=("Segoe UI", 10), padx=15, pady=7).pack(side="left", padx=8)
        tk.Button(buttons, text="Clear List", command=self.clear_files,
                  font=("Segoe UI", 10), padx=15, pady=7).pack(side="left")

        # Scrollable right-hand panel: keeps all controls reachable on short
        # screens, including when the window is maximized on Linux Mint.
        right_shell = tk.Frame(main, width=330)
        right_shell.pack(side="right", fill="y", padx=(10, 0))
        right_shell.pack_propagate(False)

        right_canvas = tk.Canvas(
            right_shell, width=310, highlightthickness=0, bd=0,
            background="#111827"
        )
        right_scrollbar = ttk.Scrollbar(
            right_shell, orient="vertical", command=right_canvas.yview
        )
        right_canvas.configure(yscrollcommand=right_scrollbar.set)
        right_scrollbar.pack(side="right", fill="y")
        right_canvas.pack(side="left", fill="both", expand=True)

        right = tk.Frame(right_canvas, width=310)
        right_window = right_canvas.create_window(
            (0, 0), window=right, anchor="nw", width=310
        )
        right.grid_columnconfigure(0, weight=1)

        def update_scroll_region(_event=None):
            right_canvas.configure(scrollregion=right_canvas.bbox("all"))

        def fit_scrollable_width(event):
            right_canvas.itemconfigure(right_window, width=event.width)

        right.bind("<Configure>", update_scroll_region)
        right_canvas.bind("<Configure>", fit_scrollable_width)

        # Support mouse-wheel scrolling on Windows, macOS and Linux Mint.
        # The wheel only scrolls this panel when the pointer is over it.
        def scroll_right_panel(event):
            widget = event.widget
            in_right_panel = False
            while widget is not None:
                if widget == right_shell:
                    in_right_panel = True
                    break
                widget = getattr(widget, "master", None)
            if not in_right_panel:
                return

            if getattr(event, "num", None) == 4:
                right_canvas.yview_scroll(-3, "units")
            elif getattr(event, "num", None) == 5:
                right_canvas.yview_scroll(3, "units")
            elif getattr(event, "delta", 0):
                direction = -1 if event.delta > 0 else 1
                right_canvas.yview_scroll(direction * 3, "units")

        right_canvas.bind_all("<MouseWheel>", scroll_right_panel, add="+")
        right_canvas.bind_all("<Button-4>", scroll_right_panel, add="+")
        right_canvas.bind_all("<Button-5>", scroll_right_panel, add="+")

        tk.Label(
            right, text="Preview",
            font=("Segoe UI", 12, "bold")
        ).grid(row=0, column=0, sticky="ew", pady=(0, 5))

        self.preview = tk.Canvas(
            right, width=285, height=220,
            bg="white", relief="sunken", bd=1,
            highlightthickness=0
        )
        self.preview.grid(row=1, column=0, sticky="ew", pady=(0, 4))
        self.preview.create_text(
            142, 110, text="No image selected",
            font=("Segoe UI", 10), fill="gray"
        )

        # Fixed-height info area. This reserves the same space before and
        # after an image is selected, so controls below never move.
        self.info_frame = tk.Frame(right, height=72)
        self.info_frame.grid(row=2, column=0, sticky="ew", pady=(0, 4))
        self.info_frame.grid_propagate(False)

        self.info_label = tk.Label(
            self.info_frame, text="", font=("Segoe UI", 9),
            justify="left", anchor="nw"
        )
        self.info_label.pack(fill="both", expand=True)

        # Dedicated rows: these never disappear when a file is selected.
        self.progress = ttk.Progressbar(
            right, orient="horizontal", mode="determinate", length=285
        )
        self.progress.grid(row=3, column=0, sticky="ew", pady=(0, 1))

        # Keep status text inside a fixed-height area. Long filenames and
        # conversion results wrap instead of changing the right panel width.
        self.status_frame = tk.Frame(right, height=34)
        self.status_frame.grid(row=4, column=0, sticky="ew", pady=(0, 5))
        self.status_frame.grid_propagate(False)
        self.status_label = tk.Label(
            self.status_frame, text="Ready — add or drop images",
            font=("Segoe UI", 8), anchor="nw", justify="left",
            wraplength=285
        )
        self.status_label.pack(fill="both", expand=True)

        options = tk.LabelFrame(
            right, text="Conversion",
            font=("Segoe UI", 10, "bold")
        )
        options.grid(row=5, column=0, sticky="ew", pady=(0, 4))

        row = tk.Frame(options)
        row.pack(fill="x", padx=10, pady=(7, 3))
        tk.Label(row, text="Format:").pack(side="left")
        self.format_var = tk.StringVar(value="PNG")
        self.format_menu = ttk.Combobox(
            row, textvariable=self.format_var,
            values=["PNG", "JPG", "WEBP", "BMP", "TIFF", "HEIC", "HEIF", "ICO"],
            state="readonly", width=9
        )
        self.format_menu.pack(side="right")
        self.format_menu.bind("<<ComboboxSelected>>", self.update_quality_state)

        row2 = tk.Frame(options)
        row2.pack(fill="x", padx=10, pady=(2, 5))
        self.quality_label = tk.Label(row2, text="Quality (JPG/WebP):", width=25, anchor="w")
        self.quality_label.pack(side="left")
        self.quality_var = tk.StringVar(value="High")
        self.quality_menu = ttk.Combobox(
            row2, textvariable=self.quality_var,
            values=["Low", "Medium", "High"],
            state="readonly", width=9
        )
        self.quality_menu.pack(side="right")
        self.update_quality_state()

        resize = tk.LabelFrame(
            right, text="Resize",
            font=("Segoe UI", 10, "bold")
        )
        resize.grid(row=6, column=0, sticky="ew", pady=(0, 4))

        self.resize_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            resize, text="Enable resizing",
            variable=self.resize_var, command=self.toggle_resize
        ).pack(anchor="w", padx=10, pady=2)

        mode_row = tk.Frame(resize)
        mode_row.pack(fill="x", padx=10, pady=1)
        tk.Label(mode_row, text="Mode:").pack(side="left")

        self.resize_mode = tk.StringVar(value="Pixels")
        mode_menu = ttk.Combobox(
            mode_row, textvariable=self.resize_mode,
            values=["Pixels", "Centimeters", "Percent"],
            state="disabled", width=9
        )
        mode_menu.pack(side="right")
        mode_menu.bind("<<ComboboxSelected>>", self.resize_mode_changed)
        self.resize_mode_menu = mode_menu

        size_row = tk.Frame(resize)
        size_row.pack(pady=2)
        tk.Label(size_row, text="Width:").grid(row=0, column=0, padx=3)
        self.width_entry = tk.Entry(size_row, width=7, state="disabled")
        self.width_entry.grid(row=0, column=1, padx=3)
        tk.Label(size_row, text="Height:").grid(row=0, column=2, padx=3)
        self.height_entry = tk.Entry(size_row, width=7, state="disabled")
        self.height_entry.grid(row=0, column=3, padx=3)

        self.dpi_row = tk.Frame(resize)
        self.dpi_row.pack(fill="x", padx=10, pady=(1, 2))
        tk.Label(self.dpi_row, text="Print resolution (DPI):").pack(side="left")
        self.dpi_var = tk.StringVar(value="300")
        self.dpi_entry = tk.Entry(self.dpi_row, width=7, textvariable=self.dpi_var, state="disabled")
        self.dpi_entry.pack(side="right")
        self.dpi_row.pack_forget()

        self.keep_ratio = tk.BooleanVar(value=True)
        self.keep_ratio_button = tk.Checkbutton(
            resize, text="Keep aspect ratio",
            variable=self.keep_ratio, state="disabled"
        )
        self.keep_ratio_button.pack(anchor="w", padx=10, pady=(0, 3))

        transform = tk.LabelFrame(
            right, text="Image Adjustments",
            font=("Segoe UI", 10, "bold")
        )
        transform.grid(row=7, column=0, sticky="ew", pady=(0, 4))

        transform_row = tk.Frame(transform)
        transform_row.pack(fill="x", padx=8, pady=5)

        tk.Label(transform_row, text="Rotation:").pack(side="left")
        self.rotation_var = tk.StringVar(value="0°")
        ttk.Combobox(
            transform_row,
            textvariable=self.rotation_var,
            values=["0°", "90°", "180°", "270°"],
            state="readonly", width=7
        ).pack(side="left", padx=(5, 12))

        self.flip_var = tk.StringVar(value="None")
        tk.Label(transform_row, text="Flip:").pack(side="left")
        ttk.Combobox(
            transform_row,
            textvariable=self.flip_var,
            values=["None", "Horizontal", "Vertical"],
            state="readonly", width=12
        ).pack(side="left", padx=5)

        # The main action gets its own permanent row.
        tk.Button(
            right, text="CONVERT", command=self.convert,
            font=("Segoe UI", 12, "bold"), padx=20, pady=9
        ).grid(row=8, column=0, sticky="ew", pady=(4, 0))

        # Long output paths must not widen the canvas-embedded settings panel.
        self.output_frame = tk.Frame(right, height=34)
        self.output_frame.grid(row=9, column=0, sticky="ew", pady=(3, 0))
        self.output_frame.grid_propagate(False)
        self.output_label = tk.Label(
            self.output_frame, text=self.output_display_text(),
            font=("Segoe UI", 8), anchor="nw", justify="left",
            wraplength=285
        )
        self.output_label.pack(fill="both", expand=True)

        tk.Button(
            right, text="Choose Output Folder",
            command=self.choose_output_dir,
            font=("Segoe UI", 8), padx=8, pady=3
        ).grid(row=10, column=0, sticky="ew", pady=(2, 0))

        if not DND_AVAILABLE:
            tk.Label(
                right, text="Install tkinterdnd2 for drag and drop support.",
                font=("Segoe UI", 8)
            ).pack(pady=5)

    def load_settings(self):
        try:
            if self.SETTINGS_FILE.exists():
                data = json.loads(self.SETTINGS_FILE.read_text(encoding="utf-8"))
                return data.get("output_dir", "")
        except Exception:
            pass
        return ""

    def save_settings(self):
        try:
            self.SETTINGS_FILE.write_text(
                json.dumps({"output_dir": self.last_output_dir}, indent=2),
                encoding="utf-8"
            )
        except Exception:
            pass

    def output_display_text(self):
        if self.last_output_dir:
            return f"Output: {self.last_output_dir}"
        return "Output: choose a folder when converting"

    def choose_output_dir(self):
        directory = filedialog.askdirectory(
            title="Choose default output folder",
            initialdir=self.last_output_dir if self.last_output_dir else None
        )
        if directory:
            self.last_output_dir = directory
            self.save_settings()
            self.output_label.configure(text=self.output_display_text())

    def choose_files(self):
        files = filedialog.askopenfilenames(
            title="Add Images",
            filetypes=[
                ("Images", "*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff *.gif *.avif *.svg"),
                ("Alle filer", "*.*")
            ]
        )
        self.add_files(files)

    def drop_files(self, event):
        self.add_files(self.root.tk.splitlist(event.data))

    def add_files(self, files):
        added = 0
        for f in files:
            path = Path(f)
            if path.is_file() and path.suffix.lower() in SUPPORTED and str(path) not in self.files:
                self.files.append(str(path))
                self.file_list.insert(tk.END, str(path))
                added += 1
        if added and self.file_list.size() == added:
            self.file_list.selection_set(0)
            self.preview_selected()

    def remove_selected(self):
        selected = list(self.file_list.curselection())
        for index in reversed(selected):
            self.file_list.delete(index)
            del self.files[index]
        self.clear_preview()
        self.progress["value"] = 0
        self.progress["maximum"] = max(1, len(self.files))
        self.status_label.configure(
            text=f"Ready — {len(self.files)} image(s) queued" if self.files else "Ready — add or drop images"
        )

    def clear_files(self):
        self.files.clear()
        self.file_list.delete(0, tk.END)
        self.clear_preview()
        self.progress["value"] = 0
        self.progress["maximum"] = 1
        self.status_label.configure(text="Ready — add or drop images")

    def clear_preview(self):
        self.preview.delete("all")
        self.preview.create_text(
            142, 110, text="No image selected",
            font=("Segoe UI", 10), fill="gray"
        )
        self.info_label.configure(text="")
        self.preview_photo = None

    def install_svg_support(self):
        """Install the self-contained resvg_py SVG renderer into this Python environment."""
        global resvg_py
        if not messagebox.askyesno(
            "Install SVG Support",
            "SVG support is missing. Would you like to install it automatically now?\n\n"
            "Dette krever internettilgang og kan ta litt tid."
        ):
            return False

        self.status_label.configure(text="Installing SVG support…")
        self.info_label.configure(text="Installing SVG support. Please wait…")
        self.root.update_idletasks()
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "resvg_py"],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode != 0:
                details = (result.stderr or result.stdout or "Ukjent feil").strip()
                messagebox.showerror(
                    "Installasjonen mislyktes",
                    "Could not install SVG support automatically.\n\n"
                    "Try this in PowerShell: python -m pip install resvg_py\n\n"
                    + details[-1800:]
                )
                self.status_label.configure(text="SVG support could not be installed")
                self.info_label.configure(text="SVG support is missing.")
                return False

            importlib.invalidate_caches()
            resvg_py = importlib.import_module("resvg_py")
            self.status_label.configure(text="SVG support installed")
            return True
        except Exception as e:
            messagebox.showerror(
                "Could not load SVG support",
                "SVG support was installed, but the renderer could not be loaded.\n\n"
                f"Detaljer: {e}"
            )
            self.status_label.configure(text="SVG support could not be loaded")
            self.info_label.configure(text="SVG support is missing or could not be loaded.")
            return False

    def preview_selected(self, event=None):
        selection = self.file_list.curselection()
        if not selection:
            return
        path = self.files[selection[0]]
        try:
            if Path(path).suffix.lower() == ".svg":
                if resvg_py is None:
                    if self.install_svg_support():
                        return self.preview_selected(event)
                    return
                import io
                svg_png = resvg_py.svg_to_bytes(svg_path=path)
                image = Image.open(io.BytesIO(svg_png))
            else:
                image = Image.open(path)
            original_size = image.size
            file_size = os.path.getsize(path)
            # Scale the image to fit inside the preview area.
            image.thumbnail((275, 210), Image.Resampling.LANCZOS)
            self.preview_photo = ImageTk.PhotoImage(image)

            self.preview.delete("all")
            self.preview.create_image(
                142, 110,
                image=self.preview_photo,
                anchor="center"
            )

            self.info_label.configure(
                text=(
                    f"File: {Path(path).name}\n"
                    f"Format: {Path(path).suffix.upper().replace('.', '')}\n"
                    f"Resolution: {original_size[0]} × {original_size[1]} px\n"
                    f"File size: {self.format_size(file_size)}"
                )
            )
            self.progress["value"] = 0
            self.progress["maximum"] = max(1, len(self.files))
            self.status_label.configure(
                text=f"Ready — {len(self.files)} image(s) queued"
            )
        except Exception as e:
            self.preview.delete("all")
            self.preview.create_text(
                142, 110, text="Could not display image",
                font=("Segoe UI", 10), fill="red"
            )
            if Path(path).suffix.lower() == ".avif":
                self.info_label.configure(
                    text="Could not open AVIF. Install support with: pip install pillow-avif-plugin"
                )
            elif Path(path).suffix.lower() == ".svg":
                self.info_label.configure(
                    text=f"Could not open SVG: {e}"
                )
            else:
                self.info_label.configure(text=str(e))

    def update_quality_state(self, event=None):
        """Enable the quality selector only for formats that use it."""
        uses_quality = self.format_var.get().upper() in ("JPG", "WEBP", "HEIC", "HEIF")
        self.quality_menu.configure(state="readonly" if uses_quality else "disabled")
        self.quality_label.configure(
            text="Quality (JPG/WebP/HEIC/HEIF):" if uses_quality else "Quality (not used):"
        )

    def toggle_resize(self):
        state = "normal" if self.resize_var.get() else "disabled"
        self.width_entry.configure(state=state)
        self.height_entry.configure(state=state)
        self.resize_mode_menu.configure(state="readonly" if self.resize_var.get() else "disabled")
        self.keep_ratio_button.configure(state=state)
        if self.resize_var.get() and self.resize_mode.get() == "Centimeters":
            self.dpi_row.pack(fill="x", padx=10, pady=(1, 2), before=self.keep_ratio_button)
            self.dpi_entry.configure(state="normal")
        else:
            self.dpi_row.pack_forget()
            self.dpi_entry.configure(state="disabled")

    def resize_mode_changed(self, event=None):
        self.width_entry.delete(0, tk.END)
        self.height_entry.delete(0, tk.END)
        mode = self.resize_mode.get()
        if mode == "Percent":
            self.width_entry.insert(0, "50")
            self.height_entry.insert(0, "50")
        elif mode == "Centimeters":
            self.width_entry.insert(0, "10")
            self.height_entry.insert(0, "15")
        else:
            self.width_entry.insert(0, "1920")
            self.height_entry.insert(0, "1080")
        self.toggle_resize()

    def convert(self):
        if not self.files:
            messagebox.showwarning("None bilder", "Please add or drop at least one image first.")
            return

        if self.last_output_dir and Path(self.last_output_dir).is_dir():
            output_dir = self.last_output_dir
        else:
            output_dir = filedialog.askdirectory(title="Choose folder for converted images")
            if not output_dir:
                return
            self.last_output_dir = output_dir
            self.save_settings()
            self.output_label.configure(text=self.output_display_text())

        output_format = self.format_var.get().lower()
        resize_enabled = self.resize_var.get()

        try:
            width_value = float(self.width_entry.get()) if resize_enabled else None
            height_value = float(self.height_entry.get()) if resize_enabled else None
            if resize_enabled and (width_value <= 0 or height_value <= 0):
                raise ValueError
            if resize_enabled and self.resize_mode.get() == "Percent":
                if width_value > 100 or height_value > 100:
                    raise ValueError
            dpi_value = float(self.dpi_var.get()) if resize_enabled and self.resize_mode.get() == "Centimeters" else None
            if dpi_value is not None and not (1 <= dpi_value <= 2400):
                raise ValueError
        except (ValueError, TypeError):
            messagebox.showerror(
                "Invalid Size",
                "Enter valid dimensions. Percentages must be 1–100 and DPI must be 1–2400."
            )
            return

        converted, errors = 0, []
        self.progress["maximum"] = len(self.files)
        self.progress["value"] = 0
        self.status_label.configure(text="Starting...")
        self.root.update_idletasks()

        for index, source in enumerate(self.files, start=1):
            try:
                source_path = Path(source)
                if source_path.suffix.lower() == ".svg":
                    if resvg_py is None:
                        if self.install_svg_support():
                            pass
                        else:
                            raise RuntimeError("SVG support is missing. Install resvg_py to convert SVG files.")
                    import io
                    svg_png = resvg_py.svg_to_bytes(svg_path=source)
                    image = Image.open(io.BytesIO(svg_png))
                else:
                    image = Image.open(source)

                if resize_enabled:
                    original_width, original_height = image.size

                    if self.resize_mode.get() == "Centimeters":
                        # Convert physical dimensions to pixels using the selected print resolution.
                        width_px = width_value / 2.54 * dpi_value
                        height_px = height_value / 2.54 * dpi_value
                        if self.keep_ratio.get():
                            width = max(1, round(width_px))
                            height = max(1, round(original_height * width / original_width))
                        else:
                            width = max(1, round(width_px))
                            height = max(1, round(height_px))
                    elif self.resize_mode.get() == "Percent":
                        if self.keep_ratio.get():
                            scale = width_value / 100.0
                            width = max(1, round(original_width * scale))
                            height = max(1, round(original_height * scale))
                        else:
                            width = max(1, round(original_width * width_value / 100.0))
                            height = max(1, round(original_height * height_value / 100.0))
                    else:
                        if self.keep_ratio.get():
                            # Use the width as the starting point and calculate the height automatically.
                            width = max(1, round(width_value))
                            height = max(1, round(original_height * width / original_width))
                        else:
                            width = max(1, round(width_value))
                            height = max(1, round(height_value))

                    image = image.resize((width, height), Image.Resampling.LANCZOS)

                # Apply rotation and mirroring.
                rotation = self.rotation_var.get()
                if rotation == "90°":
                    image = image.rotate(90, expand=True)
                elif rotation == "180°":
                    image = image.rotate(180, expand=True)
                elif rotation == "270°":
                    image = image.rotate(270, expand=True)

                if self.flip_var.get() == "Horizontal":
                    image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                elif self.flip_var.get() == "Vertical":
                    image = image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)

                if output_format in ("jpg", "jpeg"):
                    if image.mode in ("RGBA", "LA", "P"):
                        image = image.convert("RGBA")
                        background = Image.new("RGB", image.size, "white")
                        background.paste(image, mask=image.getchannel("A"))
                        image = background
                    else:
                        image = image.convert("RGB")

                extension = ".jpg" if output_format == "jpg" else (".heic" if output_format == "heic" else f".{output_format}")
                target = Path(output_dir) / f"{source_path.stem}{extension}"
                counter = 1
                original_target = target
                while target.exists():
                    target = original_target.with_name(
                        f"{original_target.stem}_{counter}{original_target.suffix}"
                    )
                    counter += 1

                save_options = {}
                if resize_enabled and self.resize_mode.get() == "Centimeters":
                    save_options["dpi"] = (dpi_value, dpi_value)
                quality_values = {"Low": 60, "Medium": 80, "High": 95}
                quality = quality_values.get(self.quality_var.get(), 95)
                if output_format == "jpg":
                    image.save(target, "JPEG", quality=quality, optimize=True, **save_options)
                elif output_format == "webp":
                    image.save(target, "WEBP", quality=quality, **save_options)
                elif output_format in ("heic", "heif"):
                    image = image.convert("RGB") if image.mode not in ("RGB", "RGBA") else image
                    image.save(target, "HEIF", quality=quality, **save_options)
                elif output_format == "ico":
                    image = image.convert("RGBA")
                    max_side = min(image.size)
                    ico_sizes = [s for s in (16, 32, 48, 64, 128, 256) if s <= max_side]
                    if not ico_sizes:
                        ico_sizes = [max(1, max_side)]
                    image.save(target, "ICO", sizes=[(s, s) for s in ico_sizes], **save_options)
                else:
                    image.save(target, output_format.upper(), **save_options)

                converted += 1
                new_size = target.stat().st_size
                old_size = source_path.stat().st_size

                if old_size > 0:
                    change = (1 - new_size / old_size) * 100
                    if change >= 0:
                        size_note = f"{self.format_size(old_size)} → {self.format_size(new_size)} ({change:.1f}% smaller)"
                    else:
                        size_note = f"{self.format_size(old_size)} → {self.format_size(new_size)} ({abs(change):.1f}% larger)"
                else:
                    size_note = f"{self.format_size(old_size)} → {self.format_size(new_size)}"

                self.progress["value"] = index
                self.status_label.configure(
                    text=f"{index}/{len(self.files)} – {source_path.name} – {size_note}"
                )
                self.root.update_idletasks()
            except Exception as e:
                errors.append(f"{Path(source).name}: {e}")
                self.progress["value"] = index
                self.root.update_idletasks()

        result = f"Done!\n\n{converted} image(s) converted."
        if errors:
            result += "\n\nCould not convert:\n" + "\n".join(errors)
        self.progress["value"] = len(self.files)
        self.status_label.configure(text=f"Done — {converted} of {len(self.files)} converted.")
        messagebox.showinfo("Image Converter", result)

    @staticmethod
    def format_size(size):
        if size < 1024:
            return f"{size} B"
        if size < 1024**2:
            return f"{size / 1024:.1f} KB"
        if size < 1024**3:
            return f"{size / 1024**2:.1f} MB"
        return f"{size / 1024**3:.1f} GB"

if DND_AVAILABLE:
    root = TkinterDnD.Tk()
else:
    root = tk.Tk()

app = ImageConverter(root)
root.mainloop()
