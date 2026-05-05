"""
config.py - Constantes globales, paleta corporativa y rutas del sistema.

Estructura de rutas:
    DB y configuración  -> AppData/Local/Asistencias/
    Reportes PDF        -> Documentos/Asistencias/reportes/
    Plantillas          -> Documentos/Asistencias/plantillas/
"""

import os
import sys

# ─────────────────────────────────────────────
#  DETECCIÓN DE ENTORNO
# ─────────────────────────────────────────────
_FROZEN = getattr(sys, "frozen", False)

# ─────────────────────────────────────────────
#  CARPETA DOCUMENTOS DE WINDOWS (dev y producción)
# ─────────────────────────────────────────────
def _get_documents_dir() -> str:
    """
    Obtiene la carpeta Documentos real del usuario usando la API de Windows.
    Funciona aunque el usuario haya movido Documentos a otro disco.
    Fallback: ~/Documents
    """
    try:
        import ctypes
        from ctypes import wintypes
        CSIDL_PERSONAL = 0x0005
        buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_PERSONAL, None, 0, buf)
        if buf.value:
            return buf.value
    except Exception:
        pass
    return os.path.join(os.path.expanduser("~"), "Documents")


# ─────────────────────────────────────────────
#  RUTAS BASE
# ─────────────────────────────────────────────
_APPDATA  = os.environ.get("LOCALAPPDATA",
            os.path.join(os.path.expanduser("~"), "AppData", "Local"))
_APP_DIR  = os.path.join(_APPDATA, "Asistencias")

_DOCS_DIR = os.path.join(_get_documents_dir(), "Asistencias")

DB_PATH       = os.path.join(_APP_DIR,  "asistencias.db")
REPORTES_DIR  = os.path.join(_DOCS_DIR, "reportes")
PLANTILLA_DIR = os.path.join(_DOCS_DIR, "plantillas")

# En desarrollo, la DB también va en AppData (consistencia con producción)
# Si prefieres la DB local al proyecto durante desarrollo, descomenta:
# if not _FROZEN:
#     DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "asistencias.db")

# ── Crear carpetas si no existen ─────────────
for _d in (os.path.dirname(DB_PATH), REPORTES_DIR, PLANTILLA_DIR):
    os.makedirs(_d, exist_ok=True)

# ─────────────────────────────────────────────
#  MODELO FACIAL
# ─────────────────────────────────────────────
MODEL_NAME            = "Facenet"
THRESHOLD             = 0.35
ANALIZAR_CADA         = 4
CONFIRMACIONES_NEEDED = 2
NUM_CAPTURAS          = 5

# ─────────────────────────────────────────────
#  PALETA — CORPORATIVO AZUL OSCURO
# ─────────────────────────────────────────────
C = {
    # Fondos
    "bg"        : "#F0F4FC",
    "topbar"    : "#FFFFFF",
    "card"      : "#FFFFFF",
    "card_alt"  : "#F5F7FD",

    # Sidebar
    "sidebar"   : "#111D35",
    "sidebar_h" : "#1A2B4A",
    "sidebar_w" : 220,

    # Primario — azul brillante
    "primary"   : "#3D7BFF",
    "primary_h" : "#2455CC",
    "primary_l" : "#EEF3FF",

    # Secundario — azul medio
    "secondary" : "#2E86C1",

    # Semánticos
    "success"   : "#1A7D4E",
    "success_l" : "#E8F5EE",
    "warning"   : "#B45309",
    "warning_l" : "#FEF3C7",
    "danger"    : "#B91C1C",
    "danger_l"  : "#FEE2E2",
    "purple"    : "#5B21B6",
    "purple_l"  : "#EDE9FE",

    # Texto
    "text"      : "#1A202C",
    "text2"     : "#4A5568",
    "text3"     : "#A0AEC0",
    "white"     : "#FFFFFF",

    # Bordes
    "border"    : "#DDE4F0",
    "border2"   : "#BDD0FF",
}