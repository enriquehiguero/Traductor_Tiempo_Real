# 🌍 Real-Time Audio Translator

> AI-powered real-time audio translation for YouTube, Teams, Zoom, and any audio source on macOS

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![macOS](https://img.shields.io/badge/Platform-macOS-lightgrey.svg)](https://www.apple.com/macos/)
[![Version](https://img.shields.io/badge/Version-2.0.0-blue.svg)](RELEASE_NOTES_v2.0.md)

Translate audio in real-time from English to Spanish (or any language pair) with both **subtitle overlays** and **audio output** using Mónica's natural Spanish voice, designed for video conferences, YouTube videos, and live presentations.

> 🎙️ **Voice**: Uses Mónica (Spanish voice from Spain) for all audio translations. Rate and volume are adjustable from the UI.

---

## 📚 Quick Links

- **[🎉 What's New in v2.0?](RELEASE_NOTES_v2.0.md)** - User-friendly release notes
- **[📝 Full Changelog](CHANGELOG.md)** - Technical changelog for developers
- **[💼 LinkedIn Announcement](LINKEDIN_POST.md)** - Share this project!

---

## ✨ Features

- 🎯 **Real-time Translation**: Translate audio as it plays with minimal latency (<3s)
- 🎤 **Multiple Audio Sources**: System audio, YouTube, Teams, Zoom, or any macOS audio
- 💬 **Floating Subtitles**: On-screen overlay with original and translated text
- 🔊 **Audio Output**: Natural Spanish voice synthesis (macOS voices)
- 🎛️ **Dual BlackHole Architecture**: Zero-feedback audio routing solution
- 🚀 **GPU Accelerated**: Optional GPU support for faster transcription
- 🎨 **Modern UI**: Clean Tkinter interface with real-time metrics

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      VIDEO/AUDIO SOURCE                      │
│              (YouTube, Teams, Zoom, Safari...)              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Multi-Output #1     │
              │  "Video Input"       │
              ├──────────┬───────────┤
              │ BH 2ch   │ Speakers  │
              └────┬─────┴──────┬────┘
                   │            │
                   │            └─────► 🔊 You hear video
                   │
                   ▼
          ┌────────────────┐
          │  BlackHole 2ch │  ← STT captures here
          └────────┬───────┘
                   │
                   ▼
        ┌──────────────────────┐
        │   STT (Whisper)      │
        │   Faster-Whisper     │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │   Translation        │
        │   Helsinki NLP       │
        └──────────┬───────────┘
                   │
                   ├─────► 📺 Subtitle Overlay
                   │
                   ▼
        ┌──────────────────────┐
        │   TTS (macOS say)    │
        └──────────┬───────────┘
                   │
                   ▼
              ┌──────────────────────┐
              │  Multi-Output #2     │
              │  "TTS Output"        │
              ├──────────┬───────────┤
              │ BH 16ch  │ Speakers  │
              └────┬─────┴──────┬────┘
                   │            │
                   │            └─────► 🔊 You hear translation
                   │
                   └─────► ❌ STT doesn't capture (different BH!)

RESULT: NO FEEDBACK LOOP! 🎉
```

### Key Components

#### STT (Speech-to-Text)
- **Engine**: Faster-Whisper (optimized Whisper)
- **Models**: `tiny`, `base`, `small`, `medium`, `large`
- **VAD**: Voice Activity Detection for better accuracy
- **Languages**: Auto-detection or explicit language setting

#### Translation
- **Model**: Helsinki-NLP OPUS-MT
- **Default**: English → Spanish (`opus-mt-en-es`)
- **Customizable**: Any language pair supported by Helsinki-NLP
- **Quality**: Professional-grade translation with context

#### TTS (Text-to-Speech)
- **Engine**: macOS `say` command with device routing
- **Voice**: Mónica (fixed - natural Spanish voice from Spain)
- **Configurable**: Speech rate (50-400 WPM) and volume (0-100%)
- **Routing**: Specific audio device (TTS Output) to prevent feedback
- **Deduplication**: Intelligent system to prevent repeated translations

#### Audio Routing
- **BlackHole 2ch**: Captures video/system audio for STT
- **BlackHole 16ch**: Routes TTS audio (isolated from STT)
- **Multi-Output Devices**: Combine virtual + physical audio

## 📋 Requirements

### System Requirements
- **OS**: macOS 10.15+ (Catalina or newer)
- **RAM**: 4GB minimum, 8GB recommended
- **CPU**: Apple Silicon (M1/M2/M3) or Intel with AVX2
- **GPU**: Optional (Metal for Apple Silicon, CUDA for Intel)

### Software Dependencies
- Python 3.9 or higher
- [BlackHole](https://existential.audio/blackhole/) audio driver (both 2ch and 16ch)
- Homebrew (for BlackHole installation)

## 🚀 Installation

### 1. Install BlackHole Audio Drivers

```bash
brew install blackhole-2ch
brew install blackhole-16ch
```

After installation, restart the audio service:

```bash
sudo killall coreaudiod
```

**Verify installation:**

```bash
system_profiler SPAudioDataType | grep "BlackHole"
```

You should see both `BlackHole 2ch` and `BlackHole 16ch`.

### 2. Configure Multi-Output Devices

Open **Audio MIDI Setup** (Spotlight → "Audio MIDI Setup"):

#### Multi-Output #1 (For Video)
1. Click **+** → **Create Multi-Output Device**
2. Name it: **"Video Input"**
3. Check:
   - ✅ BlackHole 2ch
   - ✅ Your Speakers/Headphones
4. Set **Drift Correction** on Speakers only

#### Multi-Output #2 (For TTS)
1. Click **+** → **Create Multi-Output Device**
2. Name it: **"TTS Output"**
3. Check:
   - ✅ BlackHole 16ch
   - ✅ Your Speakers/Headphones
4. Set **Drift Correction** on Speakers only

### 3. Set System Audio Output

Go to **System Preferences** → **Sound** → **Output**

Select: **"Video Input"** as default output

### 4. Clone and Install Python Dependencies

```bash
# Clone repository
git clone https://github.com/yourusername/real-time-translator.git
cd real-time-translator

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 5. Download Translation Models (First Run Only)

The first time you run the translator, it will download:
- Faster-Whisper model (~150MB for `base`)
- Helsinki-NLP translation model (~300MB)
- This happens automatically on first use

## ⚙️ Configuration

Edit `config.json` to customize behavior:

```json
{
  "audio": {
    "input_device": 1,              // BlackHole 2ch device ID
    "sample_rate": 16000,
    "input_mode": "system"
  },
  "stt": {
    "model_size": "base",           // tiny, base, small, medium, large
    "language": "en",               // Source language
    "use_faster_whisper": true,
    "vad_filter": true              // Voice Activity Detection
  },
  "translation": {
    "language_from": "en",
    "language_to": "es",
    "model": "Helsinki-NLP/opus-mt-en-es"
  },
  "tts": {
    "enabled": true,
    "voice": "Mónica",              // Fixed to Mónica (Spanish voice from Spain)
    "rate": 200,                    // Speech rate (WPM) - adjustable from UI
    "volume": 0.9,                  // Volume (0.0-1.0) - adjustable from UI
    "output_device": "TTS Output"   // Routes to BlackHole 16ch
  },
  "subtitle_overlay": {
    "enabled": true,
    "position": "bottom",
    "font_size": 32,
    "show_original": true,
    "show_translation": true,
    "auto_hide_seconds": 6
  }
}
```

## 🎮 Usage

### Quick Start

```bash
# Activate virtual environment
source venv/bin/activate

# Run translator
python3 src/main.py
```

### Using the Interface

The UI has been simplified to show only functional controls:

1. **Output Mode**:
   - **Subtitles Only** (Recommended): On-screen text overlay only, original audio continues
   - **Audio + Subtitles**: Voice translation by Mónica + on-screen text

2. **Translation Settings** (Read-only):
   - Displays current language pair from `config.json`
   - To change languages: Edit `config.json` and restart the app

3. **TTS Settings** (Only in Audio mode):
   - **Speech Rate**: Adjust Mónica's speaking speed (50-400 WPM)
   - **Volume**: Control translation audio volume (0-100%)
   - Voice is fixed to Mónica (cannot be changed)

4. **Start Translation**:
   - Click "Start Translation"
   - Play your video/audio source
   - Watch real-time transcription and translation in the text areas

5. **Monitor Output**:
   - **Original Speech**: Shows transcribed text from audio source
   - **Translated Text**: Shows translation output
   - Subtitle overlay (if enabled) appears on top of all windows

### Testing

#### Test Audio Setup
```bash
python3 test_audio_setup.py
```

This will:
- ✅ Verify BlackHole 2ch and 16ch are detected
- ✅ Check for Multi-Output devices
- ✅ Test TTS audio routing
- ✅ Play a test phrase

#### Test TTS Voice
```bash
python3 test_tts.py
```

#### Test Different Voices
```bash
python3 test_voices.py
```

This will play a sample text in different Spanish voices so you can choose your favorite.

## 🎯 Use Cases

### YouTube Videos
1. Set system output to "Video Input"
2. Run translator
3. Play YouTube video in Safari (or any browser)
4. Hear video + translation simultaneously

### Microsoft Teams / Zoom
1. In Teams/Zoom settings, set speaker to "Video Input"
2. Run translator before joining call
3. Hear real-time translation during meeting

### Live Presentations
1. Run translator in background
2. Use subtitle overlay mode for on-screen captions
3. Present normally while attendees see translations

## 🐛 Troubleshooting

### No Audio Output from TTS

**Problem**: Can't hear translated audio

**Solutions**:
1. Verify TTS is enabled in `config.json`
2. Check system volume is not muted
3. Run `python3 test_tts.py` to verify TTS works
4. Verify "TTS Output" device exists in Audio MIDI Setup

### Feedback Loop / Garbage Translations

**Problem**: TTS audio being captured by STT, causing nonsense

**Solution**: This means Dual BlackHole is not configured correctly.

1. Verify BlackHole 16ch is active:
   ```bash
   system_profiler SPAudioDataType | grep "BlackHole 16ch"
   ```

2. If not found, restart audio:
   ```bash
   sudo killall coreaudiod
   ```

3. Verify Multi-Output devices are created correctly
4. Make sure STT captures from BlackHole **2ch** only
5. Make sure TTS outputs to BlackHole **16ch** Multi-Output

### Translation Not Working

**Problem**: No subtitles or audio, but STT is capturing

**Solutions**:
1. Check internet connection (first run needs to download models)
2. Check logs for errors: `tail -f logs/translator.log`
3. Verify translation model in config matches available models
4. Try a smaller Whisper model (`tiny` or `base`)

### Audio Overlap (English + Spanish Together)

**Problem**: Hearing both original and translation, creating confusion

**Solutions**:
- **Option 1**: Mute the video (browser/player mute button)
  - ⚠️ This stops STT from capturing, so **not recommended**

- **Option 2**: Use Dual BlackHole (recommended)
  - Follow `SETUP_DUAL_BLACKHOLE.md` instructions
  - This properly isolates video audio from TTS audio

### Repetitive Translations

**Problem**: Same phrase being translated multiple times

**This is already fixed** in the current version with ultra-aggressive deduplication:
- ✅ Tracks last 5 translated texts (not just the last one)
- ✅ 85% similarity threshold to catch near-duplicates
- ✅ Exact match detection (case-insensitive)
- ✅ Minimum text length filter (15 characters)
- ✅ Single-item queue (skips new translations if already speaking)
- ✅ Post-speech delay (0.3s) to avoid capturing echo

**Important**: System does NOT pause audio capture during TTS because:
- BlackHole 2ch (input) and BlackHole 16ch (TTS output) are separate channels
- No feedback loop is possible with proper Dual BlackHole setup
- Pausing would cause loss of audio from source (YouTube, etc.)

If still happening:
1. Verify you're using Dual BlackHole setup correctly (see architecture diagram)
2. Check STT is capturing from BlackHole 2ch only
3. Check TTS is outputting to TTS Output (BlackHole 16ch) only
4. Verify VAD is enabled in config
5. Increase `vad_threshold` in config (try 0.7 or 0.8)

### Voice Quality

**Current voice**: The system uses **Mónica** (Spanish voice from Spain), which is fixed and cannot be changed through the UI.

**Mónica characteristics**:
- 🇪🇸 European Spanish accent (Spain)
- Formal, clear pronunciation
- Professional tone
- Works well for technical content and presentations

**To adjust voice quality**:
1. **Speech Rate**: Adjust from UI (50-400 WPM). Recommended: 180-200 for clarity
2. **Volume**: Adjust from UI (0-100%). Recommended: 80-90%
3. Consider using a higher quality Whisper model (`small` or `medium`) for better input transcription

**Note**: If you need a different voice (Paulina, Eddy, etc.), you must manually edit `src/main.py` and `src/ui.py` to change the hardcoded voice name.

### Slow Performance

**Problem**: High latency (>5 seconds)

**Solutions**:
1. Use smaller Whisper model (`tiny` or `base`)
2. Enable GPU acceleration (if available)
3. Reduce `chunk_size` in audio config
4. Close other CPU-intensive apps
5. Check Activity Monitor for resource usage

## 📊 Performance Optimization

### For Apple Silicon (M1/M2/M3)
- Use `base` or `small` Whisper model
- Enable Metal GPU acceleration (automatic)
- Expect <2s total latency

### For Intel Macs
- Use `tiny` or `base` Whisper model
- Disable GPU unless CUDA-capable
- Expect 2-4s total latency

### Latency Breakdown
- **STT**: 500-1500ms (depends on model size)
- **Translation**: 100-300ms
- **TTS**: 500-1000ms (depends on text length)
- **Total**: 1-3 seconds typical

## 🎉 Recent Improvements (v2.0)

### UI Simplification
- ✅ Removed non-functional controls (audio devices, STT settings, language selectors)
- ✅ Translation settings now read-only with clear instructions to edit `config.json`
- ✅ Cleaner interface showing only what actually works
- ✅ Better user experience with honest control labels

### TTS Enhancements
- ✅ **Fixed voice to Mónica**: Professional Spanish voice (Spain accent)
- ✅ Removed voice selector to avoid confusion
- ✅ Maintained adjustable speech rate and volume controls
- ✅ Ultra-aggressive deduplication system (tracks last 5 texts, 85% similarity threshold)
- ✅ Single-item queue to prevent translation backlog
- ✅ Post-speech delay (0.3s) to avoid echo capture

### Audio Processing
- ✅ **No pause during TTS**: Continuous audio capture for better subtitle quality
- ✅ Proper Dual BlackHole isolation prevents feedback without pausing
- ✅ Improved sentence accumulation and fragment merging
- ✅ Better word loop detection and cleaning

### Performance
- ✅ Non-blocking audio playback
- ✅ Reduced latency with optimized queue management
- ✅ Better resource management

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Faster-Whisper](https://github.com/guillaumekln/faster-whisper) - Optimized Whisper implementation
- [Helsinki-NLP](https://huggingface.co/Helsinki-NLP) - OPUS-MT translation models
- [BlackHole](https://existential.audio/blackhole/) - Virtual audio driver
- [Tkinter](https://docs.python.org/3/library/tkinter.html) - GUI framework



**Made with ❤️ for the global community**

*Star ⭐ this repository if you find it useful!*
