# 🔄 Continuación de Testing - Post Reinicio

> **Contexto**: Este documento te guía para continuar con las pruebas del traductor después de reiniciar el Mac para activar BlackHole 16ch.

## 📍 Estado Actual

### ✅ Completado

1. **Código implementado** con Dual BlackHole (Opción 3)
   - `src/tts_handler.py` modificado para routing a dispositivo específico
   - `config.json` configurado con voz Paulina y output_device
   - Deduplicación mejorada (threshold 0.90)
   - Filtro de textos cortos (<15 caracteres)

2. **Archivos de test creados**
   - `test_audio_setup.py` - Verificación completa del sistema
   - `test_tts.py` - Test simple de TTS
   - `test_voices.py` - Comparación de voces españolas

3. **Documentación completa**
   - `README.md` - Guía completa del proyecto
   - `SETUP_DUAL_BLACKHOLE.md` - Instrucciones detalladas de configuración

### ⏸️ Pendiente

1. **Activar BlackHole 16ch** (necesita reinicio de audio o Mac)
2. **Configurar Multi-Output Devices** en Audio MIDI Setup
3. **Probar la solución completa** sin feedback loop

---

## 🚀 Pasos a Seguir Después del Reinicio

### Paso 1: Verificar BlackHole 16ch

Después de que tu Mac se reinicie, ejecuta:

```bash
cd /Users/enrique.higuero/Documents/ProyectosPersonales/Impulsap/AgentesSSFF/AsistenteSuccess/traductorTiempoReal

# Verificar que BlackHole 16ch está activo
system_profiler SPAudioDataType | grep "BlackHole"
```

**Resultado esperado:**
```
BlackHole 2ch
BlackHole 16ch    ← Debe aparecer ahora
```

Si **BlackHole 16ch NO aparece**, intenta:
```bash
sudo killall coreaudiod
```

Y vuelve a verificar. Si sigue sin aparecer, reinicia el Mac completamente.

---

### Paso 2: Ejecutar Test de Verificación

```bash
# Activar entorno virtual
source venv/bin/activate

# Ejecutar test de audio setup
python3 test_audio_setup.py
```

**Resultado esperado:**
```
═══════════════════════════════════════════════════════════════════
🎵 Test de Dual BlackHole - Verificación Completa
═══════════════════════════════════════════════════════════════════

1️⃣ Verificando sounddevice...
✅ sounddevice y soundfile disponibles

2️⃣ Dispositivos de audio disponibles:
----------------------------------------------------------------------
  [0] Built-in Microphone (2ch)
  [1] BlackHole 2ch (2ch) ← Para VIDEO (STT captura de aquí)
  [2] BlackHole 16ch (16ch) ← Para TTS (sin feedback!)
  [3] External Headphones (2ch)
  ... (más dispositivos)
----------------------------------------------------------------------

3️⃣ Verificación de configuración:
  ✅ BlackHole 2ch encontrado
  ✅ BlackHole 16ch encontrado    ← IMPORTANTE!
  ⚠️  'TTS Output' Multi-Output NO encontrado
     → Créalo en Audio MIDI Setup (ver SETUP_DUAL_BLACKHOLE.md)
```

Si ves `✅ BlackHole 16ch encontrado`, perfecto! Continúa al Paso 3.

Si ves `❌ BlackHole 16ch NO encontrado`, hay un problema. Revisa:
- ¿El Mac se reinició completamente?
- ¿Ejecutaste `sudo killall coreaudiod`?
- ¿La instalación de BlackHole 16ch fue correcta?

---

### Paso 3: Configurar Multi-Output Devices

Ahora que BlackHole 16ch está activo, vamos a crear los dispositivos Multi-Output.

#### 3.1 Abrir Audio MIDI Setup

1. Presiona **Cmd + Space** (Spotlight)
2. Escribe: `Audio MIDI Setup`
3. Presiona Enter

#### 3.2 Crear Multi-Output #1 (Para Video)

1. Click en **+** (esquina inferior izquierda)
2. Selecciona **"Create Multi-Output Device"**
3. **Renómbralo**: Click derecho → "Rename" → escribe: **"Video Input"**
4. **Marca estos dispositivos**:
   - ✅ **BlackHole 2ch** ← Importante!
   - ✅ **External Headphones** (o tus auriculares/altavoces)
   - ❌ NO marques BlackHole 16ch aquí
5. **Drift Correction**:
   - Marca SOLO "External Headphones" (o tus auriculares)
   - NO marques BlackHole 2ch
6. Cierra la ventana (se guarda automáticamente)

#### 3.3 Crear Multi-Output #2 (Para TTS)

1. Click en **+** otra vez
2. Selecciona **"Create Multi-Output Device"**
3. **Renómbralo**: **"TTS Output"**
4. **Marca estos dispositivos**:
   - ✅ **BlackHole 16ch** ← DIFERENTE al anterior!
   - ✅ **External Headphones** (o tus auriculares/altavoces)
   - ❌ NO marques BlackHole 2ch aquí
5. **Drift Correction**:
   - Marca SOLO "External Headphones"
   - NO marques BlackHole 16ch
6. Cierra Audio MIDI Setup

**Diagrama de lo que acabas de crear:**

```
Multi-Output #1 "Video Input"
  ├─ BlackHole 2ch  ✅ (STT escucha aquí)
  └─ Auriculares    ✅ (Escuchas video aquí)

Multi-Output #2 "TTS Output"
  ├─ BlackHole 16ch ✅ (STT NO escucha, diferente!)
  └─ Auriculares    ✅ (Escuchas traducción aquí)
```

---

### Paso 4: Configurar Salida del Sistema

1. Abre **Preferencias del Sistema** (o **Configuración del Sistema** en macOS Ventura+)
2. Ve a **Sonido** → **Salida**
3. Selecciona: **"Video Input"** como dispositivo de salida

Esto hace que todo el audio del sistema (incluido YouTube, Safari, etc.) vaya a ese Multi-Output.

---

### Paso 5: Verificar Configuración Completa

Ejecuta el test de nuevo:

```bash
python3 test_audio_setup.py
```

**Ahora deberías ver:**
```
3️⃣ Verificación de configuración:
  ✅ BlackHole 2ch encontrado
  ✅ BlackHole 16ch encontrado
  ✅ 'TTS Output' Multi-Output encontrado    ← NUEVO!

4️⃣ Probando TTS con routing específico...
  Texto: 'Prueba de audio en Black Hole dieciséis canales'
  ▶️  Reproduciendo...
     (Deberías escucharlo en tus auriculares)
     (Y NO debería crear feedback)
  ✅ Test de TTS completado

═══════════════════════════════════════════════════════════════════
📊 Resumen:
  ✅ Sistema configurado correctamente para Dual BlackHole
  ✅ Puedes usar el traductor sin feedback loop

  Siguiente paso:
    python3 src/main.py
═══════════════════════════════════════════════════════════════════
```

Si ves esto, **¡PERFECTO!** El sistema está listo.

---

### Paso 6: Probar el Traductor Completo

Ahora vamos a probar con un video real:

```bash
python3 src/main.py
```

#### Test con YouTube

1. **Abre Safari** (o tu navegador preferido)
2. **Ve a YouTube** y busca un video en inglés
3. **Reproduce el video**
4. En el traductor:
   - Selecciona **"Audio + Subtitles"**
   - Click **"Start Translation"**

**Resultado esperado:**
- ✅ Escuchas el video en inglés en tus auriculares
- ✅ Escuchas la traducción en español en tus auriculares
- ✅ Ves subtítulos flotantes (original + traducción)
- ✅ **NO hay feedback** (TTS no se captura a sí mismo)
- ✅ **NO hay repeticiones** excesivas

#### Verificar en los Logs

En la consola del traductor, deberías ver:

```
🎵 Found TTS device: TTS Output (ID: X)
🔊 Playing on device X
[STT] Transcribed: "Hello everyone, welcome to this video"
[Translation] Translated: "Hola a todos, bienvenidos a este video"
[TTS] 🔊 Speaking: "Hola a todos, bienvenidos a este video"
```

Si ves cosas como:
```
[STT] Transcribed: "Desinist demials deep alopras"
```

Eso significa que hay feedback loop (TTS está siendo capturado por STT). Revisa la configuración.

---

## 🐛 Troubleshooting

### Problema 1: No escucho la traducción

**Síntomas**: Video se escucha, pero no hay audio de traducción

**Solución**:
1. Verifica que en `config.json` esté:
   ```json
   "tts": {
     "enabled": true,
     "output_device": "TTS Output"
   }
   ```

2. Verifica que el volumen del sistema no esté en mute
3. Ejecuta `python3 test_tts.py` para probar TTS aislado

### Problema 2: Sigo con feedback loop

**Síntomas**: Los logs muestran transcripciones sin sentido, audio distorsionado

**Solución**:
1. Verifica que los Multi-Output devices están bien creados:
   - "Video Input" con BlackHole **2ch**
   - "TTS Output" con BlackHole **16ch**

2. Verifica que el código esté buscando el dispositivo correcto:
   ```bash
   grep -n "TTS Output" src/tts_handler.py
   ```
   Debes ver líneas que buscan "TTS Output" o "BlackHole 16ch"

3. Ejecuta test de audio para ver qué dispositivo se está usando:
   ```bash
   python3 test_audio_setup.py
   ```

### Problema 3: No hay subtítulos

**Síntomas**: Audio funciona, pero no aparece la ventana de subtítulos

**Solución**:
1. Verifica en `config.json`:
   ```json
   "subtitle_overlay": {
     "enabled": true
   }
   ```

2. Verifica que tkinter está instalado:
   ```bash
   python3 -c "import tkinter; print('OK')"
   ```

3. Revisa los logs para errores de subtitle_overlay

### Problema 4: Audio del video no se captura

**Síntomas**: No aparecen transcripciones, el traductor no detecta audio

**Solución**:
1. Verifica que la salida del sistema es "Video Input"
2. Verifica que el video está reproduciendo con audio (no mute)
3. Ejecuta:
   ```bash
   python3 -c "import sounddevice as sd; print(sd.query_devices())"
   ```
   Y verifica que BlackHole 2ch tiene input channels > 0

---

## 📊 Métricas Esperadas

Con la configuración correcta, deberías ver:

- **STT Latency**: 500-1500ms
- **Translation Time**: 100-300ms
- **Total Latency**: 1-3 segundos
- **CPU Usage**: 30-60%
- **Memory**: 500MB-1GB

---

## 📝 Notas Adicionales

### Configuración de Navegadores

#### Safari
- Usa automáticamente la salida del sistema ✅
- No necesita configuración adicional

#### Chrome/Brave
- Puede necesitar extensión "Audio Output Switcher"
- Configurarla para usar "Video Input"

#### Firefox
- Usa salida del sistema por defecto ✅

### Teams/Zoom

#### Microsoft Teams
- En Settings → Devices → Speaker
- Seleccionar "Video Input"

#### Zoom
- En Settings → Audio → Speaker
- Seleccionar "Video Input"

---

## 🎯 Checklist Final

Antes de considerar la configuración completa, verifica:

- [ ] BlackHole 16ch aparece en `system_profiler SPAudioDataType`
- [ ] Multi-Output "Video Input" creado con BlackHole 2ch
- [ ] Multi-Output "TTS Output" creado con BlackHole 16ch
- [ ] Salida del sistema configurada a "Video Input"
- [ ] `python3 test_audio_setup.py` pasa todos los checks
- [ ] Test de TTS reproduce audio y se escucha
- [ ] `python3 src/main.py` inicia sin errores
- [ ] Video de YouTube se captura y traduce
- [ ] No hay feedback loop en los logs
- [ ] Subtítulos aparecen en pantalla

---

## 📞 Si Todo Funciona

**¡Felicitaciones!** 🎉

Ahora tienes un traductor en tiempo real completamente funcional con:
- ✅ Captura de audio del sistema
- ✅ Transcripción en tiempo real
- ✅ Traducción automática
- ✅ Síntesis de voz en español
- ✅ Subtítulos flotantes
- ✅ **Sin feedback loop**

### Próximos Pasos

1. **Ajustar configuración** según tus preferencias:
   - Probar diferentes voces (`test_voices.py`)
   - Ajustar velocidad de habla (rate en config.json)
   - Cambiar tamaño de fuente de subtítulos

2. **Probar con diferentes fuentes**:
   - YouTube videos
   - Microsoft Teams calls
   - Zoom meetings
   - Podcasts en Safari

3. **Compartir con la comunidad**:
   - El proyecto está listo para GitHub
   - Incluye README completo
   - Documentación de instalación

---

**¡Buena suerte con las pruebas!** 🚀

Si encuentras problemas, revisa:
- Este documento
- `SETUP_DUAL_BLACKHOLE.md`
- `README.md`
- Logs en `logs/translator.log`
