"""
Real-time Translation App - PROFESSIONAL VERSION (v3)

New Features:
- Faster-Whisper (10x faster STT)
- Subtitle overlay (transparent, always-on-top)
- Voice Activity Detection (VAD)
- Real-time latency monitoring
- Enhanced UI with mode selector
- Professional error handling
- Advanced metrics

Target latency: <1.5s end-to-end
"""
import sys
import threading
import time
import json
import os
import numpy as np
import torch
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

# Core handlers
from audio_handler import AudioHandler
from ui import TranslationAppUI

# New professional modules
from system_audio_capture import SystemAudioCapture, check_blackhole_installed
from audio_mixer import AudioMixer, MixerConfig
from subtitle_overlay import SubtitleOverlay, SubtitleConfig, SubtitlePosition
from utils.logger import get_logger, setup_app_logging
from utils.metrics import PerformanceMetrics, LatencyTimer

# Try Faster-Whisper first, fallback to standard
try:
    from stt_handler_fast import FastSTTHandler, STTConfig, FASTER_WHISPER_AVAILABLE
    if FASTER_WHISPER_AVAILABLE:
        STT_HANDLER = "faster-whisper"
    else:
        from stt_handler import STTHandler
        STT_HANDLER = "whisper"
except ImportError:
    from stt_handler import STTHandler
    STT_HANDLER = "whisper"
    print("⚠️  Using standard Whisper (slower). Install faster-whisper for 10x speed boost")

# Translation and TTS
try:
    from translation_handler import TranslationHandler
    TRANSLATION_AVAILABLE = True
except ImportError:
    TRANSLATION_AVAILABLE = False

try:
    from advanced_tts_handler import AdvancedTTSHandler
    TTS_AVAILABLE = True
    # Use the advanced TTS handler
    TTSHandler = AdvancedTTSHandler
except ImportError:
    # If the advanced handler is not available, fall back to the regular one
    try:
        from tts_handler import TTSHandler
        TTS_AVAILABLE = True
    except ImportError:
        TTS_AVAILABLE = False


@dataclass
class AppConfig:
    """Application configuration"""
    config_path: Path
    audio: dict
    system_audio: dict
    stt: dict
    translation: dict
    tts: dict
    mixer: dict
    subtitle_overlay: dict
    performance: dict

    @classmethod
    def load(cls, config_path: Path):
        """Load configuration from JSON file"""
        with open(config_path, 'r') as f:
            data = json.load(f)
        return cls(config_path=config_path, **data)

    def save(self):
        """Save configuration to JSON file"""
        data = {
            'audio': self.audio,
            'system_audio': self.system_audio,
            'stt': self.stt,
            'translation': self.translation,
            'tts': self.tts,
            'mixer': self.mixer,
            'subtitle_overlay': self.subtitle_overlay,
            'performance': self.performance
        }
        with open(self.config_path, 'w') as f:
            json.dump(data, f, indent=2)


class TranslationAppPro:
    """
    Professional Translation App with advanced features

    Features:
    - Faster-Whisper for 10x faster STT
    - Subtitle overlay
    - System audio + microphone
    - Audio mixing
    - Real-time metrics
    - Professional logging
    """

    def __init__(self, config_path: Optional[Path] = None):
        # Load configuration
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config.json"

        self.config = AppConfig.load(config_path)

        # Setup logging
        log_dir = None
        if self.config.performance['log_metrics']:
            log_dir = Path(self.config.performance['log_dir'])

        self.logger = setup_app_logging(log_dir=log_dir, json_output=False)

        self.logger.info("="*60)
        self.logger.info("Real-time Translation App PRO Starting")
        self.logger.info(f"STT Engine: {STT_HANDLER}")
        self.logger.info("="*60)

        # Performance metrics
        self.metrics = PerformanceMetrics()

        # Input mode
        self.input_mode = self.config.audio.get('input_mode', 'microphone')

        # Audio handlers
        self.audio_handler = AudioHandler(
            sample_rate=self.config.audio['sample_rate'],
            chunk_size=self.config.audio['chunk_size']
        )

        self.system_audio = None
        if self.input_mode == 'system' or self.config.system_audio.get('enabled'):
            self._init_system_audio()

        # Audio mixer
        self.mixer = None
        if self.config.mixer.get('enabled'):
            self._init_mixer()

        # Subtitle overlay
        self.subtitle_overlay = None
        if self.config.subtitle_overlay.get('enabled'):
            self._init_subtitle_overlay()

        # Initialize AI handlers
        self.stt_handler = self._init_stt()
        self.translation_handler = self._init_translation()
        self.tts_handler = self._init_tts()

        # Set up callbacks
        if self.stt_handler:
            if STT_HANDLER == "faster-whisper":
                self.stt_handler.set_transcription_callback(self.on_transcription)
                self.stt_handler.start_processing()
            else:
                self.stt_handler.set_transcription_callback(self.on_transcription)

        # UI reference
        self.ui = None
        self.is_translating = False
        self.current_input_device = None
        self.current_output_device = None

        # TTS control (start disabled, user selects mode from UI)
        self.tts_enabled = False

        # Latency tracking
        self.last_transcription_time = None
        self.last_translation_time = None

        # Deduplication tracking
        self.recent_transcriptions = []  # Store last N transcriptions
        self.max_recent_transcriptions = 10  # Keep last 10
        self.similarity_threshold = 0.7  # 70% similarity = duplicate

        # Sentence accumulator (for complete sentences)
        self.sentence_buffer = ""  # Accumulate fragments
        self.buffer_start_time = None  # When buffer started accumulating
        self.last_fragment_time = None  # When last fragment was added
        self.sentence_timeout = 2.5  # Seconds to wait before flushing buffer
        self.min_sentence_length = 50  # Minimum characters for a sentence

        self.logger.info(
            "TranslationApp PRO initialized",
            input_mode=self.input_mode,
            mixer_enabled=self.mixer is not None,
            subtitles_enabled=self.subtitle_overlay is not None,
            stt_engine=STT_HANDLER
        )

    def _init_system_audio(self):
        """Initialize system audio capture"""
        try:
            is_installed, device_info = check_blackhole_installed()

            if not is_installed:
                self.logger.warning("BlackHole not detected")
                return

            self.system_audio = SystemAudioCapture(
                sample_rate=self.config.audio['sample_rate'],
                chunk_size=self.config.audio['chunk_size']
            )

            if self.config.system_audio.get('auto_detect'):
                self.system_audio.setup_device()
            else:
                device_name = self.config.system_audio.get('device_name')
                self.system_audio.setup_device(device_name=device_name)

            self.logger.info(
                "System audio initialized",
                device=self.system_audio.selected_device_name
            )

        except Exception as e:
            self.logger.log_error_with_context(
                error=e,
                context="_init_system_audio"
            )

    def _init_mixer(self):
        """Initialize audio mixer"""
        try:
            mixer_config = MixerConfig(
                original_volume=self.config.mixer['original_volume'],
                translation_volume=self.config.mixer['translation_volume'],
                sample_rate=self.config.audio['sample_rate'],
                output_device=self.config.audio.get('output_device')
            )

            self.mixer = AudioMixer(mixer_config)
            self.logger.info("Audio mixer initialized")

        except Exception as e:
            self.logger.log_error_with_context(error=e, context="_init_mixer")

    def _init_subtitle_overlay(self):
        """Initialize subtitle overlay"""
        try:
            position_map = {
                "top": SubtitlePosition.TOP,
                "bottom": SubtitlePosition.BOTTOM,
                "center": SubtitlePosition.CENTER
            }

            subtitle_config = SubtitleConfig(
                position=position_map.get(
                    self.config.subtitle_overlay.get('position', 'bottom'),
                    SubtitlePosition.BOTTOM
                ),
                font_size=self.config.subtitle_overlay.get('font_size', 28),
                show_original=self.config.subtitle_overlay.get('show_original', True),
                show_translation=self.config.subtitle_overlay.get('show_translation', True),
                auto_hide_seconds=self.config.subtitle_overlay.get('auto_hide_seconds', 5)
            )

            self.subtitle_overlay = SubtitleOverlay(subtitle_config)
            self.logger.info("Subtitle overlay initialized")

        except Exception as e:
            self.logger.log_error_with_context(error=e, context="_init_subtitle_overlay")

    def _init_stt(self):
        """Initialize Speech-to-Text handler"""
        try:
            model_size = self.config.stt['model_size']
            use_gpu = self.config.stt['use_gpu']

            # Force CPU for Apple Silicon
            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                use_gpu = False

            if STT_HANDLER == "faster-whisper":
                # Use Faster-Whisper
                stt_config = STTConfig(
                    model_size=model_size,
                    device="cpu",  # Always CPU for now
                    compute_type="int8",
                    language=self.config.stt.get('language', 'auto'),
                    vad_filter=self.config.stt.get('vad_filter', True),
                    vad_threshold=self.config.stt.get('vad_threshold', 0.5),
                    min_speech_duration_ms=self.config.stt.get('min_speech_duration_ms', 250),
                    min_silence_duration_ms=self.config.stt.get('min_silence_duration_ms', 500),
                    temperature=self.config.stt.get('temperature', 0.0)
                )

                stt = FastSTTHandler(stt_config)
                self.logger.info(
                    "Faster-Whisper STT initialized (10x faster!)",
                    model=model_size,
                    vad=stt_config.vad_filter
                )
            else:
                # Use standard Whisper
                stt = STTHandler(model_size=model_size, use_gpu=use_gpu)
                stt.set_buffer_duration(1.0)
                self.logger.info("Standard Whisper STT initialized", model=model_size)

            return stt

        except Exception as e:
            self.logger.log_error_with_context(error=e, context="_init_stt")
            return None

    def _init_translation(self):
        """Initialize translation handler"""
        if not TRANSLATION_AVAILABLE:
            return None

        try:
            source_lang = self.config.translation['language_from']
            target_lang = self.config.translation['language_to']

            model_map = {
                ("es", "en"): "Helsinki-NLP/opus-mt-es-en",
                ("en", "es"): "Helsinki-NLP/opus-mt-en-es",
                ("fr", "en"): "Helsinki-NLP/opus-mt-fr-en",
                ("en", "fr"): "Helsinki-NLP/opus-mt-en-fr",
                ("de", "en"): "Helsinki-NLP/opus-mt-de-en",
                ("en", "de"): "Helsinki-NLP/opus-mt-en-de",
                ("it", "en"): "Helsinki-NLP/opus-mt-it-en",
                ("en", "it"): "Helsinki-NLP/opus-mt-en-it",
                ("pt", "en"): "Helsinki-NLP/opus-mt-pt-en",
                ("en", "pt"): "Helsinki-NLP/opus-mt-en-pt",
            }

            model_name = model_map.get(
                (source_lang, target_lang),
                self.config.translation.get('model', "Helsinki-NLP/opus-mt-en-es")
            )

            translation = TranslationHandler(model_name=model_name, use_gpu=False)

            self.logger.info(
                "Translation initialized",
                model=model_name,
                pair=f"{source_lang}->{target_lang}"
            )
            return translation

        except Exception as e:
            self.logger.log_error_with_context(error=e, context="_init_translation")
            return None

    def _init_tts(self):
        """Initialize Text-to-Speech handler with high-quality settings"""
        if not TTS_AVAILABLE or not self.config.tts.get('enabled'):
            return None

        try:
            # Always use Mónica voice - no option to change
            tts = TTSHandler(
                voice='Mónica',
                rate=self.config.tts.get('rate', 180),  # Slightly slower for better clarity
                volume=self.config.tts.get('volume', 0.9),  # Slightly lower for better quality
                use_macos_say=True,  # Force macOS 'say' for better quality
                output_device=self.config.tts.get('output_device', None)
            )

            self.logger.info("TTS initialized", voice='Mónica')
            return tts

        except Exception as e:
            self.logger.log_error_with_context(error=e, context="_init_tts")
            return None

    def set_tts_enabled(self, enabled: bool):
        """Enable or disable TTS dynamically"""
        self.tts_enabled = enabled

        if enabled:
            # Initialize TTS if not already initialized
            if not self.tts_handler and TTS_AVAILABLE:
                self.tts_handler = self._init_tts()

            if self.tts_handler:
                self.logger.info("TTS enabled dynamically")
                print("✅ TTS enabled - Audio + Subtitles mode")
                print("🔊 Usando voz: Mónica")
            else:
                self.logger.warning("Failed to enable TTS")
                print("⚠️ Failed to enable TTS - check that voice is available")
        else:
            # Disable TTS
            self.logger.info("TTS disabled dynamically")
            print("🎬 TTS disabled - Subtitles Only mode")
            # Stop current speech
            if self.tts_handler:
                self.tts_handler.stop_speaking()

    def start_translation_process(self, ui=None):
        """Start translation process"""
        if self.is_translating:
            return

        self.is_translating = True
        self.ui = ui

        try:
            # Start appropriate audio input
            if self.input_mode == 'system' and self.system_audio:
                self.system_audio.start_capture(callback=self.process_audio_chunk)
            else:
                self.audio_handler.start_recording(device_index=self.current_input_device)
                self.audio_handler.set_audio_callback(self.process_audio_chunk)

            # Show subtitle overlay if enabled
            if self.subtitle_overlay:
                self.subtitle_overlay.show()

            # Clear UI
            if ui:
                ui.clear_text_displays()

            # Provide feedback about which mode is active
            if self.tts_enabled:
                print("🔊 Audio + Subtitles mode: Original audio will be translated and spoken")
                print("   (You will hear the translated text instead of the original)")
            else:
                print("🎬 Subtitles Only mode: Original audio continues normally")
                print("   (You will see translated text but hear original audio)")

            self.logger.info("Translation process started")

        except Exception as e:
            self.logger.log_error_with_context(error=e, context="start_translation_process")
            self.is_translating = False

    def stop_translation_process(self):
        """Stop translation process"""
        if not self.is_translating:
            return

        self.is_translating = False

        try:
            # Stop audio
            if self.input_mode == 'system' and self.system_audio:
                self.system_audio.stop_capture()
            else:
                self.audio_handler.stop_recording()

            # Hide subtitles
            if self.subtitle_overlay:
                self.subtitle_overlay.hide()

            # Process any pending sentence in buffer
            if self.sentence_buffer.strip() and len(self.sentence_buffer) >= self.min_sentence_length:
                self.logger.info(f"Processing pending buffer: '{self.sentence_buffer[:50]}...'")
                if self.ui:
                    self.ui.update_original_text(self.sentence_buffer)
                self.process_translation(self.sentence_buffer)

            # Clear sentence buffer
            self.sentence_buffer = ""
            self.buffer_start_time = None
            self.last_fragment_time = None

            # Clear STT buffer
            if self.stt_handler:
                if STT_HANDLER == "faster-whisper":
                    self.stt_handler.clear_buffer()
                else:
                    self.stt_handler.clear_audio_buffer()

            # Print metrics
            if self.config.performance['log_metrics']:
                self.metrics.print_summary()

            self.logger.info("Translation process stopped")

        except Exception as e:
            self.logger.log_error_with_context(error=e, context="stop_translation_process")

    def process_audio_chunk(self, audio_data: np.ndarray):
        """Process audio chunk"""
        if not self.is_translating:
            return

        # NOTE: No need to pause capture during TTS because:
        # - System audio (BlackHole 2ch) is separate from TTS output (TTS Output/BlackHole 16ch)
        # - No feedback loop possible with this setup
        # - Pausing would cause audio loss from the source (YouTube, etc.)

        # Add to STT
        if self.stt_handler:
            if STT_HANDLER == "faster-whisper":
                self.stt_handler.add_audio_chunk(audio_data)
            else:
                self.stt_handler.add_audio_chunk_optimized(audio_data)

    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """Calculate similarity ratio between two strings (0.0 to 1.0)"""
        s1_clean = s1.lower().strip()
        s2_clean = s2.lower().strip()

        if not s1_clean or not s2_clean:
            return 0.0

        if s1_clean == s2_clean:
            return 1.0

        # Simple word-based similarity
        words1 = set(s1_clean.split())
        words2 = set(s2_clean.split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def _is_duplicate(self, text: str) -> bool:
        """Check if text is duplicate of recent transcriptions"""
        text_clean = text.lower().strip()

        # Check against recent transcriptions
        for recent in self.recent_transcriptions:
            similarity = self._calculate_similarity(text_clean, recent)
            if similarity >= self.similarity_threshold:
                return True

        return False

    def _is_sentence_complete(self, text: str) -> bool:
        """Check if text ends with sentence-ending punctuation (not ellipsis)"""
        text = text.strip()
        if not text:
            return False

        # Remove trailing ellipsis (... or ....)
        while text.endswith('...') or text.endswith('....'):
            text = text[:-3].strip()

        if not text:
            return False

        # Check if ends with real sentence-ending punctuation
        return text[-1] in '.!?;'

    def _clean_word_loops(self, text: str) -> str:
        """Remove word loops like 'new, new, new, new...'"""
        words = text.split()
        if len(words) < 3:
            return text

        cleaned = []
        i = 0
        loops_found = []

        while i < len(words):
            word = words[i]
            # Count consecutive identical words
            count = 1
            while i + count < len(words) and words[i + count].lower().rstrip(',.!?;:') == word.lower().rstrip(',.!?;:'):
                count += 1

            # If word repeats 3+ times, it's a loop - keep only first 2
            if count >= 3:
                loops_found.append(f"'{word}' x{count}")
                cleaned.append(word)
                if i + 1 < len(words):
                    cleaned.append(words[i + 1])
                i += count  # Skip all repetitions
            # If word repeats 2 times, keep only once (for better fluency)
            elif count == 2:
                cleaned.append(word)
                i += count
            else:
                cleaned.append(word)
                i += 1

        result = ' '.join(cleaned)

        if loops_found:
            self.logger.warning(f"🔄 Word loops detected and cleaned: {', '.join(loops_found)}")
            self.logger.debug(f"Original: '{text[:100]}...'")
            self.logger.debug(f"Cleaned:  '{result[:100]}...'")

        return result

    def _merge_fragments(self, buffer: str, new_fragment: str) -> str:
        """Merge new fragment with buffer, removing overlaps and repetitions"""
        if not buffer:
            return self._clean_word_loops(new_fragment)

        # Clean loops from new fragment first
        new_fragment = self._clean_word_loops(new_fragment)

        # If fragments are very similar, return the longer one
        if self._calculate_similarity(buffer, new_fragment) > 0.8:
            return buffer if len(buffer) > len(new_fragment) else new_fragment

        buffer_words = buffer.split()
        fragment_words = new_fragment.split()

        # Find overlap: check if end of buffer matches start of fragment
        max_overlap = min(len(buffer_words), len(fragment_words))
        overlap_length = 0

        for i in range(1, max_overlap + 1):
            if buffer_words[-i:] == fragment_words[:i]:
                overlap_length = i

        # Also check for partial overlaps (e.g., "hello world" + "world hello" -> avoid duplication)
        for i in range(1, max_overlap):
            if buffer_words[-i:] == fragment_words[:i]:
                overlap_length = max(overlap_length, i)
                break

        # Merge: buffer + (fragment without overlap)
        if overlap_length > 0:
            merged = buffer + ' ' + ' '.join(fragment_words[overlap_length:])
        else:
            # Check if last word of buffer matches first word of fragment
            if buffer_words and fragment_words and buffer_words[-1] == fragment_words[0]:
                # Avoid duplicate word
                merged = buffer + ' ' + ' '.join(fragment_words[1:])
            else:
                merged = buffer + ' ' + new_fragment

        # Clean loops from final merged result too
        merged = self._clean_word_loops(merged)

        return merged.strip()

    def on_transcription(self, text: str):
        """Callback when STT produces transcription (accumulate complete sentences)"""
        if not text.strip():
            return

        current_time = time.time()

        # Clean ellipsis from incoming fragment
        text_clean = text.strip()
        while text_clean.endswith('...') or text_clean.endswith('....'):
            text_clean = text_clean[:-3].strip()

        if not text_clean:
            return

        # DEDUPLICATION: Only check for exact duplicates (not similarity)
        if text_clean.lower() == self.sentence_buffer.lower().strip():
            self.logger.debug(f"Exact duplicate skipped: '{text_clean[:30]}...'")
            return

        # Start buffer timer if this is first fragment
        if not self.sentence_buffer:
            self.buffer_start_time = current_time

        # Merge with buffer (handles overlapping fragments)
        self.sentence_buffer = self._merge_fragments(self.sentence_buffer, text_clean)
        self.last_fragment_time = current_time

        self.logger.debug(f"Buffer ({len(self.sentence_buffer)} chars): '{self.sentence_buffer[:80]}...'")

        # Check if sentence is complete
        is_complete = self._is_sentence_complete(self.sentence_buffer)

        # Timeout: has buffer been accumulating too long?
        timeout_reached = (self.buffer_start_time and
                          (current_time - self.buffer_start_time) > self.sentence_timeout)

        is_long_enough = len(self.sentence_buffer) >= self.min_sentence_length

        # Process if: complete sentence OR timeout with enough text
        if is_complete or (timeout_reached and is_long_enough):
            complete_sentence = self.sentence_buffer.strip()

            # Clean up ellipsis from sentence
            while complete_sentence.endswith('...') or complete_sentence.endswith('....'):
                complete_sentence = complete_sentence[:-3].strip()

            # Skip if too short after cleanup
            if len(complete_sentence) < 20:
                self.logger.debug(f"Sentence too short after cleanup, skipping")
                self.sentence_buffer = ""
                self.buffer_start_time = None
                self.last_fragment_time = None
                return

            # Add to recent transcriptions for deduplication
            self.recent_transcriptions.append(complete_sentence.lower())
            if len(self.recent_transcriptions) > self.max_recent_transcriptions:
                self.recent_transcriptions.pop(0)

            self.last_transcription_time = current_time

            reason = "complete" if is_complete else "timeout"
            self.logger.info(f"Sentence ({reason}): '{complete_sentence[:80]}...'")

            # Update UI
            if self.ui:
                self.ui.update_original_text(complete_sentence)

            # Translate complete sentence
            self.process_translation(complete_sentence)

            # Clear buffer
            self.sentence_buffer = ""
            self.buffer_start_time = None
            self.last_fragment_time = None

    def process_translation(self, original_text: str):
        """Process translation"""
        if not TRANSLATION_AVAILABLE or not self.translation_handler:
            return

        thread = threading.Thread(
            target=self._translate_and_display,
            args=(original_text,),
            daemon=True
        )
        thread.start()

    def _translate_and_display(self, original_text: str):
        """Translate and display in background thread"""
        try:
            # Translation with timing
            with LatencyTimer() as trans_timer:
                preprocessed = self.translation_handler.preprocess_text(original_text)
                translated = self.translation_handler.translate_text(preprocessed)
                final_text = self.translation_handler.postprocess_text(translated)

            self.last_translation_time = time.time()

            # Calculate total latency
            if self.last_transcription_time:
                total_latency = (self.last_translation_time - self.last_transcription_time) * 1000
                self.logger.info(
                    "Translation completed",
                    translation_latency_ms=trans_timer.elapsed_ms,
                    total_latency_ms=total_latency
                )

            # Ensure the translated text is different from original (if translation failed, it might return original)
            # This is a critical check to make sure we're not speaking the original text
            if original_text.strip().lower() == final_text.strip().lower():
                print(f"⚠️ Translation may have failed - original and translated text are identical")
                print(f"Original: {original_text[:100]}...")
                print(f"Translated: {final_text[:100]}...")
                # If translation failed, we should not speak the original text through TTS
                # We'll still update UI and subtitles but skip TTS
            else:
                print(f"✅ Translation successful")
                print(f"🔊 Original: {original_text[:100]}...")  # Debug: show original
                print(f"🔊 Speaking (Translated): {final_text[:100]}...")  # Debug: show what we're speaking

            # Update UI (thread-safe)
            if self.ui:
                from PyQt6.QtCore import QMetaObject, Qt, Q_ARG
                QMetaObject.invokeMethod(
                    self.ui,
                    "update_translated_text",
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG(str, final_text)
                )

            # Update subtitle overlay (thread-safe via Qt)
            if self.subtitle_overlay:
                from PyQt6.QtCore import QMetaObject, Qt, Q_ARG
                QMetaObject.invokeMethod(
                    self.subtitle_overlay,
                    "update_subtitles",
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG(str, original_text),
                    Q_ARG(str, final_text)
                )

            # Speak translation if TTS is enabled (speak the translated text with Mónica voice)
            if TTS_AVAILABLE and self.tts_handler and self.tts_enabled:
                # Always use Mónica voice - no changes needed
                self.tts_handler.speak_text(final_text)

            # Record metrics
            self.metrics.record_pipeline_run(
                stt_ms=0,
                translation_ms=trans_timer.elapsed_ms,
                tts_ms=0,
                chunk_size=self.config.audio['chunk_size'],
                text_length=len(original_text),
                success=True
            )

        except Exception as e:
            self.logger.log_error_with_context(
                error=e,
                context="_translate_and_display",
                original_text=original_text
            )

    def cleanup(self):
        """Cleanup resources"""
        self.stop_translation_process()

        if self.stt_handler and STT_HANDLER == "faster-whisper":
            self.stt_handler.stop_processing()

        if self.system_audio:
            self.system_audio.cleanup()

        if self.mixer:
            self.mixer.cleanup()

        if self.subtitle_overlay:
            self.subtitle_overlay.close()

        self.logger.info("Application cleaned up")


def main():
    """Main entry point"""
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Create translator
    translator = TranslationAppPro()

    # Create UI
    ui = TranslationAppUI(app=app, translator=translator)
    ui.show()

    # Connect UI to translator
    def start_translation():
        ui.start_translation()
        translator.start_translation_process(ui=ui)

    def stop_translation():
        ui.stop_translation()
        translator.stop_translation_process()

    ui.start_button.clicked.disconnect()
    ui.stop_button.clicked.disconnect()

    ui.start_button.clicked.connect(start_translation)
    ui.stop_button.clicked.connect(stop_translation)

    # Cleanup on exit
    app.aboutToQuit.connect(translator.cleanup)

    translator.logger.info("UI started - Ready for translation")
    translator.logger.info(f"Using {STT_HANDLER} STT engine")

    if translator.subtitle_overlay:
        translator.logger.info("Subtitle overlay available - will show on Start")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
