# asistencias.spec
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Recopilar datos de modelos y librerías
datas = []
datas += collect_data_files("deepface")
datas += collect_data_files("cv2")
datas += [("Logo.ico", ".")]  # <-- copia Logo.ico a la raíz del directorio dist

# Icono embebido en el .exe
icon_path = "Logo.ico"  # debe estar junto al .spec al momento de compilar

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # DeepFace y sus backends
        "deepface",
        "deepface.models",
        "deepface.detectors",
        "deepface.commons",
        "tensorflow",
        "keras",
        # Tkinter
        "tkinter",
        "tkinter.ttk",
        "tkinter.messagebox",
        "tkinter.filedialog",
        # Otros
        "PIL",
        "PIL.Image",
        "PIL.ImageTk",
        "cv2",
        "numpy",
        "bcrypt",
        "reportlab",
        "reportlab.platypus",
        "reportlab.lib",
        "docx",
        "docx2pdf",
        "faiss",
        "sqlite3",
        "winsound",
        "comtypes",
        "comtypes.client",
        "comtypes.server",
        "comtypes.typeinfo",
        "comtypes.automation",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SistemaAsistencias",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,      # False = sin ventana de consola negra
    icon=icon_path,     # ícono embebido dentro del .exe
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="SistemaAsistencias",
)