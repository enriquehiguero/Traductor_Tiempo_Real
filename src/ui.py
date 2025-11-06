"""
Main UI for the Real-time Translation Application
"""
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QComboBox,
                             QTextEdit, QGroupBox, QFormLayout, QCheckBox, QSlider,
                             QRadioButton, QButtonGroup)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
import json
import os


class TranslationAppUI(QMainWindow):
    def __init__(self, app=None, translator=None):
        super().__init__()
        self.app = app
        self.translator = translator
        self.setWindowTitle("Real-time Translation App")
        self.setGeometry(100, 100, 800, 600)
        
        # Load configuration
        self.config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
        self.config = self.load_config()
        
        # Setup UI
        self.setup_ui()

        # Setup timers
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
    
    def load_config(self):
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Return default config if file doesn't exist (new format)
            return {
                "audio": {
                    "input_device": None,
                    "output_device": None,
                    "sample_rate": 16000,
                    "chunk_size": 512,
                    "buffer_size": 2048,
                    "input_mode": "microphone"
                },
                "translation": {
                    "language_from": "en",
                    "language_to": "es",
                    "model": "Helsinki-NLP/opus-mt-en-es"
                },
                "stt": {
                    "model_size": "tiny",
                    "use_gpu": False
                }
            }

    def get_config_value(self, *keys, default=None):
        """
        Get config value with support for both old and new format

        Example:
            get_config_value("translation", "language_from") -> tries config["translation"]["language_from"]
            If not found, tries config["language_from"] (old format)
        """
        # Try new format (nested)
        current = self.config
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                # Try old format (flat) - use last key
                if len(keys) > 1 and keys[-1] in self.config:
                    return self.config[keys[-1]]
                return default
        return current
    
    def save_config(self):
        """Save configuration to JSON file"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def setup_ui(self):
        """Setup the main UI elements"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Title
        title_label = QLabel("Real-time Translation App")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        main_layout.addWidget(title_label)
        
        # Control buttons
        controls_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start Translation")
        self.start_button.clicked.connect(self.start_translation)
        self.start_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px;")
        
        self.stop_button = QPushButton("Stop Translation")
        self.stop_button.clicked.connect(self.stop_translation)
        self.stop_button.setStyleSheet("background-color: #f44336; color: white; padding: 10px;")
        self.stop_button.setEnabled(False)
        
        controls_layout.addWidget(self.start_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addStretch()

        main_layout.addLayout(controls_layout)

        # Output Mode Selection
        mode_group = QGroupBox("Output Mode")
        mode_layout = QVBoxLayout(mode_group)

        self.mode_button_group = QButtonGroup(self)

        self.subtitles_only_radio = QRadioButton("Subtitles Only (Recommended)")
        self.subtitles_only_radio.setToolTip("Display floating subtitles over video - no audio feedback issues")
        self.subtitles_only_radio.setChecked(True)  # Default

        self.audio_subtitles_radio = QRadioButton("Audio + Subtitles")
        self.audio_subtitles_radio.setToolTip("Text-to-Speech audio + floating subtitles (may have feedback if not configured properly)")

        self.mode_button_group.addButton(self.subtitles_only_radio, 1)
        self.mode_button_group.addButton(self.audio_subtitles_radio, 2)

        # Connect mode change
        self.subtitles_only_radio.toggled.connect(self.on_mode_changed)

        mode_layout.addWidget(self.subtitles_only_radio)
        mode_layout.addWidget(self.audio_subtitles_radio)

        main_layout.addWidget(mode_group)

        # Settings info (read-only from config.json)
        settings_group = QGroupBox("Translation Settings (from config.json)")
        settings_layout = QFormLayout(settings_group)

        lang_from = self.get_config_value("translation", "language_from", default="en")
        lang_to = self.get_config_value("translation", "language_to", default="es")

        lang_names = {"en": "English", "es": "Spanish", "fr": "French", "de": "German", "it": "Italian", "pt": "Portuguese"}

        from_label = QLabel(f"{lang_names.get(lang_from, lang_from)}")
        to_label = QLabel(f"{lang_names.get(lang_to, lang_to)}")

        settings_layout.addRow("Translating from:", from_label)
        settings_layout.addRow("Translating to:", to_label)

        info_label = QLabel("ℹ️ To change languages, edit config.json and restart")
        info_label.setStyleSheet("color: gray; font-style: italic; font-size: 10px;")
        settings_layout.addRow("", info_label)

        main_layout.addWidget(settings_group)
        
        # Output text areas
        output_group = QGroupBox("Translation Output")
        output_layout = QVBoxLayout(output_group)
        
        # Original text
        orig_label = QLabel("Original Speech:")
        self.original_text = QTextEdit()
        self.original_text.setMaximumHeight(100)
        self.original_text.setReadOnly(True)
        
        # Translated text
        trans_label = QLabel("Translated Text:")
        self.translated_text = QTextEdit()
        self.translated_text.setMaximumHeight(100)
        self.translated_text.setReadOnly(True)
        
        output_layout.addWidget(orig_label)
        output_layout.addWidget(self.original_text)
        output_layout.addWidget(trans_label)
        output_layout.addWidget(self.translated_text)
        
        main_layout.addWidget(output_group)
        
        # TTS Settings
        tts_group = QGroupBox("TTS Settings (Voice: Mónica)")
        tts_layout = QFormLayout(tts_group)

        self.tts_rate_slider = QSlider(Qt.Orientation.Horizontal)
        self.tts_rate_slider.setRange(50, 400)  # Words per minute
        tts_rate = self.get_config_value("tts", "rate", default=200)
        self.tts_rate_slider.setValue(tts_rate)
        self.tts_rate_label = QLabel(f"Rate: {tts_rate} WPM")

        # Connect slider to label update
        self.tts_rate_slider.valueChanged.connect(
            lambda value: self.tts_rate_label.setText(f"Rate: {value} WPM")
        )

        self.tts_volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.tts_volume_slider.setRange(0, 100)  # Volume percentage
        tts_volume = self.get_config_value("tts", "volume", default=1.0)
        self.tts_volume_slider.setValue(int(tts_volume * 100))
        self.tts_volume_label = QLabel(f"Volume: {int(tts_volume * 100)}%")

        # Connect slider to label update
        self.tts_volume_slider.valueChanged.connect(
            lambda value: self.tts_volume_label.setText(f"Volume: {value}%")
        )

        # Voice is fixed to Mónica, no selector needed

        tts_layout.addRow("Speech Rate:", self.tts_rate_slider)
        tts_layout.addRow("", self.tts_rate_label)
        tts_layout.addRow("Volume:", self.tts_volume_slider)
        tts_layout.addRow("", self.tts_volume_label)
        
        main_layout.addWidget(tts_group)
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def start_translation(self):
        """Start the translation process"""
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.statusBar().showMessage("Translation active...")
        
        # Apply current TTS settings to the translator
        self.apply_tts_settings()
        
        # Start actual translation process
        print("Starting translation...")
        
        # Start UI update timer
        self.timer.start(100)  # Update every 100ms
    
    def stop_translation(self):
        """Stop the translation process"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.statusBar().showMessage("Translation stopped")

        # TODO: Stop actual translation process
        print("Stopping translation...")

        # Stop UI update timer
        self.timer.stop()

    def on_mode_changed(self, checked):
        """Handle output mode change"""
        if self.subtitles_only_radio.isChecked():
            mode = "Subtitles Only"
            self.statusBar().showMessage("Mode: Subtitles Only (TTS disabled)")
            print("🎬 Mode: Subtitles Only")
            # Signal to disable TTS
            if hasattr(self, 'translator') and self.translator:
                self.translator.set_tts_enabled(False)
        else:
            mode = "Audio + Subtitles"
            self.statusBar().showMessage("Mode: Audio + Subtitles (TTS enabled)")
            print("🔊 Mode: Audio + Subtitles")
            # Signal to enable TTS
            if hasattr(self, 'translator') and self.translator:
                self.translator.set_tts_enabled(True)

    def update_ui(self):
        """Update UI elements periodically"""
        # This method will be called periodically to update the UI
        # with new translation results
        pass
    
    def get_tts_settings(self):
        """Get TTS settings from UI - voice is always Mónica"""
        return {
            "voice": "Mónica",  # Fixed to Mónica
            "rate": self.tts_rate_slider.value(),
            "volume": self.tts_volume_slider.value() / 100.0  # Convert percentage back to 0-1.0
        }

    def apply_tts_settings(self):
        """Apply current UI TTS settings to the translator's TTS handler"""
        if hasattr(self, 'translator') and self.translator and self.translator.tts_handler:
            try:
                settings = self.get_tts_settings()
                # Voice is always Mónica, only update rate and volume
                self.translator.tts_handler.change_voice_settings(
                    voice="Mónica",
                    rate=settings["rate"],
                    volume=settings["volume"]
                )
                print(f"✅ TTS settings applied: Mónica at {settings['rate']} WPM, volume {settings['volume']:.2f}")
            except Exception as e:
                print(f"⚠️ Error applying TTS settings: {e}")
    
    @pyqtSlot(str)
    def update_original_text(self, text):
        """Update the original text display with auto-scroll"""
        self.original_text.append(text)
        # Auto-scroll to bottom
        scrollbar = self.original_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    @pyqtSlot(str)
    def update_translated_text(self, text):
        """Update the translated text display with auto-scroll"""
        self.translated_text.append(text)
        # Auto-scroll to bottom
        scrollbar = self.translated_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_text_displays(self):
        """Clear both original and translated text displays"""
        self.original_text.clear()
        self.translated_text.clear()
    
    def on_voice_changed(self, voice_name):
        """Handle voice selection change - disabled since voice is fixed to Mónica"""
        # Voice is always Mónica, this method is no longer used
        pass

    def refresh_available_voices(self):
        """Refresh available voices - disabled since voice is fixed to Mónica"""
        # Voice is always Mónica, no need to refresh
        print("ℹ️ La voz está configurada como Mónica (no se puede cambiar)")
    
    def closeEvent(self, event):
        """Handle application close event"""
        self.timer.stop()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TranslationAppUI()
    window.show()
    sys.exit(app.exec())