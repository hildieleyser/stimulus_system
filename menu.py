"""
Interactive menu system for experiment configuration with mouse and keyboard support.

Provides a multi-page PsychoPy-based interface for selecting experimental conditions
including modality, tiers, and repetitions.
"""

from typing import Dict, List, Optional, Tuple
from psychopy import visual, event, core


class ClickableButton:
    """
    A clickable button with visual feedback.

    Attributes:
        rect: PsychoPy Rect for button background
        text: PsychoPy TextStim for button label
        pos: Button position (x, y)
        size: Button size (width, height)
        action: Action identifier when clicked
    """

    def __init__(self, win, text: str, pos: Tuple[float, float],
                 size: Tuple[float, float], action: str,
                 enabled: bool = True, selected: bool = False):
        """
        Initialize clickable button.

        Args:
            win: PsychoPy window
            text: Button label text
            pos: Position (x, y) in window units
            size: Size (width, height) in window units
            action: Action identifier
            enabled: Whether button is enabled
            selected: Whether button is selected/active
        """
        self.win = win
        self.action = action
        self.pos = pos
        self.size = size
        self.enabled = enabled
        self.selected = selected
        self.hovered = False

        # Create rectangle
        self.rect = visual.Rect(
            win=win,
            width=size[0],
            height=size[1],
            pos=pos,
            fillColor=self._get_fill_color(),
            lineColor='white',
            lineWidth=2
        )

        # Create text
        self.text_stim = visual.TextStim(
            win=win,
            text=text,
            pos=pos,
            height=size[1] * 0.4,
            color='white',
            anchorHoriz='center',
            anchorVert='center'
        )

    def _get_fill_color(self) -> str:
        """Get fill color based on button state."""
        if not self.enabled:
            return 'gray'
        elif self.selected:
            return 'green'
        elif self.hovered:
            return 'darkblue'
        else:
            return 'blue'

    def contains(self, pos: Tuple[float, float]) -> bool:
        """Check if position is inside button."""
        x, y = pos
        left = self.pos[0] - self.size[0] / 2
        right = self.pos[0] + self.size[0] / 2
        bottom = self.pos[1] - self.size[1] / 2
        top = self.pos[1] + self.size[1] / 2
        return left <= x <= right and bottom <= y <= top

    def update_hover(self, mouse_pos: Tuple[float, float]):
        """Update hover state based on mouse position."""
        self.hovered = self.contains(mouse_pos) if self.enabled else False
        self.rect.fillColor = self._get_fill_color()

    def set_selected(self, selected: bool):
        """Update selection state."""
        self.selected = selected
        self.rect.fillColor = self._get_fill_color()

    def draw(self):
        """Draw button."""
        self.rect.draw()
        self.text_stim.draw()


class MenuSystem:
    """
    Multi-page menu system for interactive experiment configuration with mouse support.

    Attributes:
        display: DisplayManager instance for rendering
        config: Base configuration dictionary
        selections: User selections collected across pages
        current_page: Current page in the menu flow
        mouse: PsychoPy Mouse object
    """

    def __init__(self, display, config: Dict):
        """
        Initialize menu system.

        Args:
            display: DisplayManager instance
            config: Base configuration dictionary (provides defaults)
        """
        self.display = display
        self.config = config
        self.win = display.win
        self.mouse = event.Mouse(win=self.win, visible=True)

        # User selections (accumulated across pages)
        self.selections = {
            'modalities': {
                'visual-only': {'enabled': False, 'tiers': [1, 2, 3, 4], 'repeats': 10},
                'auditory-only': {'enabled': False, 'tiers': [1, 2, 3, 4], 'repeats': 10},
                'bimodal': {'enabled': True, 'tiers': [1, 2, 3, 4], 'repeats': 10}  # Default enabled
            },
            'participant_id': config.get('participant_id', 'P01'),
            'session_id': config.get('session_id', 'S01')
        }

        # Page state
        self.current_page = 'landing'
        self.page_history = []

    def run_menu_flow(self) -> Optional[Dict]:
        """
        Run complete menu flow and return configuration.

        Returns:
            Configuration dict with user selections, or None if cancelled
        """
        # Page flow
        while True:
            if self.current_page == 'landing':
                continue_flow = self.show_landing_page()
                if not continue_flow:
                    return None
                self.page_history.append('landing')
                self.current_page = 'paradigm'

            elif self.current_page == 'paradigm':
                result = self.show_paradigm_selection_page()
                if result == 'back':
                    self.current_page = self.page_history.pop() if self.page_history else 'landing'
                elif result == 'quit':
                    return None
                else:
                    self.page_history.append('paradigm')
                    self.current_page = 'visual'

            elif self.current_page == 'visual':
                result = self.show_visual_config_page()
                if result == 'back':
                    self.current_page = self.page_history.pop() if self.page_history else 'paradigm'
                elif result == 'quit':
                    return None
                else:
                    self.page_history.append('visual')
                    self.current_page = 'auditory'

            elif self.current_page == 'auditory':
                result = self.show_auditory_config_page()
                if result == 'back':
                    self.current_page = self.page_history.pop() if self.page_history else 'visual'
                elif result == 'quit':
                    return None
                else:
                    self.page_history.append('auditory')
                    self.current_page = 'cross-modal'

            elif self.current_page == 'cross-modal':
                result = self.show_crossmodal_config_page()
                if result == 'back':
                    self.current_page = self.page_history.pop() if self.page_history else 'auditory'
                elif result == 'quit':
                    return None
                else:
                    self.page_history.append('cross-modal')
                    self.current_page = 'confirmation'

            elif self.current_page == 'confirmation':
                result = self.show_confirmation_page()
                if result == 'back':
                    self.current_page = self.page_history.pop() if self.page_history else 'cross-modal'
                elif result == 'quit':
                    return None
                elif result == 'confirm':
                    return self.build_config()

    def show_landing_page(self) -> bool:
        """Display landing page with clickable start button."""
        # Title text
        title = visual.TextStim(
            win=self.win,
            text="MULTISENSORY STIMULUS SYSTEM\nNeural Decoding Experiment",
            pos=(0, 4),
            height=0.8,
            color='white',
            wrapWidth=20
        )

        # Description
        desc = visual.TextStim(
            win=self.win,
            text=("This system presents visual and auditory stimuli\n"
                  "across graded sensory complexity levels.\n\n"
                  "You will configure:\n"
                  "  • Visual-only trials (images)\n"
                  "  • Auditory-only trials (sounds)\n"
                  "  • Cross-modal trials (images + sounds)"),
            pos=(0, 0.5),
            height=0.5,
            color='white',
            wrapWidth=20
        )

        # Buttons
        start_btn = ClickableButton(self.win, "START", (0, -3), (4, 1.2), 'start')
        quit_btn = ClickableButton(self.win, "QUIT", (0, -5), (4, 1.2), 'quit')

        buttons = [start_btn, quit_btn]

        # Main loop
        while True:
            # Update hover states
            mouse_pos = self.mouse.getPos()
            for btn in buttons:
                btn.update_hover(mouse_pos)

            # Draw all
            title.draw()
            desc.draw()
            for btn in buttons:
                btn.draw()
            self.win.flip()

            # Check for clicks
            if self.mouse.getPressed()[0]:  # Left click
                for btn in buttons:
                    if btn.hovered:
                        core.wait(0.2)  # Debounce
                        if btn.action == 'start':
                            return True
                        elif btn.action == 'quit':
                            return False

            # Keyboard shortcuts
            keys = event.getKeys(['space', 'q', 'escape'])
            if 'space' in keys:
                return True
            if 'q' in keys or 'escape' in keys:
                return False

            core.wait(0.01)

    def show_paradigm_selection_page(self) -> str:
        """Display paradigm selection page with clickable buttons for each modality."""
        # Title
        title = visual.TextStim(
            win=self.win,
            text="SELECT PARADIGMS",
            pos=(0, 5),
            height=0.8,
            color='white'
        )

        # Instructions
        instructions = visual.TextStim(
            win=self.win,
            text="Click to enable/disable each paradigm:",
            pos=(0, 3.5),
            height=0.5,
            color='white'
        )

        # Paradigm buttons (large, clickable toggles)
        visual_btn = ClickableButton(
            self.win,
            f"VISUAL-ONLY\n{'✓ ENABLED' if self.selections['modalities']['visual-only']['enabled'] else '✗ DISABLED'}",
            (-4, 1),
            (5, 2.5),
            'toggle_visual',
            selected=self.selections['modalities']['visual-only']['enabled']
        )

        auditory_btn = ClickableButton(
            self.win,
            f"AUDITORY-ONLY\n{'✓ ENABLED' if self.selections['modalities']['auditory-only']['enabled'] else '✗ DISABLED'}",
            (4, 1),
            (5, 2.5),
            'toggle_auditory',
            selected=self.selections['modalities']['auditory-only']['enabled']
        )

        bimodal_btn = ClickableButton(
            self.win,
            f"CROSS-MODAL\n{'✓ ENABLED' if self.selections['modalities']['bimodal']['enabled'] else '✗ DISABLED'}",
            (0, -2),
            (5, 2.5),
            'toggle_bimodal',
            selected=self.selections['modalities']['bimodal']['enabled']
        )

        # Navigation buttons
        next_btn = ClickableButton(self.win, "NEXT →", (4, -5.5), (3, 1), 'next')
        back_btn = ClickableButton(self.win, "← BACK", (-4, -5.5), (3, 1), 'back')

        buttons = [visual_btn, auditory_btn, bimodal_btn, next_btn, back_btn]

        # Main loop
        while True:
            # Update hover states
            mouse_pos = self.mouse.getPos()
            for btn in buttons:
                btn.update_hover(mouse_pos)

            # Update selected states
            visual_btn.set_selected(self.selections['modalities']['visual-only']['enabled'])
            auditory_btn.set_selected(self.selections['modalities']['auditory-only']['enabled'])
            bimodal_btn.set_selected(self.selections['modalities']['bimodal']['enabled'])

            # Draw all
            title.draw()
            instructions.draw()
            for btn in buttons:
                btn.draw()
            self.win.flip()

            # Check for clicks
            if self.mouse.getPressed()[0]:  # Left click
                for btn in buttons:
                    if btn.hovered:
                        core.wait(0.2)  # Debounce
                        if btn.action == 'toggle_visual':
                            self.selections['modalities']['visual-only']['enabled'] = \
                                not self.selections['modalities']['visual-only']['enabled']
                            visual_btn.text_stim.text = f"VISUAL-ONLY\n{'✓ ENABLED' if self.selections['modalities']['visual-only']['enabled'] else '✗ DISABLED'}"
                        elif btn.action == 'toggle_auditory':
                            self.selections['modalities']['auditory-only']['enabled'] = \
                                not self.selections['modalities']['auditory-only']['enabled']
                            auditory_btn.text_stim.text = f"AUDITORY-ONLY\n{'✓ ENABLED' if self.selections['modalities']['auditory-only']['enabled'] else '✗ DISABLED'}"
                        elif btn.action == 'toggle_bimodal':
                            self.selections['modalities']['bimodal']['enabled'] = \
                                not self.selections['modalities']['bimodal']['enabled']
                            bimodal_btn.text_stim.text = f"CROSS-MODAL\n{'✓ ENABLED' if self.selections['modalities']['bimodal']['enabled'] else '✗ DISABLED'}"
                        elif btn.action == 'next':
                            return 'next'
                        elif btn.action == 'back':
                            return 'back'

            # Keyboard shortcuts
            keys = event.getKeys(['space', 'backspace', 'q', 'escape'])
            if 'space' in keys:
                return 'next'
            if 'backspace' in keys:
                return 'back'
            if 'q' in keys or 'escape' in keys:
                return 'quit'

            core.wait(0.01)

    def show_visual_config_page(self) -> str:
        """Display visual modality configuration page with clickable controls."""
        visual_config = self.selections['modalities']['visual-only']

        # Title
        title = visual.TextStim(
            win=self.win,
            text="VISUAL-ONLY CONFIGURATION",
            pos=(0, 5),
            height=0.7,
            color='white'
        )

        # Status
        status = visual.TextStim(
            win=self.win,
            text=f"Status: {'ENABLED' if visual_config['enabled'] else 'DISABLED'}",
            pos=(0, 3.5),
            height=0.6,
            color='green' if visual_config['enabled'] else 'red'
        )

        # Enable button
        enable_btn = ClickableButton(
            self.win,
            f"{'DISABLE' if visual_config['enabled'] else 'ENABLE'}",
            (0, 2),
            (4, 1),
            'toggle_enable',
            selected=visual_config['enabled']
        )

        buttons = [enable_btn]

        # Tier and repeat controls (only if enabled)
        if visual_config['enabled']:
            # Tier label
            tier_label = visual.TextStim(
                win=self.win,
                text=f"Tiers: {visual_config['tiers']}",
                pos=(0, 0.5),
                height=0.5,
                color='white'
            )

            # Tier buttons
            tier_buttons = []
            for i in range(1, 5):
                tier_btn = ClickableButton(
                    self.win,
                    f"Tier {i}",
                    (-3 + (i-1)*2, -1),
                    (1.5, 0.8),
                    f'toggle_tier_{i}',
                    selected=(i in visual_config['tiers'])
                )
                tier_buttons.append(tier_btn)
                buttons.append(tier_btn)

            # Repeats label
            repeat_label = visual.TextStim(
                win=self.win,
                text=f"Repetitions: {visual_config['repeats']}",
                pos=(0, -2.5),
                height=0.5,
                color='white'
            )

            # Repeat buttons
            minus_btn = ClickableButton(self.win, "-", (-2, -3.5), (1, 0.8), 'repeat_minus')
            plus_btn = ClickableButton(self.win, "+", (2, -3.5), (1, 0.8), 'repeat_plus')
            buttons.extend([minus_btn, plus_btn])

        # Navigation buttons
        next_btn = ClickableButton(self.win, "NEXT →", (4, -5.5), (3, 1), 'next')
        back_btn = ClickableButton(self.win, "← BACK", (-4, -5.5), (3, 1), 'back')
        buttons.extend([next_btn, back_btn])

        # Main loop
        while True:
            # Update hover states
            mouse_pos = self.mouse.getPos()
            for btn in buttons:
                btn.update_hover(mouse_pos)

            # Draw all
            title.draw()
            status.draw()
            for btn in buttons:
                btn.draw()

            if visual_config['enabled']:
                tier_label.draw()
                repeat_label.draw()

            self.win.flip()

            # Check for clicks
            if self.mouse.getPressed()[0]:
                for btn in buttons:
                    if btn.hovered:
                        core.wait(0.2)
                        if btn.action == 'toggle_enable':
                            visual_config['enabled'] = not visual_config['enabled']
                            return self.show_visual_config_page()
                        elif btn.action.startswith('toggle_tier_'):
                            tier = int(btn.action.split('_')[-1])
                            if tier in visual_config['tiers']:
                                visual_config['tiers'].remove(tier)
                            else:
                                visual_config['tiers'].append(tier)
                            visual_config['tiers'].sort()
                            return self.show_visual_config_page()
                        elif btn.action == 'repeat_minus':
                            visual_config['repeats'] = max(1, visual_config['repeats'] - 1)
                            return self.show_visual_config_page()
                        elif btn.action == 'repeat_plus':
                            visual_config['repeats'] = min(50, visual_config['repeats'] + 1)
                            return self.show_visual_config_page()
                        elif btn.action == 'next':
                            return 'next'
                        elif btn.action == 'back':
                            return 'back'

            # Keyboard shortcuts
            keys = event.getKeys(['space', 'backspace', 'q', 'escape'])
            if 'space' in keys:
                return 'next'
            if 'backspace' in keys:
                return 'back'
            if 'q' in keys or 'escape' in keys:
                return 'quit'

            core.wait(0.01)

    def show_auditory_config_page(self) -> str:
        """Display auditory modality configuration page with clickable controls."""
        auditory_config = self.selections['modalities']['auditory-only']

        # Title
        title = visual.TextStim(
            win=self.win,
            text="AUDITORY-ONLY CONFIGURATION",
            pos=(0, 5),
            height=0.7,
            color='white'
        )

        # Status
        status = visual.TextStim(
            win=self.win,
            text=f"Status: {'ENABLED' if auditory_config['enabled'] else 'DISABLED'}",
            pos=(0, 3.5),
            height=0.6,
            color='green' if auditory_config['enabled'] else 'red'
        )

        # Enable button
        enable_btn = ClickableButton(
            self.win,
            f"{'DISABLE' if auditory_config['enabled'] else 'ENABLE'}",
            (0, 2),
            (4, 1),
            'toggle_enable',
            selected=auditory_config['enabled']
        )

        buttons = [enable_btn]

        # Tier and repeat controls (only if enabled)
        if auditory_config['enabled']:
            # Tier label
            tier_label = visual.TextStim(
                win=self.win,
                text=f"Tiers: {auditory_config['tiers']}",
                pos=(0, 0.5),
                height=0.5,
                color='white'
            )

            # Tier buttons
            tier_buttons = []
            for i in range(1, 5):
                tier_btn = ClickableButton(
                    self.win,
                    f"Tier {i}",
                    (-3 + (i-1)*2, -1),
                    (1.5, 0.8),
                    f'toggle_tier_{i}',
                    selected=(i in auditory_config['tiers'])
                )
                tier_buttons.append(tier_btn)
                buttons.append(tier_btn)

            # Repeats label
            repeat_label = visual.TextStim(
                win=self.win,
                text=f"Repetitions: {auditory_config['repeats']}",
                pos=(0, -2.5),
                height=0.5,
                color='white'
            )

            # Repeat buttons
            minus_btn = ClickableButton(self.win, "-", (-2, -3.5), (1, 0.8), 'repeat_minus')
            plus_btn = ClickableButton(self.win, "+", (2, -3.5), (1, 0.8), 'repeat_plus')
            buttons.extend([minus_btn, plus_btn])

        # Navigation buttons
        next_btn = ClickableButton(self.win, "NEXT →", (4, -5.5), (3, 1), 'next')
        back_btn = ClickableButton(self.win, "← BACK", (-4, -5.5), (3, 1), 'back')
        buttons.extend([next_btn, back_btn])

        # Main loop
        while True:
            # Update hover states
            mouse_pos = self.mouse.getPos()
            for btn in buttons:
                btn.update_hover(mouse_pos)

            # Draw all
            title.draw()
            status.draw()
            for btn in buttons:
                btn.draw()

            if auditory_config['enabled']:
                tier_label.draw()
                repeat_label.draw()

            self.win.flip()

            # Check for clicks
            if self.mouse.getPressed()[0]:
                for btn in buttons:
                    if btn.hovered:
                        core.wait(0.2)
                        if btn.action == 'toggle_enable':
                            auditory_config['enabled'] = not auditory_config['enabled']
                            return self.show_auditory_config_page()
                        elif btn.action.startswith('toggle_tier_'):
                            tier = int(btn.action.split('_')[-1])
                            if tier in auditory_config['tiers']:
                                auditory_config['tiers'].remove(tier)
                            else:
                                auditory_config['tiers'].append(tier)
                            auditory_config['tiers'].sort()
                            return self.show_auditory_config_page()
                        elif btn.action == 'repeat_minus':
                            auditory_config['repeats'] = max(1, auditory_config['repeats'] - 1)
                            return self.show_auditory_config_page()
                        elif btn.action == 'repeat_plus':
                            auditory_config['repeats'] = min(50, auditory_config['repeats'] + 1)
                            return self.show_auditory_config_page()
                        elif btn.action == 'next':
                            return 'next'
                        elif btn.action == 'back':
                            return 'back'

            # Keyboard shortcuts
            keys = event.getKeys(['space', 'backspace', 'q', 'escape'])
            if 'space' in keys:
                return 'next'
            if 'backspace' in keys:
                return 'back'
            if 'q' in keys or 'escape' in keys:
                return 'quit'

            core.wait(0.01)

    def show_crossmodal_config_page(self) -> str:
        """Display cross-modal (bimodal) configuration page with clickable controls."""
        bimodal_config = self.selections['modalities']['bimodal']

        # Title
        title = visual.TextStim(
            win=self.win,
            text="CROSS-MODAL CONFIGURATION",
            pos=(0, 5),
            height=0.7,
            color='white'
        )

        # Status
        status = visual.TextStim(
            win=self.win,
            text=f"Status: {'ENABLED' if bimodal_config['enabled'] else 'DISABLED'}",
            pos=(0, 3.5),
            height=0.6,
            color='green' if bimodal_config['enabled'] else 'red'
        )

        # Enable button
        enable_btn = ClickableButton(
            self.win,
            f"{'DISABLE' if bimodal_config['enabled'] else 'ENABLE'}",
            (0, 2),
            (4, 1),
            'toggle_enable',
            selected=bimodal_config['enabled']
        )

        buttons = [enable_btn]

        # Tier and repeat controls (only if enabled)
        if bimodal_config['enabled']:
            # Note
            note = visual.TextStim(
                win=self.win,
                text="Cross-modal trials include both\ncongruent and incongruent pairings",
                pos=(0, 0.8),
                height=0.4,
                color='yellow'
            )

            # Tier label
            tier_label = visual.TextStim(
                win=self.win,
                text=f"Tiers: {bimodal_config['tiers']}",
                pos=(0, -0.3),
                height=0.5,
                color='white'
            )

            # Tier buttons
            tier_buttons = []
            for i in range(1, 5):
                tier_btn = ClickableButton(
                    self.win,
                    f"Tier {i}",
                    (-3 + (i-1)*2, -1.3),
                    (1.5, 0.8),
                    f'toggle_tier_{i}',
                    selected=(i in bimodal_config['tiers'])
                )
                tier_buttons.append(tier_btn)
                buttons.append(tier_btn)

            # Repeats label
            repeat_label = visual.TextStim(
                win=self.win,
                text=f"Repetitions per cell: {bimodal_config['repeats']}",
                pos=(0, -2.8),
                height=0.5,
                color='white'
            )

            # Repeat buttons
            minus_btn = ClickableButton(self.win, "-", (-2, -3.8), (1, 0.8), 'repeat_minus')
            plus_btn = ClickableButton(self.win, "+", (2, -3.8), (1, 0.8), 'repeat_plus')
            buttons.extend([minus_btn, plus_btn])

        # Navigation buttons
        next_btn = ClickableButton(self.win, "NEXT →", (4, -5.5), (3, 1), 'next')
        back_btn = ClickableButton(self.win, "← BACK", (-4, -5.5), (3, 1), 'back')
        buttons.extend([next_btn, back_btn])

        # Main loop
        while True:
            # Update hover states
            mouse_pos = self.mouse.getPos()
            for btn in buttons:
                btn.update_hover(mouse_pos)

            # Draw all
            title.draw()
            status.draw()
            for btn in buttons:
                btn.draw()

            if bimodal_config['enabled']:
                note.draw()
                tier_label.draw()
                repeat_label.draw()

            self.win.flip()

            # Check for clicks
            if self.mouse.getPressed()[0]:
                for btn in buttons:
                    if btn.hovered:
                        core.wait(0.2)
                        if btn.action == 'toggle_enable':
                            bimodal_config['enabled'] = not bimodal_config['enabled']
                            return self.show_crossmodal_config_page()
                        elif btn.action.startswith('toggle_tier_'):
                            tier = int(btn.action.split('_')[-1])
                            if tier in bimodal_config['tiers']:
                                bimodal_config['tiers'].remove(tier)
                            else:
                                bimodal_config['tiers'].append(tier)
                            bimodal_config['tiers'].sort()
                            return self.show_crossmodal_config_page()
                        elif btn.action == 'repeat_minus':
                            bimodal_config['repeats'] = max(1, bimodal_config['repeats'] - 1)
                            return self.show_crossmodal_config_page()
                        elif btn.action == 'repeat_plus':
                            bimodal_config['repeats'] = min(50, bimodal_config['repeats'] + 1)
                            return self.show_crossmodal_config_page()
                        elif btn.action == 'next':
                            return 'next'
                        elif btn.action == 'back':
                            return 'back'

            # Keyboard shortcuts
            keys = event.getKeys(['space', 'backspace', 'q', 'escape'])
            if 'space' in keys:
                return 'next'
            if 'backspace' in keys:
                return 'back'
            if 'q' in keys or 'escape' in keys:
                return 'quit'

            core.wait(0.01)

    def show_confirmation_page(self) -> str:
        """Display confirmation page with clickable start button."""
        # Build summary
        enabled_modalities = []
        summary_text = "CONFIGURATION SUMMARY\n" + "=" * 40 + "\n\n"

        for modality, config in self.selections['modalities'].items():
            if config['enabled']:
                enabled_modalities.append(modality)
                summary_text += f"{modality.upper()}:\n"
                summary_text += f"  Tiers: {config['tiers']}\n"
                summary_text += f"  Repetitions: {config['repeats']}\n\n"

        if not enabled_modalities:
            summary_text += "WARNING: No modalities enabled!\n"
            summary_text += "Please go back and enable at least one."

        # Summary text
        summary = visual.TextStim(
            win=self.win,
            text=summary_text,
            pos=(0, 2),
            height=0.5,
            color='white',
            wrapWidth=18
        )

        # Buttons
        if enabled_modalities:
            start_btn = ClickableButton(self.win, "START EXPERIMENT", (0, -3), (6, 1.5), 'confirm')
            buttons = [start_btn]
        else:
            buttons = []

        back_btn = ClickableButton(self.win, "← BACK", (0, -5), (4, 1), 'back')
        buttons.append(back_btn)

        # Main loop
        while True:
            # Update hover states
            mouse_pos = self.mouse.getPos()
            for btn in buttons:
                btn.update_hover(mouse_pos)

            # Draw all
            summary.draw()
            for btn in buttons:
                btn.draw()
            self.win.flip()

            # Check for clicks
            if self.mouse.getPressed()[0]:
                for btn in buttons:
                    if btn.hovered:
                        core.wait(0.2)
                        if btn.action == 'confirm':
                            return 'confirm'
                        elif btn.action == 'back':
                            return 'back'

            # Keyboard shortcuts
            keys = event.getKeys(['space', 'backspace', 'q', 'escape'])
            if 'space' in keys and enabled_modalities:
                return 'confirm'
            if 'backspace' in keys:
                return 'back'
            if 'q' in keys or 'escape' in keys:
                return 'quit'

            core.wait(0.01)

    def build_config(self) -> Dict:
        """
        Build configuration dictionary from user selections.

        Returns:
            Complete configuration dictionary ready for ExperimentSession
        """
        # Start with base config
        config = self.config.copy()

        # Collect enabled modalities
        enabled_modalities = []
        all_tiers = set()

        for modality, modality_config in self.selections['modalities'].items():
            if modality_config['enabled']:
                enabled_modalities.append(modality)
                all_tiers.update(modality_config['tiers'])

        # Update config
        config['modality_conditions'] = enabled_modalities
        config['tiers'] = sorted(list(all_tiers))

        # Use repeats from bimodal if enabled (most conservative)
        # Otherwise use max from enabled modalities
        if self.selections['modalities']['bimodal']['enabled']:
            config['repeats_per_cell'] = self.selections['modalities']['bimodal']['repeats']
        else:
            repeats = [cfg['repeats'] for cfg in self.selections['modalities'].values() if cfg['enabled']]
            config['repeats_per_cell'] = max(repeats) if repeats else 10

        return config
