import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional
from PIL import Image, ImageTk

from utils import (
    TRANS_PALETTE,
    TRANS_LIGHT_BLUE_HEX,
    TRANS_LIGHT_PINK_HEX,
    TRANS_WHITE_HEX,
    HAS_JXL,
    estimate_png_size,
    estimate_webp_size,
    estimate_jxl_size,
    estimate_bmp_size,
    get_file_size,
    format_file_size,
    calculate_savings_percentage,
    resize_for_preview,
    SUPPORTED_IMAGE_FORMATS
)
from transforms import apply_transforms, get_palette_info


COLOR_LIGHT_BLUE = TRANS_LIGHT_BLUE_HEX    # #5bcefa
COLOR_LIGHT_PINK = TRANS_LIGHT_PINK_HEX    # #f5a9b8
COLOR_WHITE = TRANS_WHITE_HEX              # #ffffff

COLOR_BUTTON_BG = COLOR_LIGHT_PINK
COLOR_BUTTON_FG = "#333333"
COLOR_FRAME_BG = COLOR_WHITE


class TransWritesApp:
    """main app class - handles the UI and image transformations"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("trans-writes")
        self.root.geometry("900x680")
        self.root.minsize(800, 600)
        self.root.configure(bg=COLOR_FRAME_BG)
        
        self.original_image: Optional[Image.Image] = None
        self.original_file_size: int = 0
        self.transformed_image: Optional[Image.Image] = None
        self.preview_photo: Optional[ImageTk.PhotoImage] = None
        self._estimated_size_by_format: dict[str, int] = {}

        self.dithering_method = tk.StringVar(value='none')
        self.pixelation_size = tk.IntVar(value=1)
        self.invert_colors = tk.BooleanVar(value=False)

        self._setup_styles()
        self._build_ui()

        self.root.after(100, self._show_placeholder)
        
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _setup_styles(self) -> None:
        """set up ttk styles"""
        style = ttk.Style()
        
        style.configure('Trans.TFrame', background=COLOR_FRAME_BG)
        style.configure('Blue.TFrame', background=COLOR_LIGHT_BLUE)
        
        style.configure(
            'Trans.TLabel',
            background=COLOR_FRAME_BG,
            foreground='#333333',
            font=('Terminal', 10)
        )
        
        style.configure(
            'Small.TLabel',
            background=COLOR_FRAME_BG,
            foreground='#666666',
            font=('Terminal', 9)
        )
    
    def _build_ui(self) -> None:
        """build the whole UI"""
        self.main_frame = ttk.Frame(self.root, style='Trans.TFrame', padding=0)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        self._create_flag_banner()
        self._create_title_area()
        self._create_content_area()
        self._create_info_panel()
    
    def _create_flag_banner(self) -> None:
        """trans flag banner - 5 stripes: blue-pink-white-pink-blue"""
        banner_frame = tk.Frame(self.main_frame, height=10)
        banner_frame.pack(fill=tk.X)
        banner_frame.pack_propagate(False)
        
        for stripe_color in (
            COLOR_LIGHT_BLUE,
            COLOR_LIGHT_PINK,
            COLOR_WHITE,
            COLOR_LIGHT_PINK,
            COLOR_LIGHT_BLUE,
        ):
            stripe = tk.Frame(banner_frame, bg=stripe_color, height=10)
            stripe.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    def _create_title_area(self) -> None:
        """title area with app name"""
        title_frame = tk.Frame(self.main_frame, bg=COLOR_LIGHT_BLUE, height=50)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame,
            text="✨ trans-writes ✨",
            bg=COLOR_LIGHT_BLUE,
            fg=COLOR_WHITE,
            font=('Terminal', 18, 'bold')
        )
        title_label.pack(expand=True)
    
    def _create_content_area(self) -> None:
        """main content area - controls and preview"""
        content_frame = ttk.Frame(self.main_frame, style='Trans.TFrame', padding=10)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        self._create_control_panel(content_frame)
        self._create_preview_area(content_frame)
    
    def _create_control_panel(self, parent: ttk.Frame) -> None:
        """control panel on the left"""
        control_frame = ttk.Frame(parent, style='Trans.TFrame', padding=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        self._create_load_section(control_frame)
        ttk.Separator(control_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        self._create_palette_info(control_frame)
        ttk.Separator(control_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        self._create_dithering_section(control_frame)
        ttk.Separator(control_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        self._create_pixelation_section(control_frame)
        ttk.Separator(control_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        self._create_save_section(control_frame)
    
    def _create_load_section(self, parent: ttk.Frame) -> None:
        """load image section"""
        section_frame = ttk.Frame(parent, style='Trans.TFrame')
        section_frame.pack(fill=tk.X)
        
        header = tk.Label(
            section_frame,
            text="📁 Image",
            bg=COLOR_FRAME_BG,
            fg=COLOR_LIGHT_BLUE,
            font=('Terminal', 11, 'bold')
        )
        header.pack(anchor=tk.W)
        
        self.load_button = tk.Button(
            section_frame,
            text="Load Image",
            bg=COLOR_BUTTON_BG,
            fg=COLOR_BUTTON_FG,
            font=('Terminal', 10),
            width=18,
            cursor='hand2',
            command=self._load_image
        )
        self.load_button.pack(pady=5)
        
        self.file_name_label = ttk.Label(
            section_frame,
            text="No image loaded",
            style='Trans.TLabel'
        )
        self.file_name_label.pack(anchor=tk.W)
    
    def _create_palette_info(self, parent: ttk.Frame) -> None:
        """palette info section"""
        section_frame = ttk.Frame(parent, style='Trans.TFrame')
        section_frame.pack(fill=tk.X)
        
        header = tk.Label(
            section_frame,
            text="🎨 Palette",
            bg=COLOR_FRAME_BG,
            fg=COLOR_LIGHT_BLUE,
            font=('Terminal', 11, 'bold')
        )
        header.pack(anchor=tk.W)
        
        palette_info = get_palette_info()
        info_text = f"Expanded Trans Flag ({palette_info['num_colors']} colors)"
        
        info_label = ttk.Label(
            section_frame,
            text=info_text,
            style='Trans.TLabel'
        )
        info_label.pack(anchor=tk.W, pady=2)
        
        method_text = f"Matching: {palette_info['color_matching']}"
        method_label = ttk.Label(
            section_frame,
            text=method_text,
            style='Small.TLabel'
        )
        method_label.pack(anchor=tk.W)
        
        swatch_frame = ttk.Frame(section_frame, style='Trans.TFrame')
        swatch_frame.pack(fill=tk.X, pady=5)
        
        for color in TRANS_PALETTE:
            hex_color = "#{:02x}{:02x}{:02x}".format(*color)
            swatch = tk.Frame(
                swatch_frame, 
                bg=hex_color, 
                width=20, 
                height=20,
                highlightthickness=1,
                highlightbackground='#cccccc'
            )
            swatch.pack(side=tk.LEFT, padx=1)
            swatch.pack_propagate(False)
    
    def _create_dithering_section(self, parent: ttk.Frame) -> None:
        """dithering options"""
        section_frame = ttk.Frame(parent, style='Trans.TFrame')
        section_frame.pack(fill=tk.X)
        
        header = tk.Label(
            section_frame,
            text="✨ Dithering",
            bg=COLOR_FRAME_BG,
            fg=COLOR_LIGHT_BLUE,
            font=('Terminal', 11, 'bold')
        )
        header.pack(anchor=tk.W)
        
        dither_options = [
            ('none', 'None'),
            ('floyd_steinberg', 'Floyd-Steinberg'),
            ('atkinson', 'Atkinson'),
            ('ordered', 'Ordered (Bayer)')
        ]
        
        self.dither_combo = ttk.Combobox(
            section_frame,
            values=[opt[1] for opt in dither_options],
            state='readonly',
            width=16
        )
        self.dither_combo.set('None')
        self.dither_combo.pack(pady=5)
        self.dither_combo.bind('<<ComboboxSelected>>', self._on_dither_change)
        
        self.dither_mapping = {opt[1]: opt[0] for opt in dither_options}
    
    def _create_pixelation_section(self, parent: ttk.Frame) -> None:
        """pixelation slider and entry"""
        section_frame = ttk.Frame(parent, style='Trans.TFrame')
        section_frame.pack(fill=tk.X)
        
        header = tk.Label(
            section_frame,
            text="🔲 Pixelation",
            bg=COLOR_FRAME_BG,
            fg=COLOR_LIGHT_BLUE,
            font=('Terminal', 11, 'bold')
        )
        header.pack(anchor=tk.W)
        
        slider_frame = ttk.Frame(section_frame, style='Trans.TFrame')
        slider_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(slider_frame, text="Block:", style='Trans.TLabel').pack(side=tk.LEFT)
        
        self.pixel_slider = ttk.Scale(
            slider_frame,
            from_=1,
            to=32,
            variable=self.pixelation_size,
            orient=tk.HORIZONTAL,
            length=100
        )
        self.pixel_slider.pack(side=tk.LEFT, padx=5)
        self.pixel_slider.configure(command=self._on_pixel_slider_change)
        
        self.pixel_entry = tk.Entry(
            slider_frame,
            width=3,
            font=('Terminal', 10),
            justify='center'
        )
        self.pixel_entry.insert(0, "1")
        self.pixel_entry.pack(side=tk.LEFT)
        # only update on enter or focus out, not every keystroke
        self.pixel_entry.bind('<Return>', self._on_pixel_entry_change)
        self.pixel_entry.bind('<FocusOut>', self._on_pixel_entry_change)
    
    def _create_save_section(self, parent: ttk.Frame) -> None:
        """save buttons in trans flag colors"""
        section_frame = ttk.Frame(parent, style='Trans.TFrame')
        section_frame.pack(fill=tk.X)
        
        self.save_button = tk.Button(
            section_frame,
            text="♥ Save As... ♥",
            bg=COLOR_LIGHT_BLUE,
            fg=COLOR_WHITE,
            font=('Terminal', 10),
            width=18,
            cursor='hand2',
            command=self._save_image,
            state=tk.DISABLED
        )
        self.save_button.pack(pady=5)
        
        self.reset_button = tk.Button(
            section_frame,
            text="♥ Reset ♥",
            bg=COLOR_BUTTON_BG,
            fg=COLOR_BUTTON_FG,
            font=('Terminal', 10),
            width=18,
            cursor='hand2',
            command=self._reset_settings
        )
        self.reset_button.pack(pady=5)
        
        self.clear_button = tk.Button(
            section_frame,
            text="♥ Clear ♥",
            bg=COLOR_WHITE,
            fg=COLOR_BUTTON_FG,
            font=('Terminal', 10),
            width=18,
            cursor='hand2',
            command=self._clear_image
        )
        self.clear_button.pack(pady=5)
        
        self.about_button = tk.Button(
            section_frame,
            text="♥ About ♥",
            bg=COLOR_BUTTON_BG,
            fg=COLOR_BUTTON_FG,
            font=('Terminal', 10),
            width=18,
            cursor='hand2',
            command=self._show_about
        )
        self.about_button.pack(pady=5)
        
        self.invert_button = tk.Button(
            section_frame,
            text="♥ Invert Colors ♥",
            bg=COLOR_LIGHT_BLUE,
            fg=COLOR_WHITE,
            font=('Terminal', 10),
            width=18,
            cursor='hand2',
            command=self._toggle_invert
        )
        self.invert_button.pack(pady=5)
    
    def _create_preview_area(self, parent: ttk.Frame) -> None:
        """preview area with zoom support"""
        preview_frame = ttk.Frame(parent, style='Trans.TFrame', padding=5)
        preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        header = tk.Label(
            preview_frame,
            text="📷 Preview",
            bg=COLOR_FRAME_BG,
            fg=COLOR_LIGHT_BLUE,
            font=('Terminal', 11, 'bold')
        )
        header.pack(anchor=tk.W)
        
        canvas_frame = ttk.Frame(preview_frame, style='Trans.TFrame')
        canvas_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.preview_canvas = tk.Canvas(
            canvas_frame,
            bg='#f0f0f0',
            highlightthickness=1,
            highlightbackground=COLOR_LIGHT_PINK
        )
        
        h_scroll = ttk.Scrollbar(
            canvas_frame,
            orient=tk.HORIZONTAL,
            command=self.preview_canvas.xview
        )
        v_scroll = ttk.Scrollbar(
            canvas_frame,
            orient=tk.VERTICAL,
            command=self.preview_canvas.yview
        )
        
        self.preview_canvas.configure(
            xscrollcommand=h_scroll.set,
            yscrollcommand=v_scroll.set
        )
        
        self.preview_canvas.grid(row=0, column=0, sticky='nsew')
        v_scroll.grid(row=0, column=1, sticky='ns')
        h_scroll.grid(row=1, column=0, sticky='ew')
        
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        self.zoom_level = 1.0

        self.preview_canvas.bind('<MouseWheel>', self._on_mouse_wheel)
        self.preview_canvas.bind('<Button-4>', self._on_mouse_wheel)
        self.preview_canvas.bind('<Button-5>', self._on_mouse_wheel)
        self.preview_canvas.bind('<Double-Button-1>', self._on_zoom_reset)
    
    def _create_info_panel(self) -> None:
        """file size info panel at the bottom"""
        info_frame = tk.Frame(self.main_frame, bg=COLOR_LIGHT_BLUE, height=60)
        info_frame.pack(fill=tk.X)
        info_frame.pack_propagate(False)
        
        inner_frame = tk.Frame(info_frame, bg=COLOR_LIGHT_BLUE)
        inner_frame.pack(expand=True)
        
        orig_frame = tk.Frame(inner_frame, bg=COLOR_LIGHT_BLUE)
        orig_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(
            orig_frame,
            text="Original:",
            bg=COLOR_LIGHT_BLUE,
            fg=COLOR_WHITE,
            font=('Terminal', 12)
        ).pack(side=tk.LEFT)
        
        self.original_size_label = tk.Label(
            orig_frame,
            text="-- KB",
            bg=COLOR_LIGHT_BLUE,
            fg=COLOR_WHITE,
            font=('Terminal', 12)
        )
        self.original_size_label.pack(side=tk.LEFT, padx=5)
        
        comp_frame = tk.Frame(inner_frame, bg=COLOR_LIGHT_BLUE)
        comp_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(
            comp_frame,
            text="Est.",
            bg=COLOR_LIGHT_BLUE,
            fg=COLOR_WHITE,
            font=('Terminal', 12)
        ).pack(side=tk.LEFT)
        
        self.format_var = tk.StringVar(value='PNG')
        self.format_combo = ttk.Combobox(
            comp_frame,
            textvariable=self.format_var,
            values=['PNG', 'WebP', 'JXL', 'BMP'],
            state='readonly',
            width=5
        )
        self.format_combo.pack(side=tk.LEFT, padx=2)
        self.format_combo.bind('<<ComboboxSelected>>', self._on_format_change)
        
        tk.Label(
            comp_frame,
            text=":",
            bg=COLOR_LIGHT_BLUE,
            fg=COLOR_WHITE,
            font=('Terminal', 12)
        ).pack(side=tk.LEFT)
        
        self.compressed_size_label = tk.Label(
            comp_frame,
            text="-- KB",
            bg=COLOR_LIGHT_BLUE,
            fg=COLOR_WHITE,
            font=('Terminal', 12)
        )
        self.compressed_size_label.pack(side=tk.LEFT, padx=5)
        
        savings_frame = tk.Frame(inner_frame, bg=COLOR_LIGHT_BLUE)
        savings_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(
            savings_frame,
            text="Saved:",
            bg=COLOR_LIGHT_BLUE,
            fg=COLOR_WHITE,
            font=('Terminal', 12)
        ).pack(side=tk.LEFT)
        
        self.savings_label = tk.Label(
            savings_frame,
            text="-- %",
            bg=COLOR_LIGHT_BLUE,
            fg=COLOR_WHITE,
            font=('Terminal', 12)
        )
        self.savings_label.pack(side=tk.LEFT, padx=5)

    def _load_image(self) -> None:
        """load image button handler"""
        file_path = filedialog.askopenfilename(
            title="Load Image",
            filetypes=SUPPORTED_IMAGE_FORMATS
        )
        
        if not file_path:
            return
        
        try:
            self.original_image = Image.open(file_path)
            self.original_image.load()
            self.original_file_size = get_file_size(file_path)
            
            file_name = os.path.basename(file_path)
            self.file_name_label.configure(
                text=file_name[:20] + "..." if len(file_name) > 20 else file_name
            )
            
            self.save_button.configure(state=tk.NORMAL)
            self._on_settings_change()
            
            self.original_size_label.configure(
                text=format_file_size(self.original_file_size)
            )
            
        except Exception as error:
            messagebox.showerror("Error", f"Failed to load image: {str(error)}")
    
    def _save_image(self) -> None:
        """save image button handler"""
        if self.transformed_image is None:
            messagebox.showinfo("Info", "No image to save.")
            return
        
        selected_format = self.format_var.get().lower()
        default_extension = f".{selected_format}"

        # Windows uses the first entry as the default file type.
        format_filetypes = {
            'png': ("PNG files", "*.png"),
            'webp': ("WebP files (lossless)", "*.webp"),
            'jxl': ("JPEG XL files (lossless)", "*.jxl"),
            'bmp': ("BMP files", "*.bmp")
        }
        filetypes = [format_filetypes[selected_format]]

        for format_name, filetype in format_filetypes.items():
            if format_name == selected_format:
                continue
            if format_name == 'jxl' and not HAS_JXL:
                continue
            filetypes.append(filetype)

        filetypes.append(("All files", "*.*"))
        
        file_path = filedialog.asksaveasfilename(
            title="Save Image",
            initialfile="TRANS RIGHTS!!!!",
            defaultextension=default_extension,
            filetypes=filetypes
        )
        
        if not file_path:
            return
        
        try:
            output_extension = os.path.splitext(file_path)[1].lower()

            if output_extension == '.png':
                self.transformed_image.save(file_path, format='PNG', optimize=True)
            elif output_extension == '.bmp':
                self.transformed_image.save(file_path, format='BMP')
            elif output_extension == '.webp':
                self.transformed_image.save(file_path, format='WEBP', lossless=True)
            elif output_extension == '.jxl':
                self._save_jxl(file_path)
            else:
                self.transformed_image.save(file_path, format='PNG', optimize=True)
            
            messagebox.showinfo("Success", f"Image saved to:\n{file_path}")
        except Exception as error:
            messagebox.showerror("Error", f"Failed to save: {str(error)}")

    def _save_jxl(self, file_path: str) -> None:
        """save image as lossless jpeg xl"""
        if not HAS_JXL:
            raise RuntimeError(
                "JPEG XL support not available. "
                "Install with: pip install pillow-jxl-plugin"
            )
        self.transformed_image.save(file_path, format='JXL', lossless=True)
    
    def _on_pixel_slider_change(self, value: str) -> None:
        """Handle pixelation slider change."""
        int_value = int(float(value))
        self.pixel_entry.delete(0, tk.END)
        self.pixel_entry.insert(0, str(int_value))
        self._on_settings_change()
    
    def _on_pixel_entry_change(self, _event) -> None:
        """Handle pixelation entry change - validate and sync with slider."""
        try:
            value = self.pixel_entry.get()
            if not value:
                return
            int_value = int(value)
            int_value = max(1, min(32, int_value))
            self.pixel_entry.delete(0, tk.END)
            self.pixel_entry.insert(0, str(int_value))
            self.pixelation_size.set(int_value)
            self._on_settings_change()
        except ValueError:
            current = int(self.pixelation_size.get())
            self.pixel_entry.delete(0, tk.END)
            self.pixel_entry.insert(0, str(current))
    
    def _on_dither_change(self, _event) -> None:
        """dithering dropdown changed"""
        selected = self.dither_combo.get()
        self.dithering_method.set(self.dither_mapping.get(selected, 'none'))
        self._on_settings_change()
    
    def _on_settings_change(self) -> None:
        """settings changed - update preview and file sizes"""
        if self.original_image is None:
            return
        
        self.transformed_image = apply_transforms(
            self.original_image,
            dithering=self.dithering_method.get(),
            pixelation=int(self.pixelation_size.get()),
            invert=self.invert_colors.get()
        )
        
        self._update_preview()
        self._update_file_info()
    
    def _update_preview(self) -> None:
        """update preview canvas"""
        if self.transformed_image is None:
            self._show_placeholder()
            return
        
        if self.zoom_level != 1.0:
            new_width = int(self.transformed_image.width * self.zoom_level)
            new_height = int(self.transformed_image.height * self.zoom_level)
            preview_image = self.transformed_image.resize((new_width, new_height), Image.Resampling.NEAREST)
        else:
            preview_image = resize_for_preview(
                self.transformed_image,
                max_width=600,
                max_height=450
            )
        
        self.preview_photo = ImageTk.PhotoImage(preview_image)
        
        self.preview_canvas.delete("all")
        self.preview_canvas.configure(
            scrollregion=(0, 0, preview_image.width, preview_image.height)
        )
        self.preview_canvas.create_image(0, 0, anchor=tk.NW, image=self.preview_photo)
    
    def _on_mouse_wheel(self, event) -> None:
        """mouse wheel zoom"""
        if self.transformed_image is None:
            return
        
        if event.num == 4 or event.delta > 0:
            factor = 1.1
        elif event.num == 5 or event.delta < 0:
            factor = 0.9
        else:
            return
        
        new_zoom = self.zoom_level * factor
        new_zoom = max(0.1, min(10.0, new_zoom))
        
        if new_zoom != self.zoom_level:
            self.zoom_level = new_zoom
            self._update_preview()
    
    def _on_zoom_reset(self, _event) -> None:
        """reset zoom on double-click"""
        if self.zoom_level != 1.0:
            self.zoom_level = 1.0
            self._update_preview()
    
    def _update_file_info(self) -> None:
        """Discard stale estimates and refresh the selected format."""
        self._estimated_size_by_format.clear()
        self._update_size_display()

    def _estimate_output_size(self, output_format: str) -> int:
        if self.transformed_image is None:
            return 0

        estimators = {
            'PNG': estimate_png_size,
            'WebP': estimate_webp_size,
            'JXL': estimate_jxl_size,
            'BMP': estimate_bmp_size,
        }
        if output_format not in self._estimated_size_by_format:
            estimator = estimators[output_format]
            self._estimated_size_by_format[output_format] = estimator(
                self.transformed_image
            )
        return self._estimated_size_by_format[output_format]

    def _update_size_display(self) -> None:
        if self.transformed_image is None:
            self.compressed_size_label.configure(text="-- KB")
            self.savings_label.configure(text="-- %", fg=COLOR_WHITE)
            return

        selected_format = self.format_var.get()
        compressed_size = self._estimate_output_size(selected_format)

        if selected_format == 'JXL' and compressed_size == 0:
            self.compressed_size_label.configure(text="N/A")
            self.savings_label.configure(text="N/A", fg=COLOR_WHITE)
            return

        self.compressed_size_label.configure(text=format_file_size(compressed_size))
        savings = calculate_savings_percentage(self.original_file_size, compressed_size)

        if savings >= 0:
            self.savings_label.configure(text=f"{savings:.1f}%", fg=COLOR_WHITE)
        else:
            self.savings_label.configure(text=f"+{abs(savings):.1f}%", fg="#ffcccc")

    def _on_format_change(self, _event) -> None:
        self._update_size_display()
    
    def _show_placeholder(self) -> None:
        """show placeholder text"""
        self.preview_canvas.delete("all")
        self.preview_canvas.update_idletasks()
        
        width = max(self.preview_canvas.winfo_width(), 400)
        height = max(self.preview_canvas.winfo_height(), 300)
        
        self.preview_canvas.create_text(
            width // 2,
            height // 2,
            text="Load an image to begin",
            font=('Terminal', 14),
            fill='#999999'
        )
    
    def _reset_settings(self) -> None:
        """reset settings to defaults"""
        self.dithering_method.set('none')
        self.pixelation_size.set(1)
        self.invert_colors.set(False)
        
        self.pixel_entry.delete(0, tk.END)
        self.pixel_entry.insert(0, "1")
        self.dither_combo.set('None')
        self.invert_button.config(text="♥ Invert Colors ♥")
        
        self._on_settings_change()
    
    def _clear_image(self) -> None:
        """clear image and reset app"""
        self.original_image = None
        self.original_file_size = 0
        self.transformed_image = None
        self.preview_photo = None
        self._estimated_size_by_format.clear()
        
        self.dithering_method.set('none')
        self.pixelation_size.set(1)
        self.invert_colors.set(False)
        self.pixel_entry.delete(0, tk.END)
        self.pixel_entry.insert(0, "1")
        self.dither_combo.set('None')
        self.format_var.set('PNG')
        self.invert_button.config(text="♥ Invert Colors ♥")
        
        self.zoom_level = 1.0
        
        self.file_name_label.configure(text="No image loaded")
        self.save_button.configure(state=tk.DISABLED)
        
        self.original_size_label.configure(text="-- KB")
        self.compressed_size_label.configure(text="-- KB")
        self.savings_label.configure(text="-- %", fg=COLOR_WHITE)
        
        self._show_placeholder()
    
    def _show_about(self) -> None:
        """about dialog"""
        messagebox.showinfo(
            "About trans-writes",
            "trans-writes\n\n"
            "An interactive image transformation tool that converts images "
            "to use an expanded transgender flag palette for both beauty and compression.\n\n"
            "Features:\n"
            "- 7-color expanded trans flag palette\n"
            "- Floyd-Steinberg, Atkinson, and Ordered dithering\n"
            "- Pixelation effects\n"
            "- Export to PNG, BMP, WebP, JPEG XL\n\n"
            "TRANS RIGHTS!!!!\n\n"
            "Can you believe that GLM-5 (Chinese AI) wrote that \"TRANS RIGHTS!!!!\" text by itself?"
        )
    
    def _toggle_invert(self) -> None:
        """toggle color inversion"""
        was_inverted = self.invert_colors.get()
        self.invert_colors.set(not was_inverted)
        if not was_inverted:
            self.invert_button.config(text="♥ Normal Colors ♥")
        else:
            self.invert_button.config(text="♥ Invert Colors ♥")
        self._on_settings_change()
    
    def _on_close(self) -> None:
        """window close handler"""
        self.root.destroy()


def run_app() -> None:
    """run the app standalone"""
    root = tk.Tk()
    application = TransWritesApp(root)
    root.mainloop()


if __name__ == '__main__':
    run_app()
