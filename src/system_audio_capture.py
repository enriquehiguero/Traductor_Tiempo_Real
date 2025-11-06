"""
System Audio Capture Module for macOS

Captures audio from the system (YouTube, Teams, Zoom, etc.) using:
- BlackHole virtual audio device (recommended)
- Native CoreAudio routing (advanced)

This module handles:
1. Detection of virtual audio devices
2. Configuration of audio routing
3. Capture of system audio without interrupting speaker output
"""
import pyaudio
import numpy as np
import threading
import queue
import time
import platform
from typing import Optional, Callable, List, Dict, Tuple
from pathlib import Path

try:
    from utils.logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class SystemAudioCapture:
    """
    Captures audio from macOS system output using virtual audio devices

    Supports:
    - BlackHole 2ch/16ch (recommended - free virtual audio device)
    - Soundflower (legacy alternative)
    - Multi-Output Device configuration (captures system audio + plays to speakers)
    """

    # Known virtual audio device names
    VIRTUAL_DEVICES = [
        "BlackHole 2ch",
        "BlackHole 16ch",
        "Soundflower (2ch)",
        "Soundflower (64ch)",
        "VB-Audio VoiceMeeter",
    ]

    def __init__(self, sample_rate: int = 16000, chunk_size: int = 1024):
        """
        Initialize System Audio Capture

        Args:
            sample_rate: Audio sample rate (16000 for Whisper)
            chunk_size: Number of frames per buffer
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.audio = pyaudio.PyAudio()

        # Audio stream
        self.input_stream = None
        self.is_capturing = False

        # Threading
        self.audio_queue = queue.Queue(maxsize=100)
        self.capture_thread = None

        # Callback for audio data
        self.audio_callback: Optional[Callable] = None

        # Device info
        self.selected_device_index: Optional[int] = None
        self.selected_device_name: Optional[str] = None

        # Audio format
        self.channels = 2  # Most system audio is stereo
        self.format = pyaudio.paFloat32

        logger.info("SystemAudioCapture initialized",
                   sample_rate=sample_rate, chunk_size=chunk_size)

    def detect_virtual_audio_devices(self) -> List[Dict[str, any]]:
        """
        Detect all virtual audio devices on the system

        Returns:
            List of virtual audio device info dictionaries
        """
        virtual_devices = []
        device_count = self.audio.get_device_count()

        for i in range(device_count):
            try:
                info = self.audio.get_device_info_by_index(i)
                device_name = info['name']

                # Check if it's a virtual device
                is_virtual = any(
                    vd_name.lower() in device_name.lower()
                    for vd_name in self.VIRTUAL_DEVICES
                )

                if is_virtual and info['maxInputChannels'] > 0:
                    virtual_devices.append({
                        'index': i,
                        'name': device_name,
                        'channels': info['maxInputChannels'],
                        'sample_rate': int(info['defaultSampleRate']),
                        'type': self._identify_device_type(device_name)
                    })

                    logger.debug(f"Found virtual device: {device_name}",
                               device_index=i)

            except Exception as e:
                logger.warning(f"Error querying device {i}: {e}")

        if not virtual_devices:
            logger.warning(
                "No virtual audio devices found. "
                "Please install BlackHole: brew install blackhole-2ch"
            )

        return virtual_devices

    def _identify_device_type(self, device_name: str) -> str:
        """Identify the type of virtual audio device"""
        name_lower = device_name.lower()
        if "blackhole" in name_lower:
            return "blackhole"
        elif "soundflower" in name_lower:
            return "soundflower"
        elif "voicemeeter" in name_lower:
            return "voicemeeter"
        else:
            return "unknown"

    def get_recommended_device(self) -> Optional[Dict[str, any]]:
        """
        Get the recommended virtual audio device

        Preference order:
        1. BlackHole 2ch (best for stereo system audio)
        2. BlackHole 16ch
        3. Soundflower 2ch
        4. Any other virtual device

        Returns:
            Device info dict or None if no device found
        """
        devices = self.detect_virtual_audio_devices()

        if not devices:
            return None

        # Preference order
        preferences = ["BlackHole 2ch", "BlackHole 16ch", "Soundflower (2ch)"]

        for pref in preferences:
            for device in devices:
                if pref.lower() in device['name'].lower():
                    logger.info(f"Recommended device: {device['name']}",
                               device_index=device['index'])
                    return device

        # If no preferred device, return first available
        logger.info(f"Using first available device: {devices[0]['name']}",
                   device_index=devices[0]['index'])
        return devices[0]

    def setup_device(self, device_index: Optional[int] = None,
                    device_name: Optional[str] = None) -> bool:
        """
        Setup virtual audio device for capture

        Args:
            device_index: Specific device index to use
            device_name: Specific device name to search for

        Returns:
            True if device was successfully configured
        """
        if device_index is not None:
            # Use specific device index
            try:
                info = self.audio.get_device_info_by_index(device_index)
                self.selected_device_index = device_index
                self.selected_device_name = info['name']
                logger.info(f"Device configured: {info['name']}",
                           device_index=device_index)
                return True
            except Exception as e:
                logger.error(f"Failed to configure device index {device_index}: {e}")
                return False

        elif device_name is not None:
            # Search for device by name
            devices = self.detect_virtual_audio_devices()
            for device in devices:
                if device_name.lower() in device['name'].lower():
                    self.selected_device_index = device['index']
                    self.selected_device_name = device['name']
                    logger.info(f"Device configured: {device['name']}",
                               device_index=device['index'])
                    return True

            logger.error(f"Device '{device_name}' not found")
            return False

        else:
            # Auto-select recommended device
            recommended = self.get_recommended_device()
            if recommended:
                self.selected_device_index = recommended['index']
                self.selected_device_name = recommended['name']
                return True
            else:
                logger.error("No virtual audio device found")
                return False

    def start_capture(self, callback: Optional[Callable] = None) -> bool:
        """
        Start capturing system audio

        Args:
            callback: Optional callback function(audio_data: np.ndarray)
                     Called with each audio chunk

        Returns:
            True if capture started successfully
        """
        if self.is_capturing:
            logger.warning("Already capturing")
            return False

        if self.selected_device_index is None:
            logger.error("No device configured. Call setup_device() first")
            return False

        self.audio_callback = callback

        try:
            # Open audio stream
            self.input_stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                input_device_index=self.selected_device_index,
                stream_callback=self._audio_stream_callback
            )

            self.input_stream.start_stream()
            self.is_capturing = True

            logger.log_audio_capture(
                device_name=self.selected_device_name,
                sample_rate=self.sample_rate,
                chunk_size=self.chunk_size,
                source_type="system_audio"
            )

            return True

        except Exception as e:
            logger.error_with_context(
                error=e,
                context="start_capture",
                device_index=self.selected_device_index,
                device_name=self.selected_device_name
            )
            return False

    def _audio_stream_callback(self, in_data, frame_count, time_info, status):
        """PyAudio stream callback"""
        if status:
            logger.warning(f"Audio stream status: {status}")

        try:
            # Convert bytes to numpy array
            audio_data = np.frombuffer(in_data, dtype=np.float32)

            # Convert stereo to mono if needed (average channels)
            if self.channels == 2:
                audio_data = audio_data.reshape(-1, 2).mean(axis=1)

            # Convert to int16 for compatibility with Whisper
            audio_data = (audio_data * 32767).astype(np.int16)

            # Put in queue for processing
            if not self.audio_queue.full():
                self.audio_queue.put(audio_data)

            # Call user callback if provided
            if self.audio_callback:
                try:
                    self.audio_callback(audio_data)
                except Exception as e:
                    logger.error(f"Error in audio callback: {e}")

        except Exception as e:
            logger.error(f"Error in stream callback: {e}")

        return (in_data, pyaudio.paContinue)

    def get_audio_chunk(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        """
        Get next audio chunk from queue

        Args:
            timeout: Max seconds to wait for data

        Returns:
            Audio data as numpy array or None if timeout
        """
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def stop_capture(self):
        """Stop capturing system audio"""
        if not self.is_capturing:
            return

        self.is_capturing = False

        if self.input_stream:
            try:
                self.input_stream.stop_stream()
                self.input_stream.close()
            except Exception as e:
                logger.error(f"Error stopping stream: {e}")

        self.input_stream = None

        # Clear queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

        logger.info("System audio capture stopped")

    def cleanup(self):
        """Cleanup resources"""
        self.stop_capture()
        if self.audio:
            self.audio.terminate()

    def __del__(self):
        """Destructor"""
        self.cleanup()


# Utility functions

def check_blackhole_installed() -> Tuple[bool, Optional[str]]:
    """
    Check if BlackHole is installed on the system

    Returns:
        (is_installed, version_or_message)
    """
    if platform.system() != "Darwin":
        return False, "Not running on macOS"

    p = pyaudio.PyAudio()
    device_count = p.get_device_count()

    for i in range(device_count):
        try:
            info = p.get_device_info_by_index(i)
            if "blackhole" in info['name'].lower():
                p.terminate()
                return True, info['name']
        except:
            pass

    p.terminate()
    return False, None


def get_installation_instructions() -> str:
    """Get instructions for installing BlackHole"""
    return """
    ╔══════════════════════════════════════════════════════════════════╗
    ║         BlackHole Virtual Audio Device - Installation           ║
    ╚══════════════════════════════════════════════════════════════════╝

    BlackHole is a free, open-source virtual audio device for macOS
    that allows you to capture system audio (YouTube, Teams, etc.)

    Installation Options:

    Option 1: Homebrew (Recommended)
    ─────────────────────────────────
    $ brew install blackhole-2ch

    Option 2: Manual Download
    ─────────────────────────────────
    1. Visit: https://github.com/ExistentialAudio/BlackHole
    2. Download BlackHole 2ch installer
    3. Run the installer package

    After Installation:
    ─────────────────────────────────
    1. Open "Audio MIDI Setup" (in Applications/Utilities)
    2. Click the "+" button and select "Create Multi-Output Device"
    3. Check both:
       - Your speakers/headphones (to hear audio)
       - BlackHole 2ch (to capture audio)
    4. Right-click the Multi-Output Device and select "Use This Device For Sound Output"

    Now your system audio will play AND be captured for translation!

    ╚══════════════════════════════════════════════════════════════════╝
    """


if __name__ == "__main__":
    # Test/demo code
    print("System Audio Capture - Device Detection")
    print("=" * 60)

    capture = SystemAudioCapture()

    # Check if BlackHole is installed
    is_installed, info = check_blackhole_installed()
    if is_installed:
        print(f"✓ BlackHole detected: {info}")
    else:
        print("✗ BlackHole not found")
        print(get_installation_instructions())

    # List all virtual devices
    print("\nVirtual Audio Devices:")
    devices = capture.detect_virtual_audio_devices()

    if devices:
        for device in devices:
            print(f"  [{device['index']}] {device['name']}")
            print(f"      Channels: {device['channels']}, "
                  f"Sample Rate: {device['sample_rate']}Hz, "
                  f"Type: {device['type']}")
    else:
        print("  No virtual audio devices found")

    # Get recommended device
    recommended = capture.get_recommended_device()
    if recommended:
        print(f"\nRecommended device: {recommended['name']}")

    capture.cleanup()
