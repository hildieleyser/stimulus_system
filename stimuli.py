"""
Stimulus manifest building, loading, validation, and randomization.

Handles all stimulus file discovery, validation, and assignment to trials.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import random


class StimulusManifest:
    """
    Manages stimulus files and their assignment to experimental trials.

    Attributes:
        stimuli_dir: Root directory for stimulus files
        categories: List of semantic categories
        tiers: List of tier numbers
        manifest: Dictionary mapping tier/category to available files
    """

    def __init__(self, config: Dict, categories: List[str], tiers: List[int]):
        """
        Initialize stimulus manifest and discover available files.

        Args:
            config: Configuration dictionary
            categories: List of semantic categories
            tiers: List of tier numbers to include

        Notes:
            Scans stimulus directory structure and validates file existence.
            Missing files generate warnings but don't crash the system.
        """
        self.stimuli_dir = Path(config.get('stimuli_dir', 'stimuli'))
        self.categories = categories
        self.tiers = tiers
        self.config = config

        # Manifest structure: manifest[tier][modality][category] = [file_paths]
        self.manifest = {tier: {'images': {}, 'audio': {}} for tier in tiers}

        # Build manifest
        self._discover_images()
        self._discover_audio()

    def _discover_images(self):
        """
        Discover image files for all tiers and categories.

        Notes:
            Expected structure: stimuli/images/<category>/tier<N>/<filename>
            Tier 1 images may be procedurally generated if missing.
        """
        image_dir = self.stimuli_dir / 'images'

        for tier in self.tiers:
            for category in self.categories:
                category_tier_dir = image_dir / category / f'tier{tier}'

                if category_tier_dir.exists():
                    # Find all image files (common formats)
                    image_files = []
                    for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp']:
                        image_files.extend(category_tier_dir.glob(ext))

                    if image_files:
                        self.manifest[tier]['images'][category] = [str(f) for f in image_files]
                    else:
                        print(f"Warning: No images found in {category_tier_dir}")
                        self.manifest[tier]['images'][category] = []
                else:
                    print(f"Warning: Image directory not found: {category_tier_dir}")
                    self.manifest[tier]['images'][category] = []

    def _discover_audio(self):
        """
        Discover audio files for all tiers and categories.

        Notes:
            Tier 1: Pure tones (may be generated)
            Tier 2: Environmental sounds in stimuli/audio/<category>/environmental/
            Tier 3: Spoken words in stimuli/audio/<category>/words/
            Tier 4: Sentences in stimuli/audio/<category>/sentences/
        """
        audio_dir = self.stimuli_dir / 'audio'

        for tier in self.tiers:
            if tier == 1:
                # Tier 1: Pure tones
                tone_dir = audio_dir / 'tones'
                if tone_dir.exists():
                    tone_files = list(tone_dir.glob('*.wav'))
                    # Tones are not category-specific, assign to all categories
                    for category in self.categories:
                        self.manifest[tier]['audio'][category] = [str(f) for f in tone_files]
                else:
                    print(f"Warning: Tone directory not found: {tone_dir}")
                    for category in self.categories:
                        self.manifest[tier]['audio'][category] = []

            elif tier == 2:
                # Tier 2: Environmental sounds
                for category in self.categories:
                    env_sound_dir = audio_dir / category / 'environmental'
                    if env_sound_dir.exists():
                        sound_files = list(env_sound_dir.glob('*.wav'))
                        sound_files.extend(env_sound_dir.glob('*.mp3'))
                        self.manifest[tier]['audio'][category] = [str(f) for f in sound_files]
                    else:
                        print(f"Warning: Environmental sound directory not found: {env_sound_dir}")
                        self.manifest[tier]['audio'][category] = []

            elif tier == 3:
                # Tier 3: Spoken words
                for category in self.categories:
                    word_dir = audio_dir / category / 'words'
                    if word_dir.exists():
                        word_files = list(word_dir.glob('*.wav'))
                        word_files.extend(word_dir.glob('*.mp3'))
                        self.manifest[tier]['audio'][category] = [str(f) for f in word_files]
                    else:
                        print(f"Warning: Word directory not found: {word_dir}")
                        self.manifest[tier]['audio'][category] = []

            elif tier == 4:
                # Tier 4: Sentences
                for category in self.categories:
                    sentence_dir = audio_dir / category / 'sentences'
                    if sentence_dir.exists():
                        sentence_files = list(sentence_dir.glob('*.wav'))
                        sentence_files.extend(sentence_dir.glob('*.mp3'))
                        self.manifest[tier]['audio'][category] = [str(f) for f in sentence_files]
                    else:
                        print(f"Warning: Sentence directory not found: {sentence_dir}")
                        self.manifest[tier]['audio'][category] = []

    def validate(self, modalities: List[str] = None) -> Tuple[bool, List[str]]:
        """
        Validate manifest to ensure required stimuli are available.

        Args:
            modalities: List of modalities to validate for.
                       Defaults to ['bimodal'] (requires both image and audio).
                       For unimodal conditions, only validates the relevant modality.

        Returns:
            Tuple of (is_valid, list_of_warnings)

        Notes:
            - For 'bimodal': requires both images and audio
            - For 'visual-only': requires only images
            - For 'auditory-only': requires only audio
            Returns True if at least some stimuli are available for each tier.
            Warnings list specific missing files or categories.
        """
        if modalities is None:
            modalities = ['bimodal']

        warnings = []
        valid_tiers = []

        for tier in self.tiers:
            tier_has_images = any(
                len(files) > 0 for files in self.manifest[tier]['images'].values()
            )
            tier_has_audio = any(
                len(files) > 0 for files in self.manifest[tier]['audio'].values()
            )

            # Check validity based on required modalities
            tier_valid = False

            if 'bimodal' in modalities and tier_has_images and tier_has_audio:
                tier_valid = True
            if 'visual-only' in modalities and tier_has_images:
                tier_valid = True
            if 'auditory-only' in modalities and tier_has_audio:
                tier_valid = True

            if tier_valid:
                valid_tiers.append(tier)
            else:
                missing = []
                if 'visual-only' in modalities or 'bimodal' in modalities:
                    if not tier_has_images:
                        missing.append('images')
                if 'auditory-only' in modalities or 'bimodal' in modalities:
                    if not tier_has_audio:
                        missing.append('audio')
                if missing:
                    warnings.append(f"Tier {tier} missing {', '.join(missing)} for requested modalities")

        if not valid_tiers:
            warnings.append("CRITICAL: No valid tiers found with required stimuli for selected modalities")
            return False, warnings

        return True, warnings

    def assign_stimuli_to_trials(self, trials: List[Dict], rng: random.Random) -> List[Dict]:
        """
        Assign specific stimulus files to each trial.

        Args:
            trials: List of trial dictionaries with tier/category/modality info
            rng: Random number generator for reproducible assignment

        Returns:
            Updated trials with image_file and audio_file fields

        Notes:
            - Randomly samples from available files for each category/tier
            - Samples with replacement if necessary (if more trials than files)
            - For 'visual-only' trials: only assigns image_file, audio_file = None
            - For 'auditory-only' trials: only assigns audio_file, image_file = None
            - For 'bimodal' trials: assigns both image_file and audio_file
        """
        for trial in trials:
            tier = trial['tier']
            modality = trial.get('modality', 'bimodal')  # Default to bimodal for backward compatibility
            image_category = trial.get('image_category')
            audio_category = trial.get('audio_category')

            # Assign image file (only for visual-only or bimodal)
            if modality in ['visual-only', 'bimodal'] and image_category is not None:
                available_images = self.manifest[tier]['images'].get(image_category, [])
                if available_images:
                    trial['image_file'] = rng.choice(available_images)
                else:
                    trial['image_file'] = None
                    if modality == 'visual-only' or modality == 'bimodal':
                        print(f"Warning: No image available for tier {tier}, category {image_category}")
            else:
                # Auditory-only or image_category is None
                trial['image_file'] = None

            # Assign audio file (only for auditory-only or bimodal)
            if modality in ['auditory-only', 'bimodal'] and audio_category is not None:
                available_audio = self.manifest[tier]['audio'].get(audio_category, [])
                if available_audio:
                    trial['audio_file'] = rng.choice(available_audio)
                else:
                    trial['audio_file'] = None
                    if modality == 'auditory-only' or modality == 'bimodal':
                        print(f"Warning: No audio available for tier {tier}, category {audio_category}")
            else:
                # Visual-only or audio_category is None
                trial['audio_file'] = None

        return trials

    def save_manifest(self, log_dir: Path):
        """
        Save manifest to JSON file for record-keeping.

        Args:
            log_dir: Directory to save manifest

        Notes:
            Manifest includes all discovered files and validation status.
            Useful for debugging and ensuring stimulus set consistency.
        """
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        manifest_file = log_dir / f'manifest_{timestamp}.json'

        # Create summary statistics
        summary = {
            'timestamp': timestamp,
            'tiers': self.tiers,
            'categories': self.categories,
            'manifest': self.manifest,
            'statistics': {}
        }

        # Add statistics
        for tier in self.tiers:
            summary['statistics'][f'tier_{tier}'] = {
                'n_images': sum(len(files) for files in self.manifest[tier]['images'].values()),
                'n_audio': sum(len(files) for files in self.manifest[tier]['audio'].values()),
                'categories_with_images': sum(
                    1 for files in self.manifest[tier]['images'].values() if len(files) > 0
                ),
                'categories_with_audio': sum(
                    1 for files in self.manifest[tier]['audio'].values() if len(files) > 0
                )
            }

        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)

        print(f"Manifest saved to {manifest_file}")

    def get_statistics(self) -> Dict:
        """
        Get summary statistics about available stimuli.

        Returns:
            Dictionary with counts and availability info

        Notes:
            Useful for validation and reporting.
        """
        stats = {
            'total_categories': len(self.categories),
            'total_tiers': len(self.tiers),
            'by_tier': {}
        }

        for tier in self.tiers:
            stats['by_tier'][tier] = {
                'total_images': sum(len(files) for files in self.manifest[tier]['images'].values()),
                'total_audio': sum(len(files) for files in self.manifest[tier]['audio'].values()),
                'images_by_category': {
                    cat: len(files) for cat, files in self.manifest[tier]['images'].items()
                },
                'audio_by_category': {
                    cat: len(files) for cat, files in self.manifest[tier]['audio'].items()
                }
            }

        return stats


def print_manifest_summary(manifest: StimulusManifest):
    """
    Print human-readable summary of stimulus manifest.

    Args:
        manifest: StimulusManifest instance

    Notes:
        Used for validation and dry-run output.
    """
    print("\n" + "=" * 60)
    print("STIMULUS MANIFEST SUMMARY")
    print("=" * 60)

    stats = manifest.get_statistics()

    print(f"\nCategories: {', '.join(manifest.categories)}")
    print(f"Tiers: {', '.join(map(str, manifest.tiers))}")

    for tier in manifest.tiers:
        tier_stats = stats['by_tier'][tier]
        print(f"\n--- Tier {tier} ---")
        print(f"  Total images: {tier_stats['total_images']}")
        print(f"  Total audio: {tier_stats['total_audio']}")

        # Show per-category counts
        print("  Images per category:")
        for cat, count in tier_stats['images_by_category'].items():
            status = "✓" if count > 0 else "✗"
            print(f"    {status} {cat}: {count}")

        print("  Audio per category:")
        for cat, count in tier_stats['audio_by_category'].items():
            status = "✓" if count > 0 else "✗"
            print(f"    {status} {cat}: {count}")

    print("\n" + "=" * 60)
