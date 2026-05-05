"""
vista.py — Captura facial, embeddings y reconocimiento con DeepFace.
Estrategia de inicio optimizada:
- Modelo DeepFace: se pre-carga en hilo background AL INICIAR LA APP
- Cámara: se abre SOLO cuando el usuario presiona el botón
- Detección automática de cámara: prueba índices y backends hasta encontrar uno que funcione
- La configuración de cámara se guarda en DB para no buscar cada vez
- CAP_DSHOW / CAP_MSMF / CAP_ANY se prueban según el SO
- La apertura ocurre en hilo separado para no bloquear la UI
- La ventana OpenCV se trae al frente automáticamente al abrirse
- Diálogo guiado de permisos en Windows con botón directo a Configuración
"""

import pickle
import queue
import subprocess
import threading
import datetime
import sys
import time
import numpy as np
import cv2
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from deepface import DeepFace

from config import DB_PATH, MODEL_NAME, THRESHOLD, ANALIZAR_CADA, CONFIRMACIONES_NEEDED


# ─────────────────────────────────────────────
#  UTILIDAD: TRAER VENTANA AL FRENTE (Windows)
# ─────────────────────────────────────────────
def _traer_al_frente(nombre_ventana: str):
    if sys.platform != "win32":
        return
    try:
        import ctypes
        hwnd = ctypes.windll.user32.FindWindowW(None, nombre_ventana)
        if hwnd:
            SW_RESTORE = 9
            ctypes.windll.user32.ShowWindow(hwnd, SW_RESTORE)
            ctypes.windll.user32.SetForegroundWindow(hwnd)
    except Exception:
        # Silenciar errores de ventanas
        pass


# ─────────────────────────────────────────────
#  MODELO — SE PRE-CARGA EN BACKGROUND AL INICIAR
# ─────────────────────────────────────────────
_MODELO_LISTO  = False
_modelo_lock   = threading.Lock()
_modelo_evento = threading.Event()
_CASCADE = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml")


def _cargar_modelo_background():
    """Carga el modelo en hilo separado para no bloquear la UI."""
    global _MODELO_LISTO
    dummy = np.zeros((160, 160, 3), dtype=np.uint8)
    try:
        # Forzar carga perezosa del modelo
        import os
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Silenciar TensorFlow
        
        DeepFace.represent(
            dummy,
            model_name        = MODEL_NAME,
            detector_backend  = "skip",
            enforce_detection = False,
            align             = False,
        )
        _MODELO_LISTO = True
        print("✅ Modelo facial listo (background).")
    except Exception as e:
        print(f"⚠  Error cargando modelo: {e}")
    finally:
        _modelo_evento.set()
        # Forzar liberación de recursos
        import gc
        gc.collect()


def calentar_modelo():
    if _MODELO_LISTO or _modelo_evento.is_set():
        return
    hilo = threading.Thread(target=_cargar_modelo_background, daemon=True)
    hilo.start()
    print("⏳ Cargando modelo facial en background…")





# ─────────────────────────────────────────────
#  PERMISOS DE CÁMARA EN WINDOWS
#  Detecta bloqueo y guía al usuario paso a paso
# ─────────────────────────────────────────────

def _abrir_config_camara_windows():
    """Abre directamente la página de privacidad de cámara en Windows."""
    try:
        subprocess.Popen(["start", "ms-settings:privacy-webcam"], shell=True)
    except Exception as e:
        print(f"⚠  No se pudo abrir configuración: {e}")


def _camara_bloqueada_por_windows() -> bool:
    """
    Detecta si Windows está bloqueando el acceso a la cámara
    por configuración de privacidad.
    Devuelve True si probablemente está bloqueada.
    """
    if sys.platform != "win32":
        return False
    try:
        inicio = time.time()
        cap    = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        tardo  = time.time() - inicio
        if not cap.isOpened():
            cap.release()
            # Fallo muy rápido → bloqueo de privacidad (no timeout de hardware)
            return tardo < 1.0
        # Intentar leer un frame
        ret, frame = cap.read()
        cap.release()
        if not ret or frame is None:
            return True
        return False
    except Exception:
        return False


def _mostrar_dialogo_permiso_camara(parent=None) -> bool:
    """
    Muestra un diálogo guiado cuando Windows bloquea la cámara.
    Incluye botón directo a Configuración de privacidad.
    Devuelve True si el usuario hizo clic en 'Reintentar'.
    """
    AZUL_OSC  = "#0F1C2E"
    AZUL_MED  = "#1A2B4A"
    AZUL_BTN  = "#1B4FD8"
    AZUL_HOV  = "#2563EB"
    GRIS_BTN  = "#1E2E4A"
    TEXTO     = "#B8C8E0"
    BLANCO    = "#FFFFFF"

    resultado = {"reintentar": False}

    win = tk.Toplevel(parent)
    win.title("Permiso de Cámara Requerido")
    win.geometry("500x390")
    win.resizable(False, False)
    win.configure(bg=AZUL_OSC)
    win.grab_set()
    try:
        win.lift()
        win.focus_force()
    except Exception:
        pass

    # ── Header ──────────────────────────────
    hdr = tk.Frame(win, bg=AZUL_MED)
    hdr.pack(fill="x")
    tk.Frame(hdr, bg=AZUL_BTN, width=4).pack(side="left", fill="y")
    tk.Label(hdr,
             text="  📷  Acceso a la cámara bloqueado",
             font=("Segoe UI", 12, "bold"),
             fg=BLANCO, bg=AZUL_MED, pady=14).pack(side="left")

    # ── Cuerpo ──────────────────────────────
    body = tk.Frame(win, bg=AZUL_OSC)
    body.pack(fill="both", expand=True, padx=24, pady=16)

    tk.Label(body,
             text="Windows está impidiendo que esta aplicación\n"
                  "acceda a la cámara. Sigue estos pasos para activarla:",
             font=("Segoe UI", 10),
             fg=TEXTO, bg=AZUL_OSC, justify="left").pack(anchor="w", pady=(0, 14))

    # ── Pasos ────────────────────────────────
    pasos = [
        (AZUL_BTN,  "1", "Haz clic en  'Abrir Configuración'  abajo."),
        ("#0D6E3F",  "2", "Activa  'Permitir que las aplicaciones\n"
                          "         accedan a la cámara'."),
        ("#7C3E05",  "3", "Baja en esa misma página y activa también\n"
                          "esta aplicación de forma individual."),
        ("#5B2D8E",  "4", "Cierra Configuración y haz clic en  'Reintentar'."),
    ]
    for color, num, texto in pasos:
        fr = tk.Frame(body, bg=AZUL_OSC)
        fr.pack(fill="x", pady=4)
        badge = tk.Frame(fr, bg=color, width=24, height=24)
        badge.pack(side="left", padx=(0, 12))
        badge.pack_propagate(False)
        tk.Label(badge, text=num,
                 font=("Segoe UI", 9, "bold"),
                 fg=BLANCO, bg=color).place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(fr, text=texto,
                 font=("Segoe UI", 9),
                 fg=TEXTO, bg=AZUL_OSC, justify="left").pack(side="left", anchor="nw")

    # ── Nota ────────────────────────────────
    nota = tk.Frame(win, bg="#1A2B4A", padx=16, pady=8)
    nota.pack(fill="x", padx=24, pady=(0, 10))
    tk.Label(nota,
             text="ℹ️  Si ya activaste el permiso, haz clic en 'Reintentar'.\n"
                  "    Si el problema persiste, reinicia el equipo.",
             font=("Segoe UI", 8),
             fg="#7A90B8", bg="#1A2B4A", justify="left").pack(anchor="w")

    # ── Botones ─────────────────────────────
    btn_fr = tk.Frame(win, bg=AZUL_OSC)
    btn_fr.pack(fill="x", padx=24, pady=(0, 20))

    def _abrir():
        _abrir_config_camara_windows()

    def _reintentar():
        resultado["reintentar"] = True
        win.destroy()

    def _cancelar():
        resultado["reintentar"] = False
        win.destroy()

    # Botón principal: Abrir configuración
    btn_config = tk.Button(
        btn_fr,
        text="⚙️  Abrir Configuración de Windows",
        command=_abrir,
        font=("Segoe UI", 10, "bold"),
        bg=AZUL_BTN, fg=BLANCO,
        activebackground=AZUL_HOV, activeforeground=BLANCO,
        relief="flat", bd=0, padx=16, pady=10, cursor="hand2")
    btn_config.pack(side="left", fill="x", expand=True, padx=(0, 8))
    btn_config.bind("<Enter>", lambda e: btn_config.config(bg=AZUL_HOV))
    btn_config.bind("<Leave>", lambda e: btn_config.config(bg=AZUL_BTN))

    # Botón secundario: Reintentar
    btn_ret = tk.Button(
        btn_fr,
        text="🔄  Reintentar",
        command=_reintentar,
        font=("Segoe UI", 10),
        bg=GRIS_BTN, fg=TEXTO,
        activebackground="#2A3E5A", activeforeground=BLANCO,
        relief="flat", bd=0, padx=16, pady=10, cursor="hand2")
    btn_ret.pack(side="left", padx=(0, 8))

    # Botón cancelar
    tk.Button(
        btn_fr,
        text="✖  Cancelar",
        command=_cancelar,
        font=("Segoe UI", 9),
        bg=AZUL_OSC, fg="#556680",
        activebackground=AZUL_OSC, activeforeground=TEXTO,
        relief="flat", bd=0, padx=10, pady=10, cursor="hand2"
    ).pack(side="left")

    win.wait_window()
    return resultado["reintentar"]


# ─────────────────────────────────────────────
#  DETECCIÓN AUTOMÁTICA DE CÁMARA
#  Funciona en cualquier equipo probando
#  índices (0-4) y backends disponibles
# ─────────────────────────────────────────────

_cam_result     = {"cap": None}
_cam_config_key = "camara_config"


def _get_backends_a_probar():
    if sys.platform == "win32":
        combos = []
        for idx in range(4):
            combos.append((idx, cv2.CAP_DSHOW))
            combos.append((idx, cv2.CAP_MSMF))
            combos.append((idx, cv2.CAP_ANY))
        return combos
    else:
        combos = []
        for idx in range(4): 
            if sys.platform == "linux":
                combos.append((idx, cv2.CAP_V4L2))
                combos.append((idx, cv2.CAP_ANY))
        return combos

def _probar_camara(idx: int, backend: int, intentos_frame: int = 3) -> bool:
    """Prueba si una cámara funciona. Timeout adecuado para evitar falsos negativos."""
    resultado = [False]

    def _intentar():
        try:
            cap = cv2.VideoCapture(idx, backend)
            if not cap.isOpened():
                cap.release()
                return
            frames_ok = 0
            for _ in range(intentos_frame):
                ret, frame = cap.read()
                if (ret and frame is not None
                        and frame.size > 0
                        and np.mean(frame) > 5):
                    frames_ok += 1
                    if frames_ok >= 2:
                        resultado[0] = True
                        break
            cap.release()
        except Exception:
            pass

    hilo = threading.Thread(target=_intentar, daemon=True)
    hilo.start()
    hilo.join(timeout=3.0)  # Timeout suficiente para hardware lento
    return resultado[0]


def _guardar_config_camara(idx: int, backend: int):
    try:
        valor = f"{idx},{backend}"
        with sqlite3.connect(DB_PATH) as con:
            con.execute(
                "INSERT OR REPLACE INTO config (clave, valor) VALUES (?,?)",
                (_cam_config_key, valor))
    except Exception:
        pass


def _cargar_config_camara():
    try:
        with sqlite3.connect(DB_PATH) as con:
            row = con.execute(
                "SELECT valor FROM config WHERE clave=?",
                (_cam_config_key,)).fetchone()
        if row:
            partes = row[0].split(",")
            if len(partes) == 2:
                return int(partes[0]), int(partes[1])
    except Exception:
        pass
    return None


def _limpiar_config_camara():
    """Borra config para forzar re-detección."""
    try:
        with sqlite3.connect(DB_PATH) as con:
            con.execute("DELETE FROM config WHERE clave=?", (_cam_config_key,))
        print("🧹 Config cámara limpiada (re-detección forzada).")
    except Exception:
        pass


def _detectar_camara():
    """Detección completa de cámara (legacy - ahora optimizado en _abrir_camara)."""
    print("🔍 Detectando cámara...")
#
    # 1. Probar config guardada
    config_guardada = _cargar_config_camara()
    if config_guardada:
        idx, backend = config_guardada
        print(f"⏳ Probando config guardada: idx={idx}, backend={backend}...")
        if _probar_camara(idx, backend):
            print(f"✅ Config guardada funciona: {idx},{backend}")
            return idx, backend
        else:
            print("⚠  Config guardada ya no funciona, re-detectando...")
            _limpiar_config_camara()

    # 2. Detección completa
    _nombres_backend = {
        cv2.CAP_DSHOW: "DSHOW",
        cv2.CAP_MSMF:  "MSMF",
        cv2.CAP_ANY:   "ANY",
    }
    if sys.platform == "linux":
        _nombres_backend[cv2.CAP_V4L2] = "V4L2"

    for idx, backend in _get_backends_a_probar():
        nombre_b = _nombres_backend.get(backend, str(backend))
        print(f"   Probando idx={idx}, backend={nombre_b}...")
        if _probar_camara(idx, backend):
            print(f"✅ Cámara encontrada: idx={idx}, backend={nombre_b}")
            _guardar_config_camara(idx, backend)
            return idx, backend

    print("❌ No se encontró cámara funcional.")
    return None, None


def _abrir_camara(parent_tk=None):
    """Abre la cámara optimizado para rapidez en Windows. Thread-safe."""
    
    def _puede_leer_frames(cap, intentos=3):
        """Intenta leer 3 frames para verificar que la cámara funciona."""
        for _ in range(intentos):
            try:
                ret, frame = cap.read()
                if ret and frame is not None and frame.size > 0:
                    return True
            except Exception:
                pass
            time.sleep(0.1)  # Pequeño delay entre intentos
        return False
    
    # ── 1. INTENTAR CONFIGURACIÓN GUARDADA PRIMERO (rápido) ──
    config_guardada = _cargar_config_camara()
    if config_guardada:
        idx, backend = config_guardada
        # Si backend es 0 (ANY), usar DSHOW en Windows para mayor rapidez
        if backend == 0 and sys.platform == "win32":
            backend = cv2.CAP_DSHOW
        try:
            cap = cv2.VideoCapture(idx, backend)
            if cap.isOpened():
                # Verificar que realmente funciona (tolera 1-2 frames fallidos)
                if _puede_leer_frames(cap, intentos=3):
                    _configurar_camara_async(cap)
                    _cam_result["cap"] = cap
                    return cap
            cap.release()
        except Exception:
            pass
    
    # ── 2. INTENTAR ÍNDICES COMUNES CON BACKENDS RÁPIDOS ──
    if sys.platform == "win32":
        # En Windows, DSHOW es más rápido que ANY/MSMF
        backends_a_probar = [
            (0, cv2.CAP_DSHOW),
            (1, cv2.CAP_DSHOW),
            (0, cv2.CAP_MSMF),
            (1, cv2.CAP_MSMF),
        ]
    else:
        backends_a_probar = [
            (0, cv2.CAP_V4L2),
            (1, cv2.CAP_V4L2),
            (0, cv2.CAP_ANY),
            (1, cv2.CAP_ANY),
        ]
    
    for idx, backend in backends_a_probar:
        try:
            cap = cv2.VideoCapture(idx, backend)
            if cap.isOpened():
                # Verificar que funciona (tolera 1-2 frames fallidos)
                if _puede_leer_frames(cap, intentos=3):
                    _configurar_camara_async(cap)
                    _guardar_config_camara(idx, backend)
                    _cam_result["cap"] = cap
                    return cap
            cap.release()
        except Exception:
            continue
    
    return None


def _configurar_camara_async(cap):
    """
    Configura la cámara de forma segura en el thread principal.
    NO USAR EN THREAD SEPARADO - OpenCV no es thread-safe para cap.set()
    """
    # En realidad, vamos a NO configurar nada por ahora.
    # OpenCV funciona mejor con los defaults que cuando intentamos forzar propiedades.
    # Cada hardware tiene sus limitaciones, así que es mejor dejar que OpenCV
    # maneje la resolución y FPS automáticamente.
    print("[DEBUG]   (No se configura resolución - OpenCV usa defaults)")
    pass


def cerrar_camara(cap=None):
    """
    Cierra la cámara.
    - Con argumento:  cerrar_camara(cap)  → cierra ese objeto VideoCapture.
    - Sin argumento:  cerrar_camara()     → cierra cualquier cámara activa en background.
    """
    if cap is not None:
        try:
            cap.release()
            print("📷 Cámara cerrada.")
        except Exception:
            pass
    else:
        c = _cam_result.get("cap")
        if c is not None:
            try:
                c.release()
                _cam_result["cap"] = None
                print("📷 Cámara global cerrada.")
            except Exception as e:
                print(f"⚠  Error cerrando cámara global: {e}")


# ─────────────────────────────────────────────
#  DIAGNÓSTICO DE CÁMARA (útil para soporte)
# ─────────────────────────────────────────────

def diagnosticar_camaras() -> str:
    lineas = [
        f"Sistema:  {sys.platform}",
        f"OpenCV:   {cv2.__version__}",
        f"Python:   {sys.version.split()[0]}",
        "",
        "── Chequeo de privacidad Windows ──",
    ]

    if sys.platform == "win32":
        bloqueada = _camara_bloqueada_por_windows()
        lineas.append(
            "  ⚠️  Posiblemente BLOQUEADA por privacidad"
            if bloqueada else
            "  ✅  Sin bloqueo de privacidad detectado"
        )
    else:
        lineas.append("  (No aplica en este SO)")

    lineas += ["", "── Prueba de backends ──"]
    encontradas = 0

    _nombres_backend = {
        cv2.CAP_DSHOW: "DSHOW",
        cv2.CAP_MSMF:  "MSMF",
        cv2.CAP_ANY:   "ANY",
    }
    if sys.platform == "linux":
        _nombres_backend[cv2.CAP_V4L2] = "V4L2"

    for idx, backend in _get_backends_a_probar():
        nombre_b = _nombres_backend.get(backend, str(backend))
        funciona = _probar_camara(idx, backend)
        estado   = "✅ OK  " if funciona else "❌ FAIL"
        lineas.append(f"  Idx {idx} | {nombre_b:5s} → {estado}")
        if funciona:
            encontradas += 1
        lineas.append("")
    if encontradas == 0:
        lineas += [
            "⚠️  NO SE ENCONTRÓ NINGUNA CÁMARA FUNCIONAL.",
            "",
            "SOLUCIONES:",
            "  1. Windows 10/11: Configuración → Privacidad → Cámara",
            "     → Activar 'Permitir acceso a la cámara'",
            "  2. Cierra Teams / Zoom / OBS u otras apps que usen la cámara.",
            "  3. Conecta una cámara USB y espera que Windows la instale.",
            "  4. Actualiza los drivers de la cámara desde el Administrador de dispositivos.",
            "  5. Reinicia el equipo e intenta de nuevo.",
            "  6. Prueba en terminal:",
            "     python -c \"import cv2; print(cv2.VideoCapture(0).isOpened())\"",
        ]
    else:
        lineas.append(f"✅  {encontradas} configuración(es) funcional(es) encontrada(s).")

    return "\n".join(lineas)


# ─────────────────────────────────────────────
#  EMBEDDINGS — ALMACENAMIENTO Y LECTURA
# ─────────────────────────────────────────────

def _blob_to_embedding(blob):
    buf = bytes(blob)
    if len(buf) % 4 == 0:
        arr = np.frombuffer(buf, dtype="float32")
        if len(arr) >= 128:
            return arr
    try:
        return np.array(pickle.loads(buf), dtype="float32")
    except Exception:
        return None


def get_all_embeddings():
    with sqlite3.connect(DB_PATH) as con:
        rows = con.execute(
            "SELECT id, nombre || ' ' || apellido, embedding FROM personas WHERE activo=1"
        ).fetchall()
    result = []
    for pid, nombre, blob in rows:
        emb = _blob_to_embedding(blob)
        if emb is not None:
            result.append((pid, nombre, emb))
    return result


# ─────────────────────────────────────────────
#  ÍNDICE FAISS
# ─────────────────────────────────────────────
_faiss_index   = None
_faiss_ids     = []
_faiss_nombres = []


def _faiss_disponible():
    try:
        import faiss as _f
        return True
    except ImportError:
        return False


def rebuild_faiss_index():
    global _faiss_index, _faiss_ids, _faiss_nombres
    if not _faiss_disponible():
        print("⚠  FAISS no instalado — usando comparación secuencial.")
        return False
    import faiss
    datos = get_all_embeddings()
    if not datos:
        _faiss_index   = None
        _faiss_ids     = []
        _faiss_nombres = []
        return True
    ids     = [pid for pid, _, _   in datos]
    nombres = [nom for _,   nom, _ in datos]
    matrix  = np.stack([emb for _, _, emb in datos]).astype("float32")
    faiss.normalize_L2(matrix)
    dim = matrix.shape[1]
    idx = faiss.IndexFlatIP(dim)
    idx.add(matrix)
    _faiss_index   = idx
    _faiss_ids     = ids
    _faiss_nombres = nombres
    print(f"✅ Índice FAISS listo — {len(ids)} persona(s) indexadas.")
    return True


def _buscar_faiss(emb):
    import faiss
    q = emb.astype("float32").reshape(1, -1).copy()
    faiss.normalize_L2(q)
    similitudes, indices = _faiss_index.search(q, 1)
    sim  = float(similitudes[0][0])
    dist = 1.0 - sim
    pos  = int(indices[0][0])
    if pos < 0 or pos >= len(_faiss_ids):
        return None, "Desconocido", 1.0
    return _faiss_ids[pos], _faiss_nombres[pos], dist


# ─────────────────────────────────────────────
#  DETECCIÓN Y EMBEDDING
# ─────────────────────────────────────────────

def _detect_faces(frame):
    gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = _CASCADE.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))
    return list(faces) if len(faces) > 0 else []


def _get_embedding(face_crop):
    try:
        face_rgb     = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
        face_resized = cv2.resize(face_rgb, (160, 160))
        result = DeepFace.represent(
            img_path          = face_resized,
            model_name        = MODEL_NAME,
            detector_backend  = "skip",
            enforce_detection = False,
            align             = False,
        )
        return np.array(result[0]["embedding"], dtype="float32")
    except Exception:
        return None


def _cosine_distance(a, b):
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return 1.0 if denom == 0 else 1 - np.dot(a, b) / denom


# ─────────────────────────────────────────────
#  VERIFICACIÓN DE DUPLICADOS
# ─────────────────────────────────────────────

def persona_ya_existe(nuevo_emb, umbral=THRESHOLD):
    if _faiss_index is not None:
        import faiss
        q = nuevo_emb.astype("float32").reshape(1, -1).copy()
        faiss.normalize_L2(q)
        sims, idxs = _faiss_index.search(q, 1)
        dist = 1.0 - float(sims[0][0])
        pos  = int(idxs[0][0])
        if dist < umbral and 0 <= pos < len(_faiss_ids):
            pid = _faiss_ids[pos]
            with sqlite3.connect(DB_PATH) as con:
                row = con.execute(
                    "SELECT nombre || ' ' || apellido, activo FROM personas WHERE id=?",
                    (pid,)).fetchone()
            if row:
                return pid, row[0], row[1]
        return None, None, None

    with sqlite3.connect(DB_PATH) as con:
        rows = con.execute(
            "SELECT id, nombre || ' ' || apellido, embedding, activo FROM personas"
        ).fetchall()
    mejor_pid, mejor_nombre, mejor_dist, mejor_activo = None, None, 1.0, None
    for pid, nombre, blob, activo in rows:
        emb = _blob_to_embedding(blob)
        if emb is None:
            continue
        dist = _cosine_distance(nuevo_emb, emb)
        if dist < mejor_dist:
            mejor_dist   = dist
            mejor_pid    = pid
            mejor_nombre = nombre
            mejor_activo = activo
    if mejor_dist < umbral:
        return mejor_pid, mejor_nombre, mejor_activo
    return None, None, None


# ─────────────────────────────────────────────
#  PANTALLA DE ESPERA MIENTRAS CARGA EL MODELO
# ─────────────────────────────────────────────

def _mostrar_pantalla_espera(mensaje="Iniciando sistema…", timeout=15):
    """Pantalla de espera no-bloqueante para el ejecutable. Thread-safe."""
    inicio    = time.time()
    intervalo = 0.05
    ventana_creada = False

    try:
        while True:
            # Verificar si el modelo ya está listo
            if _modelo_evento.is_set():
                try:
                    cv2.destroyWindow("Iniciando…")
                except Exception:
                    pass
                return _MODELO_LISTO

            # Timeout
            if (time.time() - inicio) >= timeout:
                try:
                    cv2.destroyWindow("Iniciando…")
                except Exception:
                    pass
                return False

            # Crear ventana solo una vez
            if not ventana_creada:
                try:
                    cv2.namedWindow("Iniciando…", cv2.WINDOW_NORMAL)
                    cv2.moveWindow("Iniciando…", 100, 100)
                    ventana_creada = True
                except Exception:
                    # Si no se puede crear la ventana, simplemente esperar sin UI
                    pass

            W, H  = 480, 160
            frame = np.zeros((H, W, 3), dtype=np.uint8)
            frame[:] = (20, 25, 35)

            try:
                cv2.putText(frame, mensaje, (20, 45),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.65, (180, 210, 255), 1)

                progreso = min((time.time() - inicio) / timeout, 1.0)
                bw       = W - 40
                cv2.rectangle(frame, (20, 70),  (20 + bw, 86), (50, 60, 80), -1)
                cv2.rectangle(frame, (20, 70),  (20 + int(bw * progreso), 86), (27, 79, 156), -1)

                segundos_restantes = max(0, int(timeout - (time.time() - inicio)))
                cv2.putText(frame,
                            f"Máximo {segundos_restantes}s restantes…",
                            (20, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (120, 140, 170), 1)
                cv2.putText(frame, "ESC para cancelar", (20, 145),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.40, (80, 90, 110), 1)

                if ventana_creada:
                    cv2.imshow("Iniciando…", frame)
            except Exception:
                pass

            # Usar waitKey con timeout corto y verificar ESC
            try:
                key = cv2.waitKey(int(intervalo * 1000)) & 0xFF
                if key == 27:
                    try:
                        cv2.destroyWindow("Iniciando…")
                    except Exception:
                        pass
                    return False
            except Exception:
                # Si waitKey falla, continuar esperando sin UI
                time.sleep(intervalo)

    except Exception:
        try:
            cv2.destroyWindow("Iniciando…")
        except Exception:
            pass
        return False
    
    return False


# ─────────────────────────────────────────────
#  MENSAJE DE ERROR DE CÁMARA CON DIAGNÓSTICO
# ─────────────────────────────────────────────

def _mostrar_error_camara(parent_tk=None):
    """
    En Windows intenta mostrar el diálogo guiado.
    En otros SO muestra el diagnóstico completo.
    """
    if sys.platform == "win32" and parent_tk is not None:
        _mostrar_dialogo_permiso_camara(parent_tk)
        return

    diagnostico = diagnosticar_camaras()
    mensaje = (
        "No se pudo abrir la cámara en este equipo.\n\n"
        "── Diagnóstico ──\n"
        f"{diagnostico}\n\n"
        "── Soluciones ──\n"
        "1. Verifica que la cámara esté conectada.\n"
        "2. En Windows 10/11:\n"
        "   Configuración → Privacidad → Cámara\n"
        "   → Activar acceso a la cámara\n"
        "3. Instala o actualiza los drivers de la cámara.\n"
        "4. Cierra otras apps que usen la cámara\n"
        "   (Teams, Zoom, OBS, etc.)\n"
        "5. Reinicia el equipo e intenta de nuevo."
    )
    messagebox.showerror("Error de Cámara", mensaje)


# ─────────────────────────────────────────────
#  CÁMARA: CAPTURA MÚLTIPLE PARA REGISTRO
# ─────────────────────────────────────────────

def capturar_embedding_multi(num_capturas=5, parent_tk=None):
    """
    Abre la cámara automáticamente, captura N embeddings y la cierra al terminar.
    parent_tk: ventana tkinter padre para diálogos de permiso (puede ser None si se ejecuta en thread).
    """
    # 1. Esperar modelo
    if not _modelo_evento.is_set():
        ok = _mostrar_pantalla_espera("Cargando modelo facial…", timeout=15)
        if not ok:
            if parent_tk is not None:
                messagebox.showerror(
                    "Error", "El modelo no pudo cargarse. Reinicie la aplicación.")
            return None

    # 2. Abrir cámara con optimizaciones
    cap = _abrir_camara(parent_tk=parent_tk)
    if cap is None:
        if parent_tk is not None:
            _mostrar_error_camara(parent_tk)
        return None

    # 3. Mostrar ventana y traerla al frente (con protección para threads)
    _NOMBRE_VENTANA_REG = "Captura Facial - Registro"
    try:
        cv2.namedWindow(_NOMBRE_VENTANA_REG, cv2.WINDOW_GUI_NORMAL)
        _traer_al_frente(_NOMBRE_VENTANA_REG)
    except Exception:
        # Si hay error creando ventana, continuar sin traerla al frente
        pass

    embeddings = []
    frames_fallidos = 0  # Contador de frames fallidos
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                frames_fallidos += 1
                # Solo limpiar configuración después de 20+ frames fallidos
                # (tolera fallas puntuales de la cámara)
                if frames_fallidos > 20:
                    _limpiar_config_camara()
                    break
                continue
            
            # Si leemos un frame OK, resetear contador
            frames_fallidos = 0

            faces   = _detect_faces(frame)
            display = frame.copy()
            ok      = len(faces) == 1
            tomadas = len(embeddings)
            total_w = 300
            lleno   = int(total_w * tomadas / num_capturas) if num_capturas > 0 else 0
            cv2.rectangle(display, (10, 55), (10 + total_w, 72), (200, 210, 225), -1)
            cv2.rectangle(display, (10, 55), (10 + lleno,   72), (27, 79, 156),   -1)
            cv2.putText(display, f"Capturas: {tomadas}/{num_capturas}", (10, 51),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (27, 79, 156), 1)
            for (x, y, w, h) in faces:
                cv2.rectangle(display, (x, y), (x+w, y+h),
                              (27, 79, 156) if ok else (185, 28, 28), 2)
            if tomadas >= num_capturas:
                cv2.putText(display, "¡Listo! Procesando…", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (26, 125, 78), 2)
                cv2.imshow(_NOMBRE_VENTANA_REG, display)
                cv2.waitKey(600)
                break
            elif ok:
                msg = f"Cara detectada - ESPACIO para tomar ({tomadas+1}/{num_capturas})"
            else:
                msg = f"Caras detectadas: {len(faces)} (necesita exactamente 1)"
            cv2.putText(display, msg, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                        (27, 79, 156) if ok else (185, 28, 28), 2)
            cv2.putText(display, "ESC=cancelar", (10, display.shape[0]-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (120, 120, 120), 1)
            cv2.imshow(_NOMBRE_VENTANA_REG, display)
            key = cv2.waitKey(1) & 0xFF
            if key == 27:
                cv2.destroyAllWindows()
                return None
            if key == 32 and ok:
                x, y, w, h = faces[0]
                emb = _get_embedding(frame[y:y+h, x:x+w])
                if emb is not None:
                    embeddings.append(emb)
                    flash = display.copy()
                    cv2.rectangle(flash, (x, y), (x+w, y+h), (26, 125, 78), 3)
                    cv2.putText(flash, f"Captura {len(embeddings)}", (x, y-10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (26, 125, 78), 2)
                    cv2.imshow(_NOMBRE_VENTANA_REG, flash)
                    cv2.waitKey(350)
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        cerrar_camara(cap)
        cv2.destroyAllWindows()
        cv2.waitKey(1)

    if not embeddings:
        return None
    avg  = np.mean(np.stack(embeddings), axis=0).astype("float32")
    norm = np.linalg.norm(avg)
    if norm > 0:
        avg = avg / norm
    return avg


# ─────────────────────────────────────────────
#  ETIQUETAS DE ESTADO
# ─────────────────────────────────────────────
_LABELS_INVALIDOS = {
    "Buscando...", "Desconocido", "Ya registrado",
    "Solo una persona a la vez", "Posicionate frente a la camara",
    "Capacitacion no es hoy",
}


# ─────────────────────────────────────────────
#  CÁMARA: RECONOCIMIENTO CONTINUO
# ─────────────────────────────────────────────

def reconocer_cara(known_data, cap_id, parent_tk=None):
    """
    Abre la cámara al llamarse y la cierra al terminar.
    parent_tk: ventana tkinter padre para diálogos de permiso (puede ser None si se ejecuta en thread).
    """
    if not known_data and _faiss_index is None:
        if parent_tk is not None:
            messagebox.showwarning("Sin registros", "No hay personas registradas.")
        return []

    # 1. Esperar modelo (sin UI si se ejecuta en thread)
    if not _modelo_evento.is_set():
        # Esperar sin UI si no hay parent_tk (ejecutándose en thread daemon)
        if parent_tk is not None:
            ok = _mostrar_pantalla_espera("Cargando modelo facial…", timeout=15)
            if not ok:
                messagebox.showerror(
                    "Error", "El modelo no pudo cargarse. Reinicie la aplicación.")
                return []
        else:
            # Esperar silenciosamente en thread
            if not _modelo_evento.wait(timeout=15):
                return []

    # 2. Abrir cámara con optimizaciones
    cap = _abrir_camara(parent_tk=parent_tk)
    if cap is None:
        if parent_tk is not None:
            _mostrar_error_camara(parent_tk)
        return []

    # 3. Crear ventana (sin protección de thread)
    _NOMBRE_VENTANA = "Reconocimiento - Sistema de Asistencias"
    
    try:
        cv2.namedWindow(_NOMBRE_VENTANA, cv2.WINDOW_GUI_NORMAL)
        _traer_al_frente(_NOMBRE_VENTANA)
    except Exception:
        pass

    usar_faiss = _faiss_index is not None and len(_faiss_ids) > 0

    registrados_sesion  = set()
    cooldown            = {}
    nombres_registrados = []
    COOLDOWN_SEG = 10

    frame_count    = 0
    confirmaciones = 0
    ultimo_pid     = None
    ultimo_label   = "Buscando..."
    ultimo_color   = (46, 134, 193)

    hoy = datetime.date.today().isoformat()
    try:
        with sqlite3.connect(DB_PATH) as con:
            row_cap = con.execute(
                "SELECT fecha FROM capacitaciones WHERE id=?", (cap_id,)).fetchone()
        fecha_cap     = row_cap[0] if row_cap else None
        cap_es_de_hoy = (fecha_cap == hoy)
    except Exception:
        fecha_cap     = None
        cap_es_de_hoy = False

    _resultado_q = queue.Queue(maxsize=1)
    _frame_q     = queue.Queue(maxsize=1)
    _analizando  = threading.Event()

    def _worker():
        while True:
            try:
                crop = _frame_q.get(timeout=0.5)
                if crop is None:
                    break
                emb = _get_embedding(crop)
                try:
                    _resultado_q.get_nowait()
                except queue.Empty:
                    pass
                _resultado_q.put(emb)
            except queue.Empty:
                pass
            finally:
                _analizando.clear()

    hilo = threading.Thread(target=_worker, daemon=True)
    hilo.start()

    def _dibujar_panel(frm, nombres):
        h_f, w_f = frm.shape[:2]
        ph = max(36, 28 + 22 * len(nombres))
        py = h_f - ph
        cv2.rectangle(frm, (0, py), (w_f, h_f), (20, 30, 50), -1)
        cv2.putText(frm, f"Registrados: {len(nombres)}",
                    (10, py + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 200, 255), 1)
        for i, n in enumerate(nombres[-3:]):
            cv2.putText(frm, f"  ✓ {n}",
                        (10, py + 36 + i * 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (74, 222, 128), 1)

    def _mostrar_flash(frm, fx, fy, fw, fh, color, mensaje,
                    nombre_txt, cargo_txt, hora_txt, iniciales):
        VERDE_CLA    = (74, 222, 128)
        FLASH_MS     = 800
        INTERVALO_MS = 30
        pasos        = FLASH_MS // INTERVALO_MS
        h_f, w_f     = frm.shape[:2]
        PANEL_H      = 70
        BARRA_H      = 6
        for paso in range(pasos + 1):
            progreso = 1.0 - (paso / pasos)
            cf       = frm.copy()
            cv2.rectangle(cf, (fx, fy), (fx+fw, fy+fh), color, 3)
            cv2.rectangle(cf, (0, 0), (w_f, BARRA_H), (15, 60, 30), -1)
            cv2.rectangle(cf, (0, 0), (int(w_f * progreso), BARRA_H), color, -1)
            cv2.circle(cf, (18, BARRA_H + 16), 5, VERDE_CLA, -1)
            cv2.putText(cf, mensaje, (30, BARRA_H + 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1)
            cv2.putText(cf,
                        f"ESC para terminar  |  {len(registrados_sesion)} registrado(s)",
                        (w_f - 320, BARRA_H + 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 210, 255), 1)
            panel_y = h_f - PANEL_H
            cv2.rectangle(cf, (0, panel_y), (w_f, h_f), color, -1)
            av_cx = 34; av_cy = panel_y + PANEL_H // 2
            ov2 = cf.copy()
            cv2.circle(ov2, (av_cx, av_cy), 26, (255, 255, 255), -1)
            cv2.addWeighted(ov2, 0.18, cf, 0.82, 0, cf)
            cv2.circle(cf, (av_cx, av_cy), 26, (255, 255, 255), 1)
            off_ini = -14 if len(iniciales) > 1 else -7
            cv2.putText(cf, iniciales, (av_cx + off_ini, av_cy + 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
            cv2.putText(cf, nombre_txt, (70, panel_y + 28),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
            if cargo_txt:
                cv2.putText(cf, cargo_txt, (70, panel_y + 52),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.42, (200, 240, 200), 1)
            hora_size = cv2.getTextSize(hora_txt, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.putText(cf, hora_txt,
                        (w_f - hora_size[0] - 14, panel_y + 32),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(cf, "Hora",
                        (w_f - hora_size[0] - 14, panel_y + 52),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.38, (200, 240, 200), 1)
            cv2.imshow(_NOMBRE_VENTANA, cf)
            if cv2.waitKey(INTERVALO_MS) & 0xFF == 27:
                return True
        return False

    frames_sin_datos = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                frames_sin_datos += 1
                if frames_sin_datos > 30:
                    
                    messagebox.showwarning(
                        "Cámara desconectada",
                        "Se perdió la conexión con la cámara durante la sesión.\n"
                        "Verifica la conexión y vuelve a intentar.")
                    break
                continue
            frames_sin_datos = 0

            faces       = _detect_faces(frame)
            display     = frame.copy()
            frame_count += 1
            ahora       = datetime.datetime.now().timestamp()

            if not cap_es_de_hoy:
                h_f, w_f = display.shape[:2]
                cv2.rectangle(display, (0, 0), (w_f, 44), (0, 0, 160), -1)
                cv2.putText(display,
                            f"Capacitacion programada para {fecha_cap} - no se puede registrar hoy",
                            (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 200, 100), 1)
                cv2.putText(display, "ESC=salir", (10, display.shape[0] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (120, 120, 120), 1)
                cv2.imshow(_NOMBRE_VENTANA, display)
                if cv2.waitKey(1) & 0xFF == 27:
                    break
                continue

            if len(faces) == 1:
                x, y, w, h = faces[0]

                if frame_count % ANALIZAR_CADA == 0 and not _analizando.is_set():
                    _analizando.set()
                    crop = frame[y:y+h, x:x+w].copy()
                    try:
                        _frame_q.get_nowait()
                    except queue.Empty:
                        pass
                    _frame_q.put(crop)

                try:
                    emb = _resultado_q.get_nowait()
                    if emb is not None:
                        if usar_faiss:
                            mejor_pid, mejor_nombre, mejor_dist = _buscar_faiss(emb)
                        else:
                            mejor_pid, mejor_nombre, mejor_dist = None, "Desconocido", 1.0
                            for pid_k, nombre_k, known_emb in known_data:
                                dist = _cosine_distance(emb, known_emb)
                                if dist < mejor_dist:
                                    mejor_dist, mejor_pid, mejor_nombre = dist, pid_k, nombre_k

                        en_cooldown = (
                            mejor_pid is not None and
                            mejor_pid in cooldown and
                            ahora - cooldown[mejor_pid] < COOLDOWN_SEG
                        )

                        if mejor_dist < THRESHOLD and mejor_pid is not None and not en_cooldown:
                            if mejor_pid == ultimo_pid:
                                confirmaciones += 1
                            else:
                                confirmaciones = 1
                                ultimo_pid     = mejor_pid
                                ultimo_label   = mejor_nombre
                                ultimo_color   = (27, 79, 156)
                        else:
                            confirmaciones = 0
                            ultimo_pid     = None
                            if mejor_pid is not None and en_cooldown:
                                ultimo_label = "Ya registrado"
                                ultimo_color = (200, 140, 0)
                            else:
                                ultimo_label = "Desconocido"
                                ultimo_color = (185, 28, 28)
                except queue.Empty:
                    pass

                if confirmaciones >= CONFIRMACIONES_NEEDED and ultimo_pid is not None:
                    pid_reg    = ultimo_pid
                    nombre_reg = ultimo_label

                    confirmaciones = 0
                    ultimo_pid     = None
                    ultimo_label   = "Buscando..."
                    ultimo_color   = (46, 134, 193)

                    if nombre_reg not in _LABELS_INVALIDOS:
                        ya_registrado = False
                        try:
                            with sqlite3.connect(DB_PATH) as con:
                                con.execute(
                                    "INSERT INTO asistencias "
                                    "(persona_id, capacitacion_id, fecha_dia) "
                                    "VALUES (?,?,?)",
                                    (pid_reg, cap_id, hoy))
                            registrados_sesion.add(pid_reg)
                            nombres_registrados.append(nombre_reg)
                        except sqlite3.IntegrityError:
                            ya_registrado = True
                        except Exception as e:
                            print(f"[ERROR] INSERT asistencia: {e}")
                            ya_registrado = True

                        cooldown[pid_reg] = ahora

                        try:
                            with sqlite3.connect(DB_PATH) as _con:
                                _row = _con.execute(
                                    "SELECT cargo FROM personas WHERE id=?",
                                    (pid_reg,)).fetchone()
                            cargo_txt = (_row[0] or "") if _row else ""
                        except Exception:
                            cargo_txt = ""

                        VERDE    = (26, 125, 78)
                        AMARILLO = (0, 140, 200)
                        color_flash = AMARILLO if ya_registrado else VERDE
                        msg_flash   = ("YA REGISTRADO EN ESTA CAPACITACION"
                                       if ya_registrado else "ASISTENCIA REGISTRADA")

                        hora_txt  = datetime.datetime.now().strftime("%H:%M")
                        partes    = nombre_reg.split()
                        iniciales = (partes[0][0] + (partes[-1][0] if len(partes) > 1 else "")).upper()

                        MAX_N = 26; MAX_C = 32
                        n_txt = nombre_reg[:MAX_N] + ("..." if len(nombre_reg) > MAX_N else "")
                        c_txt = (cargo_txt[:MAX_C] + ("..." if len(cargo_txt) > MAX_C else "")
                                 if cargo_txt else "")

                        esc = _mostrar_flash(frame, x, y, w, h,
                                             color_flash, msg_flash,
                                             n_txt, c_txt, hora_txt, iniciales)
                        if esc:
                            break
                        continue

                cv2.rectangle(display, (x, y), (x+w, y+h), ultimo_color, 2)
                cv2.putText(display, ultimo_label, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.75, ultimo_color, 2)

                if ultimo_pid is not None:
                    bw    = 220
                    lleno = int(bw * confirmaciones / CONFIRMACIONES_NEEDED)
                    cv2.rectangle(display, (10, 42), (10+bw,    60), (200, 210, 225), -1)
                    cv2.rectangle(display, (10, 42), (10+lleno, 60), (27, 79, 156),   -1)
                    cv2.putText(display, "Verificando identidad...", (10, 38),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (27, 79, 156), 1)
                else:
                    cv2.putText(display, "Buscando trabajador...", (10, 38),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (46, 134, 193), 2)

            else:
                confirmaciones = 0
                ultimo_pid     = None
                msg = ("Posicionate frente a la camara" if len(faces) == 0
                       else "Solo una persona a la vez")
                cv2.putText(display, msg, (10, 38),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (46, 134, 193), 2)

            cv2.putText(display,
                        f"ESC para terminar  |  {len(registrados_sesion)} registrado(s)",
                        (display.shape[1] - 320, 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 210, 255), 1)
            cv2.putText(display, "ESC=terminar sesion", (10, display.shape[0] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (120, 120, 120), 1)
            _dibujar_panel(display, nombres_registrados)
            cv2.imshow(_NOMBRE_VENTANA, display)

            if cv2.waitKey(1) & 0xFF == 27:
                break

    finally:
        try:
            _frame_q.get_nowait()
        except queue.Empty:
            pass
        _frame_q.put(None)
        hilo.join(timeout=1.0)
        cerrar_camara(cap)
        cv2.destroyAllWindows()

    return list(registrados_sesion)