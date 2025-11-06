# 🏗️ Arquitectura del Sistema

## Visión General

El **Real-Time Audio Translator** es un sistema modular diseñado para traducir audio en tiempo real con latencia mínima (<3s) utilizando una arquitectura de pipeline con múltiples componentes especializados.

---

## 📐 Diagrama de Flujo de Datos

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUDIO SOURCE                                  │
│         (YouTube, Teams, Zoom, Safari, etc.)                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Audio Stream (Stereo PCM)
                         │
                         ▼
              ┌──────────────────────┐
              │  Multi-Output Device │
              │   "Video Input"      │
              ├─────────┬────────────┤
              │ BH 2ch  │  Speakers  │
              └────┬────┴─────┬──────┘
                   │          │
                   │          └──────► 🔊 User Hears Video
                   │
                   ▼
          ┌────────────────────┐
          │  BlackHole 2ch     │  Virtual Audio Device
          │  (Loopback)        │
          └──────────┬─────────┘
                     │
                     ▼
          ┌──────────────────────────┐
          │  SYSTEM AUDIO CAPTURE    │  system_audio_capture.py
          │  - Monitors BlackHole    │
          │  - 16kHz resampling      │
          │  - Chunk buffering       │
          └──────────┬───────────────┘
                     │
                     │ Audio Chunks (NumPy arrays)
                     │
                     ▼
          ┌──────────────────────────┐
          │      STT HANDLER         │  stt_handler_fast.py
          │  - Faster-Whisper        │
          │  - VAD (Voice Activity)  │
          │  - Language detection    │
          └──────────┬───────────────┘
                     │
                     │ Transcribed Text (English)
                     │
                     ▼
          ┌──────────────────────────┐
          │  TRANSLATION HANDLER     │  translation_handler.py
          │  - Helsinki-NLP OPUS-MT  │
          │  - Context-aware         │
          │  - Batch processing      │
          └──────────┬───────────────┘
                     │
                     │ Translated Text (Spanish)
                     │
        ┌────────────┴─────────────┐
        │                          │
        ▼                          ▼
┌──────────────────┐    ┌──────────────────────┐
│ SUBTITLE OVERLAY │    │    TTS HANDLER       │  tts_handler.py
│  - Tkinter window│    │  - macOS 'say'       │
│  - Floating text │    │  - Paulina voice     │
│  - Auto-hide     │    │  - Device routing    │
└──────────────────┘    └──────────┬───────────┘
                                   │
                                   │ Generated Audio (AIFF)
                                   │
                                   ▼
                        ┌──────────────────────┐
                        │  Multi-Output Device │
                        │    "TTS Output"      │
                        ├─────────┬────────────┤
                        │ BH 16ch │  Speakers  │
                        └────┬────┴─────┬──────┘
                             │          │
                             │          └──────► 🔊 User Hears Translation
                             │
                             └──────► ❌ STT doesn't capture
                                        (Different BlackHole!)

RESULT: NO FEEDBACK LOOP! 
```

---

## 🔧 Componentes Principales

### 1. System Audio Capture (`system_audio_capture.py`)

**Responsabilidad**: Capturar audio del sistema en tiempo real.

```python
class SystemAudioCapture:
    - Monitors: BlackHole 2ch
    - Sample Rate: 16000 Hz (Whisper optimized)
    - Chunk Size: 4096 samples
    - Buffer: 16384 samples (1 second)
```

**Características**:
- Resampling automático a 16kHz
- Buffer circular para evitar pérdida de audio
- Detección de silencio
- Thread-safe operation

---

### 2. STT Handler (`stt_handler_fast.py`)

**Responsabilidad**: Transcribir audio a texto usando Faster-Whisper.

```python
class STTHandlerFast:
    - Model: Faster-Whisper (tiny/base/small/medium/large)
    - VAD: Voice Activity Detection
    - Language: Auto-detect or explicit
    - Device: CPU/GPU auto-selection
```

**Características**:
- **VAD Filter**: Solo transcribe cuando hay voz
- **Batch Processing**: Procesa chunks de 30 segundos
- **GPU Acceleration**: Automático en Apple Silicon (Metal)
- **Low Latency**: 500-1500ms según modelo

**Modelos disponibles**:
| Model  | Size | VRAM | Speed | Quality |
|--------|------|------|-------|---------|
| tiny   | 75MB | <1GB | Fast  | Basic   |
| base   | 150MB| <2GB | Good  | Good    |
| small  | 500MB| <3GB | OK    | Better  |
| medium | 1.5GB| <5GB | Slow  | Great   |
| large  | 3GB  | <10GB| Slower| Best    |

---

### 3. Translation Handler (`translation_handler.py`)

**Responsabilidad**: Traducir texto usando Helsinki-NLP.

```python
class TranslationHandler:
    - Model: Helsinki-NLP/opus-mt-{src}-{tgt}
    - Pipeline: HuggingFace Transformers
    - Batching: Dynamic batch size
    - Cache: Recent translations
```

**Características**:
- **Context-Aware**: Mantiene contexto entre frases
- **Fast Inference**: 100-300ms por frase
- **Quality**: Professional-grade translation
- **Extensible**: Soporta múltiples pares de idiomas

**Pares de idiomas soportados**:
```
en → es (English → Spanish)
es → en (Spanish → English)
en → fr (English → French)
en → de (English → German)
... (50+ language pairs available)
```

---

### 4. TTS Handler (`tts_handler.py`)

**Responsabilidad**: Sintetizar voz en español con routing a dispositivo específico.

```python
class TTSHandler:
    - Engine: macOS 'say' command
    - Voice: Paulina (configurable)
    - Rate: 200 WPM
    - Routing: BlackHole 16ch Multi-Output
```

**Características**:
- **Device Routing**: Usa sounddevice para rutear a dispositivo específico
- **Natural Voices**: Paulina, Mónica, Eddy, Juan
- **Deduplication**: Threshold 0.90 para evitar repeticiones
- **Queue Management**: FIFO con límite de 3 items
- **Volume Control**: Ajustable por configuración

**Flujo de TTS**:
```
Text → say -o temp.aiff → soundfile.read() → sounddevice.play(device=TTS_OUTPUT)
```

---

### 5. Subtitle Overlay (`subtitle_overlay.py`)

**Responsabilidad**: Mostrar subtítulos flotantes en pantalla.

```python
class SubtitleOverlay:
    - Framework: Tkinter
    - Position: Bottom/Top/Center
    - Style: Customizable font/size/color
    - Auto-hide: 6 seconds default
```

**Características**:
- **Always on Top**: Se mantiene sobre todas las ventanas
- **Transparent Background**: Solo texto visible
- **Dual Text**: Original + traducción
- **Smooth Animations**: Fade in/out
- **Multi-Monitor**: Soporta múltiples pantallas

---

### 6. UI (`ui.py`)

**Responsabilidad**: Interfaz gráfica para control y monitoreo.

```python
class TranslatorUI:
    - Framework: Tkinter
    - Modes: Audio+Subtitles / Subtitles Only
    - Metrics: Real-time latency tracking
    - Controls: Start/Stop/Settings
```

**Características**:
- **Real-time Metrics**:
  - STT Latency
  - Translation Time
  - Total Latency
  - Transcriptions per minute
- **Device Selection**: Audio input device picker
- **Visual Feedback**: Status indicators
- **Error Handling**: User-friendly error messages

---

## 🎛️ Dual BlackHole Architecture

### Problema Original

```
Video → Multi-Output → BlackHole 2ch → STT ✅
                     → Speakers → User ✅

TTS → Multi-Output → BlackHole 2ch → STT ❌ FEEDBACK!
                   → Speakers → User ✅
```

**Resultado**: TTS audio era capturado por STT, creando loop infinito.

### Solución: Dual BlackHole

```
Video → Multi-Output #1 → BlackHole 2ch → STT ✅
                        → Speakers → User ✅

TTS → Multi-Output #2 → BlackHole 16ch → STT ❌ NO captura
                      → Speakers → User ✅
```

**Resultado**: STT solo escucha BlackHole 2ch, TTS va a BlackHole 16ch. ¡Sin feedback!

---

## ⚙️ Configuración (`config.json`)

```json
{
  "audio": {
    "input_device": 1,              // BlackHole 2ch ID
    "sample_rate": 16000,           // Whisper optimized
    "chunk_size": 4096,             // Latency vs accuracy
    "buffer_size": 16384            // 1 second buffer
  },
  "stt": {
    "model_size": "base",           // Model selection
    "language": "en",               // Source language
    "vad_filter": true,             // Voice Activity Detection
    "vad_threshold": 0.6            // Sensitivity
  },
  "translation": {
    "language_from": "en",
    "language_to": "es",
    "model": "Helsinki-NLP/opus-mt-en-es"
  },
  "tts": {
    "voice": "Paulina",             // Natural Spanish
    "rate": 200,                    // Speed (WPM)
    "volume": 0.9,
    "output_device": "TTS Output"   // BlackHole 16ch routing
  }
}
```

---

## 🔄 Flujo de Ejecución

### Secuencia Completa

1. **Inicio**:
   ```
   User runs: python3 src/main.py
   → UI inicializa
   → Componentes cargan modelos
   → Audio devices detectados
   ```

2. **Usuario inicia traducción**:
   ```
   User clicks "Start Translation"
   → System audio capture starts monitoring BlackHole 2ch
   → STT handler en espera
   → Subtitle overlay aparece
   ```

3. **Audio detectado**:
   ```
   Video plays audio
   → Multi-Output #1 envía a BlackHole 2ch + Speakers
   → System audio capture captura chunks
   → Chunks enviados a STT handler
   ```

4. **Transcripción**:
   ```
   STT handler recibe audio chunk
   → VAD verifica si hay voz
   → Faster-Whisper transcribe
   → Texto enviado a Translation handler
   ```

5. **Traducción**:
   ```
   Translation handler recibe texto
   → Helsinki-NLP traduce
   → Texto traducido enviado a:
     a) Subtitle overlay
     b) TTS handler
   ```

6. **Salida**:
   ```
   Subtitle overlay muestra texto
   TTS handler genera audio
   → Audio enviado a Multi-Output #2
   → BlackHole 16ch + Speakers
   → User escucha traducción
   → STT NO captura (diferente BlackHole)
   ```

---

## 📊 Performance Characteristics

### Latencia

| Component           | Latency   | Notes                    |
|---------------------|-----------|--------------------------|
| Audio Capture       | <50ms     | Buffer overhead          |
| STT (base)          | 500-800ms | Model dependent          |
| Translation         | 100-200ms | Sentence length dependent|
| TTS                 | 500-1000ms| Text length dependent    |
| Subtitle Rendering  | <50ms     | Tkinter overhead         |
| **Total (typical)** | **1.5-2.5s** | From speech to output |

### Recursos

| Component       | CPU  | RAM   | GPU    |
|-----------------|------|-------|--------|
| Audio Capture   | 5%   | 50MB  | -      |
| STT (base)      | 40%  | 500MB | 20%*   |
| Translation     | 20%  | 300MB | -      |
| TTS             | 10%  | 100MB | -      |
| UI + Subtitles  | 5%   | 100MB | -      |
| **Total**       | **80%** | **1GB** | **20%*** |

*GPU usage on Apple Silicon with Metal acceleration

---

## 🔐 Seguridad y Privacidad

### Datos Locales

- ✅ **Todo el procesamiento es local**
- ✅ No se envían datos a servidores externos
- ✅ No hay telemetría
- ✅ No se guardan grabaciones (por defecto)

### Modelos

- ✅ Modelos de Faster-Whisper descargados localmente
- ✅ Modelos de Helsinki-NLP descargados localmente
- ✅ TTS usa macOS nativo (no internet)

### Logs

- Logs almacenados en `logs/translator.log`
- No contienen información sensible
- Rotación automática
- Ignorados por git

---

## 🧪 Testing Strategy

### Unit Tests (futuro)
```python
tests/
├── test_audio_capture.py
├── test_stt_handler.py
├── test_translation_handler.py
├── test_tts_handler.py
└── test_subtitle_overlay.py
```

### Integration Tests
```python
test_audio_setup.py   # Audio routing verification
test_tts.py           # TTS simple test
test_voices.py        # Voice comparison
```

### End-to-End Tests (manual)
1. YouTube video translation
2. Teams call translation
3. Zoom meeting translation

---

## 🚀 Extensibilidad

### Agregar Nuevo Motor de TTS

```python
# En tts_handler.py
class TTSHandler:
    def _speak_elevenlabs(self, text: str):
        # Implementación ElevenLabs
        pass

    def _speak_google(self, text: str):
        # Implementación Google TTS
        pass
```

### Agregar Nuevo Par de Idiomas

```json
// En config.json
{
  "translation": {
    "language_from": "fr",
    "language_to": "en",
    "model": "Helsinki-NLP/opus-mt-fr-en"
  }
}
```

### Agregar Nueva Fuente de Audio

```python
# En system_audio_capture.py
class MicrophoneCapture(SystemAudioCapture):
    def __init__(self):
        super().__init__(device_name="Built-in Microphone")
```

---

**Este documento describe la arquitectura actual del sistema. Para uso práctico, consulta README.md.**
