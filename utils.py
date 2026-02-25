"""
utils.py - helper functions for trans-writes

file size estimation, image conversion, color matching stuff
"""

import os
from io import BytesIO
from typing import Tuple, List, Optional
import numpy as np
from PIL import Image, ImageTk

# jxl support is optional
try:
    import pillow_jxl
except ImportError:
    pass

# scikit-image for LAB color space (perceptually uniform matching)
try:
    from skimage import color as skimage_color
    HAS_SKIMAGE = True
except ImportError:
    HAS_SKIMAGE = False


# expanded trans flag palette (7 colors for better gradients)
TRANS_PALETTE = [
    (91, 206, 250),   # light blue (#5bcefa) - official
    (150, 220, 250),  # medium blue (#96dcfa)
    (200, 235, 255),  # very light blue (#c8ebff)
    (255, 255, 255),  # white (#ffffff) - official
    (255, 220, 240),  # very light pink (#ffdcf0)
    (245, 169, 184),  # light pink (#f5a9b8) - official
    (217, 108, 158),  # darker pink (#d96c9e)
]

# inverted palette - swaps blue and pink tones
INVERTED_PALETTE = [
    (245, 169, 184),  # light pink (was light blue)
    (255, 190, 215),  # medium pink (was medium blue)
    (255, 230, 245),  # very light pink (was very light blue)
    (255, 255, 255),  # white stays white
    (200, 235, 255),  # very light blue (was very light pink)
    (91, 206, 250),   # light blue (was light pink)
    (70, 150, 200),   # darker blue (was darker pink)
]

# hex versions for tkinter
TRANS_LIGHT_BLUE_HEX = "#5bcefa"
TRANS_LIGHT_PINK_HEX = "#f5a9b8"
TRANS_WHITE_HEX = "#ffffff"

# cache for LAB palette
_LAB_PALETTE_CACHE: Optional[np.ndarray] = None


def _get_lab_palette() -> np.ndarray:
    """get palette in LAB color space (cached)"""
    global _LAB_PALETTE_CACHE
    
    if _LAB_PALETTE_CACHE is not None:
        return _LAB_PALETTE_CACHE
    
    if HAS_SKIMAGE:
        palette_rgb = np.array(TRANS_PALETTE, dtype=np.float32) / 255.0
        palette_rgb = palette_rgb.reshape(-1, 1, 3)
        _LAB_PALETTE_CACHE = skimage_color.rgb2lab(palette_rgb).reshape(-1, 3)
    else:
        _LAB_PALETTE_CACHE = None
    
    return _LAB_PALETTE_CACHE


def estimate_png_size(image: Image.Image) -> int:
    """estimate png file size"""
    buffer = BytesIO()
    image.save(buffer, format='PNG', optimize=True)
    return buffer.tell()


def estimate_webp_size(image: Image.Image) -> int:
    """estimate lossless webp file size"""
    buffer = BytesIO()
    image.save(buffer, format='WEBP', lossless=True)
    return buffer.tell()


def estimate_jxl_size(image: Image.Image) -> int:
    """estimate lossless jxl file size, returns 0 if jxl not available"""
    try:
        buffer = BytesIO()
        image.save(buffer, format='JXL', lossless=True)
        return buffer.tell()
    except Exception:
        return 0


def estimate_bmp_size(image: Image.Image) -> int:
    """estimate bmp file size"""
    buffer = BytesIO()
    image.save(buffer, format='BMP')
    return buffer.tell()


def get_file_size(file_path: str) -> int:
    """get file size in bytes"""
    return os.path.getsize(file_path)


def format_file_size(size_bytes: int) -> str:
    """format file size as human readable string"""
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        size_kb = size_bytes / 1024
        return f"{size_kb:.1f} KB"
    else:
        size_mb = size_bytes / (1024 * 1024)
        return f"{size_mb:.2f} MB"


def calculate_savings_percentage(original_size: int, compressed_size: int) -> float:
    """calculate percentage savings from compression"""
    if original_size == 0:
        return 0.0
    return ((original_size - compressed_size) / original_size) * 100


def pil_to_photoimage(image: Image.Image) -> ImageTk.PhotoImage:
    """convert PIL image to tkinter PhotoImage"""
    return ImageTk.PhotoImage(image)


def resize_for_preview(
    image: Image.Image, 
    max_width: int = 700, 
    max_height: int = 500
) -> Image.Image:
    """resize image to fit in preview area"""
    width, height = image.size
    
    if width <= max_width and height <= max_height:
        return image
    
    scale = min(max_width / width, max_height / height)
    new_width = int(width * scale)
    new_height = int(height * scale)
    
    return image.resize((new_width, new_height), Image.LANCZOS)


def validate_image_file(file_path: str) -> bool:
    """check if file is a valid image"""
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except Exception:
        return False


def find_nearest_color_lab(
    pixel_rgb: np.ndarray,
    palette_rgb: np.ndarray,
    palette_lab: Optional[np.ndarray] = None
) -> Tuple[int, int, int]:
    """find nearest palette color using LAB color space"""
    if HAS_SKIMAGE and palette_lab is not None:
        pixel_normalized = pixel_rgb.reshape(1, 1, 3).astype(np.float32) / 255.0
        pixel_lab = skimage_color.rgb2lab(pixel_normalized).flatten()
        
        distances = np.linalg.norm(palette_lab - pixel_lab, axis=1)
        nearest_idx = np.argmin(distances)
    else:
        nearest_idx = find_nearest_color_weighted_rgb(pixel_rgb, palette_rgb)
    
    return tuple(palette_rgb[nearest_idx])


def find_nearest_color_weighted_rgb(
    pixel_rgb: np.ndarray,
    palette_rgb: np.ndarray
) -> int:
    """find nearest color using weighted rgb (green weighted more)"""
    weights = np.array([2, 4, 3], dtype=np.float32)
    
    diff = palette_rgb.astype(np.float32) - pixel_rgb.astype(np.float32)
    distances = np.sum(weights * (diff ** 2), axis=1)
    
    return np.argmin(distances)


def find_nearest_color_bulk(
    pixels: np.ndarray,
    palette_rgb: np.ndarray
) -> np.ndarray:
    """find nearest colors for all pixels at once"""
    palette_lab = _get_lab_palette()
    
    if HAS_SKIMAGE and palette_lab is not None:
        pixels_normalized = pixels.astype(np.float32) / 255.0
        pixels_lab = skimage_color.rgb2lab(pixels_normalized.reshape(-1, 1, 3)).reshape(-1, 3)
        
        distances = np.linalg.norm(
            pixels_lab[:, np.newaxis, :] - palette_lab[np.newaxis, :, :],
            axis=2
        )
        
        nearest_indices = np.argmin(distances, axis=1)
        
        return palette_rgb[nearest_indices]
    else:
        weights = np.array([2, 4, 3], dtype=np.float32)
        
        diff = pixels[:, np.newaxis, :].astype(np.float32) - palette_rgb[np.newaxis, :, :].astype(np.float32)
        distances = np.sum(weights * (diff ** 2), axis=2)
        
        nearest_indices = np.argmin(distances, axis=1)
        return palette_rgb[nearest_indices]


SUPPORTED_IMAGE_FORMATS = [
    ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.jxl *.webp"),
    ("JPEG XL files", "*.jxl"),
    ("WebP files", "*.webp"),
    ("All files", "*.*")
]
