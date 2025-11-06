"""
Audio Handler Module
Handles audio input/output operations for the real-time translation app
"""
import pyaudio
import numpy as np
import threading
import queue
import time
from typing import Optional, Callable


class AudioHandler:
    def __init__(self, sample_rate: int = 16000, chunk_size: int = 1024):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.audio = pyaudio.PyAudio()
        
        # Audio stream references
        self.input_stream = None
        self.output_stream = None
        
        # Threading and queues
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.is_playing = False
        
        # Callback for audio data processing
        self.audio_callback: Optional[Callable] = None
        
        # Recording parameters
        self.channels = 1
        self.format = pyaudio.paInt16
        
    def list_audio_devices(self):
        """List all available audio devices"""
        device_count = self.audio.get_device_count()
        devices = []
        
        for i in range(device_count):
            info = self.audio.get_device_info_by_index(i)
            devices.append({
                'index': i,
                'name': info['name'],
                'max_input_channels': info['maxInputChannels'],
                'max_output_channels': info['maxOutputChannels'],
                'default_samplerate': info['defaultSampleRate']
            })
        
        return devices
    
    def start_recording(self, device_index: Optional[int] = None):
        """Start recording audio from input device"""
        if self.input_stream is not None:
            self.stop_recording()
            
        try:
            self.input_stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                input_device_index=device_index,
                stream_callback=self._record_callback if self.audio_callback else None
            )
            
            self.is_recording = True
            
            # If no callback is set, run the recording in a thread
            if not self.audio_callback:
                self._record_thread = threading.Thread(target=self._record_audio)
                self._record_thread.daemon = True
                self._record_thread.start()
            else:
                self.input_stream.start_stream()
            
            print(f"Started recording at {self.sample_rate}Hz, chunk size: {self.chunk_size}")
        except Exception as e:
            print(f"Error starting recording: {e}")
            raise
    
    def stop_recording(self):
        """Stop recording audio"""
        self.is_recording = False
        
        if self.input_stream:
            if self.audio_callback:
                # If using callbacks, just stop the stream
                self.input_stream.stop_stream()
            else:
                # If using thread, wait for it to finish
                if hasattr(self, '_record_thread') and self._record_thread.is_alive():
                    self._record_thread.join(timeout=1.0)
            
            self.input_stream.close()
            self.input_stream = None
            print("Recording stopped")
    
    def _record_callback(self, in_data, frame_count, time_info, status):
        """Callback for audio stream - processes data in real-time"""
        if self.is_recording:
            audio_data = np.frombuffer(in_data, dtype=np.int16)
            
            # Put audio data in queue for processing
            self.audio_queue.put(audio_data)
            
            # Call the registered callback if available
            if self.audio_callback:
                self.audio_callback(audio_data)
        
        return (None, pyaudio.paContinue)
    
    def _record_audio(self):
        """Internal method to handle audio recording in thread (when no callback is used)"""
        while self.is_recording:
            try:
                data = self.input_stream.read(self.chunk_size, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16)
                
                # Put audio data in queue for processing
                self.audio_queue.put(audio_data)
                
                # Call the registered callback if available
                if self.audio_callback:
                    self.audio_callback(audio_data)
                    
            except Exception as e:
                print(f"Error during recording: {e}")
                break
    
    def play_audio(self, audio_data: np.ndarray):
        """Play audio data through output device"""
        if not self.is_playing:
            try:
                self.output_stream = self.audio.open(
                    format=self.format,
                    channels=self.channels,
                    rate=self.sample_rate,
                    output=True
                )
                self.is_playing = True
            except Exception as e:
                print(f"Error opening output stream: {e}")
                return
        
        # Convert to bytes if needed
        if audio_data.dtype == np.int16:
            audio_bytes = audio_data.tobytes()
        else:
            # Convert float to int16 (ensure values are in correct range)
            audio_float = np.clip(audio_data, -1.0, 1.0)
            audio_bytes = (audio_float * 32767).astype(np.int16).tobytes()
        
        try:
            self.output_stream.write(audio_bytes)
        except Exception as e:
            print(f"Error playing audio: {e}")
    
    def play_raw_audio(self, audio_bytes: bytes):
        """Play raw audio bytes through output device"""
        if not self.is_playing:
            try:
                self.output_stream = self.audio.open(
                    format=self.format,
                    channels=self.channels,
                    rate=self.sample_rate,
                    output=True
                )
                self.is_playing = True
            except Exception as e:
                print(f"Error opening output stream: {e}")
                return
        
        try:
            self.output_stream.write(audio_bytes)
        except Exception as e:
            print(f"Error playing raw audio: {e}")
    
    def stop_playback(self):
        """Stop audio playback"""
        if self.output_stream:
            self.output_stream.stop_stream()
            self.output_stream.close()
            self.output_stream = None
            self.is_playing = False
            
    def set_audio_callback(self, callback: Callable[[np.ndarray], None]):
        """Set callback function to process audio data"""
        self.audio_callback = callback
        
        # If currently recording, restart with new callback
        if self.is_recording:
            was_recording = True
            device_index = self._get_current_input_device_index()
            self.stop_recording()
            self.start_recording(device_index)
        else:
            self._record_thread = None
    
    def set_audio_callback_optimized(self, callback: Callable[[np.ndarray], None]):
        """Set callback function with optimized parameters for lower latency"""
        self.audio_callback = callback
        
        # Adjust chunk size for better real-time performance
        if self.chunk_size > 512:
            self.chunk_size = 512  # Smaller chunks for lower latency
        
        # If currently recording, restart with new settings
        if self.is_recording:
            was_recording = True
            device_index = self._get_current_input_device_index()
            self.stop_recording()
            self.start_recording(device_index)
    
    def _get_current_input_device_index(self):
        """Get the index of the currently used input device (if any)"""
        # This is a simplified implementation
        # In a real app, you'd want to store the device index when starting recording
        return getattr(self.input_stream, '_input_device_index', None) if self.input_stream else None
    
    def close(self):
        """Clean up audio resources"""
        self.stop_recording()
        self.stop_playback()
        
        if self.audio:
            self.audio.terminate()