# Stimulus Presentation System for Neural Decoding

A high-precision stimulus presentation system for neural decoding experiments using cross-modal (visual + auditory) stimuli. Designed for use with EEG, fNIRS, and eye tracking.

## Features

- **Cross-modal stimulus matrix**: 4 tiers × 2 congruence conditions
- **Two experimental modes**: Passive viewing and active tasks (oddball/n-back)
- **Precise timing**: PsychoPy-based with microsecond accuracy
- **Event marking**: LSL (Lab Streaming Layer) integration for multi-modal recording
- **Flexible configuration**: YAML-based configuration for all parameters
- **Stimulus generation**: Automatic tone generation and text-to-speech
- **Data logging**: CSV logs with comprehensive trial information

## Cross-Modal Sensory Matrix

| Tier | Visual | Auditory | Description |
|------|--------|----------|-------------|
| 1 | Greyscale object | Pure tone (440-880 Hz) | Minimal sensory information |
| 2 | Color object | Environmental sound | Single object, matched sound |
| 3 | Object in scene | Spoken word | Object in context, linguistic |
| 4 | Full scene | Descriptive sentence | Complete naturalistic load |

Each tier can be **congruent** (matching categories) or **incongruent** (mismatched categories).

## Installation

### Requirements
- Python 3.10 or higher
- Display with known physical dimensions
- Audio output device
- Optional: LSL for streaming to recording software

### Setup

1. Clone the repository:
```bash
git clone https://github.com/hildieleyser/stimulus_system.git
cd stimulus_system
```

2. Create virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Prepare stimulus directories:
```bash
mkdir -p stimuli/images stimuli/audio
```

## Stimulus Directory Structure

Organize your stimuli as follows:

```
stimuli/
├── images/
│   ├── dog/
│   │   ├── tier1/    # Greyscale isolated objects
│   │   ├── tier2/    # Color isolated objects
│   │   ├── tier3/    # Objects in scenes
│   │   └── tier4/    # Full naturalistic scenes
│   ├── car/
│   │   └── ...
│   └── ...
├── audio/
│   ├── tones/        # Auto-generated pure tones
│   ├── dog/
│   │   ├── environmental/  # Dog barks, etc.
│   │   ├── words/          # "dog" (auto-generated via TTS)
│   │   └── sentences/      # "A dog is running in the park"
│   └── ...
```

**Note**: Tier 1 tones and Tier 3 words can be auto-generated if `generate_tones` and `generate_words_tts` are enabled in config.

## Configuration

Edit `config.yaml` to customize:

- Participant and session IDs
- Experimental mode (passive/active)
- Task type (oddball/n-back)
- Stimulus categories
- Timing parameters
- Display settings
- Audio settings
- Event marking options

See `config.yaml` for detailed comments on all parameters.

## Usage

### Validate Setup (Dry Run)

Test configuration and check stimulus availability without running:

```bash
python run_experiment.py --dry-run
```

This will:
- Validate configuration
- Build stimulus manifest
- Check all file paths
- Display experiment statistics
- Estimate duration

### Run Experiment

```bash
python run_experiment.py
```

**Controls**:
- `Space`: Progress through instructions, rest periods, responses (in active mode)
- `Escape`: Quit experiment at any time

### Custom Configuration

```bash
python run_experiment.py --config my_experiment.yaml
```

## Experimental Modes

### Passive Mode

Participant observes stimuli without responding. Used for baseline neural recordings.

**Trial structure**:
1. Fixation cross (500 ms)
2. Stimulus presentation (image + audio simultaneously)
3. ISI (600-1000 ms, jittered)

### Active Mode: Oddball Task

Participant presses space when detecting incongruent image-audio pairs.

- 80% congruent (standard)
- 20% incongruent (oddball)
- Feedback enabled (configurable)

### Active Mode: N-Back Task

Participant presses space when current image category matches the category from N trials ago.

- Configurable N (default: 1-back)
- Audio varies independently of n-back target

## Event Marking

All events are marked via LSL and logged to CSV with:

- Event type (onset, offset, response, block_start, block_end)
- Trial information (tier, congruence, categories, files)
- Timing (precise timestamps)
- Response data (key, RT, correctness)

### LSL Stream

Stream name: `StimulusMarkers`
Type: `Markers`
Format: JSON strings

Connect your recording software (e.g., Lab Recorder) to capture markers synchronized with neural data.

## Data Output

### CSV Log
Location: `logs/session_<id>_<timestamp>.csv`

Contains all trial and event information with timestamps.

### Stimulus Manifest
Location: `logs/manifest_<timestamp>.json`

Records all available stimuli and their assignments.

## Timing Accuracy

- Visual presentation: Synchronized to display refresh (~16.7 ms precision @ 60 Hz)
- Audio playback: Low-latency backends (PsychoPy, sounddevice)
- Event marking: Immediate LSL transmission after flip
- All timing via `psychopy.core.Clock` (no `time.sleep()`)

## Troubleshooting

### Audio Issues

If audio playback fails, the system tries backends in order:
1. PsychoPy sound (preferred)
2. sounddevice
3. pygame

Check audio device index in config.yaml if needed.

### Display Issues

Ensure physical display dimensions are correct in config for accurate visual angle calculations:
- `screen_width_cm`: Physical width in cm
- `viewing_distance_cm`: Distance from participant to screen
- `screen_width_px`: Resolution in pixels

### LSL Not Working

Install LSL library:
```bash
pip install pylsl
```

Test LSL with LabRecorder or LSL viewer applications.

### Missing Stimuli

Run dry-run to check which stimuli are missing:
```bash
python run_experiment.py --dry-run
```

The system will generate tones and TTS words if configured, but you must provide:
- Images for all tiers
- Environmental sounds (Tier 2)
- Sentence audio (Tier 4)

## Citation

If you use this system in your research, please cite:

```bibtex
@software{stimulus_presentation_system,
  title = {Stimulus Presentation System for Neural Decoding},
  author = {Your Name},
  year = {2024},
  url = {https://github.com/hildieleyser/stimulus_system}
}
```

## License

MIT License - see LICENSE file for details.

## Contact

For questions or issues, please open an issue on GitHub.

## Acknowledgments

Built with:
- [PsychoPy](https://www.psychopy.org/) - Stimulus presentation
- [Lab Streaming Layer](https://labstreaminglayer.org/) - Event synchronization
- [gTTS](https://github.com/pndurette/gTTS) - Text-to-speech
