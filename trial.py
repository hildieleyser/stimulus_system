"""
Single trial logic for both passive and active modes.

Handles precise timing of fixation, stimulus presentation, response collection, and ISI.
"""

from typing import Dict, Optional, Tuple
from psychopy import core, event


class TrialRunner:
    """
    Manages execution of individual trials with precise timing.

    Attributes:
        display: DisplayManager instance
        audio: AudioManager instance
        markers: MarkerSystem instance
        config: Configuration dictionary
        clock: PsychoPy Clock for timing
    """

    def __init__(self, display, audio, markers, config: Dict):
        """
        Initialize trial runner with required managers.

        Args:
            display: DisplayManager instance
            audio: AudioManager instance
            markers: MarkerSystem instance
            config: Configuration dictionary

        Notes:
            Clock is initialized for precise timing measurements.
        """
        self.display = display
        self.audio = audio
        self.markers = markers
        self.config = config
        self.clock = core.Clock()

    def run_trial_passive(self, trial_data: Dict, trial_index: int) -> Dict:
        """
        Run a single passive viewing trial.

        Args:
            trial_data: Dictionary with trial information (tier, files, etc.)
            trial_index: Index of current trial in sequence

        Returns:
            Dictionary with trial results and timing

        Notes:
            Sequence: fixation → stimulus (image + audio) → ISI
            All timing via PsychoPy Clock, no sleep calls.
        """
        results = {
            'trial_index': trial_index,
            'trial_data': trial_data,
            'fixation_onset': None,
            'stimulus_onset': None,
            'stimulus_offset': None,
            'isi_onset': None
        }

        # Get timing parameters
        fixation_dur = self.config.get('fixation_duration_ms', 500) / 1000.0
        tier = trial_data['tier']
        stim_dur_ms = self.config['stimulus_duration_ms'][f'tier{tier}']
        stim_dur = stim_dur_ms / 1000.0

        # 1. FIXATION
        self.display.show_fixation()
        results['fixation_onset'] = self.display.flip()
        self.clock.reset()

        # Wait for fixation duration
        while self.clock.getTime() < fixation_dur:
            if self.display.check_for_quit():
                results['quit'] = True
                return results
            core.wait(0.001)  # Small wait to prevent CPU spinning

        # 2. STIMULUS PRESENTATION
        # Get modality (default to bimodal for backward compatibility)
        modality = trial_data.get('modality', 'bimodal')

        # Draw visual stimulus based on modality
        if modality in ['visual-only', 'bimodal']:
            if trial_data.get('image_file'):
                self.display.show_image(trial_data['image_file'])
        elif modality == 'auditory-only':
            # For auditory-only, show continuous fixation
            self.display.show_fixation()

        # Flip to show stimulus and get precise onset time
        results['stimulus_onset'] = self.display.flip()

        # Send onset marker immediately after flip
        self.markers.send_onset_marker(trial_data, trial_index, mode='passive')

        # Play audio based on modality (after onset marker)
        if modality in ['auditory-only', 'bimodal']:
            if trial_data.get('audio_file'):
                self.audio.play_audio_file(trial_data['audio_file'])

        # Reset clock for stimulus duration
        self.clock.reset()

        # Wait for stimulus duration
        while self.clock.getTime() < stim_dur:
            if self.display.check_for_quit():
                results['quit'] = True
                return results
            core.wait(0.001)

        # 3. STIMULUS OFFSET
        # Clear screen
        self.display.clear()
        results['stimulus_offset'] = self.display.flip()

        # Send offset marker
        self.markers.send_offset_marker(trial_data, trial_index, mode='passive')

        # 4. ISI (inter-stimulus interval)
        isi_min = self.config.get('isi_min_ms', 600) / 1000.0
        isi_max = self.config.get('isi_max_ms', 1000) / 1000.0

        # Jitter ISI
        import random
        isi_dur = random.uniform(isi_min, isi_max)

        results['isi_onset'] = self.display.flip()
        self.clock.reset()

        # Wait for ISI
        while self.clock.getTime() < isi_dur:
            if self.display.check_for_quit():
                results['quit'] = True
                return results
            core.wait(0.001)

        return results

    def run_trial_active(self, trial_data: Dict, trial_index: int, task: str) -> Dict:
        """
        Run a single active task trial with response collection.

        Args:
            trial_data: Dictionary with trial information
            trial_index: Index of current trial
            task: Task type ('oddball' or 'nback')

        Returns:
            Dictionary with trial results, timing, and response data

        Notes:
            Collects responses during stimulus presentation.
            Determines correctness based on task type.
        """
        results = {
            'trial_index': trial_index,
            'trial_data': trial_data,
            'fixation_onset': None,
            'stimulus_onset': None,
            'stimulus_offset': None,
            'response': None,
            'rt_ms': None,
            'correct': None,
            'isi_onset': None
        }

        # Get timing parameters
        fixation_dur = self.config.get('fixation_duration_ms', 500) / 1000.0
        tier = trial_data['tier']
        stim_dur_ms = self.config['stimulus_duration_ms'][f'tier{tier}']
        stim_dur = stim_dur_ms / 1000.0
        response_key = self.config.get('response_key', 'space')

        # Determine if response is expected
        is_target = trial_data.get('trial_type') in ['oddball', 'target']

        # 1. FIXATION
        self.display.show_fixation()
        results['fixation_onset'] = self.display.flip()
        self.clock.reset()

        # Clear any previous key presses
        event.clearEvents()

        while self.clock.getTime() < fixation_dur:
            if self.display.check_for_quit():
                results['quit'] = True
                return results
            core.wait(0.001)

        # 2. STIMULUS PRESENTATION
        # Get modality (default to bimodal for backward compatibility)
        modality = trial_data.get('modality', 'bimodal')

        # Draw visual stimulus based on modality
        if modality in ['visual-only', 'bimodal']:
            if trial_data.get('image_file'):
                self.display.show_image(trial_data['image_file'])
        elif modality == 'auditory-only':
            # For auditory-only, show continuous fixation
            self.display.show_fixation()

        results['stimulus_onset'] = self.display.flip()

        # Send onset marker
        self.markers.send_onset_marker(trial_data, trial_index, mode='active', task=task)

        # Play audio based on modality
        if modality in ['auditory-only', 'bimodal']:
            if trial_data.get('audio_file'):
                self.audio.play_audio_file(trial_data['audio_file'])

        # Reset clock for stimulus duration and response collection
        self.clock.reset()
        response_made = False
        response_time = None

        # Wait for stimulus duration, collecting responses
        while self.clock.getTime() < stim_dur:
            if self.display.check_for_quit():
                results['quit'] = True
                return results

            # Check for response
            if not response_made:
                keys = event.getKeys([response_key], timeStamped=self.clock)
                if keys:
                    response_made = True
                    response_time = keys[0][1]  # Time of first key press
                    results['response'] = response_key
                    results['rt_ms'] = response_time * 1000

            core.wait(0.001)

        # 3. DETERMINE CORRECTNESS
        if is_target and response_made:
            # Hit
            correct = True
        elif is_target and not response_made:
            # Miss
            correct = False
        elif not is_target and response_made:
            # False alarm
            correct = False
        else:
            # Correct rejection
            correct = True

        results['correct'] = correct

        # Send response marker if response was made
        if response_made:
            self.markers.send_response_marker(
                trial_data, trial_index, response_key,
                results['rt_ms'], correct, mode='active', task=task
            )

        # 4. FEEDBACK (if enabled)
        if self.config.get('feedback_enabled', True) and response_made:
            feedback_dur = self.config.get('feedback_duration_ms', 200) / 1000.0

            self.display.show_feedback(correct)
            self.display.flip()
            self.clock.reset()

            while self.clock.getTime() < feedback_dur:
                if self.display.check_for_quit():
                    results['quit'] = True
                    return results
                core.wait(0.001)

        # 5. STIMULUS OFFSET / ISI
        self.display.clear()
        results['stimulus_offset'] = self.display.flip()

        self.markers.send_offset_marker(trial_data, trial_index, mode='active', task=task)

        # ISI
        isi_min = self.config.get('isi_min_ms', 600) / 1000.0
        isi_max = self.config.get('isi_max_ms', 1000) / 1000.0

        import random
        isi_dur = random.uniform(isi_min, isi_max)

        results['isi_onset'] = core.getTime()
        self.clock.reset()

        while self.clock.getTime() < isi_dur:
            if self.display.check_for_quit():
                results['quit'] = True
                return results
            core.wait(0.001)

        return results

    def run_rest_period(self, block_number: int, total_blocks: int) -> bool:
        """
        Display rest screen and wait for participant to continue.

        Args:
            block_number: Number of completed block
            total_blocks: Total number of blocks

        Returns:
            False if quit requested, True otherwise

        Notes:
            Participant presses space to continue.
        """
        self.display.show_rest_screen(block_number, total_blocks)
        self.display.flip()

        # Wait for space key
        continue_exp = self.display.wait_for_keypress('space')

        return continue_exp

    def show_instructions_and_wait(self, mode: str, task: Optional[str] = None) -> bool:
        """
        Display instructions and wait for participant to start.

        Args:
            mode: Experimental mode ('passive' or 'active')
            task: Task type if active mode

        Returns:
            False if quit requested, True otherwise

        Notes:
            Called at beginning of session.
        """
        self.display.show_instructions(mode, task)
        self.display.flip()

        # Wait for space key
        continue_exp = self.display.wait_for_keypress('space')

        return continue_exp

    def show_modality_instructions(self, modality: str, mode: str, task: Optional[str] = None) -> bool:
        """
        Display modality-specific instructions and wait for participant to continue.

        Args:
            modality: Sensory modality ('visual-only', 'auditory-only', 'bimodal')
            mode: Experimental mode ('passive' or 'active')
            task: Task type if active mode

        Returns:
            False if quit requested, True otherwise

        Notes:
            Called at the start of each modality block.
        """
        # Build modality-specific instruction text
        if modality == 'visual-only':
            text = "VISUAL ONLY TRIALS\n\n"
            text += "In this section, you will see images only.\n"
            if mode == 'passive':
                text += "Please maintain fixation on the cross and observe the images.\n"
            elif mode == 'active' and task == 'oddball':
                text += "Press SPACE when you detect an oddball stimulus.\n"
            elif mode == 'active' and task == 'nback':
                text += f"Press SPACE when the current image matches the image from {self.config.get('nback_n', 1)} trials ago.\n"

        elif modality == 'auditory-only':
            text = "AUDITORY ONLY TRIALS\n\n"
            text += "In this section, you will hear sounds only.\n"
            if mode == 'passive':
                text += "Please maintain fixation on the cross and listen to the sounds.\n"
            elif mode == 'active' and task == 'oddball':
                text += "Press SPACE when you detect an oddball stimulus.\n"
            elif mode == 'active' and task == 'nback':
                text += f"Press SPACE when the current sound matches the sound from {self.config.get('nback_n', 1)} trials ago.\n"

        elif modality == 'bimodal':
            text = "CROSS-MODAL TRIALS\n\n"
            text += "In this section, you will experience\n"
            text += "images and sounds together.\n"
            if mode == 'passive':
                text += "Please maintain fixation and observe both modalities.\n"
            elif mode == 'active' and task == 'oddball':
                text += "\nPress SPACE when the image and sound do not match.\n"
            elif mode == 'active' and task == 'nback':
                text += f"\nPress SPACE when the current image matches the image from {self.config.get('nback_n', 1)} trials ago.\n"

        text += "\n\nPress SPACE to begin."

        self.display.show_text(text, height=30)
        self.display.flip()

        # Wait for space key
        continue_exp = self.display.wait_for_keypress('space')

        return continue_exp

    def show_end_message(self):
        """
        Display end-of-experiment message.

        Notes:
            Waits for space before closing.
        """
        self.display.show_text(
            "Experiment complete.\n\nThank you for participating!\n\nPress SPACE to exit.",
            height=30
        )
        self.display.flip()

        self.display.wait_for_keypress('space')
