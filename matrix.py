"""
Cross-modal matrix: tier/congruence cell assignment.

Defines the 8-cell experimental design (4 tiers × 2 congruence conditions)
and generates trial sequences with proper randomization and constraints.
"""

import random
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class MatrixCell:
    """
    Represents a single cell in the cross-modal matrix.

    Attributes:
        modality: Sensory modality ('visual-only', 'auditory-only', 'bimodal')
        tier: Sensory tier (1-4)
        congruence: 'congruent', 'incongruent', or None (for unimodal)
        image_category: Semantic category for image (None for auditory-only)
        audio_category: Semantic category for audio (None for visual-only)
    """
    modality: str
    tier: int
    congruence: str
    image_category: str
    audio_category: str


def create_matrix_cells(categories: List[str], tiers: List[int], modalities: List[str] = None) -> List[Dict[str, any]]:
    """
    Create all cells in the cross-modal matrix.

    Args:
        categories: List of semantic categories
        tiers: List of tier numbers to include
        modalities: List of modalities ('visual-only', 'auditory-only', 'bimodal').
                   Defaults to ['bimodal'] for backward compatibility.

    Returns:
        List of dict representations of matrix cells

    Notes:
        - For 'visual-only': only image_category assigned, audio_category = None, congruence = None
        - For 'auditory-only': only audio_category assigned, image_category = None, congruence = None
        - For 'bimodal': both categories assigned with congruence conditions
        Each tier × modality combination creates cells for all categories.
    """
    # Default to bimodal for backward compatibility
    if modalities is None:
        modalities = ['bimodal']

    cells = []

    for modality in modalities:
        for tier in tiers:
            if modality == 'visual-only':
                # Visual-only: image only, no audio, no congruence
                for category in categories:
                    cell = {
                        'modality': modality,
                        'tier': tier,
                        'congruence': None,
                        'image_category': category,
                        'audio_category': None
                    }
                    cells.append(cell)

            elif modality == 'auditory-only':
                # Auditory-only: audio only, no image, no congruence
                for category in categories:
                    cell = {
                        'modality': modality,
                        'tier': tier,
                        'congruence': None,
                        'image_category': None,
                        'audio_category': category
                    }
                    cells.append(cell)

            elif modality == 'bimodal':
                # Bimodal: both modalities with congruence manipulation
                for congruence in ['congruent', 'incongruent']:
                    for category in categories:
                        cell = {
                            'modality': modality,
                            'tier': tier,
                            'congruence': congruence,
                            'image_category': category,
                            'audio_category': category if congruence == 'congruent' else None  # Will be assigned later
                        }
                        cells.append(cell)

    return cells


def assign_incongruent_pairs(cells: List[Dict[str, any]], categories: List[str], rng: random.Random) -> List[Dict[str, any]]:
    """
    Assign audio categories to incongruent trials.

    Args:
        cells: List of matrix cells
        categories: List of available categories
        rng: Random number generator for reproducibility

    Returns:
        Updated cells with audio categories assigned

    Notes:
        For incongruent trials, audio category is randomly selected from
        categories other than the image category.
        Only applies to bimodal trials (unimodal trials have None for congruence).
    """
    for cell in cells:
        if cell.get('congruence') == 'incongruent':
            # Select a different category for audio
            available_categories = [c for c in categories if c != cell['image_category']]
            cell['audio_category'] = rng.choice(available_categories)

    return cells


def generate_trial_sequence(cells: List[Dict[str, any]], repeats_per_cell: int,
                           rng: random.Random, mode: str = 'passive',
                           task: str = None, oddball_proportion: float = 0.2) -> List[Dict[str, any]]:
    """
    Generate a randomized trial sequence.

    Args:
        cells: List of matrix cells
        repeats_per_cell: Number of repetitions per cell
        rng: Random number generator
        mode: 'passive' or 'active'
        task: 'oddball', 'nback', or None
        oddball_proportion: Proportion of oddball trials (for oddball task)

    Returns:
        List of trial dictionaries with assigned trial types

    Notes:
        - In passive mode: all cells repeated equally
        - In oddball mode: adjust proportions to achieve target oddball rate
        - In n-back mode: maintain balanced cell distribution
        - Trials are randomized within blocks to prevent predictability
    """
    trials = []

    if mode == 'active' and task == 'oddball':
        # Special handling for oddball task
        # Standard trials (congruent) should be ~80%, oddball (incongruent) ~20%
        congruent_cells = [c for c in cells if c['congruence'] == 'congruent']
        incongruent_cells = [c for c in cells if c['congruence'] == 'incongruent']

        # Calculate repeats to achieve target proportion
        total_trials = len(cells) * repeats_per_cell
        n_oddball = int(total_trials * oddball_proportion)
        n_standard = total_trials - n_oddball

        # Distribute repeats
        repeats_standard = n_standard // len(congruent_cells) if congruent_cells else 0
        repeats_oddball = n_oddball // len(incongruent_cells) if incongruent_cells else 0

        for cell in congruent_cells:
            for _ in range(repeats_standard):
                trial = cell.copy()
                trial['trial_type'] = 'standard'
                trials.append(trial)

        for cell in incongruent_cells:
            for _ in range(repeats_oddball):
                trial = cell.copy()
                trial['trial_type'] = 'oddball'
                trials.append(trial)

    else:
        # Standard trial generation (passive or n-back)
        for cell in cells:
            for _ in range(repeats_per_cell):
                trial = cell.copy()

                # For n-back, trial_type will be assigned during session based on sequence
                if mode == 'active' and task == 'nback':
                    trial['trial_type'] = 'nontarget'  # Default, updated during presentation
                else:
                    trial['trial_type'] = 'standard'

                trials.append(trial)

    # Shuffle trials to randomize order
    rng.shuffle(trials)

    return trials


def generate_block_structure(categories: List[str], tiers: List[int],
                            repeats_per_cell: int, rng: random.Random,
                            mode: str = 'passive', task: str = None,
                            oddball_proportion: float = 0.2,
                            modalities: List[str] = None) -> Dict[str, Dict[int, List[Dict[str, any]]]]:
    """
    Generate trial structure organized by modality and blocks (one block per tier within each modality).

    Args:
        categories: List of semantic categories
        tiers: List of tier numbers
        repeats_per_cell: Repetitions per matrix cell
        rng: Random number generator
        mode: Experimental mode
        task: Task type (if active mode)
        oddball_proportion: Proportion of oddball trials
        modalities: List of modalities ('visual-only', 'auditory-only', 'bimodal').
                   Defaults to ['bimodal'] for backward compatibility.

    Returns:
        Dictionary mapping modality → tier number → list of trials for that block
        Format: {modality: {tier: [trials]}}

    Notes:
        Each modality contains blocks organized by tier.
        For 'visual-only' and 'auditory-only', congruence is not applicable.
        For 'bimodal', both congruence conditions are represented.
        Trials within blocks are randomized.
    """
    # Default to bimodal for backward compatibility
    if modalities is None:
        modalities = ['bimodal']

    blocks = {}

    for modality in modalities:
        blocks[modality] = {}

        for tier in tiers:
            # Create cells for this tier and modality
            tier_cells = []

            if modality == 'visual-only':
                # Visual-only: image only, no congruence
                for category in categories:
                    cell = {
                        'modality': modality,
                        'tier': tier,
                        'congruence': None,
                        'image_category': category,
                        'audio_category': None
                    }
                    tier_cells.append(cell)

            elif modality == 'auditory-only':
                # Auditory-only: audio only, no congruence
                for category in categories:
                    cell = {
                        'modality': modality,
                        'tier': tier,
                        'congruence': None,
                        'image_category': None,
                        'audio_category': category
                    }
                    tier_cells.append(cell)

            elif modality == 'bimodal':
                # Bimodal: both modalities with congruence
                for congruence in ['congruent', 'incongruent']:
                    for category in categories:
                        cell = {
                            'modality': modality,
                            'tier': tier,
                            'congruence': congruence,
                            'image_category': category,
                            'audio_category': category if congruence == 'congruent' else None
                        }
                        tier_cells.append(cell)

                # Assign incongruent pairs for bimodal only
                tier_cells = assign_incongruent_pairs(tier_cells, categories, rng)

            # Generate trial sequence for this block
            block_trials = generate_trial_sequence(
                tier_cells, repeats_per_cell, rng, mode, task, oddball_proportion
            )

            blocks[modality][tier] = block_trials

    return blocks


def assign_nback_targets(trials: List[Dict[str, any]], n: int) -> List[Dict[str, any]]:
    """
    Assign target/nontarget labels for n-back task based on trial sequence.

    Args:
        trials: List of trials in presentation order
        n: N for n-back task (e.g., 1 for 1-back, 2 for 2-back)

    Returns:
        Updated trials with trial_type set to 'target' or 'nontarget'

    Notes:
        A trial is a target if its image_category matches the image_category
        from N trials ago. First N trials cannot be targets.
    """
    for i in range(len(trials)):
        if i < n:
            # First N trials cannot be targets
            trials[i]['trial_type'] = 'nontarget'
        else:
            # Check if current image category matches N trials back
            if trials[i]['image_category'] == trials[i - n]['image_category']:
                trials[i]['trial_type'] = 'target'
            else:
                trials[i]['trial_type'] = 'nontarget'

    return trials


def validate_trial_balance(trials: List[Dict[str, any]]) -> Dict[str, int]:
    """
    Validate and report trial balance across conditions.

    Args:
        trials: List of generated trials

    Returns:
        Dictionary with counts for each condition

    Notes:
        Used for quality checking trial generation.
    """
    counts = {
        'total': len(trials),
        'congruent': sum(1 for t in trials if t['congruence'] == 'congruent'),
        'incongruent': sum(1 for t in trials if t['congruence'] == 'incongruent'),
    }

    # Count by tier
    for tier in set(t['tier'] for t in trials):
        counts[f'tier_{tier}'] = sum(1 for t in trials if t['tier'] == tier)

    # Count by trial type if present
    if 'trial_type' in trials[0]:
        for trial_type in set(t['trial_type'] for t in trials):
            counts[f'type_{trial_type}'] = sum(1 for t in trials if t['trial_type'] == trial_type)

    return counts
