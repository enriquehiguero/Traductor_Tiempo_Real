# 🎉 Release Notes - Version 2.0

## Real-Time Audio Translator v2.0 - "Mónica Edition"

**Release Date**: January 6, 2025

---

## 🌟 What's New?

### 🎙️ Meet Mónica - Your Professional Spanish Voice

The translator now uses **Mónica**, a high-quality Spanish voice from Spain, for all audio translations. Mónica offers:

- ✅ Clear, professional European Spanish accent (🇪🇸)
- ✅ Formal pronunciation perfect for business and technical content
- ✅ Natural intonation that sounds human-like
- ✅ Adjustable speed (50-400 words per minute)
- ✅ Adjustable volume (0-100%)

**Why Mónica?** After testing multiple voices, Mónica provides the best balance of clarity, professionalism, and natural sound for real-time translation.

---

## 🎨 Simplified Interface

We've cleaned up the UI to show **only what actually works**. No more confusing buttons!

### What's Changed:

#### ❌ Removed (These didn't work anyway):
- Audio device selectors
- Language dropdown menus
- STT model and GPU options
- Voice selector

#### ✅ Kept (These work great):
- **Output Mode**: Choose between "Subtitles Only" or "Audio + Subtitles"
- **Speech Rate**: Adjust how fast Mónica speaks (recommended: 180-200 WPM)
- **Volume**: Control how loud the translation audio is (recommended: 80-90%)
- **Translation Output**: See original and translated text in real-time

#### 📋 Now Read-Only:
- **Translation Settings**: Shows your current language pair from config.json
- Want to change languages? Just edit `config.json` and restart the app!

---

## 🚀 Major Improvements

### 1. No More Repetitions! 🎯

Version 1.0 sometimes repeated the same translation multiple times. This is **completely fixed** in v2.0 with:

- 🧠 **Smart memory**: Remembers the last 5 translations (not just 1)
- 🔍 **Similarity detection**: Catches near-duplicates (85% similarity threshold)
- ⏭️ **Skip if busy**: Won't queue up translations if already speaking
- ⏱️ **Echo prevention**: 0.3 second pause after speaking to avoid capturing echo

**Result**: Each sentence is translated exactly once. No more annoying repeats!

### 2. Better Subtitle Quality 📺

In version 1.0, subtitles got worse when audio mode was enabled. **Fixed!**

**The Problem**: The system was pausing audio capture while Mónica spoke, losing parts of the video.

**The Solution**: Continuous audio capture! The Dual BlackHole architecture keeps video audio and translation audio completely separate, so there's no need to pause.

**Result**: Subtitles are now the **same high quality** whether you use "Subtitles Only" or "Audio + Subtitles" mode.

### 3. Smoother Performance ⚡

- Non-blocking audio playback for better responsiveness
- Optimized queue management (max 1 item instead of 3)
- Better resource utilization

**Result**: The app feels snappier and more responsive.

---

## 🎮 How to Use v2.0

### Quick Start

1. **Launch the app**: `python3 src/main.py`

2. **Choose your mode**:
   - **Subtitles Only** (Recommended for beginners): See translations on-screen, hear original audio
   - **Audio + Subtitles** (Full experience): Hear Mónica's translation + see subtitles

3. **Adjust TTS settings** (if using Audio mode):
   - **Speech Rate**: Slower = more clarity, Faster = less delay
   - **Volume**: Make sure you can hear Mónica over the original audio

4. **Click "Start Translation"** and play your video!

### Tips for Best Results

✅ **DO**:
- Use "Subtitles Only" mode when first testing
- Adjust speech rate to 180-200 for best clarity
- Keep volume at 80-90% to hear both original and translation
- Verify your Dual BlackHole setup (see README.md)

❌ **DON'T**:
- Try to change the voice (it's fixed to Mónica)
- Try to change languages from UI (use config.json instead)
- Expect it to work without BlackHole 2ch and 16ch installed
- Mute the video source (STT won't capture anything!)

---

## 🔧 Configuration Changes

### To Change Languages

**Before (v1.0)**: UI dropdowns (but they didn't work!)
**Now (v2.0)**: Edit `config.json` and restart

Example: French → Spanish

```json
{
  "stt": {
    "language": "fr"  // ← Change this
  },
  "translation": {
    "language_from": "fr",  // ← And this
    "language_to": "es",
    "model": "Helsinki-NLP/opus-mt-fr-es"  // ← And this
  }
}
```

Then restart the app. Easy!

### To Change Voice

**Current**: Mónica (fixed)

**Want a different voice?**
You'll need to edit the source code:
- `src/main.py` line 374
- `src/ui.py` line 403

Change `"Mónica"` to your preferred voice (e.g., `"Paulina"`, `"Eddy"`)

---

## 🐛 Bug Fixes

### Fixed Issues:

1. ✅ **Repetitive translations** - Completely eliminated with smart deduplication
2. ✅ **Poor subtitles in Audio mode** - Fixed with continuous audio capture
3. ✅ **Queue backlog** - Fixed with single-item queue
4. ✅ **Confusing UI** - Removed non-functional controls
5. ✅ **Echo capture** - Fixed with post-speech delay

---

## 📊 Performance

**Still lightning fast!**
- Total latency: **<3 seconds** (same as v1.0)
- STT: 500-1500ms
- Translation: 100-300ms
- TTS: 500-1000ms

No performance regression despite all the improvements!

---

## ⚠️ Breaking Changes

If you're upgrading from v1.0, here's what changed:

### 1. Voice Selection
- **Before**: Selectable from UI
- **Now**: Fixed to Mónica
- **Reason**: Simplifies UX, ensures consistent quality

### 2. Language Selection
- **Before**: UI dropdowns (that didn't work)
- **Now**: config.json only
- **Reason**: Honest UX - show what actually works

### 3. Audio Devices
- **Before**: UI dropdowns (that didn't work)
- **Now**: config.json only
- **Reason**: Honest UX - show what actually works

### 4. STT Settings
- **Before**: UI controls (that didn't work)
- **Now**: config.json only
- **Reason**: Honest UX - show what actually works

**Bottom line**: Everything that worked in v1.0 still works in v2.0. We just removed the UI controls that never actually did anything!

---

## 🙏 Feedback Welcome!

Found a bug? Have a feature request? Want to contribute?

- 🐛 **Report bugs**: Open an issue on GitHub
- 💡 **Feature requests**: Open an issue on GitHub
- 🤝 **Contribute**: Fork and submit a Pull Request
- ⭐ **Like it?**: Star the repository!

---

## 📚 Documentation

- **Full README**: `README.md`
- **Technical Changelog**: `CHANGELOG.md`
- **Setup Guide**: `SETUP_DUAL_BLACKHOLE.md` (if it exists)
- **Config Reference**: See `config.json` with comments

---

## 🎓 What's Next?

### Planned for v2.1 (Coming Soon):

- [ ] Configurable voice via config.json (no code editing needed!)
- [ ] Multiple voice profiles (switch between Mónica, Paulina, Eddy, etc.)
- [ ] Language preset system (quick switch between language pairs)
- [ ] Hot-reload config (change settings without restart)
- [ ] Performance dashboard (see real-time metrics)

### Your Input Matters!

What features would YOU like to see? Let us know on GitHub!

---

## 🎉 Thank You!

Thanks for using Real-Time Audio Translator v2.0!

We hope Mónica becomes your favorite translation companion. Whether you're watching YouTube, attending international meetings, or learning a new language, we're here to break down language barriers.

**Made with ❤️ for the global community**

---

**Version**: 2.0.0
**Release Date**: January 6, 2025
**License**: MIT
**Platform**: macOS 10.15+
**Python**: 3.9+
