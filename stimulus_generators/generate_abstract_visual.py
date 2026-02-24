#!/usr/bin/env python3
"""
Generate abstract visual stimuli for Tier 1.

Creates procedural Gabor patches and geometric shapes with category-specific parameters.
"""

import argparse
import numpy as np
from PIL import Image, ImageDraw
from pathlib import Path
from typing import List, Tuple
import random


def generate_gabor_patch(size: Tuple[int, int] = (400, 400),
                        frequency: float = 0.05,
                        theta: float = 0.0,
                        sigma: float = 80.0,
                        phase: float = 0.0,
                        contrast: float = 1.0) -> np.ndarray:
    """
    Generate a Gabor patch stimulus.

    Args:
        size: Image size (width, height) in pixels
        frequency: Spatial frequency of sinusoid
        theta: Orientation in radians (0 = horizontal)
        sigma: Standard deviation of Gaussian envelope
        phase: Phase offset of sinusoid
        contrast: Contrast multiplier (0-1)

    Returns:
        Numpy array with Gabor patch (grayscale, 0-255)
    """
    width, height = size
    x = np.linspace(-width // 2, width // 2, width)
    y = np.linspace(-height // 2, height // 2, height)
    X, Y = np.meshgrid(x, y)

    # Rotate coordinates
    x_theta = X * np.cos(theta) + Y * np.sin(theta)
    y_theta = -X * np.sin(theta) + Y * np.cos(theta)

    # Gaussian envelope
    gaussian = np.exp(-(x_theta**2 + y_theta**2) / (2 * sigma**2))

    # Sinusoidal grating
    sinusoid = np.cos(2 * np.pi * frequency * x_theta + phase)

    # Gabor patch (Gaussian * sinusoid)
    gabor = gaussian * sinusoid * contrast

    # Normalize to 0-255 range
    gabor = ((gabor + 1) / 2 * 255).astype(np.uint8)

    return gabor


def generate_geometric_shape(size: Tuple[int, int] = (400, 400),
                             shape_type: str = 'circle',
                             shape_size: float = 0.5,
                             rotation: float = 0.0,
                             fill_color: int = 128) -> np.ndarray:
    """
    Generate a simple geometric shape.

    Args:
        size: Image size (width, height) in pixels
        shape_type: Type of shape ('circle', 'square', 'triangle', 'diamond')
        shape_size: Size as proportion of image (0-1)
        rotation: Rotation angle in degrees
        fill_color: Grayscale fill value (0-255)

    Returns:
        Numpy array with geometric shape (grayscale, 0-255)
    """
    width, height = size
    img = Image.new('L', size, color=200)  # Light gray background
    draw = ImageDraw.Draw(img)

    # Calculate shape bounds
    center_x, center_y = width // 2, height // 2
    shape_width = int(width * shape_size)
    shape_height = int(height * shape_size)

    half_w = shape_width // 2
    half_h = shape_height // 2

    if shape_type == 'circle':
        # Draw circle/ellipse
        bbox = [center_x - half_w, center_y - half_h,
                center_x + half_w, center_y + half_h]
        draw.ellipse(bbox, fill=fill_color)

    elif shape_type == 'square':
        # Draw square/rectangle
        bbox = [center_x - half_w, center_y - half_h,
                center_x + half_w, center_y + half_h]
        draw.rectangle(bbox, fill=fill_color)

    elif shape_type == 'triangle':
        # Draw triangle pointing up
        points = [
            (center_x, center_y - half_h),  # Top
            (center_x - half_w, center_y + half_h),  # Bottom left
            (center_x + half_w, center_y + half_h)   # Bottom right
        ]
        draw.polygon(points, fill=fill_color)

    elif shape_type == 'diamond':
        # Draw diamond (rotated square)
        points = [
            (center_x, center_y - half_h),  # Top
            (center_x + half_w, center_y),  # Right
            (center_x, center_y + half_h),  # Bottom
            (center_x - half_w, center_y)   # Left
        ]
        draw.polygon(points, fill=fill_color)

    # Apply rotation if specified
    if rotation != 0:
        img = img.rotate(rotation, fillcolor=200, expand=False)

    return np.array(img)


def generate_category_specific_gabor(category: str, variant: int,
                                     size: Tuple[int, int] = (400, 400)) -> np.ndarray:
    """
    Generate category-specific Gabor patch using category as seed.

    Args:
        category: Category name (used for reproducible parameters)
        variant: Variant number (0-based)
        size: Image size

    Returns:
        Gabor patch as numpy array
    """
    # Use category + variant as seed for reproducibility
    seed = hash(f"{category}_{variant}") % (2**32)
    rng = random.Random(seed)

    # Category-specific parameter ranges
    frequency = rng.uniform(0.03, 0.08)  # Spatial frequency
    theta = rng.uniform(0, np.pi)  # Orientation
    sigma = rng.uniform(60, 100)  # Envelope size
    phase = rng.uniform(0, 2 * np.pi)  # Phase
    contrast = rng.uniform(0.7, 1.0)  # Contrast

    return generate_gabor_patch(size, frequency, theta, sigma, phase, contrast)


def generate_category_specific_shape(category: str, variant: int,
                                     size: Tuple[int, int] = (400, 400)) -> np.ndarray:
    """
    Generate category-specific geometric shape using category as seed.

    Args:
        category: Category name (used for reproducible parameters)
        variant: Variant number (0-based)
        size: Image size

    Returns:
        Geometric shape as numpy array
    """
    # Use category + variant as seed
    seed = hash(f"{category}_{variant}") % (2**32)
    rng = random.Random(seed)

    # Map category to shape types (deterministic but varied)
    shapes = ['circle', 'square', 'triangle', 'diamond']
    shape_type = shapes[hash(category) % len(shapes)]

    # Vary size and rotation per variant
    shape_size = rng.uniform(0.4, 0.7)
    rotation = rng.uniform(0, 360)
    fill_color = rng.randint(40, 160)  # Dark to medium gray

    return generate_geometric_shape(size, shape_type, shape_size, rotation, fill_color)


def generate_tier1_stimuli(categories: List[str],
                           output_dir: Path,
                           n_per_category: int = 10,
                           stimulus_type: str = 'both'):
    """
    Generate all Tier 1 abstract visual stimuli.

    Args:
        categories: List of category names
        output_dir: Base output directory (stimuli/)
        n_per_category: Number of variants per category
        stimulus_type: 'gabor', 'shapes', or 'both'
    """
    print("=" * 60)
    print("GENERATING TIER 1 ABSTRACT VISUAL STIMULI")
    print("=" * 60)

    for category in categories:
        print(f"\nCategory: {category}")

        # Create category/tier1 directory
        category_dir = output_dir / 'images' / category / 'tier1'
        category_dir.mkdir(parents=True, exist_ok=True)

        n_generated = 0

        # Generate Gabor patches
        if stimulus_type in ['gabor', 'both']:
            n_gabor = n_per_category // 2 if stimulus_type == 'both' else n_per_category

            for i in range(n_gabor):
                gabor = generate_category_specific_gabor(category, i)
                img = Image.fromarray(gabor, mode='L')

                filename = category_dir / f"{category}_1_gabor_{i+1}.png"
                img.save(filename)
                n_generated += 1

            print(f"  Generated {n_gabor} Gabor patches")

        # Generate geometric shapes
        if stimulus_type in ['shapes', 'both']:
            n_shapes = n_per_category // 2 if stimulus_type == 'both' else n_per_category

            for i in range(n_shapes):
                shape = generate_category_specific_shape(category, i)
                img = Image.fromarray(shape, mode='L')

                filename = category_dir / f"{category}_1_shape_{i+1}.png"
                img.save(filename)
                n_generated += 1

            print(f"  Generated {n_shapes} geometric shapes")

        print(f"  Total: {n_generated} stimuli → {category_dir}")

    print("\n" + "=" * 60)
    print("TIER 1 VISUAL STIMULI GENERATION COMPLETE")
    print("=" * 60)


def main():
    """Command-line interface for abstract visual stimulus generation."""
    parser = argparse.ArgumentParser(
        description='Generate abstract visual stimuli for Tier 1',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--categories',
        type=str,
        default='dog,car,apple,chair',
        help='Comma-separated list of categories'
    )

    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('stimuli'),
        help='Base output directory (default: stimuli/)'
    )

    parser.add_argument(
        '--n-per-category',
        type=int,
        default=10,
        help='Number of stimuli per category (default: 10)'
    )

    parser.add_argument(
        '--type',
        choices=['gabor', 'shapes', 'both'],
        default='both',
        help='Type of stimuli to generate (default: both)'
    )

    args = parser.parse_args()

    # Parse categories
    categories = [c.strip() for c in args.categories.split(',')]

    # Generate stimuli
    generate_tier1_stimuli(
        categories=categories,
        output_dir=args.output_dir,
        n_per_category=args.n_per_category,
        stimulus_type=args.type
    )


if __name__ == '__main__':
    main()
