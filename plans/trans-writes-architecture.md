# trans-writes Architecture Plan

## Project Overview

**trans-writes** is an interactive image transformation tool that applies lossy compression techniques to create stylized pixel art. The application features a transgender flag color theme as a visual tribute.

## Color Theme

| Color Name   | Hex Code  | Usage                           |
|--------------|-----------|---------------------------------|
| Light Blue   | #5bcefa   | Background, headers             |
| Light Pink   | #f5a9b8   | Buttons, accents, sliders       |
| White        | #ffffff   | Text, backgrounds, borders      |
| Dark Pink    | #d96c9e   | Contrast color for trans palette|

## Project Structure

```
trans-writes/
├── main.py           # Entry point, launches the application
├── gui.py            # Main GUI class and all UI components
├── transforms.py     # Image transformation algorithms
├── utils.py          # Helper functions
├── README.md         # Documentation
└── plans/            # Planning documents
    └── trans-writes-architecture.md
```

## Module Architecture

### 1. transforms.py - Image Transformation Module

```mermaid
classDiagram
    class ImageTransformer {
        -image: PIL.Image
        +reduce_palette n_colors: int
        +apply_custom_palette palette_colors: list
        +dither_floyd_steinberg palette_colors: list
        +dither_atkinson palette_colors: list
        +dither_ordered palette_colors: list
        +pixelate block_size: int
        +apply_transforms settings: dict
    }
    
    class PaletteReducer {
        +quantize image, n_colors: int
        +nearest_color_match image, palette: list
        +get_trans_palette void
    }
    
    class Ditherer {
        +floyd_steinberg image, palette: list
        +atkinson image, palette: list
        +ordered_bayer image, palette: list
        -bayer_matrix: numpy.ndarray
        -find_nearest_color pixel, palette: list
        -distribute_error pixels, x, y, error, coefficients
    }
    
    class Pixelator {
        +pixelate image, block_size: int
        +downsample image, factor: int
        +upsample image, size: tuple
    }
    
    ImageTransformer --> PaletteReducer
    ImageTransformer --> Ditherer
    ImageTransformer --> Pixelator
```

#### Key Functions

| Function | Description | Parameters |
|----------|-------------|------------|
| `reduce_palette_pillow` | Reduce colors using Pillow quantize | image, n_colors |
| `apply_custom_palette` | Apply fixed color palette | image, palette_colors |
| `dither_floyd_steinberg` | Floyd-Steinberg error diffusion | image, palette_colors |
| `dither_atkinson` | Atkinson error diffusion | image, palette_colors |
| `dither_ordered` | Bayer 4x4 ordered dithering | image, palette_colors |
| `pixelate` | Block-based pixelation | image, block_size |

### 2. utils.py - Utility Module

```mermaid
classDiagram
    class FileUtils {
        +get_file_size file_path: str
        +estimate_png_size image: PIL.Image
        +format_size bytes: int
        +calculate_savings original: int, compressed: int
    }
    
    class ImageUtils {
        +pil_to_photoimage image: PIL.Image
        +resize_for_preview image, max_size: tuple
        +validate_image file_path: str
    }
    
    class ColorUtils {
        +color_distance c1: tuple, c2: tuple
        +hex_to_rgb hex_color: str
        +rgb_to_hex rgb: tuple
    }
```

#### Key Functions

| Function | Description | Returns |
|----------|-------------|---------|
| `estimate_png_size` | Calculate PNG size using BytesIO | int (bytes) |
| `format_file_size` | Format bytes as KB/MB string | str |
| `pil_to_photoimage` | Convert PIL Image to tkinter PhotoImage | ImageTk.PhotoImage |
| `calculate_savings_percentage` | Calculate compression ratio | float |
| `hex_to_rgb` | Convert hex color to RGB tuple | tuple |

### 3. gui.py - GUI Module

```mermaid
classDiagram
    class TransWritesApp {
        -root: tk.Tk
        -original_image: PIL.Image
        -transformed_image: PIL.Image
        -settings: dict
        +__init__ root: tk.Tk
        +setup_ui void
        +create_menu_bar void
        +create_flag_banner void
        +create_control_panel void
        +create_preview_area void
        +create_info_panel void
        +load_image void
        +save_image void
        +update_preview void
        +on_settings_change void
        +reset_settings void
    }
    
    class ControlPanel {
        -parent: tk.Frame
        -palette_var: tk.IntVar
        -dither_var: tk.StringVar
        -pixel_var: tk.IntVar
        +create_load_section void
        +create_palette_section void
        +create_dither_section void
        +create_pixelation_section void
        +create_save_section void
    }
    
    class PreviewArea {
        -parent: tk.Frame
        -canvas: tk.Canvas
        -photo_image: ImageTk.PhotoImage
        +display_image image: PIL.Image
        +clear void
        +add_scrollbars void
    }
    
    class InfoPanel {
        -parent: tk.Frame
        -original_size_label: tk.Label
        -compressed_size_label: tk.Label
        -savings_label: tk.Label
        +update_sizes original: int, compressed: int
    }
    
    TransWritesApp --> ControlPanel
    TransWritesApp --> PreviewArea
    TransWritesApp --> InfoPanel
```

#### GUI Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│  █████████████████████████████████████████████████████████  │ <- Flag banner
│  █████████████████████████████████████████████████████████  │    (blue/pink/white stripes)
├─────────────────────────────────────────────────────────────┤
│                    trans-writes                             │ <- Title
├──────────────────┬──────────────────────────────────────────┤
│                  │                                          │
│  ┌────────────┐  │                                          │
│  │ Load Image │  │                                          │
│  └────────────┘  │                                          │
│                  │                                          │
│  Palette: [====]│           PREVIEW AREA                   │
│  Colors:  16    │                                          │
│  ☐ Trans Flag   │        (scrollable canvas)               │
│                  │                                          │
│  Dithering:      │                                          │
│  [Dropdown   ▼] │                                          │
│                  │                                          │
│  Pixelation:     │                                          │
│  [====] 4       │                                          │
│                  │                                          │
│  ┌────────────┐  │                                          │
│  │  Save As   │  │                                          │
│  └────────────┘  │                                          │
│                  │                                          │
├──────────────────┴──────────────────────────────────────────┤
│  Original: 245 KB  │  Compressed: 87 KB  │  Saved: 64.5%   │ <- Info panel
└─────────────────────────────────────────────────────────────┘
```

### 4. main.py - Entry Point

```python
# Simple entry point that creates the main window and launches the app
import tkinter as tk
from gui import TransWritesApp

def main():
    root = tk.Tk()
    app = TransWritesApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
```

## Data Flow

```mermaid
flowchart TD
    A[User loads image] --> B[Store original_image]
    B --> C[Display in preview]
    C --> D{User changes settings}
    D --> E[Get current settings]
    E --> F[Apply palette reduction]
    F --> G{Dithering enabled?}
    G -->|Yes| H[Apply dithering algorithm]
    G -->|No| I{Pixelation enabled?}
    H --> I
    I -->|Yes| J[Apply pixelation]
    I -->|No| K[Store transformed_image]
    J --> K
    K --> L[Update preview]
    L --> M[Calculate file sizes]
    M --> N[Update info panel]
    N --> D
    D -->|Save| O[Save transformed_image as PNG]
```

## Transformation Pipeline

The transformations are applied in a specific order:

1. **Palette Reduction** - Reduce the number of colors in the image
2. **Dithering** - Apply error diffusion or ordered dithering
3. **Pixelation** - Downsample and upsample for mosaic effect

```mermaid
flowchart LR
    A[Original Image] --> B[Palette Reduction]
    B --> C[Dithering]
    C --> D[Pixelation]
    D --> E[Final Image]
```

## Dithering Algorithm Details

### Floyd-Steinberg Dithering
Spreads quantization error to neighboring pixels:
```
        *   7/16
  3/16  5/16  1/16
```

### Atkinson Dithering
Spreads error to fewer neighbors for a sharper look:
```
        *   1/8  1/8
  1/8  1/8  1/8
       1/8
```

### Ordered Dithering (Bayer 4x4)
Uses a threshold matrix to determine pixel values:
```
 0  8  2 10
12  4 14  6
 3 11  1  9
15  7 13  5
```
Each value is divided by 16 and compared against pixel intensity.

## Settings Dictionary Structure

```python
settings = {
    'palette_colors': 16,        # 2-256
    'use_trans_palette': False,  # Use trans flag colors
    'dithering': 'none',         # 'none', 'floyd_steinberg', 'atkinson', 'ordered'
    'pixelation': 1              # 1, 2, 4, 8, 16 (1 = no pixelation)
}
```

## Error Handling

| Scenario | Handling |
|----------|----------|
| No image loaded | Show info message, disable transform controls |
| Invalid file format | Show error dialog, supported formats listed |
| Palette size < 2 | Clamp to minimum of 2 |
| Image too large for preview | Resize for display, keep original for processing |
| Save cancelled | No action needed, user cancelled dialog |

## Dependencies

```
Pillow>=9.0.0
numpy>=1.20.0
```

Note: `tkinter` is included with Python standard library.

## Implementation Order

1. **utils.py** - Foundation utilities needed by other modules
2. **transforms.py** - Core transformation algorithms
3. **gui.py** - User interface and event handling
4. **main.py** - Entry point
5. **README.md** - Documentation

## Optional Features (If Time Permits)

### Show Bytes View
A separate window showing the raw palette indices as a grid of colored squares. This visualizes how the image data is stored after palette reduction.

### Undo/History
Store a list of previous states and allow stepping back through transformations. Would require:
- `history: list` of PIL Images
- `history_index: int` to track current position
- Undo/Redo buttons in UI

### Batch Processing
Apply the same settings to multiple images:
- Select folder dialog
- Process all images with current settings
- Save to output folder
- Progress bar for batch operation
