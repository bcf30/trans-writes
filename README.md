# trans-writes
## Proudly vibe-coded

**trans-writes** transforms images and writes them to your disk. 

Apply lossy transforms (palette reduction, dithering, pixelation), then write the result to your computer. A celebration of diversity in tech.

An interactive image transformation tool that converts any image to use an expanded transgender flag palette with perceptually uniform color matching for beautiful, natural-looking results. It even renames the files for you!

### Features

- **Expanded Trans Flag Palette (7 colors)** – Smoother gradients while staying true to trans flag colors:
  - Light Blue (#5bcefa) - official
  - Medium Blue (#96dcfa)
  - Very Light Blue (#c8ebff)
  - White (#ffffff) - official
  - Very Light Pink (#ffdcf0)
  - Light Pink (#f5a9b8) - official
  - Darker Pink (#d96c9e)

- **Perceptually Uniform Color Matching**:
  - Uses LAB color space (via scikit-image) for color matching that matches human perception
  - Falls back to weighted RGB distance if scikit-image is not installed

- **Dithering Algorithms**:
  - Floyd-Steinberg (classic error diffusion)
  - Atkinson (sharper, retro look)
  - Ordered/Bayer 4×4 (crosshatch pattern)

- **Optimized Performance**:
  - Numba JIT compilation for 10-50x faster dithering (optional)
  - Parallel processing for palette application

- **Pixelation** – Create mosaic effects with block sizes 1-16
- **Live Preview** – See changes instantly
- **File Size Comparison** – View original size, compressed size, and savings
- **Multiple Export Formats**:
  - PNG (optimized compression)
  - BMP (uncompressed)
  - WebP (lossless)
  - JPEG XL (lossless, if supported)

- **Optimized for Data & Energy Efficiency**:
  - Modern formats like JPEG XL and WebP offer superior compression compared to legacy formats
  - Smaller file sizes mean less storage, faster transfers, and reduced energy consumption
  - please lock in and help defeat the monopoly of Google trying to kill jpegxl

### Installation

#### Requirements

- Python 3.8+
- Pillow (PIL)
- numpy
- pillow-jxl-plugin (for JPEG XL support)
- scikit-image (recommended for better color matching)
- numba (recommended for faster processing)

#### Install Dependencies

```bash
# Basic installation (includes JPEG XL support)
pip install Pillow numpy pillow-jxl-plugin

# Recommended for better color matching
pip install scikit-image

# Recommended for much faster processing (10-50x speedup)
pip install numba
```

Or install all at once:
```bash
pip install Pillow numpy pillow-jxl-plugin scikit-image numba
```

#### Run the Application

```bash
python main.py
```

### Usage

1. **Load an image** – Click "Load Image" and select any JPG, PNG, BMP, or GIF file
2. **Choose dithering** – Select from None, Floyd-Steinberg, Atkinson, or Ordered
3. **Set pixelation** – Adjust the block size slider (1 = no pixelation)
4. **Preview** – See your changes in real-time
5. **Save** – Click "Save As..." to export (default filename: "TRANS RIGHTS!!!!")

### Expanded Palette Colors

| Color Name          | Hex Code | RGB              |
|---------------------|----------|------------------|
| Light Blue          | #5bcefa  | (91, 206, 250)   |
| Medium Blue         | #96dcfa  | (150, 220, 250)  |
| Very Light Blue     | #c8ebff  | (200, 235, 255)  |
| White               | #ffffff  | (255, 255, 255)  |
| Very Light Pink     | #ffdcf0  | (255, 220, 240)  |
| Light Pink          | #f5a9b8  | (245, 169, 184)  |
| Darker Pink         | #d96c9e  | (217, 108, 158)  |

### Color Matching Methods

#### LAB Color Space (Recommended)
When scikit-image is installed, the app uses LAB color space for matching. LAB distance closely matches human perception, producing more natural color mapping.

#### Weighted RGB Fallback
Without scikit-image, the app uses weighted RGB distance (green weighted more heavily) to approximate perceptual uniformity.

### Dithering Algorithms

#### Floyd-Steinberg
Classic error diffusion for smooth gradients:
```
        *   7/16
  3/16  5/16  1/16
```

#### Atkinson
Sharper look with less error distribution:
```
        *   1/8  1/8
  1/8  1/8  1/8
        1/8
```

#### Ordered (Bayer 4×4)
Crosshatch pattern using threshold matrix.

### Performance Tips

For the best experience with large images:
1. **Install Numba** - Provides 10-50x speedup for dithering operations
   ```bash
   pip install numba
   ```
2. **Install scikit-image** - Better color matching with LAB color space
   ```bash
   pip install scikit-image
   ```

### Project Structure

```
trans-writes/
├── main.py           # Entry point
├── gui.py            # Main GUI with trans flag theme
├── transforms.py     # Image transformation algorithms (Numba-optimized)
├── utils.py          # Helper functions and palette
├── requirements.txt  # Dependencies
└── README.md         # Documentation
```

### Building with PyInstaller

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "trans-writes" main.py
```

### License

Provided as-is for educational and personal use.

### Acknowledgments

- The transgender flag was created by Monica Helms in 1999
- LAB color space matching provides perceptually uniform results
- Built with Python, tkinter, Pillow, and numpy
- Optimized with Numba JIT compilation
