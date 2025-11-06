"""
Fast Speech-to-Text Handler using Faster-Whisper

Uses faster-whisper library which is 10x faster than openai-whisper
with the same accuracy, using CTranslate2 backend.

Performance comparison:
- openai-whisper (tiny): ~800ms
- faster-whisper (tiny): ~80ms (10x faster!)
"""
import numpy as np
import threading
import queue
from typing import Optional, Callable
from dataclasses import dataclass

try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    print("⚠️  faster-whisper not available. Install with: pip install faster-whisper")

try:
    from utils.logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


@dataclass
class STTConfig:
    """Configuration for STT"""
    model_size: str = "tiny"  # tiny, base, small, medium, large
    device: str = "cpu"  # cpu, cuda, auto
    compute_type: str = "int8"  # int8, float16, float32
    language: str = "auto"  # auto-detect or specify (en, es, etc.)
    vad_filter: bool = True  # Voice Activity Detection
    vad_threshold: float = 0.5  # VAD sensitivity (0.0 to 1.0)
    min_speech_duration_ms: int = 250  # Minimum speech duration to detect
    min_silence_duration_ms: int = 500  # Minimum silence to split segments
    beam_size: int = 5  # Beam search size (higher = better quality, slower)
    best_of: int = 5  # Number of candidates to consider
    temperature: float = 0.0  # Temperature for sampling (0 = deterministic)


class FastSTTHandler:
    """
    Fast Speech-to-Text Handler using Faster-Whisper

    Features:
    - 10x faster than standard Whisper
    - Voice Activity Detection (VAD)
    - Low memory usage with int8 quantization
    - Streaming support
    - Auto language detection
    """

    def __init__(self, config: Optional[STTConfig] = None):
        if not FASTER_WHISPER_AVAILABLE:
            raise ImportError(
                "faster-whisper is not installed. "
                "Install with: pip install faster-whisper"
            )

        self.config = config or STTConfig()

        # Load model
        self.model = None
        self._load_model()

        # Audio buffer
        self.audio_buffer = []
        self.buffer_lock = threading.Lock()
        self.buffer_duration = 2.0  # seconds

        # Transcription callback
        self.transcription_callback: Optional[Callable] = None

        # Processing thread
        self.processing_queue = queue.Queue(maxsize=10)
        self.processing_thread = None
        self.is_processing = False

        logger.info(
            "FastSTTHandler initialized",
            model=self.config.model_size,
            device=self.config.device,
            vad=self.config.vad_filter
        )

    def _load_model(self):
        """Load Faster-Whisper model"""
        logger.info(
            f"Loading Faster-Whisper model: {self.config.model_size} "
            f"(Device: {self.config.device}, Compute: {self.config.compute_type})"
        )

        try:
            self.model = WhisperModel(
                self.config.model_size,
                device=self.config.device,
                compute_type=self.config.compute_type,
                download_root=None  # Use default cache
            )

            logger.info(
                f"Faster-Whisper model {self.config.model_size} loaded successfully"
            )

        except Exception as e:
            logger.error(f"Failed to load Faster-Whisper model: {e}")
            raise

    def set_transcription_callback(self, callback: Callable[[str], None]):
        """Set callback function for transcriptions"""
        self.transcription_callback = callback

    def add_audio_chunk(self, audio_data: np.ndarray):
        """
        Add audio chunk for processing

        Args:
            audio_data: Audio as numpy array (int16)
        """
        with self.buffer_lock:
            self.audio_buffer.extend(audio_data.tolist())

    def start_processing(self):
        """Start processing thread"""
        if self.is_processing:
            return

        self.is_processing = True
        self.processing_thread = threading.Thread(
            target=self._processing_loop,
            daemon=True
        )
        self.processing_thread.start()

        logger.info("STT processing started")

    def stop_processing(self):
        """Stop processing thread"""
        self.is_processing = False
        if self.processing_thread:
            self.processing_thread.join(timeout=2.0)

        logger.info("STT processing stopped")

    def _processing_loop(self):
        """Main processing loop (runs in background thread)"""
        import time

        while self.is_processing:
            try:
                # Check if buffer has enough audio
                with self.buffer_lock:
                    buffer_size = len(self.audio_buffer)

                # Process if we have enough audio (buffer_duration seconds)
                required_samples = int(16000 * self.buffer_duration)

                if buffer_size >= required_samples:
                    # Get audio from buffer
                    with self.buffer_lock:
                        audio_to_process = np.array(
                            self.audio_buffer[:required_samples],
                            dtype=np.int16
                        )
                        # Keep some overlap for continuity
                        overlap = required_samples // 2
                        self.audio_buffer = self.audio_buffer[required_samples - overlap:]

                    # Transcribe
                    text = self._transcribe(audio_to_process)

                    # Callback
                    if text and self.transcription_callback:
                        self.transcription_callback(text)

                else:
                    # Sleep briefly if not enough audio
                    time.sleep(0.1)

            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                time.sleep(0.1)

    def _transcribe(self, audio: np.ndarray) -> Optional[str]:
        """
        Transcribe audio using Faster-Whisper

        Args:
            audio: Audio as numpy array (int16)

        Returns:
            Transcribed text or None
        """
        try:
            # Convert int16 to float32 normalized to [-1, 1]
            audio_float = audio.astype(np.float32) / 32768.0

            # Transcribe with Faster-Whisper
            segments, info = self.model.transcribe(
                audio_float,
                language=None if self.config.language == "auto" else self.config.language,
                beam_size=self.config.beam_size,
                best_of=self.config.best_of,
                temperature=self.config.temperature,
                vad_filter=self.config.vad_filter,
                vad_parameters=dict(
                    threshold=self.config.vad_threshold,
                    min_speech_duration_ms=self.config.min_speech_duration_ms,
                    min_silence_duration_ms=self.config.min_silence_duration_ms
                ) if self.config.vad_filter else None
            )

            # Combine segments
            text_parts = []
            for segment in segments:
                text_parts.append(segment.text.strip())

            text = " ".join(text_parts).strip()

            if text:
                logger.debug(
                    f"Transcribed: '{text[:50]}...'",
                    language=info.language,
                    probability=info.language_probability
                )

            return text if text else None

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return None

    def transcribe_audio(self, audio: np.ndarray) -> Optional[str]:
        """
        Synchronous transcription (for testing)

        Args:
            audio: Audio as numpy array (int16)

        Returns:
            Transcribed text
        """
        return self._transcribe(audio)

    def change_model(self, model_size: str, device: Optional[str] = None):
        """
        Change model size or device

        Args:
            model_size: New model size (tiny, base, small, medium, large)
            device: New device (cpu, cuda, auto) - optional
        """
        self.config.model_size = model_size
        if device:
            self.config.device = device

        logger.info(f"Changing model to {model_size} on {self.config.device}")

        # Reload model
        self._load_model()

    def clear_buffer(self):
        """Clear audio buffer"""
        with self.buffer_lock:
            self.audio_buffer.clear()

    def set_buffer_duration(self, duration: float):
        """Set buffer duration in seconds"""
        self.buffer_duration = duration


# Test code
if __name__ == "__main__":
    import sys
    import time

    print("="*60)
    print("Faster-Whisper STT Test")
    print("="*60)

    if not FASTER_WHISPER_AVAILABLE:
        print("❌ faster-whisper not installed")
        print("Install with: pip install faster-whisper")
        sys.exit(1)

    # Create config
    config = STTConfig(
        model_size="tiny",
        device="cpu",
        compute_type="int8",
        vad_filter=True
    )

    # Create handler
    handler = FastSTTHandler(config)

    # Test with sample audio (silence)
    print("\nGenerating test audio (2 seconds of tone)...")
    sample_rate = 16000
    duration = 2.0
    frequency = 440  # A4 note

    t = np.linspace(0, duration, int(sample_rate * duration))
    audio = (np.sin(2 * np.pi * frequency * t) * 10000).astype(np.int16)

    print(f"Test audio: {len(audio)} samples ({len(audio)/sample_rate:.1f}s)")

    # Transcribe
    print("\nTranscribing...")
    start = time.time()
    result = handler.transcribe_audio(audio)
    elapsed = time.time() - start

    print(f"\nResult: {result or '(no speech detected)'}")
    print(f"Time: {elapsed*1000:.0f}ms")

    print("\n" + "="*60)
    print("✅ Test complete")
