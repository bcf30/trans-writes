"""
transforms.py - image transformation algorithms

uses an expanded trans flag palette with perceptually uniform color matching.
has numba jit for speed, falls back to numpy if not available.
"""

from typing import List, Tuple
import numpy as np
from PIL import Image

from utils import (
    TRANS_PALETTE,
    INVERTED_PALETTE,
    find_nearest_color_bulk,
    HAS_SKIMAGE
)

# numba is optional but gives big speedup
try:
    from numba import jit, prange
    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False
    def jit(*args, **kwargs):
        def decorator(func):
            return func
        if len(args) == 1 and callable(args[0]):
            return args[0]
        return decorator
    prange = range


# bayer matrix for ordered dithering
BAYER_MATRIX = np.array([
    [ 0,  8,  2, 10],
    [12,  4, 14,  6],
    [ 3, 11,  1,  9],
    [15,  7, 13,  5]
], dtype=np.float32) / 16.0

# cached palette arrays for performance
_TRANS_PALETTE_ARRAY = np.array(TRANS_PALETTE, dtype=np.uint8)
_INVERTED_PALETTE_ARRAY = np.array(INVERTED_PALETTE, dtype=np.uint8)


@jit(nopython=True, cache=True)
def _find_nearest_color_idx_rgb(pixel: np.ndarray, palette: np.ndarray) -> int:
    """find nearest color using weighted rgb distance"""
    min_dist = float('inf')
    best_idx = 0
    
    weights_r, weights_g, weights_b = 2.0, 4.0, 3.0
    
    for i in range(len(palette)):
        dr = pixel[0] - palette[i, 0]
        dg = pixel[1] - palette[i, 1]
        db = pixel[2] - palette[i, 2]
        dist = weights_r * dr * dr + weights_g * dg * dg + weights_b * db * db
        
        if dist < min_dist:
            min_dist = dist
            best_idx = i
    
    return best_idx


@jit(nopython=True, parallel=True, cache=True)
def _apply_palette_numba(pixels: np.ndarray, palette: np.ndarray) -> np.ndarray:
    """apply palette to all pixels in parallel"""
    height, width = pixels.shape[:2]
    output = np.empty((height, width, 3), dtype=np.uint8)
    
    for y in prange(height):
        for x in range(width):
            idx = _find_nearest_color_idx_rgb(pixels[y, x], palette)
            output[y, x, 0] = palette[idx, 0]
            output[y, x, 1] = palette[idx, 1]
            output[y, x, 2] = palette[idx, 2]
    
    return output


@jit(nopython=True, cache=True)
def _dither_floyd_steinberg_numba(pixels: np.ndarray, palette: np.ndarray) -> np.ndarray:
    """floyd-steinberg dithering"""
    height, width = pixels.shape[:2]
    result = pixels.astype(np.float32).copy()
    
    for y in range(height):
        for x in range(width):
            old_pixel = result[y, x].copy()
            
            idx = _find_nearest_color_idx_rgb(old_pixel, palette)
            new_pixel = palette[idx].astype(np.float32)
            result[y, x] = new_pixel
            
            error = old_pixel - new_pixel
            
            # distribute error to neighbors
            if x + 1 < width:
                result[y, x + 1] += error * (7.0 / 16.0)
            if y + 1 < height:
                if x > 0:
                    result[y + 1, x - 1] += error * (3.0 / 16.0)
                result[y + 1, x] += error * (5.0 / 16.0)
                if x + 1 < width:
                    result[y + 1, x + 1] += error * (1.0 / 16.0)
    
    return np.clip(result, 0, 255).astype(np.uint8)


@jit(nopython=True, cache=True)
def _dither_atkinson_numba(pixels: np.ndarray, palette: np.ndarray) -> np.ndarray:
    """atkinson dithering"""
    height, width = pixels.shape[:2]
    result = pixels.astype(np.float32).copy()
    
    for y in range(height):
        for x in range(width):
            old_pixel = result[y, x].copy()
            
            idx = _find_nearest_color_idx_rgb(old_pixel, palette)
            new_pixel = palette[idx].astype(np.float32)
            result[y, x] = new_pixel
            
            error = old_pixel - new_pixel
            
            # atkinson pattern - 1/8 to each of 6 neighbors
            if x + 1 < width:
                result[y, x + 1] += error * (1.0 / 8.0)
            if x + 2 < width:
                result[y, x + 2] += error * (1.0 / 8.0)
            if y + 1 < height:
                if x > 0:
                    result[y + 1, x - 1] += error * (1.0 / 8.0)
                result[y + 1, x] += error * (1.0 / 8.0)
                if x + 1 < width:
                    result[y + 1, x + 1] += error * (1.0 / 8.0)
            if y + 2 < height:
                result[y + 2, x] += error * (1.0 / 8.0)
    
    return np.clip(result, 0, 255).astype(np.uint8)


@jit(nopython=True, parallel=True, cache=True)
def _dither_ordered_numba(pixels: np.ndarray, palette: np.ndarray, bayer: np.ndarray) -> np.ndarray:
    """ordered (bayer) dithering - parallelized"""
    height, width = pixels.shape[:2]
    output = np.empty((height, width, 3), dtype=np.uint8)
    
    for y in prange(height):
        for x in range(width):
            threshold = bayer[y % 4, x % 4]
            offset = (threshold - 0.5) * 64.0
            adjusted = pixels[y, x].astype(np.float32) + offset
            
            idx = _find_nearest_color_idx_rgb(adjusted, palette)
            output[y, x, 0] = palette[idx, 0]
            output[y, x, 1] = palette[idx, 1]
            output[y, x, 2] = palette[idx, 2]
    
    return output


def apply_trans_palette(image: Image.Image, palette: list = None) -> Image.Image:
    """reduce image to trans flag palette (7 colors)"""
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    pixels = np.array(image)
    palette_array = np.array(palette, dtype=np.uint8) if palette else _TRANS_PALETTE_ARRAY
    
    if HAS_NUMBA:
        output = _apply_palette_numba(pixels, palette_array)
    else:
        height, width = pixels.shape[:2]
        pixels_flat = pixels.reshape(-1, 3)
        output_flat = find_nearest_color_bulk(pixels_flat, palette_array)
        output = output_flat.reshape(height, width, 3).astype(np.uint8)
    
    return Image.fromarray(output, mode='RGB')


def dither_floyd_steinberg(image: Image.Image, palette: list = None) -> Image.Image:
    """floyd-steinberg dithering"""
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    pixels = np.array(image, dtype=np.uint8)
    palette_array = np.array(palette, dtype=np.uint8) if palette else _TRANS_PALETTE_ARRAY
    
    if HAS_NUMBA:
        output = _dither_floyd_steinberg_numba(pixels, palette_array)
    else:
        output = _dither_floyd_steinberg_fallback(image, palette_array)
    
    return Image.fromarray(output, mode='RGB')


def _dither_floyd_steinberg_fallback(image: Image.Image, palette: np.ndarray) -> np.ndarray:
    """floyd-steinberg without numba"""
    pixels = np.array(image, dtype=np.float32)
    height, width = pixels.shape[:2]
    
    for y in range(height):
        for x in range(width):
            old_pixel = pixels[y, x].copy()
            idx = _find_nearest_color_idx_rgb(old_pixel, palette)
            new_pixel = palette[idx].astype(np.float32)
            pixels[y, x] = new_pixel
            
            error = old_pixel - new_pixel
            
            if x + 1 < width:
                pixels[y, x + 1] += error * (7/16)
            if y + 1 < height:
                if x > 0:
                    pixels[y + 1, x - 1] += error * (3/16)
                pixels[y + 1, x] += error * (5/16)
                if x + 1 < width:
                    pixels[y + 1, x + 1] += error * (1/16)
    
    return np.clip(pixels, 0, 255).astype(np.uint8)


def dither_atkinson(image: Image.Image, palette: list = None) -> Image.Image:
    """atkinson dithering"""
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    pixels = np.array(image, dtype=np.uint8)
    palette_array = np.array(palette, dtype=np.uint8) if palette else _TRANS_PALETTE_ARRAY
    
    if HAS_NUMBA:
        output = _dither_atkinson_numba(pixels, palette_array)
    else:
        output = _dither_atkinson_fallback(image, palette_array)
    
    return Image.fromarray(output, mode='RGB')


def _dither_atkinson_fallback(image: Image.Image, palette: np.ndarray) -> np.ndarray:
    """atkinson without numba"""
    pixels = np.array(image, dtype=np.float32)
    height, width = pixels.shape[:2]
    
    for y in range(height):
        for x in range(width):
            old_pixel = pixels[y, x].copy()
            idx = _find_nearest_color_idx_rgb(old_pixel, palette)
            new_pixel = palette[idx].astype(np.float32)
            pixels[y, x] = new_pixel
            
            error = old_pixel - new_pixel
            
            if x + 1 < width:
                pixels[y, x + 1] += error * (1/8)
            if x + 2 < width:
                pixels[y, x + 2] += error * (1/8)
            if y + 1 < height:
                if x > 0:
                    pixels[y + 1, x - 1] += error * (1/8)
                pixels[y + 1, x] += error * (1/8)
                if x + 1 < width:
                    pixels[y + 1, x + 1] += error * (1/8)
            if y + 2 < height:
                pixels[y + 2, x] += error * (1/8)
    
    return np.clip(pixels, 0, 255).astype(np.uint8)


def dither_ordered(image: Image.Image, palette: list = None) -> Image.Image:
    """ordered (bayer 4x4) dithering"""
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    pixels = np.array(image, dtype=np.uint8)
    palette_array = np.array(palette, dtype=np.uint8) if palette else _TRANS_PALETTE_ARRAY
    
    if HAS_NUMBA:
        output = _dither_ordered_numba(pixels, palette_array, BAYER_MATRIX)
    else:
        output = _dither_ordered_fallback(pixels, palette_array)
    
    return Image.fromarray(output, mode='RGB')


def _dither_ordered_fallback(pixels: np.ndarray, palette: np.ndarray) -> np.ndarray:
    """ordered dithering without numba"""
    height, width = pixels.shape[:2]
    output = np.zeros_like(pixels, dtype=np.uint8)
    
    for y in range(height):
        for x in range(width):
            threshold = BAYER_MATRIX[y % 4, x % 4]
            offset = (threshold - 0.5) * 64
            adjusted = pixels[y, x].astype(np.float32) + offset
            idx = _find_nearest_color_idx_rgb(adjusted, palette)
            output[y, x] = palette[idx]
    
    return output


def pixelate(image: Image.Image, block_size: int) -> Image.Image:
    """pixelate using nearest-neighbor resampling"""
    if block_size <= 1:
        return image.copy()
    
    width, height = image.size
    small_w = max(1, width // block_size)
    small_h = max(1, height // block_size)
    
    small = image.resize((small_w, small_h), Image.NEAREST)
    return small.resize((width, height), Image.NEAREST)


def apply_transforms(
    image: Image.Image,
    dithering: str = 'none',
    pixelation: int = 1,
    invert: bool = False
) -> Image.Image:
    """apply all transformations - dithering then pixelation"""
    # use cached palette arrays for performance
    if invert:
        palette_array = _INVERTED_PALETTE_ARRAY
        palette_list = INVERTED_PALETTE
    else:
        palette_array = _TRANS_PALETTE_ARRAY
        palette_list = None  # None means use default (TRANS_PALETTE)
    
    if image.mode != 'RGB':
        result = image.convert('RGB')
    else:
        result = image.copy()
    
    if dithering == 'floyd_steinberg':
        result = dither_floyd_steinberg(result, palette_list if invert else None)
    elif dithering == 'atkinson':
        result = dither_atkinson(result, palette_list if invert else None)
    elif dithering == 'ordered':
        result = dither_ordered(result, palette_list if invert else None)
    else:
        result = apply_trans_palette(result, palette_list if invert else None)
    
    # apply pixelation
    if pixelation > 1:
        result = pixelate(result, pixelation)
    
    return result


def get_palette_info() -> dict:
    """get info about the current palette"""
    return {
        'num_colors': len(TRANS_PALETTE),
        'colors': TRANS_PALETTE,
        'has_skimage': HAS_SKIMAGE,
        'has_numba': HAS_NUMBA,
        'color_matching': 'LAB (perceptually uniform)' if HAS_SKIMAGE else 'Weighted RGB',
        'optimization': 'Numba JIT' if HAS_NUMBA else 'NumPy'
    }
