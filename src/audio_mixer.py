"""
Audio Mixer Module

Mixes original audio (attenuated) with translated audio for simultaneous playback.
This allows users to hear both the original audio (reduced volume) and the
translation (full volume) at the same time.
"""
import numpy as np
import pyaudio
import threading
import queue
from typing import Optional, Tuple
from dataclasses import dataclass

try:
    from utils.logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


@dataclass
class MixerConfig:
    """Configuration for audio mixing"""
    original_volume: float = 0.3  # 30% of original volume
    translation_volume: float = 1.0  # 100% of translation volume
    sample_rate: int = 16000
    channels: int = 1
    output_device: Optional[int] = None


class AudioMixer:
    """
    Mixes original audio with translated audio

    Features:
    - Adjustable volume levels for original and translation
    - Real-time mixing and playback
    - Handles different audio lengths gracefully
    - Thread-safe operation
    """

    def __init__(self, config: Optional[MixerConfig] = None):
        """
        Initialize Audio Mixer

        Args:
            config: Mixer configuration (uses defaults if None)
        """
        self.config = config or MixerConfig()

        self.audio = pyaudio.PyAudio()
        self.output_stream = None
        self.is_playing = False

        # Mixing queue
        self.mix_queue = queue.Queue(maxsize=50)
        self.playback_thread = None

        # Thread control
        self._stop_event = threading.Event()

        logger.info("AudioMixer initialized",
                   original_volume=self.config.original_volume,
                   translation_volume=self.config.translation_volume)

    def mix_audio_arrays(self, original: np.ndarray,
                        translation: np.ndarray) -> np.ndarray:
        """
        Mix two audio arrays with volume adjustment

        Args:
            original: Original audio as numpy array (int16)
            translation: Translation audio as numpy array (int16)

        Returns:
            Mixed audio array (int16)
        """
        # Convert to float32 for mixing to avoid clipping
        original_float = original.astype(np.float32)
        translation_float = translation.astype(np.float32)

        # Apply volume levels
        original_attenuated = original_float * self.config.original_volume
        translation_amplified = translation_float * self.config.translation_volume

        # Align lengths - use the longer one and pad the shorter
        max_len = max(len(original_attenuated), len(translation_amplified))

        if len(original_attenuated) < max_len:
            original_attenuated = np.pad(
                original_attenuated,
                (0, max_len - len(original_attenuated)),
                mode='constant'
            )

        if len(translation_amplified) < max_len:
            translation_amplified = np.pad(
                translation_amplified,
                (0, max_len - len(translation_amplified)),
                mode='constant'
            )

        # Mix by adding
        mixed = original_attenuated + translation_amplified

        # Normalize to prevent clipping
        max_val = np.abs(mixed).max()
        if max_val > 32767:
            mixed = mixed * (32767 / max_val)

        # Convert back to int16
        mixed_int16 = mixed.astype(np.int16)

        logger.debug(
            "Audio mixed",
            original_length=len(original),
            translation_length=len(translation),
            mixed_length=len(mixed_int16),
            max_amplitude=int(max_val)
        )

        return mixed_int16

    def overlay_translation(self, original: np.ndarray,
                           translation: np.ndarray,
                           delay_ms: int = 0) -> np.ndarray:
        """
        Overlay translation audio on original with optional delay

        This is useful for aligning the translation timing with the original speech.

        Args:
            original: Original audio
            translation: Translation audio
            delay_ms: Delay before translation starts (milliseconds)

        Returns:
            Mixed audio with translation overlaid
        """
        # Calculate delay in samples
        delay_samples = int((delay_ms / 1000) * self.config.sample_rate)

        # Convert to float
        original_float = original.astype(np.float32) * self.config.original_volume
        translation_float = translation.astype(np.float32) * self.config.translation_volume

        # Calculate total length
        total_length = max(
            len(original_float),
            delay_samples + len(translation_float)
        )

        # Create output array
        mixed = np.zeros(total_length, dtype=np.float32)

        # Add original (full length)
        mixed[:len(original_float)] += original_float

        # Add translation (delayed)
        translation_start = delay_samples
        translation_end = delay_samples + len(translation_float)
        mixed[translation_start:translation_end] += translation_float

        # Normalize
        max_val = np.abs(mixed).max()
        if max_val > 32767:
            mixed = mixed * (32767 / max_val)

        return mixed.astype(np.int16)

    def play_mixed_audio(self, mixed_audio: np.ndarray):
        """
        Play mixed audio through speakers

        Args:
            mixed_audio: Mixed audio array to play
        """
        if self.output_stream is None:
            self._open_output_stream()

        try:
            # Convert to bytes
            audio_bytes = mixed_audio.tobytes()

            # Write to stream
            self.output_stream.write(audio_bytes)

            logger.debug(
                "Mixed audio played",
                duration_seconds=len(mixed_audio) / self.config.sample_rate
            )

        except Exception as e:
            logger.error_with_context(
                error=e,
                context="play_mixed_audio",
                audio_length=len(mixed_audio)
            )

    def play_translation_only(self, translation: np.ndarray):
        """
        Play only the translation audio (no mixing)

        Args:
            translation: Translation audio to play
        """
        if self.output_stream is None:
            self._open_output_stream()

        try:
            # Apply volume
            translation_float = translation.astype(np.float32)
            translation_adjusted = translation_float * self.config.translation_volume

            # Normalize
            max_val = np.abs(translation_adjusted).max()
            if max_val > 32767:
                translation_adjusted = translation_adjusted * (32767 / max_val)

            # Convert to bytes
            audio_bytes = translation_adjusted.astype(np.int16).tobytes()

            # Write to stream
            self.output_stream.write(audio_bytes)

            logger.debug("Translation audio played (solo mode)")

        except Exception as e:
            logger.error_with_context(
                error=e,
                context="play_translation_only"
            )

    def _open_output_stream(self):
        """Open PyAudio output stream"""
        try:
            self.output_stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=self.config.channels,
                rate=self.config.sample_rate,
                output=True,
                frames_per_buffer=1024,
                output_device_index=self.config.output_device
            )

            logger.info("Output stream opened for mixing")

        except Exception as e:
            logger.error_with_context(
                error=e,
                context="_open_output_stream",
                output_device=self.config.output_device
            )
            raise

    def start_continuous_mixing(self, original_stream_callback: callable,
                                translation_queue: queue.Queue):
        """
        Start continuous mixing mode (advanced)

        This allows real-time mixing of a continuous audio stream with
        queued translations as they arrive.

        Args:
            original_stream_callback: Callback to get original audio chunks
            translation_queue: Queue receiving translation audio
        """
        if self.is_playing:
            logger.warning("Continuous mixing already running")
            return

        self.is_playing = True
        self._stop_event.clear()

        self.playback_thread = threading.Thread(
            target=self._continuous_mix_loop,
            args=(original_stream_callback, translation_queue),
            daemon=True
        )
        self.playback_thread.start()

        logger.info("Continuous mixing started")

    def _continuous_mix_loop(self, original_callback, translation_queue):
        """Continuous mixing loop (runs in background thread)"""
        self._open_output_stream()

        current_translation = None
        translation_position = 0

        while not self._stop_event.is_set():
            try:
                # Get original audio chunk
                original_chunk = original_callback()

                if original_chunk is None:
                    continue

                # Check for new translation
                try:
                    current_translation = translation_queue.get_nowait()
                    translation_position = 0
                    logger.debug("New translation queued for mixing")
                except queue.Empty:
                    pass

                # Mix if we have a translation
                if current_translation is not None:
                    chunk_len = len(original_chunk)
                    translation_chunk = current_translation[
                        translation_position:translation_position + chunk_len
                    ]

                    if len(translation_chunk) > 0:
                        # Pad translation chunk if needed
                        if len(translation_chunk) < chunk_len:
                            translation_chunk = np.pad(
                                translation_chunk,
                                (0, chunk_len - len(translation_chunk)),
                                mode='constant'
                            )

                        # Mix
                        mixed = self.mix_audio_arrays(original_chunk, translation_chunk)
                        translation_position += chunk_len

                        # Check if translation finished
                        if translation_position >= len(current_translation):
                            current_translation = None
                    else:
                        # No more translation, just play original
                        mixed = (original_chunk.astype(np.float32) *
                                self.config.original_volume).astype(np.int16)
                else:
                    # No translation, play attenuated original
                    mixed = (original_chunk.astype(np.float32) *
                            self.config.original_volume).astype(np.int16)

                # Play mixed audio
                self.output_stream.write(mixed.tobytes())

            except Exception as e:
                logger.error(f"Error in continuous mix loop: {e}")

        logger.info("Continuous mixing stopped")

    def stop_continuous_mixing(self):
        """Stop continuous mixing mode"""
        if not self.is_playing:
            return

        self._stop_event.set()
        self.is_playing = False

        if self.playback_thread:
            self.playback_thread.join(timeout=2.0)

        logger.info("Continuous mixing stopped")

    def set_volumes(self, original_volume: Optional[float] = None,
                   translation_volume: Optional[float] = None):
        """
        Adjust volume levels

        Args:
            original_volume: Volume level for original audio (0.0 to 1.0)
            translation_volume: Volume level for translation (0.0 to 1.0)
        """
        if original_volume is not None:
            self.config.original_volume = max(0.0, min(1.0, original_volume))
            logger.info(f"Original volume set to {self.config.original_volume}")

        if translation_volume is not None:
            self.config.translation_volume = max(0.0, min(1.0, translation_volume))
            logger.info(f"Translation volume set to {self.config.translation_volume}")

    def cleanup(self):
        """Cleanup resources"""
        self.stop_continuous_mixing()

        if self.output_stream:
            try:
                self.output_stream.stop_stream()
                self.output_stream.close()
            except:
                pass

        if self.audio:
            self.audio.terminate()

        logger.info("AudioMixer cleaned up")

    def __del__(self):
        """Destructor"""
        self.cleanup()


# Utility functions

def create_fade_effect(audio: np.ndarray, fade_in_ms: int = 50,
                      fade_out_ms: int = 50,
                      sample_rate: int = 16000) -> np.ndarray:
    """
    Apply fade in/out effect to audio

    Args:
        audio: Input audio array
        fade_in_ms: Fade in duration in milliseconds
        fade_out_ms: Fade out duration in milliseconds
        sample_rate: Audio sample rate

    Returns:
        Audio with fade applied
    """
    audio_float = audio.astype(np.float32)

    # Calculate fade lengths in samples
    fade_in_samples = int((fade_in_ms / 1000) * sample_rate)
    fade_out_samples = int((fade_out_ms / 1000) * sample_rate)

    # Apply fade in
    if fade_in_samples > 0 and len(audio_float) > fade_in_samples:
        fade_in_curve = np.linspace(0, 1, fade_in_samples)
        audio_float[:fade_in_samples] *= fade_in_curve

    # Apply fade out
    if fade_out_samples > 0 and len(audio_float) > fade_out_samples:
        fade_out_curve = np.linspace(1, 0, fade_out_samples)
        audio_float[-fade_out_samples:] *= fade_out_curve

    return audio_float.astype(np.int16)


if __name__ == "__main__":
    # Test code
    print("Audio Mixer Test")
    print("=" * 60)

    # Create test audio
    sample_rate = 16000
    duration = 2.0

    # Generate test tones
    t = np.linspace(0, duration, int(sample_rate * duration))
    original = (np.sin(2 * np.pi * 440 * t) * 10000).astype(np.int16)  # 440 Hz
    translation = (np.sin(2 * np.pi * 880 * t) * 10000).astype(np.int16)  # 880 Hz

    # Create mixer
    config = MixerConfig(
        original_volume=0.3,
        translation_volume=1.0,
        sample_rate=sample_rate
    )

    mixer = AudioMixer(config)

    # Test mixing
    print("Mixing test audio...")
    mixed = mixer.mix_audio_arrays(original, translation)
    print(f"Mixed audio length: {len(mixed)} samples ({len(mixed)/sample_rate:.2f}s)")

    # Test fade
    print("\nApplying fade effect...")
    faded = create_fade_effect(translation, fade_in_ms=100, fade_out_ms=100)
    print(f"Faded audio created")

    mixer.cleanup()
    print("\nTest complete!")
