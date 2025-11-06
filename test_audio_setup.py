#!/usr/bin/env python3
"""
Test de verificación para Dual BlackHole
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*70)
print("🎵 Test de Dual BlackHole - Verificación Completa")
print("="*70)

# Test 1: Verificar sounddevice
print("\n1️⃣ Verificando sounddevice...")
try:
    import sounddevice as sd
    import soundfile as sf
    print("✅ sounddevice y soundfile disponibles")
except ImportError as e:
    print(f"❌ Error: {e}")
    print("Instala con: pip install sounddevice soundfile")
    sys.exit(1)

# Test 2: Listar dispositivos
print("\n2️⃣ Dispositivos de audio disponibles:")
print("-" * 70)
try:
    devices = sd.query_devices()
    blackhole_2ch_found = False
    blackhole_16ch_found = False
    tts_output_found = False

    for idx, device in enumerate(devices):
        # Solo mostrar dispositivos de salida
        if device['max_output_channels'] > 0:
            name = device['name']
            channels = device['max_output_channels']

            # Marcar dispositivos importantes
            marker = ""
            if "blackhole 2ch" in name.lower():
                marker = " ← Para VIDEO (STT captura de aquí)"
                blackhole_2ch_found = True
            elif "blackhole 16ch" in name.lower():
                marker = " ← Para TTS (sin feedback!)"
                blackhole_16ch_found = True
            elif "tts output" in name.lower():
                marker = " ← Multi-Output para TTS"
                tts_output_found = True
            elif "video input" in name.lower():
                marker = " ← Multi-Output para VIDEO"

            print(f"  [{idx}] {name} ({channels}ch){marker}")

    print("-" * 70)

    # Verificación
    print("\n3️⃣ Verificación de configuración:")
    if blackhole_2ch_found:
        print("  ✅ BlackHole 2ch encontrado")
    else:
        print("  ❌ BlackHole 2ch NO encontrado")

    if blackhole_16ch_found:
        print("  ✅ BlackHole 16ch encontrado")
    else:
        print("  ❌ BlackHole 16ch NO encontrado")
        print("     → Ejecuta: sudo killall coreaudiod")
        print("     → O reinicia el Mac")

    if tts_output_found:
        print("  ✅ 'TTS Output' Multi-Output encontrado")
    else:
        print("  ⚠️  'TTS Output' Multi-Output NO encontrado")
        print("     → Créalo en Audio MIDI Setup (ver SETUP_DUAL_BLACKHOLE.md)")

except Exception as e:
    print(f"❌ Error listando dispositivos: {e}")
    sys.exit(1)

# Test 3: Probar TTS con routing
if blackhole_16ch_found or tts_output_found:
    print("\n4️⃣ Probando TTS con routing específico...")
    try:
        from tts_handler import TTSHandler

        tts = TTSHandler(
            voice="Paulina",
            rate=200,
            volume=0.9,
            use_macos_say=True,
            output_device="TTS Output"
        )

        texto = "Prueba de audio en Black Hole dieciséis canales"
        print(f"  Texto: '{texto}'")
        print("  ▶️  Reproduciendo...")
        print("     (Deberías escucharlo en tus auriculares)")
        print("     (Y NO debería crear feedback)")

        tts.speak_text(texto)

        import time
        time.sleep(5)

        print("  ✅ Test de TTS completado")

    except Exception as e:
        print(f"  ❌ Error en test de TTS: {e}")
        import traceback
        traceback.print_exc()
else:
    print("\n4️⃣ ⚠️  Saltando test de TTS (BlackHole 16ch no disponible)")

print("\n" + "="*70)
print("📊 Resumen:")
if blackhole_16ch_found and (tts_output_found or blackhole_16ch_found):
    print("  ✅ Sistema configurado correctamente para Dual BlackHole")
    print("  ✅ Puedes usar el traductor sin feedback loop")
    print("\n  Siguiente paso:")
    print("    python3 src/main_v3_pro.py")
elif not blackhole_16ch_found:
    print("  ⚠️  BlackHole 16ch no está activo")
    print("\n  Solución:")
    print("    sudo killall coreaudiod")
    print("    # O reinicia el Mac")
else:
    print("  ⚠️  Falta crear 'TTS Output' Multi-Output")
    print("\n  Solución:")
    print("    Lee: SETUP_DUAL_BLACKHOLE.md")
    print("    Crea el Multi-Output en Audio MIDI Setup")

print("="*70)
