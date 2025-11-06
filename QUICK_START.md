# ⚡ Quick Start Guide

> **5 minutos para empezar a traducir en tiempo real**

## 🚀 Instalación Rápida

### 1. Instalar BlackHole
```bash
brew install blackhole-2ch blackhole-16ch
sudo killall coreaudiod
```

### 2. Verificar Instalación
```bash
system_profiler SPAudioDataType | grep "BlackHole"
# Debes ver: BlackHole 2ch y BlackHole 16ch
```

### 3. Configurar Audio MIDI Setup

**Multi-Output #1 "Video Input":**
- Abre: Audio MIDI Setup (Spotlight → Audio MIDI Setup)
- Click + → Create Multi-Output Device
- Nombre: "Video Input"
- Marca: ✅ BlackHole 2ch + ✅ Tus Auriculares

**Multi-Output #2 "TTS Output":**
- Click + → Create Multi-Output Device
- Nombre: "TTS Output"
- Marca: ✅ BlackHole 16ch + ✅ Tus Auriculares

### 4. Configurar Sistema
- Preferences → Sound → Output
- Selecciona: **"Video Input"**

### 5. Instalar Python Dependencies
```bash
cd traductorTiempoReal
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 6. Test Rápido
```bash
python3 test_audio_setup.py
```

Si ves `✅ Sistema configurado correctamente`, ¡estás listo!

---

## 🎮 Uso Básico

### Ejecutar Traductor
```bash
source venv/bin/activate
python3 src/main.py
```

### En la Interfaz
1. Click **"Start Translation"**
2. Reproduce un video en YouTube
3. ¡Disfruta la traducción en tiempo real!

---

## 🐛 Problemas Comunes

### No escucho traducción
```bash
# Verifica config
grep -A5 '"tts"' config.json
# Debe tener: "enabled": true, "output_device": "TTS Output"
```

### Feedback loop
```bash
# Verifica dispositivos
python3 test_audio_setup.py
# Debe mostrar BlackHole 16ch y TTS Output
```

### Video no se captura
- Verifica que la salida del sistema es "Video Input"
- Verifica que el video está reproduciendo (no mute)

---

## 📚 Documentación Completa

- **README.md** - Guía completa
- **CONTINUE_TESTING.md** - Testing detallado
- **SETUP_DUAL_BLACKHOLE.md** - Setup de audio
- **ARCHITECTURE.md** - Arquitectura técnica

---

## 💡 Tips

### Mejor Rendimiento
```json
// En config.json
{
  "stt": {
    "model_size": "tiny"  // O "base" para mejor balance
  }
}
```

### Mejor Calidad de Voz
```bash
# Probar diferentes voces
python3 test_voices.py

# Editar config.json
"voice": "Paulina"  // Más natural
```

### Subtítulos Más Grandes
```json
// En config.json
{
  "subtitle_overlay": {
    "font_size": 40  // De 32 a 40
  }
}
```

---

## 🆘 Ayuda

- **Issues**: [GitHub Issues](https://github.com/yourusername/real-time-translator/issues)
- **Docs**: Revisa README.md y otros .md files
- **Logs**: `tail -f logs/translator.log`

---

**¡Listo! En 5 minutos ya deberías estar traduciendo.** 🎉

Para más detalles, consulta `README.md`.
