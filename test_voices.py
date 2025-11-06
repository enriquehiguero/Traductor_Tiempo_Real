#!/usr/bin/env python3
"""
Test comparativo de voces en español para elegir la mejor
"""
import subprocess
import time

texto_prueba = "Hola, esta es una prueba del sistema de traducción en tiempo real"

voces = [
    ("Paulina", "México - Voz femenina natural (RECOMENDADA)"),
    ("Mónica", "España - Voz femenina formal"),
    ("Eddy", "España/México - Voz masculina joven"),
    ("Grandpa", "España - Voz masculina mayor")
]

print("="*70)
print("🎤 Test Comparativo de Voces en Español")
print("="*70)
print("\nTexto de prueba:")
print(f"  '{texto_prueba}'")
print("\n" + "="*70)

for i, (voz, descripcion) in enumerate(voces, 1):
    print(f"\n{i}. Voz: {voz}")
    print(f"   {descripcion}")
    print(f"   ▶️  Reproduciendo...")
    
    subprocess.run([
        "say", "-v", voz, "-r", "200", texto_prueba
    ], capture_output=True)
    
    time.sleep(1)
    print(f"   ✅ Completado")

print("\n" + "="*70)
print("¿Cuál voz te gustó más?")
print("\n💡 Recomendación: Paulina (natural) o Eddy (masculina)")
print("\nPara cambiar la voz:")
print("  1. Edita config.json")
print("  2. Cambia 'voice' en la sección 'tts'")
print("  3. Reinicia el traductor")
print("="*70)
