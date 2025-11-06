# Changelog

All notable changes to the Real-Time Audio Translator project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-01-06

### 🎉 Major Release - UI Overhaul & TTS Improvements

This release focuses on simplifying the user interface and dramatically improving TTS reliability and quality.

### Added
- **Ultra-aggressive TTS deduplication system**
  - Tracks last 5 translated texts (not just the last one)
  - 85% similarity threshold for near-duplicate detection
  - Exact match detection (case-insensitive)
  - Minimum text length filter (15 characters)
  - Single-item queue to prevent translation backlog
  - Debug logging for skipped duplicates

- **Post-speech delay**
  - 0.3 second delay after TTS completion
  - Prevents echo capture from speakers

- **Read-only configuration display**
  - Translation settings show current config.json values
  - Clear instructions for changing settings
  - Prevents user confusion about non-functional controls

- **CHANGELOG.md** for tracking project evolution

### Changed
- **Fixed TTS voice to Mónica**
  - Removed voice selector from UI
  - Voice is now hardcoded to Mónica (Spanish voice from Spain)
  - Rate and volume remain adjustable
  - Clearer UI title: "TTS Settings (Voice: Mónica)"

- **Removed non-functional UI controls**
  - Removed Audio Devices selectors (not connected to backend)
  - Removed STT Settings controls (not connected to backend)
  - Removed Language selector dropdowns (now read-only labels)
  - UI now only shows controls that actually work

- **Continuous audio capture during TTS**
  - System no longer pauses audio capture when TTS is speaking
  - Prevents audio loss from source (YouTube, meetings, etc.)
  - Relies on Dual BlackHole architecture for feedback prevention
  - Result: Subtitle quality is consistent regardless of TTS state

- **Non-blocking audio playback**
  - Changed from `blocking=True` to `blocking=False` + `sd.wait()`
  - Reduces system contention
  - Better overall performance

### Fixed
- **Repetitive translations completely eliminated**
  - Previous version: 90% threshold on last text only
  - Current version: 85% threshold on last 5 texts
  - Catches more edge cases and variations

- **Poor subtitle quality in Audio mode**
  - Issue: Pausing capture during TTS caused audio loss
  - Fix: Continuous capture with Dual BlackHole isolation
  - Result: Subtitles are now identical quality in both modes

- **TTS queue backlog**
  - Previous: Queue up to 3 items
  - Current: Maximum 1 item
  - Translations that arrive while speaking are skipped
  - Prevents outdated translations from playing

- **Confusing UI controls**
  - Removed controls that appeared functional but didn't work
  - Added tooltips and explanatory text
  - Users now understand what's configurable and what's not

### Technical Details

#### TTS Handler (`tts_handler.py`)
- Added `_recent_texts` list to track last 5 texts
- Added `_max_recent` configuration (default: 5)
- Enhanced `speak_text()` with multi-text comparison
- Queue size reduced from 3 to 1
- Added 0.3s sleep after speech completion
- Improved logging with emojis for better visibility

#### Main Application (`main.py`)
- Removed audio capture pause during TTS (`is_speaking` check)
- Fixed voice to "Mónica" in `_init_tts()`
- Simplified TTS enable/disable logic
- Removed dependency on UI voice settings

#### UI (`ui.py`)
- Removed `lang_from_combo` and `lang_to_combo`
- Removed `input_device_combo` and `output_device_combo`
- Removed `stt_model_combo` and `gpu_checkbox`
- Removed `tts_voice_combo`
- Removed `populate_device_lists()` method
- Removed `get_selected_input_device()` method
- Removed `get_selected_output_device()` method
- Removed `get_selected_languages()` method
- Removed `get_stt_settings()` method
- Simplified `get_tts_settings()` to always return "Mónica"
- Simplified `apply_tts_settings()` to hardcode "Mónica"
- Disabled `on_voice_changed()` method
- Disabled `refresh_available_voices()` method

### Documentation
- Updated README.md with all changes
- Added "Recent Improvements (v2.0)" section
- Updated TTS section with Mónica details
- Updated "Using the Interface" section
- Updated Troubleshooting sections
- Updated Voice Quality section
- Created LINKEDIN_POST.md for social media announcement
- Created this CHANGELOG.md

### Performance
- Latency remains <3 seconds typical
- Better resource utilization with non-blocking playback
- Reduced memory usage with smaller queue

### Breaking Changes
- Voice can no longer be changed from UI
- To use a different voice, must edit source code
- Language pair changes require config.json edit + restart
- Audio device selection no longer available in UI

### Migration Guide from v1.x

If you're upgrading from version 1.x:

1. **Voice Selection**
   - The voice is now fixed to Mónica
   - If you prefer another voice, edit `src/main.py` line 374 and `src/ui.py` line 403

2. **Language Configuration**
   - Language pairs are now configured exclusively via `config.json`
   - Edit the file and restart the application
   - Example for French to Spanish:
     ```json
     "stt": { "language": "fr" },
     "translation": {
       "language_from": "fr",
       "language_to": "es",
       "model": "Helsinki-NLP/opus-mt-fr-es"
     }
     ```

3. **Audio Devices**
   - Audio device selection is now exclusively via `config.json`
   - Set `input_device` ID in `audio` section
   - Set `output_device` name in `tts` section

4. **STT Model**
   - Model size selection is now exclusively via `config.json`
   - Edit `stt.model_size` to: `tiny`, `base`, `small`, `medium`, or `large`

### Known Issues
- None at this time

### Roadmap for v2.1
- [ ] Make voice selection configurable via config.json
- [ ] Add support for multiple voice options in config
- [ ] Add language pair presets for quick switching
- [ ] Implement config hot-reload (no restart needed)
- [ ] Add performance profiling dashboard

---

## [1.0.0] - 2024-12-XX

### Added
- Initial release with basic functionality
- Faster-Whisper STT integration
- Helsinki-NLP translation
- macOS TTS with multiple voices
- Dual BlackHole architecture
- Subtitle overlay
- PyQt6 UI
- Configuration system
- Basic deduplication

---

**Legend**:
- 🎉 Major feature
- ✨ Minor feature
- 🐛 Bug fix
- 📝 Documentation
- 🔧 Configuration
- ⚡ Performance improvement
- 🔒 Security fix
