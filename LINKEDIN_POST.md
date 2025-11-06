# LinkedIn Post - Real-Time Audio Translator

---

🌍 **Acabo de lanzar mi traductor de audio en tiempo real con IA para macOS**

Después de varias semanas de desarrollo, estoy emocionado de compartir mi proyecto open-source: un traductor de audio en tiempo real que utiliza IA para traducir videos de YouTube, reuniones de Teams/Zoom, y cualquier fuente de audio.

## 🎯 ¿Qué hace?

El sistema captura audio en tiempo real, lo transcribe usando Whisper (OpenAI), traduce el texto con modelos Helsinki-NLP, y genera subtítulos flotantes + audio traducido con voz natural en español (Mónica).

## 🔧 Características técnicas destacadas:

✅ **Arquitectura Dual BlackHole**: Sistema innovador con dos canales virtuales de audio (2ch y 16ch) que elimina completamente los loops de retroalimentación. El audio original va por un canal, la traducción por otro.

✅ **Faster-Whisper**: Implementación optimizada de Whisper con detección de actividad de voz (VAD) para transcripción precisa y rápida (<1.5s).

✅ **Deduplicación inteligente**: Sistema anti-repeticiones con historial de textos y umbral de similitud del 85%, evitando traducciones duplicadas.

✅ **Subtítulos flotantes**: Overlay transparente always-on-top con texto original y traducido, ideal para presentaciones y videos.

✅ **UI simplificada**: Interfaz limpia que solo muestra controles funcionales. La configuración avanzada se gestiona via JSON.

## 🚀 Casos de uso:

• 📹 **YouTube**: Traduce videos en inglés mientras los ves
• 💼 **Teams/Zoom**: Reuniones internacionales con traducción en vivo
• 🎓 **Formación**: Cursos online en otros idiomas
• 🎬 **Entretenimiento**: Series y películas sin subtítulos

## 🎨 Stack tecnológico:

- Python 3.11+
- Faster-Whisper (STT)
- Helsinki-NLP OPUS-MT (Traducción)
- PyQt6 (UI)
- BlackHole Audio Driver
- macOS native TTS (voz Mónica)

## 📊 Rendimiento:

• Latencia total: <3 segundos
• Procesamiento: Base model (Whisper)
• CPU/GPU: Optimizado para Apple Silicon

## 🔗 Código abierto

El proyecto está disponible en GitHub bajo licencia MIT. Incluye documentación completa de setup, guías de troubleshooting, y scripts de testing.

**Link en mi perfil** o búscalo: "Real-Time Audio Translator macOS"

---

💬 **¿Te gustaría probar algo así en tu día a día?**
Comparte tu caso de uso en los comentarios 👇

#MachineLearning #AI #Python #OpenSource #Translation #RealTime #NLP #SpeechRecognition #macOS #DeveloperTools

---

**Nota**: Si te ha gustado el proyecto, ⭐ en GitHub es muy apreciado. Siempre estoy abierto a colaboraciones y mejoras.

---

## Versión corta (si prefieres algo más breve):

🌍 Nuevo proyecto open-source: **Traductor de audio en tiempo real con IA para macOS**

Traduce automáticamente videos de YouTube, reuniones de Teams/Zoom y cualquier audio con:
• Whisper (STT) + Helsinki-NLP (Traducción)
• Subtítulos flotantes + voz natural en español
• Arquitectura Dual BlackHole (sin feedback)
• Latencia <3 segundos

Stack: Python, Faster-Whisper, PyQt6, BlackHole
Licencia: MIT

¿Tu caso de uso? 👇

#AI #Python #OpenSource #Translation #macOS #NLP

[Link al repo]
