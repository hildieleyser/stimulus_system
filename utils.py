"""
Utility functions for timing, config validation, and path checking.

Helper functions used across the stimulus presentation system.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Tuple


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to config.yaml file

    Returns:
        Configuration dictionary

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid
    """
    config_file = Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    return config


def validate_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate configuration dictionary.

    Args:
        config: Configuration dictionary to validate

    Returns:
        Tuple of (is_valid, list_of_errors)

    Notes:
        Checks for required fields and valid values.
        Returns True if config is valid, False otherwise.
    """
    errors = []

    # Required fields
    required_fields = [
        'participant_id',
        'session_id',
        'mode',
        'tiers',
        'categories',
        'repeats_per_cell',
        'stimulus_duration_ms',
        'log_dir',
        'stimuli_dir'
    ]

    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: {field}")

    # Validate mode
    if 'mode' in config:
        valid_modes = ['passive', 'active']
        if config['mode'] not in valid_modes:
            errors.append(f"Invalid mode: {config['mode']}. Must be one of {valid_modes}")

        # If active mode, check task is specified
        if config['mode'] == 'active':
            if 'task' not in config or config['task'] is None:
                errors.append("Active mode requires 'task' to be specified")
            elif config['task'] not in ['oddball', 'nback']:
                errors.append(f"Invalid task: {config['task']}. Must be 'oddball' or 'nback'")

    # Validate tiers
    if 'tiers' in config:
        if not isinstance(config['tiers'], list) or not config['tiers']:
            errors.append("'tiers' must be a non-empty list")
        elif not all(isinstance(t, int) and 1 <= t <= 4 for t in config['tiers']):
            errors.append("All tiers must be integers between 1 and 4")

    # Validate categories
    if 'categories' in config:
        if not isinstance(config['categories'], list) or not config['categories']:
            errors.append("'categories' must be a non-empty list")
        elif len(config['categories']) < 2:
            errors.append("Need at least 2 categories for congruent/incongruent pairings")

    # Validate stimulus durations
    if 'stimulus_duration_ms' in config and 'tiers' in config:
        for tier in config['tiers']:
            key = f'tier{tier}'
            if key not in config['stimulus_duration_ms']:
                errors.append(f"Missing stimulus duration for tier {tier}")

    # Validate timing parameters
    timing_params = [
        ('fixation_duration_ms', 0, 5000),
        ('isi_min_ms', 0, 10000),
        ('isi_max_ms', 0, 10000),
        ('rest_between_blocks_ms', 0, 300000)
    ]

    for param, min_val, max_val in timing_params:
        if param in config:
            val = config[param]
            if not isinstance(val, (int, float)) or not (min_val <= val <= max_val):
                errors.append(f"{param} must be between {min_val} and {max_val}")

    # Validate ISI range
    if 'isi_min_ms' in config and 'isi_max_ms' in config:
        if config['isi_min_ms'] > config['isi_max_ms']:
            errors.append("isi_min_ms cannot be greater than isi_max_ms")

    # Validate repeats
    if 'repeats_per_cell' in config:
        if not isinstance(config['repeats_per_cell'], int) or config['repeats_per_cell'] < 1:
            errors.append("repeats_per_cell must be a positive integer")

    # Validate n-back parameter
    if config.get('task') == 'nback':
        if 'nback_n' not in config:
            errors.append("nback task requires 'nback_n' parameter")
        elif not isinstance(config['nback_n'], int) or config['nback_n'] < 1:
            errors.append("nback_n must be a positive integer")

    # Validate oddball proportion
    if config.get('task') == 'oddball':
        if 'oddball_proportion' in config:
            prop = config['oddball_proportion']
            if not isinstance(prop, (int, float)) or not (0 < prop < 1):
                errors.append("oddball_proportion must be between 0 and 1")

    # Validate modality conditions (NEW)
    if 'modality_conditions' in config:
        valid_modalities = ['visual-only', 'auditory-only', 'bimodal']
        modalities = config['modality_conditions']

        if not isinstance(modalities, list) or not modalities:
            errors.append("modality_conditions must be a non-empty list")
        else:
            for modality in modalities:
                if modality not in valid_modalities:
                    errors.append(f"Invalid modality: {modality}. Must be one of {valid_modalities}")

    # Validate menu mode (NEW)
    if 'menu_mode' in config:
        if not isinstance(config['menu_mode'], bool):
            errors.append("menu_mode must be a boolean (true/false)")

    is_valid = len(errors) == 0
    return is_valid, errors


def check_paths(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Check that required paths exist or can be created.

    Args:
        config: Configuration dictionary

    Returns:
        Tuple of (all_ok, list_of_warnings)

    Notes:
        Creates log directory if it doesn't exist.
        Warns if stimuli directory is missing.
    """
    warnings = []
    all_ok = True

    # Check/create log directory
    log_dir = Path(config.get('log_dir', 'logs'))
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        warnings.append(f"Cannot create log directory: {e}")
        all_ok = False

    # Check stimuli directory exists
    stimuli_dir = Path(config.get('stimuli_dir', 'stimuli'))
    if not stimuli_dir.exists():
        warnings.append(f"Stimuli directory not found: {stimuli_dir}")
        # Don't set all_ok to False - manifest validation will handle this

    return all_ok, warnings


def print_config_summary(config: Dict[str, Any]):
    """
    Print human-readable configuration summary.

    Args:
        config: Configuration dictionary

    Notes:
        Used for validation and user confirmation.
    """
    print("\n" + "="*60)
    print("CONFIGURATION SUMMARY")
    print("="*60)

    print(f"\nParticipant ID: {config['participant_id']}")
    print(f"Session ID: {config['session_id']}")
    print(f"Mode: {config['mode']}")

    if config['mode'] == 'active':
        print(f"Task: {config.get('task', 'not specified')}")
        if config.get('task') == 'nback':
            print(f"N-back N: {config.get('nback_n', 1)}")
        elif config.get('task') == 'oddball':
            print(f"Oddball proportion: {config.get('oddball_proportion', 0.2)}")

    print(f"\nModality:")
    modalities = config.get('modality_conditions', ['bimodal'])
    print(f"  Conditions: {', '.join(modalities)}")
    print(f"  Menu mode: {config.get('menu_mode', False)}")

    print(f"\nTiers: {config['tiers']}")
    print(f"Categories: {config['categories']}")
    print(f"Repeats per cell: {config['repeats_per_cell']}")

    print(f"\nTiming:")
    print(f"  Fixation: {config.get('fixation_duration_ms', 500)} ms")
    print(f"  ISI: {config.get('isi_min_ms', 600)}-{config.get('isi_max_ms', 1000)} ms")
    print(f"  Stimulus durations:")
    for tier in config['tiers']:
        dur = config['stimulus_duration_ms'].get(f'tier{tier}', 'not set')
        print(f"    Tier {tier}: {dur} ms")

    print(f"\nDisplay:")
    print(f"  Screen index: {config.get('screen_index', 0)}")
    print(f"  Fullscreen: {config.get('fullscreen', True)}")
    print(f"  Visual angle: {config.get('visual_angle_deg', 10)}°")

    print(f"\nAudio:")
    print(f"  Sample rate: {config.get('sample_rate', 44100)} Hz")
    print(f"  Target loudness: {config.get('target_loudness_lufs', -23)} LUFS")

    print(f"\nMarkers:")
    print(f"  LSL enabled: {config.get('lsl_enabled', True)}")
    print(f"  Parallel port enabled: {config.get('parallel_port_enabled', False)}")

    print(f"\nPaths:")
    print(f"  Log directory: {config.get('log_dir', 'logs/')}")
    print(f"  Stimuli directory: {config.get('stimuli_dir', 'stimuli/')}")

    print("\n" + "="*60)


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string (e.g., "2m 30s" or "45s")

    Notes:
        Used for displaying timing information.
    """
    if seconds < 60:
        return f"{seconds:.0f}s"
    else:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"


def ensure_dir_exists(path: Path):
    """
    Ensure directory exists, creating it if necessary.

    Args:
        path: Path to directory

    Raises:
        OSError: If directory cannot be created
    """
    path.mkdir(parents=True, exist_ok=True)
