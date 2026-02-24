#!/usr/bin/env python3
"""
Generate abstract audio stimuli for Tier 1.

Creates procedural harmonic complexes, noise bursts, and amplitude-modulated tones
with category-specific parameters.
"""

import argparse
import numpy as np
import soundfile as sf
from pathlib import Path
from typing import List, Tuple
import random


def generate_pure_tone(frequency: float,
                       duration: float,
                       sample_rate: int = 44100,
                       amplitude: float = 0.3) -> np.ndarray:
    """
    Generate a pure sine wave tone.

    Args:
        frequency: Frequency in Hz
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        amplitude: Amplitude (0-1)

    Returns:
        Audio signal as numpy array
    """
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    signal = amplitude * np.sin(2 * np.pi * frequency * t)

    # Apply fade in/out
    fade_samples = int(sample_rate * 0.01)  # 10ms fade
    fade_in = np.linspace(0, 1, fade_samples)
    fade_out = np.linspace(1, 0, fade_samples)

    signal[:fade_samples] *= fade_in
    signal[-fade_samples:] *= fade_out

    return signal.astype(np.float32)


def generate_harmonic_complex(fundamental: float,
                              n_harmonics: int,
                              harmonic_amplitudes: List[float],
                              duration: float,
                              sample_rate: int = 44100) -> np.ndarray:
    """
    Generate a harmonic complex tone.

    Args:
        fundamental: Fundamental frequency in Hz
        n_harmonics: Number of harmonics to include
        harmonic_amplitudes: Amplitude for each harmonic
        duration: Duration in seconds
        sample_rate: Sample rate in Hz

    Returns:
        Audio signal as numpy array
    """
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    signal = np.zeros_like(t)

    # Sum harmonics
    for i in range(min(n_harmonics, len(harmonic_amplitudes))):
        frequency = fundamental * (i + 1)
        amplitude = harmonic_amplitudes[i]
        signal += amplitude * np.sin(2 * np.pi * frequency * t)

    # Normalize
    signal = signal / np.max(np.abs(signal)) * 0.3

    # Apply fade in/out
    fade_samples = int(sample_rate * 0.01)
    fade_in = np.linspace(0, 1, fade_samples)
    fade_out = np.linspace(1, 0, fade_samples)

    signal[:fade_samples] *= fade_in
    signal[-fade_samples:] *= fade_out

    return signal.astype(np.float32)


def generate_noise_burst(center_freq: float,
                        bandwidth: float,
                        duration: float,
                        sample_rate: int = 44100,
                        amplitude: float = 0.3) -> np.ndarray:
    """
    Generate a band-limited noise burst.

    Args:
        center_freq: Center frequency in Hz
        bandwidth: Bandwidth in Hz
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        amplitude: Amplitude (0-1)

    Returns:
        Audio signal as numpy array
    """
    n_samples = int(sample_rate * duration)

    # Generate white noise
    noise = np.random.randn(n_samples)

    # Design bandpass filter using FFT
    fft = np.fft.rfft(noise)
    freqs = np.fft.rfftfreq(n_samples, 1 / sample_rate)

    # Create bandpass mask
    low_freq = center_freq - bandwidth / 2
    high_freq = center_freq + bandwidth / 2
    mask = (freqs >= low_freq) & (freqs <= high_freq)

    # Apply filter
    fft_filtered = fft * mask
    signal = np.fft.irfft(fft_filtered, n=n_samples)

    # Normalize
    signal = signal / np.max(np.abs(signal)) * amplitude

    # Apply fade in/out
    fade_samples = int(sample_rate * 0.01)
    fade_in = np.linspace(0, 1, fade_samples)
    fade_out = np.linspace(1, 0, fade_samples)

    signal[:fade_samples] *= fade_in
    signal[-fade_samples:] *= fade_out

    return signal.astype(np.float32)


def generate_am_tone(carrier_freq: float,
                    modulation_freq: float,
                    modulation_depth: float,
                    duration: float,
                    sample_rate: int = 44100,
                    amplitude: float = 0.3) -> np.ndarray:
    """
    Generate an amplitude-modulated tone.

    Args:
        carrier_freq: Carrier frequency in Hz
        modulation_freq: Modulation frequency in Hz
        modulation_depth: Modulation depth (0-1)
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        amplitude: Overall amplitude (0-1)

    Returns:
        Audio signal as numpy array
    """
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

    # Carrier signal
    carrier = np.sin(2 * np.pi * carrier_freq * t)

    # Modulation signal
    modulator = 1 + modulation_depth * np.sin(2 * np.pi * modulation_freq * t)

    # AM signal
    signal = amplitude * carrier * modulator

    # Apply fade in/out
    fade_samples = int(sample_rate * 0.01)
    fade_in = np.linspace(0, 1, fade_samples)
    fade_out = np.linspace(1, 0, fade_samples)

    signal[:fade_samples] *= fade_in
    signal[-fade_samples:] *= fade_out

    return signal.astype(np.float32)


def generate_category_specific_tone(category: str,
                                   variant: int,
                                   duration: float = 0.5,
                                   sample_rate: int = 44100,
                                   tone_type: str = 'harmonic') -> np.ndarray:
    """
    Generate category-specific tone using category as seed.

    Args:
        category: Category name (used for reproducible parameters)
        variant: Variant number (0-based)
        duration: Duration in seconds
        sample_rate: Sample rate
        tone_type: 'harmonic', 'noise', or 'am'

    Returns:
        Audio signal as numpy array
    """
    # Use category + variant as seed
    seed = hash(f"{category}_{variant}_{tone_type}") % (2**32)
    rng = random.Random(seed)
    np.random.seed(seed)

    if tone_type == 'harmonic':
        # Harmonic complex tone
        fundamental = rng.uniform(200, 600)
        n_harmonics = rng.randint(3, 6)

        # Random harmonic amplitudes (decreasing with harmonic number)
        amplitudes = [1.0 / (i + 1) for i in range(n_harmonics)]

        signal = generate_harmonic_complex(
            fundamental, n_harmonics, amplitudes, duration, sample_rate
        )

    elif tone_type == 'noise':
        # Band-limited noise burst
        center_freq = rng.uniform(500, 2000)
        bandwidth = rng.uniform(200, 800)

        signal = generate_noise_burst(
            center_freq, bandwidth, duration, sample_rate
        )

    elif tone_type == 'am':
        # Amplitude-modulated tone
        carrier_freq = rng.uniform(300, 800)
        modulation_freq = rng.uniform(4, 20)
        modulation_depth = rng.uniform(0.3, 0.9)

        signal = generate_am_tone(
            carrier_freq, modulation_freq, modulation_depth, duration, sample_rate
        )

    return signal


def generate_tier1_audio(categories: List[str],
                        output_dir: Path,
                        n_per_category: int = 10,
                        duration: float = 0.5,
                        sample_rate: int = 44100,
                        tone_types: List[str] = None):
    """
    Generate all Tier 1 abstract audio stimuli.

    Args:
        categories: List of category names
        output_dir: Base output directory (stimuli/)
        n_per_category: Number of variants per category
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        tone_types: List of tone types to generate
    """
    if tone_types is None:
        tone_types = ['harmonic', 'noise', 'am']

    print("=" * 60)
    print("GENERATING TIER 1 ABSTRACT AUDIO STIMULI")
    print("=" * 60)

    # Tier 1 audio goes in tones/ directory (shared across categories)
    tones_dir = output_dir / 'audio' / 'tones'
    tones_dir.mkdir(parents=True, exist_ok=True)

    n_per_type = max(1, n_per_category // len(tone_types))

    for category in categories:
        print(f"\nCategory: {category}")
        n_generated = 0

        for tone_type in tone_types:
            for i in range(n_per_type):
                # Generate audio
                signal = generate_category_specific_tone(
                    category, i, duration, sample_rate, tone_type
                )

                # Save to file
                filename = tones_dir / f"{category}_{tone_type}_{i+1}.wav"
                sf.write(filename, signal, sample_rate)
                n_generated += 1

            print(f"  Generated {n_per_type} {tone_type} tones")

        print(f"  Total: {n_generated} stimuli")

    print(f"\n  All Tier 1 audio → {tones_dir}")
    print("\n" + "=" * 60)
    print("TIER 1 AUDIO STIMULI GENERATION COMPLETE")
    print("=" * 60)


def main():
    """Command-line interface for abstract audio stimulus generation."""
    parser = argparse.ArgumentParser(
        description='Generate abstract audio stimuli for Tier 1',
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
        default=9,
        help='Number of stimuli per category (default: 9, 3 per type)'
    )

    parser.add_argument(
        '--duration',
        type=float,
        default=0.5,
        help='Duration in seconds (default: 0.5)'
    )

    parser.add_argument(
        '--sample-rate',
        type=int,
        default=44100,
        help='Sample rate in Hz (default: 44100)'
    )

    parser.add_argument(
        '--types',
        type=str,
        default='harmonic,noise,am',
        help='Comma-separated tone types (default: harmonic,noise,am)'
    )

    args = parser.parse_args()

    # Parse arguments
    categories = [c.strip() for c in args.categories.split(',')]
    tone_types = [t.strip() for t in args.types.split(',')]

    # Generate stimuli
    generate_tier1_audio(
        categories=categories,
        output_dir=args.output_dir,
        n_per_category=args.n_per_category,
        duration=args.duration,
        sample_rate=args.sample_rate,
        tone_types=tone_types
    )


if __name__ == '__main__':
    main()
