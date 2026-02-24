"""
Session orchestration for passive and active experimental modes.

Manages block structure, trial sequences, and coordinates all subsystems.
"""

import random
from typing import Dict, List
from pathlib import Path

from display import DisplayManager
from audio import AudioManager
from markers import MarkerSystem
from stimuli import StimulusManifest, print_manifest_summary
from matrix import generate_block_structure, assign_nback_targets
from trial import TrialRunner


class ExperimentSession:
    """
    Orchestrates full experimental session across all blocks and trials.

    Attributes:
        config: Configuration dictionary
        display: DisplayManager instance
        audio: AudioManager instance
        markers: MarkerSystem instance
        manifest: StimulusManifest instance
        trial_runner: TrialRunner instance
        rng: Random number generator (seeded for reproducibility)
    """

    def __init__(self, config: Dict, dry_run: bool = False):
        """
        Initialize experiment session and all subsystems.

        Args:
            config: Configuration dictionary
            dry_run: If True, validate setup without running

        Notes:
            RNG is seeded from participant_id + session_id for reproducibility.
            All subsystems are initialized in proper order.
        """
        self.config = config
        self.dry_run = dry_run

        # Create RNG seed from participant and session IDs
        seed_string = f"{config['participant_id']}_{config['session_id']}"
        seed = hash(seed_string) % (2**32)  # Convert to valid seed range
        self.rng = random.Random(seed)
        print(f"RNG seed: {seed} (from {seed_string})")

        # Initialize subsystems
        print("\nInitializing subsystems...")

        # Create session ID for logging
        self.session_id = f"{config['participant_id']}_{config['session_id']}"

        # Initialize markers first (for logging)
        self.markers = MarkerSystem(config, self.session_id, dry_run=dry_run)

        # Initialize display
        self.display = DisplayManager(config, dry_run=dry_run)

        # Initialize audio
        self.audio = AudioManager(config, dry_run=dry_run)

        # Generate tones and TTS if configured
        if not dry_run:
            if config.get('generate_tones', True):
                print("Generating pure tones...")
                self.audio.generate_tone_set()

            if config.get('generate_words_tts', True):
                print("Generating TTS words...")
                self.audio.generate_words_for_categories(config['categories'])

        # Build stimulus manifest
        print("\nBuilding stimulus manifest...")
        self.manifest = StimulusManifest(
            config,
            config['categories'],
            config['tiers']
        )

        # Validate manifest (pass modalities if specified)
        modalities = config.get('modality_conditions', ['bimodal'])
        is_valid, warnings = self.manifest.validate(modalities=modalities)
        if warnings:
            print("\nManifest warnings:")
            for warning in warnings:
                print(f"  - {warning}")

        if not is_valid:
            raise ValueError("Stimulus manifest validation failed - insufficient stimuli")

        # Save manifest
        log_dir = Path(config.get('log_dir', 'logs'))
        self.manifest.save_manifest(log_dir)

        # Print summary
        if dry_run:
            print_manifest_summary(self.manifest)

        # Initialize trial runner
        self.trial_runner = TrialRunner(
            self.display,
            self.audio,
            self.markers,
            config
        )

        print("\nSession initialization complete")

    def run(self):
        """
        Run the full experimental session.

        Notes:
            Handles both passive and active modes.
            Manages block structure and rest periods.
            Ensures proper cleanup on exit or error.
        """
        try:
            mode = self.config['mode']
            task = self.config.get('task')

            print(f"\nStarting {mode} mode" + (f" with {task} task" if task else ""))

            # Show instructions
            if not self.dry_run:
                continue_exp = self.trial_runner.show_instructions_and_wait(mode, task)
                if not continue_exp:
                    print("Experiment cancelled by user")
                    return

            # Get modality conditions (default to bimodal for backward compatibility)
            modalities = self.config.get('modality_conditions', ['bimodal'])

            # Generate block structure (organized by modality → tier)
            blocks = generate_block_structure(
                categories=self.config['categories'],
                tiers=self.config['tiers'],
                repeats_per_cell=self.config['repeats_per_cell'],
                rng=self.rng,
                mode=mode,
                task=task,
                oddball_proportion=self.config.get('oddball_proportion', 0.2),
                modalities=modalities
            )

            # Calculate total blocks for progress tracking
            total_blocks = sum(len(tier_blocks) for tier_blocks in blocks.values())
            block_idx = 0

            # Run blocks organized by modality → tier
            for modality in modalities:
                print(f"\n{'='*60}")
                print(f"MODALITY: {modality.upper()}")
                print(f"{'='*60}")

                # Show modality-specific instructions
                if not self.dry_run:
                    continue_exp = self.trial_runner.show_modality_instructions(modality, mode, task)
                    if not continue_exp:
                        print("Experiment cancelled by user")
                        return

                # Run all tier blocks for this modality
                for tier, trials in blocks[modality].items():
                    block_idx += 1
                    print(f"\n--- Block {block_idx}/{total_blocks}: {modality} - Tier {tier} ---")
                    print(f"Trials in block: {len(trials)}")

                    # For n-back task, assign targets based on sequence
                    if mode == 'active' and task == 'nback':
                        n = self.config.get('nback_n', 1)
                        trials = assign_nback_targets(trials, n)

                    # Assign stimulus files to trials
                    trials = self.manifest.assign_stimuli_to_trials(trials, self.rng)

                    # Send block start marker (include modality info)
                    self.markers.send_block_marker('block_start', block_idx, tier, mode, task, modality=modality)

                    # Run all trials in block
                    quit_requested = self._run_block(trials, mode, task)

                    # Send block end marker
                    self.markers.send_block_marker('block_end', block_idx, tier, mode, task, modality=modality)

                    # Flush markers
                    self.markers.flush()

                    if quit_requested:
                        print("\nExperiment terminated by user")
                        break

                    # Rest period between blocks (except after last block)
                    if block_idx < total_blocks:
                        rest_duration_ms = self.config.get('rest_between_blocks_ms', 0)
                        if rest_duration_ms > 0 and not self.dry_run:
                            continue_exp = self.trial_runner.run_rest_period(block_idx, total_blocks)
                            if not continue_exp:
                                print("\nExperiment terminated by user")
                                break

                # Break out of modality loop if quit requested
                if quit_requested:
                    break

            # Show end message
            if not self.dry_run and not quit_requested:
                self.trial_runner.show_end_message()

            print("\nExperiment complete")

        except KeyboardInterrupt:
            print("\n\nExperiment interrupted by user")
            raise

        except Exception as e:
            print(f"\n\nError during experiment: {e}")
            raise

        finally:
            self.cleanup()

    def _run_block(self, trials: List[Dict], mode: str, task: str = None) -> bool:
        """
        Run all trials in a block.

        Args:
            trials: List of trial dictionaries
            mode: Experimental mode
            task: Task type if active mode

        Returns:
            True if quit requested, False otherwise

        Notes:
            Runs trials sequentially with proper timing.
        """
        for trial_idx, trial_data in enumerate(trials):
            if self.dry_run:
                # In dry run, validate trial data based on modality
                modality = trial_data.get('modality', 'bimodal')
                if modality in ['visual-only', 'bimodal'] and not trial_data.get('image_file'):
                    print(f"  Warning: Trial {trial_idx} missing image file (modality: {modality})")
                if modality in ['auditory-only', 'bimodal'] and not trial_data.get('audio_file'):
                    print(f"  Warning: Trial {trial_idx} missing audio file (modality: {modality})")
                continue

            # Run trial based on mode
            if mode == 'passive':
                results = self.trial_runner.run_trial_passive(trial_data, trial_idx)
            else:  # active
                results = self.trial_runner.run_trial_active(trial_data, trial_idx, task)

            # Check for quit
            if results.get('quit', False):
                return True

            # Print progress every 10 trials
            if (trial_idx + 1) % 10 == 0:
                print(f"  Completed {trial_idx + 1}/{len(trials)} trials")

        return False

    def cleanup(self):
        """
        Clean up all subsystems and ensure data is saved.

        Notes:
            Called automatically via try/finally.
            Ensures CSV is flushed and LSL is closed.
        """
        print("\nCleaning up...")

        try:
            if self.markers:
                self.markers.close()
        except Exception as e:
            print(f"Warning during marker cleanup: {e}")

        try:
            if self.audio:
                self.audio.stop_all()
        except Exception as e:
            print(f"Warning during audio cleanup: {e}")

        try:
            if self.display:
                self.display.close()
        except Exception as e:
            print(f"Warning during display cleanup: {e}")

        print("Cleanup complete")

    def validate_only(self):
        """
        Perform validation without running experiment (dry run).

        Notes:
            Checks config, manifest, and generates summary statistics.
        """
        print("\n" + "="*60)
        print("DRY RUN - VALIDATION ONLY")
        print("="*60)

        # Config summary
        print("\nConfiguration:")
        print(f"  Participant: {self.config['participant_id']}")
        print(f"  Session: {self.config['session_id']}")
        print(f"  Mode: {self.config['mode']}")
        if self.config['mode'] == 'active':
            print(f"  Task: {self.config.get('task')}")
        print(f"  Tiers: {self.config['tiers']}")
        print(f"  Categories: {len(self.config['categories'])}")
        print(f"  Repeats per cell: {self.config['repeats_per_cell']}")

        # Calculate trial counts
        mode = self.config['mode']
        task = self.config.get('task')
        modalities = self.config.get('modality_conditions', ['bimodal'])

        blocks = generate_block_structure(
            categories=self.config['categories'],
            tiers=self.config['tiers'],
            repeats_per_cell=self.config['repeats_per_cell'],
            rng=self.rng,
            mode=mode,
            task=task,
            oddball_proportion=self.config.get('oddball_proportion', 0.2),
            modalities=modalities
        )

        # Calculate total trials across all modalities
        total_trials = sum(
            sum(len(trials) for trials in tier_blocks.values())
            for tier_blocks in blocks.values()
        )

        # Calculate total blocks
        total_blocks = sum(len(tier_blocks) for tier_blocks in blocks.values())

        print(f"\nExperiment structure:")
        print(f"  Modalities: {', '.join(modalities)}")
        print(f"  Total blocks: {total_blocks}")
        print(f"  Total trials: {total_trials}")

        block_idx = 0
        for modality in modalities:
            print(f"\n  {modality.upper()}:")
            for tier, trials in blocks[modality].items():
                block_idx += 1
                print(f"    Block {block_idx} (Tier {tier}): {len(trials)} trials")

        # Estimate duration
        avg_trial_dur = 3.0  # Rough estimate in seconds
        estimated_duration = (total_trials * avg_trial_dur) / 60.0  # minutes
        print(f"\nEstimated duration: ~{estimated_duration:.1f} minutes")

        print("\n" + "="*60)
        print("Validation complete - ready to run")
        print("="*60)
