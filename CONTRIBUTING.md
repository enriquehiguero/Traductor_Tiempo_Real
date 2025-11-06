# Contributing to Real-Time Audio Translator

First off, thank you for considering contributing to this project! 🎉

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the issue
- **Expected vs actual behavior**
- **System information** (macOS version, Python version)
- **Logs** if applicable (`logs/translator.log`)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Clear title and description**
- **Use case** - why would this be useful?
- **Possible implementation** if you have ideas

### Pull Requests

1. **Fork** the repository
2. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/my-feature
   ```
3. **Make your changes** following the code style
4. **Test your changes** thoroughly
5. **Commit** with clear messages:
   ```bash
   git commit -m "Add feature: description"
   ```
6. **Push** to your fork:
   ```bash
   git push origin feature/my-feature
   ```
7. **Open a Pull Request** with:
   - Clear description of changes
   - Related issue number (if applicable)
   - Screenshots/videos for UI changes

## Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/real-time-translator.git
cd real-time-translator

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (if added)
pip install -r requirements-dev.txt  # (when available)
```

## Code Style

- Follow **PEP 8** for Python code
- Use **type hints** where appropriate
- Add **docstrings** for functions and classes
- Keep functions **focused and small**
- Write **descriptive variable names**

Example:

```python
def transcribe_audio(audio_data: np.ndarray, sample_rate: int) -> str:
    """
    Transcribe audio data to text using Whisper.

    Args:
        audio_data: Audio samples as numpy array
        sample_rate: Sample rate in Hz

    Returns:
        Transcribed text
    """
    # Implementation
    pass
```

## Testing

Before submitting a PR:

```bash
# Run basic tests
python3 test_audio_setup.py
python3 test_tts.py

# Test main app
python3 src/main.py
```

## Areas for Contribution

### High Priority
- [ ] Support for more languages (FR, DE, IT, PT, etc.)
- [ ] Performance optimizations
- [ ] Better error handling and recovery
- [ ] Unit tests coverage

### Medium Priority
- [ ] Alternative TTS engines (Google, Azure, ElevenLabs)
- [ ] Alternative STT engines (Google, Azure)
- [ ] Better UI/UX improvements
- [ ] Configuration presets for common use cases

### Nice to Have
- [ ] Windows/Linux support
- [ ] Browser extension
- [ ] Multi-speaker detection
- [ ] Voice cloning for TTS
- [ ] Cloud deployment option

## Community Guidelines

- Be respectful and constructive
- Help others learn and grow
- Focus on the problem, not the person
- Assume good intentions

## Questions?

Feel free to open an issue with the **question** label or start a discussion in GitHub Discussions.

---

Thank you for contributing! 🙌
