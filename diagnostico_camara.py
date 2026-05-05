#!/usr/bin/env python3
"""
Diagnóstico completo de cámara — Ejecuta esto para identificar el problema.
"""

import cv2
import sys
import time
import sqlite3
from config import DB_PATH

print("=" * 60)
print("DIAGNÓSTICO DE CÁMARA")
print("=" * 60)

# 1. Información del sistema
print(f"\n✓ Sistema: {sys.platform}")
print(f"✓ Python: {sys.version.split()[0]}")
print(f"✓ OpenCV: {cv2.__version__}")

# 2. Checar privacidad en Windows
if sys.platform == "win32":
    print("\n" + "─" * 60)
    print("VERIFICAR PERMISOS EN WINDOWS:")
    print("─" * 60)
    print("1. Abre: Configuración > Privacidad > Cámara")
    print("2. Verifica que 'Permitir acceso a la cámara' esté ACTIVO")
    print("3. Baja y verifica que esta app esté habilitada")
    print("4. Cierra Teams, Zoom, OBS u otras apps que usen cámara")
    
    # Intentar abrir cámara rápidamente para detectar bloqueo
    inicio = time.time()
    cap_test = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    tardo = time.time() - inicio
    
    if not cap_test.isOpened():
        cap_test.release()
        if tardo < 1.0:
            print("\n❌ CÁMARA BLOQUEADA POR PRIVACIDAD DE WINDOWS")
            print("   → La llamada falló muy rápido (< 1s) = bloqueo de privacidad")
            print("   → Abre Configuración > Privacidad > Cámara y actívala")
        else:
            print("\n❌ CÁMARA NO DISPONIBLE")
            print(f"   → Intento tardó {tardo:.1f}s (posible timeout de hardware)")
    else:
        cap_test.release()
        print("\n✅ Windows NO está bloqueando la cámara")

# 3. Probar backends en Windows
if sys.platform == "win32":
    print("\n" + "─" * 60)
    print("PROBANDO BACKENDS:")
    print("─" * 60)
    
    backends = [
        (0, cv2.CAP_DSHOW, "DSHOW"),
        (0, cv2.CAP_MSMF, "MSMF"),
        (0, cv2.CAP_ANY, "ANY"),
        (1, cv2.CAP_DSHOW, "DSHOW (idx=1)"),
        (1, cv2.CAP_MSMF, "MSMF (idx=1)"),
        (1, cv2.CAP_ANY, "ANY (idx=1)"),
    ]
    
    encontrada = False
    for idx, backend, nombre in backends:
        try:
            cap = cv2.VideoCapture(idx, backend)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None and frame.size > 0:
                    print(f"  ✅ {nombre} → FUNCIONA")
                    encontrada = True
                    cap.release()
                    break
                else:
                    print(f"  ❌ {nombre} → Abierta pero no lee frames")
            else:
                print(f"  ❌ {nombre} → No se puede abrir")
            cap.release()
        except Exception as e:
            print(f"  ❌ {nombre} → Error: {e}")
    
    if not encontrada:
        print("\n❌ NINGÚN BACKEND FUNCIONA")
        print("   Posibles soluciones:")
        print("   • Cierra otras apps que usen la cámara (Teams, Zoom, OBS)")
        print("   • Actualiza drivers: Administrador de dispositivos > Cámaras")
        print("   • Reinicia el equipo")
        print("   • Intenta con una cámara USB diferente")

# 4. Comprobar configuración guardada en BD
print("\n" + "─" * 60)
print("CONFIGURACIÓN GUARDADA EN BASE DE DATOS:")
print("─" * 60)

try:
    with sqlite3.connect(DB_PATH) as con:
        row = con.execute(
            "SELECT valor FROM config WHERE clave='camara_config'").fetchone()
    
    if row:
        print(f"  Guardado: {row[0]}")
        partes = row[0].split(",")
        if len(partes) == 2:
            idx, backend = int(partes[0]), int(partes[1])
            print(f"  → Intentando idx={idx}, backend={backend}")
            
            cap = cv2.VideoCapture(idx, backend)
            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                if ret and frame is not None and frame.size > 0:
                    print(f"  ✅ Configuración guardada FUNCIONA")
                else:
                    print(f"  ⚠️  Configuración abierta pero no lee frames")
                    print(f"     → Limpiando configuración...")
                    con.execute("DELETE FROM config WHERE clave='camara_config'")
            else:
                print(f"  ❌ Configuración guardada NO FUNCIONA")
                print(f"     → Limpiando configuración...")
                con.execute("DELETE FROM config WHERE clave='camara_config'")
    else:
        print("  (Sin configuración previa guardada)")
except Exception as e:
    print(f"  Error accediendo BD: {e}")

# 5. Resumen y siguientes pasos
print("\n" + "=" * 60)
print("RESUMEN Y SIGUIENTES PASOS:")
print("=" * 60)
print("\n✓ Si TODO es ✅:")
print("  → El problema es probablemente temporal")
print("  → Reinicia la aplicación")
print("")
print("✗ Si hay ❌ en privacidad Windows:")
print("  → Abre: Configuración > Privacidad > Cámara")
print("  → Activa 'Permitir acceso a la cámara'")
print("  → Baja y activa esta aplicación en la lista")
print("")
print("✗ Si NO FUNCIONA ningún backend:")
print("  1. Cierra Teams, Zoom, OBS")
print("  2. Actualiza drivers de cámara")
print("  3. Reinicia el equipo")
print("  4. Prueba con otra cámara USB")
print("\n" + "=" * 60)
