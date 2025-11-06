# 🎵 Configuración Dual BlackHole - Solución Definitiva

## ⚠️ IMPORTANTE: Primero Activa BlackHole 16ch

BlackHole 16ch está instalado pero necesita activarse:

### Paso 1: Reiniciar Servicio de Audio

Ejecuta en Terminal:
```bash
sudo killall coreaudiod
```

**Esto reiniciará el audio del sistema (todos los sonidos se cortarán por 1 segundo y volverán)**

### Paso 2: Verificar que Aparece

Ejecuta:
```bash
system_profiler SPAudioDataType | grep "BlackHole"
```

Deberías ver:
```
BlackHole 2ch
BlackHole 16ch    ← Debe aparecer
```

Si NO aparece BlackHole 16ch:
1. Reinicia el Mac
2. Vuelve a verificar

---

## 🎛️ Arquitectura de la Solución

```
┌─────────────────────────────────────────────────────────┐
│ VIDEO/TEAMS (Inglés)                                    │
└──────────┬──────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────┐
│ Multi-Output Device #1 (PARA VIDEO)                    │
│  ├─ BlackHole 2ch  ✅ (STT escucha aquí)               │
│  └─ Auriculares    ✅ (Tú escuchas el video)           │
└──────────┬──────────────────────────────────────────────┘
           │
           ├─→ BlackHole 2ch → STT captura ✅
           └─→ Auriculares → Escuchas video ✅

┌─────────────────────────────────────────────────────────┐
│ TTS TRADUCTOR (Español)                                 │
└──────────┬──────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────┐
│ Multi-Output Device #2 (PARA TTS)                      │
│  ├─ BlackHole 16ch ✅ (STT NO escucha, diferente!)     │
│  └─ Auriculares    ✅ (Tú escuchas traducción)         │
└──────────┬──────────────────────────────────────────────┘
           │
           └─→ Auriculares → Escuchas traducción ✅

RESULTADO: ¡SIN FEEDBACK LOOP! 🎉
```

---

## 🔧 Configuración Paso a Paso

### Paso 3: Abrir Audio MIDI Setup

1. Abre **Spotlight** (Cmd+Space)
2. Escribe: `Audio MIDI Setup`
3. Presiona Enter

### Paso 4: Crear Multi-Output Device #1 (Para Video)

1. Click en **+** (esquina inferior izquierda)
2. Selecciona **"Create Multi-Output Device"**
3. Renómbralo: **"Video Input (BlackHole 2ch)"**
4. **Marca:**
   - ✅ BlackHole 2ch
   - ✅ Auriculares externos (o Altavoces del MacBook Pro)
5. **Drift Correction:** Marca solo "Auriculares externos"
6. Cierra la ventana (se guarda automáticamente)

### Paso 5: Crear Multi-Output Device #2 (Para TTS)

1. Click en **+** otra vez
2. Selecciona **"Create Multi-Output Device"**
3. Renómbralo: **"TTS Output (BlackHole 16ch)"**
4. **Marca:**
   - ✅ BlackHole 16ch ← DIFERENTE al anterior
   - ✅ Auriculares externos (o Altavoces del MacBook Pro)
5. **Drift Correction:** Marca solo "Auriculares externos"
6. Cierra Audio MIDI Setup

### Paso 6: Configurar Salida del Sistema

1. Abre **Preferencias del Sistema** → **Sonido** → **Salida**
2. Selecciona: **"Video Input (BlackHole 2ch)"**
   
   (Esto hace que todo el sistema use este dispositivo por defecto)

### Paso 7: Configurar Navegador (Solo para Chrome/Brave)

Si usas Chrome/Brave:
1. Instala extensión "Audio Output Switcher"
2. Configúrala para usar "Video Input (BlackHole 2ch)"

Safari usa automáticamente el dispositivo del sistema ✅

---

## 🧪 Test de Verificación

### Test 1: Verificar Dispositivos

```bash
# Ver todos los dispositivos disponibles
python3 -c "import sounddevice as sd; print(sd.query_devices())"
```

Debes ver:
- BlackHole 2ch
- BlackHole 16ch
- Video Input (BlackHole 2ch)
- TTS Output (BlackHole 16ch)
- Auriculares externos

### Test 2: Test de Audio Simple

```bash
# El traductor usará automáticamente el nuevo dispositivo
python3 src/main_v3_pro.py
```

---

## ✅ Resultado Final

Cuando esté todo configurado:

1. **Video** → Va a "Video Input (BlackHole 2ch)"
   - BlackHole 2ch → STT captura ✅
   - Auriculares → Escuchas video ✅

2. **TTS** → Va a "TTS Output (BlackHole 16ch)"
   - BlackHole 16ch → STT NO captura ✅ (diferente dispositivo)
   - Auriculares → Escuchas traducción ✅

3. **Escuchas en tus auriculares:**
   - Audio original del video (inglés)
   - Audio traducido (español)
   - SIN FEEDBACK porque STT solo escucha BlackHole 2ch

---

## 🚨 Troubleshooting

### No veo BlackHole 16ch en Audio MIDI Setup
→ Reinicia el Mac
→ Verifica instalación: `brew list --cask | grep blackhole`

### El video no tiene audio
→ Verifica que el navegador use "Video Input (BlackHole 2ch)"
→ En Safari, debe ser el dispositivo predeterminado del sistema

### Sigo con feedback
→ Verifica que el TTS esté configurado para usar "TTS Output (BlackHole 16ch)"
→ Revisa los logs del traductor

### Audio desincronizado
→ En Audio MIDI Setup, configura "Drift Correction" solo en Auriculares

---

## 📞 Siguiente Paso

Una vez completados estos pasos, ejecuta:
```bash
python3 src/main_v3_pro.py
```

El código ya está modificado para usar "TTS Output (BlackHole 16ch)" automáticamente.

¡Ya no habrá feedback loop! 🎉
