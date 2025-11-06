"""
TTS (Text-to-Speech) Handler Module
Handles text-to-speech conversion for the real-time translation app
Supports both macOS built-in 'say' command and pyttsx3 library
"""
import os
import subprocess
import sys
import threading
import queue
from typing import Optional, Callable
import time
import tempfile

# Try to import sounddevice for device-specific playback
try:
    import sounddevice as sd
    import soundfile as sf
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False

# Try to import pyttsx3 for more advanced TTS features
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False


class TTSHandler:
    def __init__(self, voice: str = None, rate: int = 200, volume: float = 1.0, use_macos_say: bool = True, output_device: str = None):
        """
        Initialize TTS handler
        :param voice: Voice identifier (varies by system)
        :param rate: Speech rate (words per minute)
        :param volume: Volume level (0.0 to 1.0)
        :param use_macos_say: Whether to use macOS built-in 'say' command
        :param output_device: Specific audio output device name (macOS only)
        """
        self.voice = voice
        self.rate = rate
        self.volume = volume
        self.use_macos_say = use_macos_say and sys.platform == "darwin"
        self.output_device = output_device
        
        # Initialize pyttsx3 engine if available and not using macOS say
        self.engine = None
        if PYTTSX3_AVAILABLE and not self.use_macos_say:
            try:
                self.engine = pyttsx3.init()
                
                # Configure the engine
                if self.rate:
                    self.engine.setProperty('rate', self.rate)
                if self.volume:
                    self.engine.setProperty('volume', self.volume)
                if self.voice:
                    self.engine.setProperty('voice', self.voice)
            except Exception as e:
                print(f"Warning: Could not initialize pyttsx3 engine: {e}")
                print("Falling back to macOS 'say' command")
                self.use_macos_say = True
        
        # Threading and queues
        self.tts_queue = queue.Queue()
        self.is_speaking = False
        self._stop_worker = False
        self._last_text = ""  # For deduplication
        self._recent_texts = []  # Store last N texts for better deduplication
        self._max_recent = 5  # Keep last 5 texts

        # Callback for completion
        self.completion_callback: Optional[Callable] = None

        # Start persistent worker thread
        self._worker_thread = threading.Thread(target=self._queue_worker, daemon=True)
        self._worker_thread.start()

    def _is_similar(self, text1: str, text2: str, threshold: float = 0.8) -> bool:
        """Check if two texts are similar (simple word-based similarity)"""
        if not text1 or not text2:
            return False

        # Normalize texts
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return False

        # Calculate Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        similarity = intersection / union if union > 0 else 0

        return similarity >= threshold

    def speak_text(self, text: str):
        """Speak the provided text (adds to queue for sequential processing)"""
        if not text or not text.strip():
            return

        # Also check if text is too short (likely a fragment)
        if len(text.strip()) < 15:
            print(f"[TTS] 🔇 Skipping too short text: '{text}'")
            return

        # ULTRA-AGGRESSIVE deduplication: check against recent texts
        text_clean = text.strip().lower()

        # Check exact match first
        if text_clean in [t.lower() for t in self._recent_texts]:
            print(f"[TTS] 🔇 Skipping exact duplicate: '{text[:50]}...'")
            return

        # Check similarity against all recent texts
        for recent in self._recent_texts:
            if self._is_similar(text, recent, threshold=0.85):
                print(f"[TTS] 🔇 Skipping similar to recent: '{text[:50]}...'")
                return

        # Add to recent texts list
        self._recent_texts.append(text)
        if len(self._recent_texts) > self._max_recent:
            self._recent_texts.pop(0)

        self._last_text = text

        # Add to queue for sequential processing
        # Keep queue small to reduce latency - only 1 item at a time!
        if self.tts_queue.qsize() < 1:
            self.tts_queue.put(text)
            print(f"[TTS] 🔊 Queued: '{text[:60]}...'")
        else:
            # Queue is full, skip this one to avoid backlog
            print(f"[TTS] ⏭️  Skipping (busy speaking): '{text[:50]}...'")
            return

    def _queue_worker(self):
        """Persistent worker thread that processes queue sequentially"""
        while not self._stop_worker:
            try:
                # Wait for next text (with timeout to check _stop_worker)
                text = self.tts_queue.get(timeout=0.5)

                # Process the text
                self.is_speaking = True
                if self.use_macos_say:
                    self._speak_macos(text)
                else:
                    self._speak_pyttsx3(text)

                # Add small delay after speaking to avoid capturing echo/feedback
                time.sleep(0.3)
                self.is_speaking = False

                self.tts_queue.task_done()

            except queue.Empty:
                # No items in queue, continue waiting
                continue
            except Exception as e:
                print(f"Error in TTS queue worker: {e}")
                self.is_speaking = False

    def _speak_worker(self, text: str):
        """DEPRECATED: Old worker method (kept for compatibility)"""
        try:
            if self.use_macos_say:
                self._speak_macos(text)
            else:
                self._speak_pyttsx3(text)
        except Exception as e:
            print(f"Error in TTS worker: {e}")
    
    def _find_tts_output_device(self):
        """Find the TTS Output device (BlackHole 16ch or Multi-Output)"""
        if not SOUNDDEVICE_AVAILABLE:
            return None

        try:
            devices = sd.query_devices()

            # PASS 1: Look for exact match with "TTS Output" prefix (Multi-Output devices)
            # These contain both BlackHole AND physical speakers - THIS IS WHAT WE WANT!
            for idx, device in enumerate(devices):
                device_name = device['name']
                if device_name.startswith("TTS Output") and device['max_output_channels'] > 0:
                    print(f"🎵 Found TTS Multi-Output device: {device_name} (ID: {idx})")
                    return idx

            # PASS 2: Look for exact match with "BlackHole 16ch" ONLY (virtual device)
            # This is LAST RESORT - it's virtual only, no physical audio!
            for idx, device in enumerate(devices):
                device_name = device['name']
                if device_name == "BlackHole 16ch" and device['max_output_channels'] > 0:
                    print(f"⚠️ Using virtual BlackHole 16ch (ID: {idx}) - you won't hear audio!")
                    print(f"   Create 'TTS Output' Multi-Output in Audio MIDI Setup for physical audio")
                    return idx

            print("⚠️ TTS Output device not found, using system default")
            return None

        except Exception as e:
            print(f"Error finding TTS device: {e}")
            return None

    def _speak_macos(self, text: str):
        """Speak using macOS 'say' with device routing to BlackHole 16ch"""
        try:
            # Sanitize text
            sanitized_text = text.replace('"', '').replace("'", "")

            # If we have a specific output device configured OR sounddevice available
            # Generate audio file and play through specific device
            if SOUNDDEVICE_AVAILABLE and (self.output_device or True):  # Always try device routing
                # Create temporary audio file
                with tempfile.NamedTemporaryFile(suffix='.aiff', delete=False) as tmp_file:
                    tmp_path = tmp_file.name

                try:
                    # Generate audio with 'say'
                    cmd = ["say", "-v", self.voice or "Paulina"]
                    cmd.extend(["-r", str(self.rate)])
                    cmd.extend(["-o", tmp_path])
                    cmd.append(sanitized_text)

                    subprocess.run(cmd, check=True, capture_output=True)

                    # Find TTS output device
                    device_id = self._find_tts_output_device()

                    # Read audio file
                    data, samplerate = sf.read(tmp_path, dtype='float32')

                    # Apply volume
                    if self.volume != 1.0:
                        data = data * self.volume

                    # Play on specific device - NON-BLOCKING to avoid interfering
                    if device_id is not None:
                        print(f"🔊 Playing on device {device_id}")
                        sd.play(data, samplerate, device=device_id, blocking=False)
                        # Wait for playback to finish without blocking the thread
                        sd.wait()
                    else:
                        print(f"🔊 Playing on default device (fallback)")
                        sd.play(data, samplerate, blocking=False)
                        sd.wait()

                finally:
                    # Clean up
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)

            else:
                # Fallback: direct 'say' command (uses system default)
                cmd = ["say", "-v", self.voice or "Paulina"]
                cmd.extend(["-r", str(self.rate)])
                cmd.append(sanitized_text)
                subprocess.run(cmd, check=True, capture_output=True)

            # Call completion callback
            if self.completion_callback:
                self.completion_callback(text)

        except Exception as e:
            print(f"Error in TTS: {e}")
            import traceback
            traceback.print_exc()
    
    def _speak_pyttsx3(self, text: str):
        """Speak using pyttsx3 library"""
        if not PYTTSX3_AVAILABLE or not self.engine:
            # Fallback to macOS 'say' if pyttsx3 is not available
            self._speak_macos(text)
            return
        
        try:
            # Queue the text to be spoken
            self.engine.say(text)
            
            # Wait for the speaking to finish
            self.engine.runAndWait()
            
            # Call completion callback if set
            if self.completion_callback:
                self.completion_callback(text)
                
        except Exception as e:
            print(f"Error with pyttsx3: {e}")
            # Fallback to macOS 'say'
            self._speak_macos(text)
    
    def set_completion_callback(self, callback: Callable[[str], None]):
        """Set callback function to handle TTS completion"""
        self.completion_callback = callback
    
    def stop_speaking(self):
        """Stop current speech and clear queue"""
        # Clear the queue
        while not self.tts_queue.empty():
            try:
                self.tts_queue.get_nowait()
                self.tts_queue.task_done()
            except queue.Empty:
                break

        # Stop pyttsx3 engine if active
        if self.engine and PYTTSX3_AVAILABLE:
            try:
                self.engine.stop()
            except Exception as e:
                print(f"Error stopping speech: {e}")

        # Kill any running 'say' processes (macOS)
        if self.use_macos_say and sys.platform == "darwin":
            try:
                subprocess.run(["killall", "say"], check=False, capture_output=True)
            except Exception:
                pass

        self.is_speaking = False
        self._last_text = ""  # Reset deduplication
        self._recent_texts = []  # Clear recent texts history

    def cleanup(self):
        """Cleanup resources and stop worker thread"""
        self._stop_worker = True
        self.stop_speaking()
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2.0)
    
    def get_available_voices(self):
        """Get list of available voices with prioritization of high-quality ones"""
        voices = []
        
        if self.use_macos_say:
            # Get available voices using 'say' command with detailed info
            try:
                result = subprocess.run(["say", "-v", "?"], 
                                      capture_output=True, text=True, check=True)
                lines = result.stdout.strip().split('\n')[1:]  # Skip first line
                for line in lines:
                    if line.strip():
                        # Split by multiple spaces to separate name, language and info
                        parts = line.split()
                        if len(parts) >= 3:
                            voice_name = parts[0]
                            # Add voice if it's not a duplicate
                            if voice_name not in voices:
                                voices.append(voice_name)
            except Exception as e:
                print(f"Could not get voices from 'say': {e}")
                # Return some default high-quality voices
                voices = [
                    "Samantha",   # High-quality female voice
                    "Alex",       # High-quality male voice
                    "Victoria",   # High-quality female voice
                    "Daniel",     # British male voice
                    "Karen",      # British female voice
                    "Moira",      # Irish female voice
                    "Rishi",      # Indian male voice
                    "Tessa",      # South African female voice
                    "Veena",      # Indian female voice
                    "Eddy",       # Young adult male voice
                    "Fred",       # Funny male voice
                    "Junior",     # Child male voice
                    "Kathy"       # Standard female voice
                ]
        elif PYTTSX3_AVAILABLE and self.engine:
            try:
                available_voices = self.engine.getProperty('voices')
                for voice in available_voices:
                    voices.append(voice.id)
            except Exception as e:
                print(f"Could not get voices from pyttsx3: {e}")
        
        # Return only high-quality voices, prioritized by quality
        high_quality_voices = [
            "Samantha", "Victoria", "Alex", "Daniel", "Karen", 
            "Moira", "Rishi", "Tessa", "Veena", "Eddy"
        ]
        
        # Return intersection of available voices with high-quality ones if possible
        if voices:
            return [v for v in high_quality_voices if v in voices] or voices
        else:
            return high_quality_voices
    
    def change_voice_settings(self, voice: str = None, rate: int = None, volume: float = None):
        """Change voice settings"""
        changed = False
        
        if voice is not None and self.voice != voice:
            self.voice = voice
            changed = True
            
        if rate is not None and self.rate != rate:
            self.rate = rate
            changed = True
            if self.engine and PYTTSX3_AVAILABLE:
                try:
                    self.engine.setProperty('rate', rate)
                except Exception as e:
                    print(f"Could not set rate: {e}")
        
        if volume is not None and self.volume != volume:
            self.volume = volume
            changed = True
            if self.engine and PYTTSX3_AVAILABLE:
                try:
                    self.engine.setProperty('volume', volume)
                except Exception as e:
                    print(f"Could not set volume: {e}")
        
        return changed
    
    def is_available(self):
        """Check if TTS functionality is available"""
        return self.use_macos_say or PYTTSX3_AVAILABLE