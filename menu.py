"""
Interactive menu system for experiment configuration.

Provides a multi-page PsychoPy-based interface for selecting experimental conditions
including modality, tiers, and repetitions.
"""

from typing import Dict, List, Optional, Tuple
from psychopy import visual, event, core


class MenuSystem:
    """
    Multi-page menu system for interactive experiment configuration.

    Attributes:
        display: DisplayManager instance for rendering
        config: Base configuration dictionary
        selections: User selections collected across pages
        current_page: Current page in the menu flow
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

        Notes:
            State machine: landing → visual → auditory → cross-modal → confirmation
            User can navigate back with ESC, quit with 'q'
        """
        # Page flow
        while True:
            if self.current_page == 'landing':
                continue_flow = self.show_landing_page()
                if not continue_flow:
                    return None
                self.page_history.append('landing')
                self.current_page = 'visual'

            elif self.current_page == 'visual':
                result = self.show_visual_config_page()
                if result == 'back':
                    self.current_page = self.page_history.pop() if self.page_history else 'landing'
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
                    # Build and return final config
                    return self.build_config()

    def show_landing_page(self) -> bool:
        """
        Display landing page with welcome message.

        Returns:
            False if quit requested, True to continue
        """
        text = "=" * 50 + "\n"
        text += "MULTISENSORY STIMULUS SYSTEM\n"
        text += "Neural Decoding Experiment\n"
        text += "=" * 50 + "\n\n"
        text += "This system presents visual and auditory stimuli\n"
        text += "across graded sensory complexity levels.\n\n"
        text += "You will configure:\n"
        text += "  • Visual-only trials (images)\n"
        text += "  • Auditory-only trials (sounds)\n"
        text += "  • Cross-modal trials (images + sounds)\n\n"
        text += "Press SPACE to begin configuration\n"
        text += "Press Q to quit"

        self.display.show_text(text, height=24)
        self.display.flip()

        # Wait for input
        while True:
            keys = event.getKeys(['space', 'q', 'escape'])
            if 'space' in keys:
                return True
            if 'q' in keys or 'escape' in keys:
                return False
            core.wait(0.01)

    def show_visual_config_page(self) -> str:
        """
        Display visual modality configuration page.

        Returns:
            'next', 'back', or 'quit'
        """
        visual_config = self.selections['modalities']['visual-only']

        text = "=" * 50 + "\n"
        text += "VISUAL-ONLY CONFIGURATION\n"
        text += "=" * 50 + "\n\n"
        text += f"Enable visual-only trials: {'YES' if visual_config['enabled'] else 'NO'}\n"
        text += f"  (Press E to toggle)\n\n"

        if visual_config['enabled']:
            text += f"Tiers to include: {visual_config['tiers']}\n"
            text += f"  (Press 1-4 to toggle tiers)\n\n"
            text += f"Repetitions per category: {visual_config['repeats']}\n"
            text += f"  (Press +/- to adjust)\n\n"

        text += "\nPress SPACE to continue\n"
        text += "Press BACKSPACE to go back\n"
        text += "Press Q to quit"

        self.display.show_text(text, height=20)
        self.display.flip()

        # Handle input
        while True:
            keys = event.getKeys(['space', 'backspace', 'q', 'escape', 'e',
                                  '1', '2', '3', '4', 'plus', 'minus', 'equal'])

            if 'space' in keys:
                return 'next'
            if 'backspace' in keys:
                return 'back'
            if 'q' in keys or 'escape' in keys:
                return 'quit'

            # Toggle enable
            if 'e' in keys:
                visual_config['enabled'] = not visual_config['enabled']
                return self.show_visual_config_page()  # Refresh

            # Toggle tiers
            if visual_config['enabled']:
                for i in range(1, 5):
                    if str(i) in keys:
                        if i in visual_config['tiers']:
                            visual_config['tiers'].remove(i)
                        else:
                            visual_config['tiers'].append(i)
                        visual_config['tiers'].sort()
                        return self.show_visual_config_page()  # Refresh

                # Adjust repeats
                if 'plus' in keys or 'equal' in keys:  # equal is + without shift
                    visual_config['repeats'] = min(50, visual_config['repeats'] + 1)
                    return self.show_visual_config_page()  # Refresh
                if 'minus' in keys:
                    visual_config['repeats'] = max(1, visual_config['repeats'] - 1)
                    return self.show_visual_config_page()  # Refresh

            core.wait(0.01)

    def show_auditory_config_page(self) -> str:
        """
        Display auditory modality configuration page.

        Returns:
            'next', 'back', or 'quit'
        """
        auditory_config = self.selections['modalities']['auditory-only']

        text = "=" * 50 + "\n"
        text += "AUDITORY-ONLY CONFIGURATION\n"
        text += "=" * 50 + "\n\n"
        text += f"Enable auditory-only trials: {'YES' if auditory_config['enabled'] else 'NO'}\n"
        text += f"  (Press E to toggle)\n\n"

        if auditory_config['enabled']:
            text += f"Tiers to include: {auditory_config['tiers']}\n"
            text += f"  (Press 1-4 to toggle tiers)\n\n"
            text += f"Repetitions per category: {auditory_config['repeats']}\n"
            text += f"  (Press +/- to adjust)\n\n"

        text += "\nPress SPACE to continue\n"
        text += "Press BACKSPACE to go back\n"
        text += "Press Q to quit"

        self.display.show_text(text, height=20)
        self.display.flip()

        # Handle input
        while True:
            keys = event.getKeys(['space', 'backspace', 'q', 'escape', 'e',
                                  '1', '2', '3', '4', 'plus', 'minus', 'equal'])

            if 'space' in keys:
                return 'next'
            if 'backspace' in keys:
                return 'back'
            if 'q' in keys or 'escape' in keys:
                return 'quit'

            # Toggle enable
            if 'e' in keys:
                auditory_config['enabled'] = not auditory_config['enabled']
                return self.show_auditory_config_page()  # Refresh

            # Toggle tiers
            if auditory_config['enabled']:
                for i in range(1, 5):
                    if str(i) in keys:
                        if i in auditory_config['tiers']:
                            auditory_config['tiers'].remove(i)
                        else:
                            auditory_config['tiers'].append(i)
                        auditory_config['tiers'].sort()
                        return self.show_auditory_config_page()  # Refresh

                # Adjust repeats
                if 'plus' in keys or 'equal' in keys:
                    auditory_config['repeats'] = min(50, auditory_config['repeats'] + 1)
                    return self.show_auditory_config_page()  # Refresh
                if 'minus' in keys:
                    auditory_config['repeats'] = max(1, auditory_config['repeats'] - 1)
                    return self.show_auditory_config_page()  # Refresh

            core.wait(0.01)

    def show_crossmodal_config_page(self) -> str:
        """
        Display cross-modal (bimodal) configuration page.

        Returns:
            'next', 'back', or 'quit'
        """
        bimodal_config = self.selections['modalities']['bimodal']

        text = "=" * 50 + "\n"
        text += "CROSS-MODAL CONFIGURATION\n"
        text += "=" * 50 + "\n\n"
        text += f"Enable cross-modal trials: {'YES' if bimodal_config['enabled'] else 'NO'}\n"
        text += f"  (Press E to toggle)\n\n"

        if bimodal_config['enabled']:
            text += f"Tiers to include: {bimodal_config['tiers']}\n"
            text += f"  (Press 1-4 to toggle tiers)\n\n"
            text += f"Repetitions per cell: {bimodal_config['repeats']}\n"
            text += f"  (Press +/- to adjust)\n\n"
            text += "Note: Cross-modal trials include both\n"
            text += "congruent and incongruent pairings.\n"

        text += "\nPress SPACE to continue\n"
        text += "Press BACKSPACE to go back\n"
        text += "Press Q to quit"

        self.display.show_text(text, height=20)
        self.display.flip()

        # Handle input
        while True:
            keys = event.getKeys(['space', 'backspace', 'q', 'escape', 'e',
                                  '1', '2', '3', '4', 'plus', 'minus', 'equal'])

            if 'space' in keys:
                return 'next'
            if 'backspace' in keys:
                return 'back'
            if 'q' in keys or 'escape' in keys:
                return 'quit'

            # Toggle enable
            if 'e' in keys:
                bimodal_config['enabled'] = not bimodal_config['enabled']
                return self.show_crossmodal_config_page()  # Refresh

            # Toggle tiers
            if bimodal_config['enabled']:
                for i in range(1, 5):
                    if str(i) in keys:
                        if i in bimodal_config['tiers']:
                            bimodal_config['tiers'].remove(i)
                        else:
                            bimodal_config['tiers'].append(i)
                        bimodal_config['tiers'].sort()
                        return self.show_crossmodal_config_page()  # Refresh

                # Adjust repeats
                if 'plus' in keys or 'equal' in keys:
                    bimodal_config['repeats'] = min(50, bimodal_config['repeats'] + 1)
                    return self.show_crossmodal_config_page()  # Refresh
                if 'minus' in keys:
                    bimodal_config['repeats'] = max(1, bimodal_config['repeats'] - 1)
                    return self.show_crossmodal_config_page()  # Refresh

            core.wait(0.01)

    def show_confirmation_page(self) -> str:
        """
        Display confirmation page showing all selections.

        Returns:
            'confirm', 'back', or 'quit'
        """
        # Build summary
        text = "=" * 50 + "\n"
        text += "CONFIGURATION SUMMARY\n"
        text += "=" * 50 + "\n\n"

        enabled_modalities = []
        for modality, config in self.selections['modalities'].items():
            if config['enabled']:
                enabled_modalities.append(modality)
                text += f"{modality.upper()}:\n"
                text += f"  Tiers: {config['tiers']}\n"
                text += f"  Repetitions: {config['repeats']}\n\n"

        if not enabled_modalities:
            text += "WARNING: No modalities enabled!\n"
            text += "Please go back and enable at least one.\n\n"

        text += "\nPress SPACE to START experiment\n"
        text += "Press BACKSPACE to go back\n"
        text += "Press Q to quit"

        self.display.show_text(text, height=20)
        self.display.flip()

        # Handle input
        while True:
            keys = event.getKeys(['space', 'backspace', 'q', 'escape'])

            if 'space' in keys:
                if enabled_modalities:  # Only allow confirm if at least one modality enabled
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
