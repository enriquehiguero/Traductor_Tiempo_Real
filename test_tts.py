#!/usr/bin/env python3
"""
Test simple del TTS para verificar que funciona correctamente
"""
import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from tts_handler import TTSHandler

print("="*60)
print("Test de TTS - Traductor en Tiempo Real")
print("="*60)

# Crear handler con voz española
print("\n1. Creando TTSHandler con voz Mónica (español)...")
tts = TTSHandler(
    voice="Mónica",
    rate=180,
    volume=0.9,
    use_macos_say=True
)

print("✅ TTSHandler creado")

# Probar voz
texto_prueba = "Hola, esto es una prueba del sistema de texto a voz en español"
print(f"\n2. Probando con texto: '{texto_prueba}'")
print("   (Deberías escuchar este texto ahora...)")

tts.speak_text(texto_prueba)

print("\n3. Esperando a que termine de hablar...")
time.sleep(5)

print("\n✅ Test completado")
print("\n" + "="*60)
print("Si escuchaste el audio en español, el TTS funciona correctamente.")
print("Si NO escuchaste nada:")
print("  - Verifica que el volumen del sistema no esté en mute")
print("  - Verifica que 'Dispositivo de salida múltiple' incluya tus auriculares/altavoces")
print("  - Abre Audio MIDI Setup y verifica la configuración")
print("="*60)
