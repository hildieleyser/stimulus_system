"""
PsychoPy window management, image rendering, fixation, and feedback.

Handles all visual stimulus presentation with precise timing and correct scaling.
"""

import numpy as np
from pathlib import Path
from typing import Dict, Optional, Tuple
from PIL import Image


class DisplayManager:
    """
    Manages visual stimulus presentation using PsychoPy.

    Attributes:
        win: PsychoPy window object
        config: Configuration dictionary
        fixation: Fixation cross stimulus
        feedback_correct: Green fixation for correct feedback
        feedback_incorrect: Red fixation for incorrect feedback
        image_stim: ImageStim object for displaying images
    """

    def __init__(self, config: Dict, dry_run: bool = False):
        """
        Initialize PsychoPy window and visual stimuli.

        Args:
            config: Configuration dictionary
            dry_run: If True, skip window creation

        Notes:
            Window is created in fullscreen by default.
            All stimuli scaled to maintain visual angle.
        """
        self.config = config
        self.dry_run = dry_run
        self.win = None
        self.fixation = None
        self.feedback_correct = None
        self.feedback_incorrect = None
        self.image_stim = None

        if not dry_run:
            self._create_window()
            self._create_stimuli()

    def _create_window(self):
        """
        Create PsychoPy window with specified parameters.

        Notes:
            Uses RGB color space (-1 to 1).
            Disables frame rate warnings for cleaner output.
        """
        from psychopy import visual, core

        # Suppress some warnings for cleaner output
        import warnings
        warnings.filterwarnings('ignore', category=FutureWarning)

        screen_index = self.config.get('screen_index', 0)
        fullscreen = self.config.get('fullscreen', True)
        screen_width_px = self.config.get('screen_width_px', 1920)
        screen_height_px = self.config.get('screen_height_px', 1080)
        background_color = self.config.get('background_color', [0, 0, 0])

        self.win = visual.Window(
            size=[screen_width_px, screen_height_px],
            screen=screen_index,
            fullscr=fullscreen,
            color=background_color,
            colorSpace='rgb',
            units='pix',  # Use pixels for precise control
            allowGUI=False,
            waitBlanking=True
        )

        # Hide mouse cursor
        self.win.mouseVisible = False

        print(f"Display window created: {screen_width_px}x{screen_height_px}, screen {screen_index}")

    def _create_stimuli(self):
        """
        Create reusable visual stimuli (fixation cross, feedback).

        Notes:
            Fixation cross is simple + shape.
            Feedback stimuli are colored fixation crosses.
        """
        from psychopy import visual

        # Fixation cross (white)
        self.fixation = visual.TextStim(
            self.win,
            text='+',
            color='white',
            colorSpace='rgb',
            height=40,  # pixels
            bold=True
        )

        # Feedback: correct (green)
        self.feedback_correct = visual.TextStim(
            self.win,
            text='+',
            color='green',
            colorSpace='rgb',
            height=40,
            bold=True
        )

        # Feedback: incorrect (red)
        self.feedback_incorrect = visual.TextStim(
            self.win,
            text='+',
            color='red',
            colorSpace='rgb',
            height=40,
            bold=True
        )

        # Image stimulus placeholder
        self.image_stim = visual.ImageStim(
            self.win,
            size=None,  # Will be set per image
            interpolate=True
        )

    def calculate_image_size(self, visual_angle_deg: float) -> float:
        """
        Calculate image size in pixels from visual angle.

        Args:
            visual_angle_deg: Desired visual angle in degrees

        Returns:
            Size in pixels

        Notes:
            Uses viewing distance and screen dimensions from config.
            Formula: size_px = 2 * distance * tan(angle/2) * (px/cm)
        """
        viewing_distance_cm = self.config.get('viewing_distance_cm', 70)
        screen_width_cm = self.config.get('screen_width_cm', 52)
        screen_width_px = self.config.get('screen_width_px', 1920)

        # Convert angle to radians
        angle_rad = np.deg2rad(visual_angle_deg)

        # Calculate physical size
        size_cm = 2 * viewing_distance_cm * np.tan(angle_rad / 2)

        # Convert to pixels
        px_per_cm = screen_width_px / screen_width_cm
        size_px = size_cm * px_per_cm

        return size_px

    def load_and_scale_image(self, image_path: str, visual_angle_deg: Optional[float] = None) -> Image.Image:
        """
        Load image and scale to specified visual angle.

        Args:
            image_path: Path to image file
            visual_angle_deg: Visual angle (uses config default if None)

        Returns:
            PIL Image object scaled appropriately

        Notes:
            Maintains aspect ratio during scaling.
            Images are scaled to fit within target size.
        """
        if visual_angle_deg is None:
            visual_angle_deg = self.config.get('visual_angle_deg', 10)

        target_size_px = self.calculate_image_size(visual_angle_deg)

        # Load image
        img = Image.open(image_path)

        # Calculate scaling to fit within target size (maintain aspect ratio)
        width, height = img.size
        max_dim = max(width, height)
        scale = target_size_px / max_dim

        new_width = int(width * scale)
        new_height = int(height * scale)

        # Resize
        img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        return img_resized

    def show_fixation(self):
        """
        Display fixation cross.

        Notes:
            Does not call flip() - caller must flip to display.
        """
        if self.dry_run:
            return

        self.fixation.draw()

    def show_image(self, image_path: str):
        """
        Display image stimulus scaled to visual angle.

        Args:
            image_path: Path to image file

        Notes:
            Does not call flip() - caller must flip to display.
            Image is centered on screen.
        """
        if self.dry_run:
            return

        # Load and scale image
        img = self.load_and_scale_image(image_path)

        # Update image stimulus
        self.image_stim.setImage(img)
        self.image_stim.draw()

    def show_feedback(self, correct: bool):
        """
        Display feedback (colored fixation cross).

        Args:
            correct: True for correct (green), False for incorrect (red)

        Notes:
            Does not call flip() - caller must flip to display.
        """
        if self.dry_run:
            return

        if correct:
            self.feedback_correct.draw()
        else:
            self.feedback_incorrect.draw()

    def show_text(self, text: str, height: int = 40, color: str = 'white'):
        """
        Display text message.

        Args:
            text: Text to display
            height: Text height in pixels
            color: Text color

        Notes:
            Does not call flip() - caller must flip to display.
            Text is centered on screen.
        """
        if self.dry_run:
            return

        from psychopy import visual

        text_stim = visual.TextStim(
            self.win,
            text=text,
            color=color,
            colorSpace='rgb',
            height=height,
            wrapWidth=self.win.size[0] * 0.8  # 80% of screen width
        )
        text_stim.draw()

    def show_rest_screen(self, block_number: int, total_blocks: int):
        """
        Display rest screen between blocks.

        Args:
            block_number: Current block number
            total_blocks: Total number of blocks

        Notes:
            Shows progress and instructions to continue.
            Does not call flip() - caller must flip.
        """
        if self.dry_run:
            return

        text = f"Block {block_number} of {total_blocks} complete.\n\n"
        text += "Take a short rest.\n\n"
        text += "Press SPACE to continue."

        self.show_text(text, height=30)

    def show_instructions(self, mode: str, task: Optional[str] = None):
        """
        Display task instructions.

        Args:
            mode: 'passive' or 'active'
            task: Task type if active mode

        Notes:
            Shows mode-specific instructions.
            Does not call flip() - caller must flip.
        """
        if self.dry_run:
            return

        if mode == 'passive':
            text = "PASSIVE VIEWING\n\n"
            text += "Please watch and listen to the stimuli.\n"
            text += "Try to maintain fixation on the cross when it appears.\n\n"
            text += "Press SPACE to begin."

        elif mode == 'active' and task == 'oddball':
            text = "ODDBALL TASK\n\n"
            text += "Press SPACE when you detect a mismatch\n"
            text += "between the image and sound.\n\n"
            text += "Press SPACE to begin."

        elif mode == 'active' and task == 'nback':
            n = self.config.get('nback_n', 1)
            text = f"{n}-BACK TASK\n\n"
            text += f"Press SPACE when the current image category\n"
            text += f"matches the category from {n} trial(s) ago.\n\n"
            text += "Press SPACE to begin."

        else:
            text = "Press SPACE to begin."

        self.show_text(text, height=30)

    def clear(self):
        """
        Clear screen to background color.

        Notes:
            Does not call flip() - caller must flip to display.
        """
        if self.dry_run:
            return

        # Just calling flip with nothing drawn will clear screen
        pass

    def flip(self) -> float:
        """
        Flip window buffers to display drawn stimuli.

        Returns:
            Timestamp of flip (from PsychoPy clock)

        Notes:
            Timing-critical: this is the moment stimuli appear on screen.
            Returns precise flip timestamp for event marking.
        """
        if self.dry_run:
            from psychopy import core
            return core.getTime()

        return self.win.flip()

    def close(self):
        """
        Close display window and cleanup.

        Notes:
            Should be called at end of session.
        """
        if self.win is not None:
            self.win.close()
            print("Display window closed")

    def wait_for_keypress(self, key: str = 'space') -> bool:
        """
        Wait for specific key press.

        Args:
            key: Key name to wait for (default 'space')

        Returns:
            True when key pressed, False if quit key pressed

        Notes:
            Blocking call - waits until key is pressed.
            Returns False if escape key pressed (quit signal).
        """
        if self.dry_run:
            return True

        from psychopy import event

        event.clearEvents()

        while True:
            keys = event.waitKeys(keyList=[key, 'escape'])

            if 'escape' in keys:
                return False
            if key in keys:
                return True

    def check_for_quit(self) -> bool:
        """
        Check if quit key (escape) has been pressed.

        Returns:
            True if quit requested, False otherwise

        Notes:
            Non-blocking check.
        """
        if self.dry_run:
            return False

        from psychopy import event

        keys = event.getKeys(['escape'])
        return 'escape' in keys

    def get_frame_rate(self) -> float:
        """
        Get actual frame rate of display.

        Returns:
            Frame rate in Hz

        Notes:
            Useful for validation and debugging timing.
        """
        if self.dry_run:
            return 60.0

        # Measure frame rate if not already done
        if not hasattr(self.win, '_measuredRefreshRate') or self.win._measuredRefreshRate is None:
            from psychopy import visual
            self.win.recordFrameIntervals = True
            # Flip several times to measure
            for _ in range(60):
                self.win.flip()
            self.win.recordFrameIntervals = False

        return self.win.fps() if hasattr(self.win, 'fps') else 60.0
