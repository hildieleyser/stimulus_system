#!/usr/bin/env python3
"""
Master script for setting up all experimental stimuli.

Orchestrates generation of abstract stimuli and provides guidance for dataset integration.
"""

import argparse
import sys
from pathlib import Path

# Import local generators
try:
    from generate_abstract_visual import generate_tier1_stimuli as gen_visual
    from generate_abstract_audio import generate_tier1_audio as gen_audio
except ImportError:
    # Try relative import if run as module
    from .generate_abstract_visual import generate_tier1_stimuli as gen_visual
    from .generate_abstract_audio import generate_tier1_audio as gen_audio


def setup_tier1(categories, output_dir, n_stimuli=10):
    """Generate Tier 1 abstract stimuli."""
    print("\n" + "=" * 70)
    print("TIER 1: ABSTRACT STIMULI")
    print("=" * 70)

    # Generate visual stimuli (Gabor patches + geometric shapes)
    gen_visual(
        categories=categories,
        output_dir=output_dir,
        n_per_category=n_stimuli,
        stimulus_type='both'
    )

    # Generate audio stimuli (harmonic complexes, noise, AM tones)
    gen_audio(
        categories=categories,
        output_dir=output_dir,
        n_per_category=n_stimuli,
        duration=0.5,
        tone_types=['harmonic', 'noise', 'am']
    )

    print("\n✓ Tier 1 complete")


def show_tier2_instructions():
    """Display instructions for Tier 2 dataset integration."""
    print("\n" + "=" * 70)
    print("TIER 2: SINGLE OBJECTS & ENVIRONMENTAL SOUNDS")
    print("=" * 70)

    print("""
For Tier 2, you'll need naturalistic stimuli:

VISUAL (Images):
  Source: ImageNet, COCO, or custom photography
  Requirements:
    - Isolated objects on neutral backgrounds
    - Consistent resolution (suggested: 400x400px)
    - Format: PNG or JPG
  Organization:
    stimuli/images/<category>/tier2/<category>_2_<N>.png

  Example sources:
    - ImageNet: https://www.image-net.org/
    - COCO Dataset: https://cocodataset.org/
    - Flickr Creative Commons

AUDITORY (Sounds):
  Source: ESC-50, FSD50K, or field recordings
  Requirements:
    - Environmental sounds (dog barks, car engines, etc.)
    - Duration: 1-2 seconds
    - Format: WAV (44.1kHz recommended)
  Organization:
    stimuli/audio/<category>/environmental/<category>_sound_<N>.wav

  Example sources:
    - ESC-50: https://github.com/karolpiczak/ESC-50
    - FSD50K: https://zenodo.org/record/4060432
    - Freesound: https://freesound.org/

Manual Integration Steps:
  1. Download datasets
  2. Filter by your categories
  3. Rename and organize into directory structure above
  4. Run validation: python run_experiment.py --dry-run
""")


def show_tier3_instructions():
    """Display instructions for Tier 3 stimuli."""
    print("\n" + "=" * 70)
    print("TIER 3: OBJECTS IN CONTEXT & SPOKEN WORDS")
    print("=" * 70)

    print("""
For Tier 3, you'll need contextual stimuli:

VISUAL (Scenes):
  Source: COCO, Places365, or photography
  Requirements:
    - Objects in simple scene context
    - Clear main subject
    - Format: PNG or JPG
  Organization:
    stimuli/images/<category>/tier3/<category>_3_<N>.png

AUDITORY (Words):
  Source: Auto-generated via TTS or speech recordings
  Requirements:
    - Spoken category labels
    - Clear pronunciation
    - Format: WAV
  Organization:
    stimuli/audio/<category>/words/<category>_word_<N>.wav

  TTS Generation:
    The system can auto-generate these!
    Set in config.yaml:
      generate_words_tts: true

  Or record manually:
    - Use consistent speaker
    - Neutral tone
    - Minimal background noise
""")


def show_tier4_instructions():
    """Display instructions for Tier 4 stimuli."""
    print("\n" + "=" * 70)
    print("TIER 4: NATURALISTIC SCENES & SENTENCES")
    print("=" * 70)

    print("""
For Tier 4, you'll need complex naturalistic stimuli:

VISUAL (Complex Scenes):
  Source: COCO, Places365, or photography
  Requirements:
    - Rich naturalistic scenes
    - Multiple objects/elements
    - Real-world complexity
    - Format: PNG or JPG
  Organization:
    stimuli/images/<category>/tier4/<category>_4_<N>.png

AUDITORY (Sentences):
  Source: TTS or speech recordings
  Requirements:
    - Descriptive sentences about category
    - Natural prosody
    - Format: WAV
  Organization:
    stimuli/audio/<category>/sentences/<category>_sentence_<N>.wav

  Example sentences:
    - "The dog is running through the grass"
    - "A red car drives down the street"
    - "She picks up the ripe red apple"

  TTS Generation:
    Edit your category labels to full sentences
    The system can generate via gTTS
""")


def validate_setup(output_dir):
    """Validate stimulus directory structure."""
    print("\n" + "=" * 70)
    print("VALIDATION")
    print("=" * 70)

    base = Path(output_dir)
    issues = []

    # Check base directories
    if not (base / 'images').exists():
        issues.append("Missing images/ directory")
    if not (base / 'audio').exists():
        issues.append("Missing audio/ directory")

    # Check tier 1
    if (base / 'audio' / 'tones').exists():
        n_tones = len(list((base / 'audio' / 'tones').glob('*.wav')))
        print(f"✓ Tier 1 audio: {n_tones} files in tones/")
    else:
        issues.append("Missing Tier 1 audio (tones/ directory)")

    if issues:
        print("\n⚠ Issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n✓ Stimulus directory structure valid")

    print("\nTo complete validation, run:")
    print("  python run_experiment.py --dry-run")


def main():
    """Main entry point for stimulus setup."""
    parser = argparse.ArgumentParser(
        description='Setup experimental stimuli',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate Tier 1 abstract stimuli only
  python setup_stimuli.py --tiers 1 --categories dog,car,apple,chair

  # Show instructions for all tiers
  python setup_stimuli.py --tiers 1,2,3,4 --instructions-only

  # Validate existing stimuli
  python setup_stimuli.py --validate-only
        """
    )

    parser.add_argument(
        '--tiers',
        type=str,
        default='1',
        help='Comma-separated tiers to setup (default: 1)'
    )

    parser.add_argument(
        '--categories',
        type=str,
        default='dog,car,apple,chair',
        help='Comma-separated category list'
    )

    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('../stimuli'),
        help='Output directory (default: ../stimuli/)'
    )

    parser.add_argument(
        '--n-stimuli',
        type=int,
        default=10,
        help='Number of stimuli per category (default: 10)'
    )

    parser.add_argument(
        '--instructions-only',
        action='store_true',
        help='Show instructions without generating stimuli'
    )

    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Validate existing stimulus directory'
    )

    args = parser.parse_args()

    # Parse arguments
    tiers = [int(t.strip()) for t in args.tiers.split(',')]
    categories = [c.strip() for c in args.categories.split(',')]

    print("=" * 70)
    print("STIMULUS SETUP TOOL")
    print("=" * 70)
    print(f"\nTiers: {tiers}")
    print(f"Categories: {categories}")
    print(f"Output: {args.output_dir}")

    # Validate only mode
    if args.validate_only:
        validate_setup(args.output_dir)
        sys.exit(0)

    # Generate Tier 1
    if 1 in tiers and not args.instructions_only:
        setup_tier1(categories, args.output_dir, args.n_stimuli)

    # Show instructions for higher tiers
    if 2 in tiers:
        show_tier2_instructions()

    if 3 in tiers:
        show_tier3_instructions()

    if 4 in tiers:
        show_tier4_instructions()

    print("\n" + "=" * 70)
    print("SETUP COMPLETE")
    print("=" * 70)

    if not args.instructions_only:
        print("\nNext steps:")
        print("  1. Review generated Tier 1 stimuli")
        print("  2. Follow instructions above for higher tiers")
        print("  3. Run validation: python run_experiment.py --dry-run")
    else:
        print("\nFollow the instructions above to complete stimulus setup.")


if __name__ == '__main__':
    main()
