#!/usr/bin/env python3

# Copyright 2025 Frank Sommers
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import click
import os
import random
import math
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter

# Intensity presets: (min, max) ranges for each effect
INTENSITY_PRESETS = {
    'low': {
        'rotation': (0.2, 0.7),
        'noise_opacity': (0.02, 0.05),
        'brightness': (0.97, 1.03),
        'contrast': (0.97, 1.03),
        'perspective': (0.001, 0.003),
        'vignette_strength': (0.05, 0.12),
        'regional_blur_prob': 0.15,
        'wrinkle_prob': 0.10,
        'wrinkle_count': (1, 2),
        'wrinkle_amplitude': (1, 3),
    },
    'medium': {
        'rotation': (0.5, 1.5),
        'noise_opacity': (0.04, 0.10),
        'brightness': (0.93, 1.07),
        'contrast': (0.93, 1.07),
        'perspective': (0.003, 0.008),
        'vignette_strength': (0.10, 0.25),
        'regional_blur_prob': 0.30,
        'wrinkle_prob': 0.25,
        'wrinkle_count': (1, 3),
        'wrinkle_amplitude': (2, 5),
    },
    'high': {
        'rotation': (1.0, 2.5),
        'noise_opacity': (0.08, 0.18),
        'brightness': (0.88, 1.12),
        'contrast': (0.88, 1.12),
        'perspective': (0.008, 0.015),
        'vignette_strength': (0.20, 0.40),
        'regional_blur_prob': 0.50,
        'wrinkle_prob': 0.45,
        'wrinkle_count': (2, 4),
        'wrinkle_amplitude': (4, 8),
    },
}


def randomize_params(preset):
    """Pick random values within preset ranges for per-page variation."""
    p = INTENSITY_PRESETS[preset]
    return {
        'rotation_angle': random.uniform(*p['rotation']) * random.choice([-1, 1]),
        'noise_opacity': random.uniform(*p['noise_opacity']),
        'brightness': random.uniform(*p['brightness']),
        'contrast': random.uniform(*p['contrast']),
        'perspective_magnitude': random.uniform(*p['perspective']),
        'vignette_strength': random.uniform(*p['vignette_strength']),
        'vignette_radius': random.uniform(0.7, 0.9),
        'regional_blur_prob': p['regional_blur_prob'],
        'regional_blur_radius': random.uniform(1.5, 3.0),
        'regional_blur_fraction': random.uniform(0.05, 0.15),
        'wrinkle_prob': p['wrinkle_prob'],
        'wrinkle_count': random.randint(*p['wrinkle_count']),
        'wrinkle_amplitude': random.uniform(*p['wrinkle_amplitude']),
    }


def apply_rotation(image, angle, fill_color=(255, 255, 255)):
    """Apply slight random rotation and center-crop back to original size."""
    w, h = image.size
    rotated = image.rotate(angle, resample=Image.BICUBIC, expand=True,
                           fillcolor=fill_color)
    # Center-crop back to original dimensions
    rw, rh = rotated.size
    left = (rw - w) // 2
    top = (rh - h) // 2
    return rotated.crop((left, top, left + w, top + h))


def apply_noise(image, opacity):
    """Apply Gaussian grain noise. Generate at 1/4 resolution and upscale for performance."""
    w, h = image.size
    small_w = max(1, w // 4)
    small_h = max(1, h // 4)

    # Generate small noise image
    noise_pixels = [random.randint(0, 255) for _ in range(small_w * small_h)]
    noise_small = Image.new('L', (small_w, small_h))
    noise_small.putdata(noise_pixels)

    # Upscale to full size for natural-looking grain
    noise_full = noise_small.resize((w, h), Image.BILINEAR)

    # Convert to RGB for blending
    noise_rgb = Image.merge('RGB', [noise_full, noise_full, noise_full])

    # Blend with original
    return Image.blend(image, noise_rgb, opacity)


def apply_brightness_contrast(image, brightness, contrast):
    """Apply brightness and contrast adjustments using ImageEnhance."""
    image = ImageEnhance.Brightness(image).enhance(brightness)
    image = ImageEnhance.Contrast(image).enhance(contrast)
    return image


def find_perspective_coeffs(src, dst):
    """
    Compute perspective transform coefficients from 4 source to 4 destination points.
    Pure-Python 8x8 Gaussian elimination (no numpy dependency).

    src and dst are lists of 4 (x, y) tuples.
    Returns 8 coefficients for Image.transform(PERSPECTIVE).
    """
    # Build the 8x8 system of equations
    matrix = []
    for (x, y), (X, Y) in zip(dst, src):
        matrix.append([x, y, 1, 0, 0, 0, -X * x, -X * y, X])
        matrix.append([0, 0, 0, x, y, 1, -Y * x, -Y * y, Y])

    A = [row[:8] for row in matrix]
    B = [row[8] for row in matrix]

    # Gaussian elimination with partial pivoting
    n = 8
    for col in range(n):
        # Find pivot
        max_row = col
        max_val = abs(A[col][col])
        for row in range(col + 1, n):
            if abs(A[row][col]) > max_val:
                max_val = abs(A[row][col])
                max_row = row
        A[col], A[max_row] = A[max_row], A[col]
        B[col], B[max_row] = B[max_row], B[col]

        pivot = A[col][col]
        if abs(pivot) < 1e-10:
            continue

        for row in range(col + 1, n):
            factor = A[row][col] / pivot
            for j in range(col, n):
                A[row][j] -= factor * A[col][j]
            B[row] -= factor * B[col]

    # Back substitution
    coeffs = [0.0] * n
    for i in range(n - 1, -1, -1):
        s = B[i]
        for j in range(i + 1, n):
            s -= A[i][j] * coeffs[j]
        if abs(A[i][i]) < 1e-10:
            coeffs[i] = 0.0
        else:
            coeffs[i] = s / A[i][i]

    return coeffs


def apply_perspective_warp(image, magnitude):
    """Apply subtle perspective warp with random corner displacements."""
    w, h = image.size

    # Original corners: top-left, top-right, bottom-right, bottom-left
    src = [(0, 0), (w, 0), (w, h), (0, h)]

    # Displace each corner randomly
    max_dx = w * magnitude
    max_dy = h * magnitude
    dst = [
        (random.uniform(0, max_dx), random.uniform(0, max_dy)),
        (w - random.uniform(0, max_dx), random.uniform(0, max_dy)),
        (w - random.uniform(0, max_dx), h - random.uniform(0, max_dy)),
        (random.uniform(0, max_dx), h - random.uniform(0, max_dy)),
    ]

    coeffs = find_perspective_coeffs(src, dst)
    return image.transform((w, h), Image.PERSPECTIVE, coeffs, Image.BICUBIC,
                           fillcolor=(255, 255, 255))


def apply_vignette_fast(image, strength, radius_factor):
    """
    Fast vignette using downscaled mask generation.
    Generates mask at 1/8 resolution and upscales.
    """
    w, h = image.size
    # Generate mask at reduced resolution
    scale = 8
    sw, sh = max(1, w // scale), max(1, h // scale)
    cx, cy = sw / 2, sh / 2

    mask_small = Image.new('L', (sw, sh))
    pixels = []
    for y_pos in range(sh):
        for x_pos in range(sw):
            dx = (x_pos - cx) / cx if cx > 0 else 0
            dy = (y_pos - cy) / cy if cy > 0 else 0
            dist = math.sqrt(dx * dx + dy * dy)
            t = max(0.0, (dist - radius_factor) / (1.4142 - radius_factor))
            t = min(1.0, t)
            pixels.append(int(255 * (1.0 - strength * t)))
    mask_small.putdata(pixels)

    # Upscale to full size
    mask = mask_small.resize((w, h), Image.BILINEAR)

    dark = Image.new('RGB', (w, h), (0, 0, 0))
    return Image.composite(image, dark, mask)


def apply_regional_blur(image, probability, radius, region_fraction):
    """Crop a random horizontal band, blur it, and paste back."""
    if random.random() > probability:
        return image

    w, h = image.size
    band_height = max(1, int(h * region_fraction))
    top = random.randint(0, max(0, h - band_height))
    bottom = min(h, top + band_height)

    band = image.crop((0, top, w, bottom))
    band = band.filter(ImageFilter.GaussianBlur(radius=radius))
    image = image.copy()
    image.paste(band, (0, top))
    return image


def apply_wrinkle(image, num_wrinkles, amplitude, blur_radius=1.5):
    """Simulate paper wrinkles via sinusoidal displacement and brightness modulation."""
    if num_wrinkles <= 0 or amplitude < 0.5:
        return image

    w, h = image.size
    src_pixels = image.load()
    result = image.copy()
    dst_pixels = result.load()

    for _ in range(num_wrinkles):
        # Choose orientation: horizontal or vertical wrinkle
        horizontal = random.random() < 0.5
        # Slight random angle perturbation (radians)
        angle = random.uniform(-0.08, 0.08)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        # Wrinkle center line position and falloff width
        if horizontal:
            center = random.randint(int(h * 0.15), int(h * 0.85))
            falloff = random.randint(int(h * 0.03), int(h * 0.08))
        else:
            center = random.randint(int(w * 0.15), int(w * 0.85))
            falloff = random.randint(int(w * 0.03), int(w * 0.08))

        falloff = max(falloff, 4)
        # Wavelength for the sine displacement along the wrinkle
        wavelength = random.uniform(80, 200)

        for y in range(h):
            for x in range(w):
                # Distance from wrinkle center line (accounting for slight angle)
                if horizontal:
                    dist = (y - center) * cos_a + (x - w / 2) * sin_a
                    along = x
                else:
                    dist = (x - center) * cos_a + (y - h / 2) * sin_a
                    along = y

                abs_dist = abs(dist)
                if abs_dist >= falloff:
                    continue

                # Falloff envelope: strongest at center, zero at edge
                envelope = 1.0 - (abs_dist / falloff)
                envelope = envelope * envelope  # quadratic falloff

                # Sinusoidal displacement perpendicular to wrinkle line
                displacement = amplitude * envelope * math.sin(2 * math.pi * along / wavelength)

                # Compute source coordinate
                if horizontal:
                    sy = y + displacement
                    sx = x
                else:
                    sx = x + displacement
                    sy = y

                # Bilinear sample from source
                sx = max(0.0, min(w - 1.001, float(sx)))
                sy = max(0.0, min(h - 1.001, float(sy)))
                x0 = int(sx)
                y0 = int(sy)
                x1 = min(x0 + 1, w - 1)
                y1 = min(y0 + 1, h - 1)
                fx = sx - x0
                fy = sy - y0

                p00 = src_pixels[x0, y0]
                p10 = src_pixels[x1, y0]
                p01 = src_pixels[x0, y1]
                p11 = src_pixels[x1, y1]

                r = (p00[0] * (1 - fx) * (1 - fy) + p10[0] * fx * (1 - fy) +
                     p01[0] * (1 - fx) * fy + p11[0] * fx * fy)
                g = (p00[1] * (1 - fx) * (1 - fy) + p10[1] * fx * (1 - fy) +
                     p01[1] * (1 - fx) * fy + p11[1] * fx * fy)
                b = (p00[2] * (1 - fx) * (1 - fy) + p10[2] * fx * (1 - fy) +
                     p01[2] * (1 - fx) * fy + p11[2] * fx * fy)

                # Brightness modulation: dark on one side of crease, light on other
                shadow = 0.0
                if abs_dist < falloff * 0.4:
                    sign = 1.0 if dist > 0 else -1.0
                    shadow_envelope = 1.0 - (abs_dist / (falloff * 0.4))
                    shadow = sign * shadow_envelope * 0.06 * 255

                r = max(0, min(255, int(r - shadow)))
                g = max(0, min(255, int(g - shadow)))
                b = max(0, min(255, int(b - shadow)))

                dst_pixels[x, y] = (r, g, b)

        # Update source for next wrinkle so they compound
        src_pixels = result.load()

    return result


def distort_page(image, intensity='medium'):
    """Apply all distortion effects to a single page image with randomized params."""
    params = randomize_params(intensity)

    # Ensure RGB mode
    if image.mode != 'RGB':
        image = image.convert('RGB')

    # Apply effects in sequence
    image = apply_rotation(image, params['rotation_angle'])
    image = apply_perspective_warp(image, params['perspective_magnitude'])
    if random.random() < params['wrinkle_prob']:
        image = apply_wrinkle(image, params['wrinkle_count'],
                              params['wrinkle_amplitude'])
    image = apply_brightness_contrast(image, params['brightness'], params['contrast'])
    image = apply_noise(image, params['noise_opacity'])
    image = apply_vignette_fast(image, params['vignette_strength'],
                                params['vignette_radius'])
    image = apply_regional_blur(image, params['regional_blur_prob'],
                                params['regional_blur_radius'],
                                params['regional_blur_fraction'])

    return image


def distort_pdf(pdf_path, intensity='medium', dpi=200):
    """
    Render PDF pages as images via PyMuPDF, apply distortions, save back as PDF.
    Uses atomic file replacement (.tmp + os.replace) to prevent data loss.
    """
    import fitz  # PyMuPDF

    doc = fitz.open(pdf_path)
    distorted_pages = []

    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(matrix=mat)

        # Convert PyMuPDF pixmap to PIL Image
        img = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)

        # Apply distortions
        img = distort_page(img, intensity)
        distorted_pages.append(img)

    doc.close()

    # Save all pages as a single PDF via Pillow
    if distorted_pages:
        tmp_path = pdf_path + '.tmp'
        first = distorted_pages[0]
        if len(distorted_pages) > 1:
            first.save(tmp_path, 'PDF', save_all=True,
                       append_images=distorted_pages[1:], resolution=dpi)
        else:
            first.save(tmp_path, 'PDF', resolution=dpi)

        # Atomic replacement
        os.replace(tmp_path, pdf_path)


@click.command()
@click.option('--input-dir', '-i', required=True, type=click.Path(exists=True),
              help='Directory containing PDF files to distort')
@click.option('--output-dir', '-o', default=None, type=click.Path(),
              help='Output directory (default: overwrite in place)')
@click.option('--intensity', '-n', default='medium',
              type=click.Choice(['low', 'medium', 'high']),
              help='Distortion intensity preset (default: medium)')
@click.option('--dpi', '-d', default=200, type=int,
              help='DPI for rendering PDF pages (default: 200)')
@click.option('--pattern', default='*.pdf',
              help='Glob pattern for PDF files (default: *.pdf)')
@click.option('--seed', type=int, default=None,
              help='Random seed for reproducible results')
def main(input_dir, output_dir, intensity, dpi, pattern, seed):
    """
    Apply scan-like distortion effects to PDF documents.

    Renders each PDF page as an image, applies randomized distortions
    (rotation, noise, brightness/contrast, perspective warp, vignetting,
    regional blur), and saves back as PDF.

    Examples:

    Distort all PDFs in a directory:
        python distort_scan.py -i output/ -n medium

    High intensity with custom DPI:
        python distort_scan.py -i output/ -n high -d 300

    Reproducible results:
        python distort_scan.py -i output/ -n low --seed 42

    Output to different directory:
        python distort_scan.py -i output/ -o distorted/ -n medium
    """
    if seed is not None:
        random.seed(seed)

    input_path = Path(input_dir)
    pdf_files = sorted(input_path.glob(pattern))

    if not pdf_files:
        click.echo(f"No files matching '{pattern}' found in {input_dir}")
        return

    # If output dir specified, copy files there first
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        import shutil
        out_path = Path(output_dir)
        new_pdf_files = []
        for pdf in pdf_files:
            dest = out_path / pdf.name
            shutil.copy2(pdf, dest)
            new_pdf_files.append(dest)
        pdf_files = new_pdf_files

    click.echo(f"Distorting {len(pdf_files)} PDFs (intensity: {intensity}, dpi: {dpi})")

    for i, pdf_file in enumerate(pdf_files, 1):
        click.echo(f"  [{i}/{len(pdf_files)}] {pdf_file.name}")
        distort_pdf(str(pdf_file), intensity=intensity, dpi=dpi)

    click.echo(f"Done. Distorted {len(pdf_files)} PDFs.")


if __name__ == '__main__':
    main()
