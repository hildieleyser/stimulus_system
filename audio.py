"""
Audio loading, normalization, tone generation, TTS, and playback.

Handles all audio stimulus generation and presentation with precise timing.
"""

import numpy as np
import soundfile as sf
from pathlib import Path
from typing import Dict, Optional, List
import warnings


class AudioManager:
    """
    Manages audio stimulus generation, loading, and playback.

    Attributes:
        config: Configuration dictionary
        sample_rate: Audio sample rate in Hz
        sounds: Dictionary caching loaded audio data
        backend: Audio backend (psychopy, sounddevice, or pygame)
    """

    def __init__(self, config: Dict, dry_run: bool = False):
        """
        Initialize audio manager and select playback backend.

        Args:
            config: Configuration dictionary
            dry_run: If True, skip backend initialization

        Notes:
            Tries psychopy.sound first, falls back to sounddevice or pygame.
            All audio normalized to target LUFS on load.
        """
        self.config = config
        self.sample_rate = config.get('sample_rate', 44100)
        self.target_loudness = config.get('target_loudness_lufs', -23)
        self.sounds = {}  # Cache for loaded sounds
        self.backend = None
        self.dry_run = dry_run

        if not dry_run:
            self._initialize_backend()

        # Ensure tone directory exists
        tone_dir = Path(config.get('stimuli_dir', 'stimuli')) / 'audio' / 'tones'
        tone_dir.mkdir(parents=True, exist_ok=True)

    def _initialize_backend(self):
        """
        Initialize audio playback backend.

        Notes:
            Priority: psychopy.sound > sounddevice > pygame
            PsychoPy sound is preferred for timing accuracy.
        """
        # Try psychopy first (best for stimulus presentation)
        try:
            from psychopy import sound
            sound.init(rate=self.sample_rate, buffer=128)
            self.backend = 'psychopy'
            print(f"Audio backend: PsychoPy (sample rate: {self.sample_rate} Hz)")
            return
        except ImportError:
            pass
        except Exception as e:
            print(f"Warning: PsychoPy sound initialization failed: {e}")

        # Try sounddevice
        try:
            import sounddevice as sd
            sd.default.samplerate = self.sample_rate
            device_index = self.config.get('audio_device_index', 0)
            if device_index >= 0:
                sd.default.device = device_index
            self.backend = 'sounddevice'
            print(f"Audio backend: sounddevice (sample rate: {self.sample_rate} Hz)")
            return
        except ImportError:
            pass
        except Exception as e:
            print(f"Warning: sounddevice initialization failed: {e}")

        # Fallback to pygame
        try:
            import pygame
            pygame.mixer.init(frequency=self.sample_rate, size=-16, channels=2, buffer=512)
            self.backend = 'pygame'
            print(f"Audio backend: pygame (sample rate: {self.sample_rate} Hz)")
            return
        except ImportError:
            pass
        except Exception as e:
            print(f"Warning: pygame initialization failed: {e}")

        print("Warning: No audio backend available")
        self.backend = None

    def generate_pure_tone(self, frequency: float, duration_ms: float,
                          output_path: Optional[Path] = None) -> np.ndarray:
        """
        Generate a pure sine wave tone.

        Args:
            frequency: Frequency in Hz
            duration_ms: Duration in milliseconds
            output_path: Optional path to save WAV file

        Returns:
            Audio data as numpy array (float32, range -1 to 1)

        Notes:
            Uses simple sine wave generation. Adds 5ms fade in/out to prevent clicks.
        """
        duration_s = duration_ms / 1000.0
        n_samples = int(self.sample_rate * duration_s)

        # Generate sine wave
        t = np.linspace(0, duration_s, n_samples, endpoint=False)
        audio = np.sin(2 * np.pi * frequency * t).astype(np.float32)

        # Add fade in/out to prevent clicks (5ms)
        fade_samples = int(self.sample_rate * 0.005)
        fade_in = np.linspace(0, 1, fade_samples)
        fade_out = np.linspace(1, 0, fade_samples)

        audio[:fade_samples] *= fade_in
        audio[-fade_samples:] *= fade_out

        # Normalize to -1 to 1 range
        audio = audio * 0.5  # Reduce amplitude to be comfortable

        # Save if path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            sf.write(str(output_path), audio, self.sample_rate)

        return audio

    def generate_tone_set(self, n_tones: int = 10) -> List[Path]:
        """
        Generate a set of pure tones with varying frequencies.

        Args:
            n_tones: Number of tones to generate

        Returns:
            List of paths to generated tone files

        Notes:
            Frequencies linearly spaced between freq_min and freq_max from config.
            Only generates tones that don't already exist.
        """
        if not self.config.get('generate_tones', True):
            return []

        freq_min = self.config.get('tone_freq_min_hz', 440)
        freq_max = self.config.get('tone_freq_max_hz', 880)
        duration_ms = self.config.get('tone_duration_ms', 500)

        tone_dir = Path(self.config.get('stimuli_dir', 'stimuli')) / 'audio' / 'tones'
        tone_dir.mkdir(parents=True, exist_ok=True)

        frequencies = np.linspace(freq_min, freq_max, n_tones)
        tone_paths = []

        for i, freq in enumerate(frequencies):
            tone_path = tone_dir / f'tone_{int(freq)}hz.wav'

            if not tone_path.exists():
                print(f"Generating tone: {freq:.1f} Hz")
                self.generate_pure_tone(freq, duration_ms, tone_path)

            tone_paths.append(tone_path)

        return tone_paths

    def generate_word_tts(self, word: str, output_path: Path, language: str = 'en'):
        """
        Generate spoken word using text-to-speech.

        Args:
            word: Word to synthesize
            output_path: Path to save audio file
            language: Language code (default 'en')

        Notes:
            Uses gTTS (Google Text-to-Speech).
            Requires internet connection.
            Only generates if file doesn't exist.
        """
        if output_path.exists():
            return

        try:
            from gtts import gTTS
            output_path.parent.mkdir(parents=True, exist_ok=True)

            tts = gTTS(text=word, lang=language, slow=False)
            tts.save(str(output_path))
            print(f"Generated TTS for word: {word}")

        except ImportError:
            print("Warning: gTTS not installed, cannot generate speech")
        except Exception as e:
            print(f"Warning: Failed to generate TTS for '{word}': {e}")

    def generate_words_for_categories(self, categories: List[str]):
        """
        Generate TTS words for all categories.

        Args:
            categories: List of category names to generate words for

        Notes:
            Creates spoken word files for Tier 3 stimuli.
            Only generates missing files.
        """
        if not self.config.get('generate_words_tts', True):
            return

        language = self.config.get('tts_language', 'en')
        audio_dir = Path(self.config.get('stimuli_dir', 'stimuli')) / 'audio'

        for category in categories:
            word_dir = audio_dir / category / 'words'
            word_dir.mkdir(parents=True, exist_ok=True)

            word_path = word_dir / f'{category}.wav'
            if not word_path.exists():
                self.generate_word_tts(category, word_path, language)

    def load_audio(self, file_path: str) -> np.ndarray:
        """
        Load audio file and normalize.

        Args:
            file_path: Path to audio file

        Returns:
            Audio data as numpy array (float32)

        Notes:
            Caches loaded audio to avoid reloading.
            Normalizes to target LUFS using pyloudnorm.
        """
        # Check cache
        if file_path in self.sounds:
            return self.sounds[file_path]

        # Load audio file
        try:
            audio, sr = sf.read(file_path, always_2d=False, dtype='float32')

            # Resample if necessary
            if sr != self.sample_rate:
                audio = self._resample(audio, sr, self.sample_rate)

            # Normalize loudness
            audio = self._normalize_loudness(audio)

            # Cache
            self.sounds[file_path] = audio

            return audio

        except Exception as e:
            print(f"Error loading audio {file_path}: {e}")
            # Return silence as fallback
            return np.zeros(int(self.sample_rate * 0.5), dtype=np.float32)

    def _resample(self, audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """
        Resample audio to target sample rate.

        Args:
            audio: Audio data
            orig_sr: Original sample rate
            target_sr: Target sample rate

        Returns:
            Resampled audio

        Notes:
            Uses simple linear interpolation for speed.
            For better quality, could use scipy.signal.resample.
        """
        if orig_sr == target_sr:
            return audio

        # Simple linear interpolation (fast but lower quality)
        duration = len(audio) / orig_sr
        n_samples_new = int(duration * target_sr)

        indices = np.linspace(0, len(audio) - 1, n_samples_new)
        resampled = np.interp(indices, np.arange(len(audio)), audio)

        return resampled.astype(np.float32)

    def _normalize_loudness(self, audio: np.ndarray) -> np.ndarray:
        """
        Normalize audio to target LUFS loudness.

        Args:
            audio: Audio data

        Returns:
            Normalized audio

        Notes:
            Uses pyloudnorm for perceptually-based loudness normalization.
            Falls back to peak normalization if pyloudnorm unavailable.
        """
        try:
            import pyloudnorm as pyln

            # Ensure audio is 2D for loudness meter (handles mono/stereo)
            if audio.ndim == 1:
                audio_2d = audio.reshape(-1, 1)
            else:
                audio_2d = audio

            # Measure loudness
            meter = pyln.Meter(self.sample_rate)
            loudness = meter.integrated_loudness(audio_2d)

            # Normalize
            normalized = pyln.normalize.loudness(audio_2d, loudness, self.target_loudness)

            # Return in original shape
            if audio.ndim == 1:
                normalized = normalized.flatten()

            return normalized.astype(np.float32)

        except ImportError:
            # Fallback: simple peak normalization
            peak = np.abs(audio).max()
            if peak > 0:
                return (audio / peak * 0.5).astype(np.float32)
            return audio
        except Exception as e:
            print(f"Warning: Loudness normalization failed: {e}")
            return audio

    def play_audio(self, audio_data: np.ndarray):
        """
        Play audio through selected backend.

        Args:
            audio_data: Audio data to play (numpy array)

        Notes:
            Non-blocking - returns immediately while audio plays.
            Timing-critical: call immediately after onset marker.
        """
        if self.dry_run or self.backend is None:
            return

        try:
            if self.backend == 'psychopy':
                from psychopy import sound
                # Create sound object and play
                snd = sound.Sound(audio_data, sampleRate=self.sample_rate)
                snd.play()

            elif self.backend == 'sounddevice':
                import sounddevice as sd
                # Play non-blocking
                sd.play(audio_data, self.sample_rate)

            elif self.backend == 'pygame':
                import pygame
                # Convert to pygame Sound
                # Need to convert to 16-bit int for pygame
                audio_int16 = (audio_data * 32767).astype(np.int16)
                sound_obj = pygame.sndarray.make_sound(audio_int16)
                sound_obj.play()

        except Exception as e:
            print(f"Warning: Audio playback failed: {e}")

    def play_audio_file(self, file_path: str):
        """
        Load and play audio file.

        Args:
            file_path: Path to audio file

        Notes:
            Convenience method that loads (with caching) and plays.
        """
        audio_data = self.load_audio(file_path)
        self.play_audio(audio_data)

    def stop_all(self):
        """
        Stop all playing audio.

        Notes:
            Backend-specific stop methods.
        """
        if self.dry_run or self.backend is None:
            return

        try:
            if self.backend == 'psychopy':
                from psychopy import sound
                sound.Sound().stop()

            elif self.backend == 'sounddevice':
                import sounddevice as sd
                sd.stop()

            elif self.backend == 'pygame':
                import pygame
                pygame.mixer.stop()

        except Exception as e:
            print(f"Warning: Failed to stop audio: {e}")

    def get_duration(self, file_path: str) -> float:
        """
        Get duration of audio file in seconds.

        Args:
            file_path: Path to audio file

        Returns:
            Duration in seconds

        Notes:
            Reads file metadata without loading full audio.
        """
        try:
            info = sf.info(file_path)
            return info.duration
        except Exception as e:
            print(f"Warning: Could not get duration for {file_path}: {e}")
            return 1.0  # Default fallback
