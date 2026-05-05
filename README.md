# 📖 Sistema de Asistencias a Capacitaciones - Documentación Completa

**Es un sistema de escritorio moderno para registrar y gestionar asistencias en capacitaciones mediante reconocimiento facial con IA.**

---

## 🎯 Tabla de Contenidos

- [Descripción](#descripción)
- [Características](#características)
- [Requisitos Previos](#requisitos-previos)
- [Inicio Rápido (5 minutos)](#-inicio-rápido-5-minutos)
- [Instalación Detallada](#instalación-detallada)
- [Uso de la Aplicación](#-uso-de-la-aplicación)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Configuración](#-configuración)
- [Solución de Problemas](#-solución-de-problemas-completa)
- [Desarrollo y Extensiones](#-para-desarrolladores-extensiones-y-api)
- [Compilación y Distribución](#-compilación-y-distribución)
- [Seguridad](#-seguridad-y-buenas-prácticas)
- [Conceptos Técnicos](#-conceptos-técnicos)
- [Licencia](#-licencia)

---

## 📝 Descripción

**Sistema de Asistencias a Capacitaciones** es una aplicación de escritorio desarrollada en **Python** que permite registrar y gestionar asistencias en eventos de capacitación utilizando:

- ✅ **Reconocimiento facial inteligente** con DeepFace y IA
- ✅ **Interfaz gráfica moderna** (Tkinter con tema corporativo azul 2026)
- ✅ **Base de datos SQLite** segura y eficiente
- ✅ **Generación de reportes PDF** automáticos
- ✅ **Autenticación segura** con contraseñas encriptadas (bcrypt)
- ✅ **Gestión de usuarios y roles**

Perfecto para:
- Capacitaciones corporativas
- Eventos empresariales
- Sesiones de formación
- Control de asistencia automatizado

---

## ✨ Características

### 🔐 Seguridad y Autenticación
- Autenticación de usuarios con contraseña encriptada (bcrypt)
- Sistema de roles: administrador, operador
- Control de sesión de usuario
- Logs de auditoría en base de datos

### 👤 Reconocimiento Facial
- Captura de rostros mediante cámara web
- Generación de embeddings faciales usando DeepFace
- Índice FAISS para búsquedas rápidas
- Detección automática y configuración de cámara
- Soporte para múltiples confirmaciones de identidad
- Diálogo guiado de permisos de Windows

### 📊 Gestión de Datos
- Base de datos SQLite integrada
- Almacenamiento de personas con embeddings faciales
- Registro de capacitaciones y asistentes
- Historial completo de eventos

### 📄 Reportes
- Generación de reportes PDF profesionales
- Soporte para múltiples formatos de conversión:
  - docx2pdf
  - Word COM (Windows)
  - LibreOffice
- Plantillas personalizables
- Exportación a múltiples formatos

### 🎨 Interfaz de Usuario
- Diseño moderno con paleta azul corporativa
- Temas oscuro/claro
- Navegación intuitiva
- Retroalimentación sonora (beeps de éxito/error)
- Soporte para temas TTK

---

## 🔧 Requisitos 

### Sistema Operativo
- **Windows 7+** (recomendado Windows 10/11)
- Python 3.9+

### Hardware
- Procesador: Intel/AMD de doble núcleo (mínimo)
- RAM: 4GB (recomendado 8GB)
- Cámara web para reconocimiento facial
- Micrófono (opcional)

### Software Requerido
- **Python 3.9+** (3.11+ recomendado)
- pip (gestor de paquetes Python)
- Una cámara web conectada

### Para generación de reportes (opcional)
- Microsoft Word (para conversión DOCX → PDF)
- O LibreOffice (alternativa gratuita)

---

## 🚀 Inicio Rápido (5 minutos)

Sigue estos pasos para instalar y ejecutar la aplicación en **5 minutos**.

### 1️⃣ Clonar o descargar el repositorio

```bash
cd C:\Users\tu_usuario\OneDrive\Escritorio
git clone https://github.com/tu_usuario/asistencias.git
cd asistencias
```

### 2️⃣ Crear entorno virtual

**En CMD o PowerShell:**
```bash
python -m venv venv
venv\Scripts\activate
```

**En PowerShell (si falla):**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3️⃣ Instalar dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

⏱️ **Toma ~5-10 minutos** (DeepFace es pesado)

### 4️⃣ Ejecutar la aplicación

```bash
python main.py
```

✅ **¡Listo!** La aplicación debería abrirse.

### 🔓 Acceder a la Aplicación

Al iniciar, usa estas credenciales por defecto:

```
Usuario: admin
Contraseña: camara26*
```

⚠️ **IMPORTANTE:** Cambiar la contraseña en producción.

### 📁 Primera Ejecución

La primera vez tarda **30-60 segundos** en cargar DeepFace.

El sistema crea automáticamente:
- ✅ Base de datos en `C:\Users\[usuario]\AppData\Local\Asistencias\`
- ✅ Carpeta de reportes en `Documentos\Asistencias\`

---

## 📥 Instalación Detallada

### Opción 1: Instalación de Desarrollo 

#### 1️⃣ Clonar o descargar el repositorio

```bash
cd C:\Users\tu_usuario\OneDrive\Escritorio
git clone https://github.com/tu_usuario/asistencias.git
cd asistencias
```

#### 2️⃣ Crear entorno virtual

```bash
python -m venv venv
venv\Scripts\activate
```

En PowerShell:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### 3️⃣ Instalar dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Dependencias principales:**
- tkinter (incluido con Python)
- sqlite3 (incluido con Python)
- deepface >= 0.0.75
- opencv-python >= 4.8.0
- numpy >= 1.24.0
- bcrypt >= 4.0.0
- reportlab >= 4.0.0
- pillow >= 10.0.0
- python-docx >= 0.8.11
- docx2pdf >= 0.1.8
- faiss-cpu >= 1.7.4

#### 4️⃣ Ejecutar la aplicación

```bash
python main.py
```

### Opción 2: Compilación a Ejecutable Windows (Producción)

#### 1️⃣ Instalar PyInstaller

Con el entorno virtual activado:

```bash
pip install pyinstaller
```

#### 2️⃣ Compilar la aplicación

```bash
pyinstaller asistencias.spec
```

El ejecutable se creará en la carpeta `dist/asistencias/`.

#### 3️⃣ Crear instalador (Inno Setup)

**Requisitos:**
- [Descargar Inno Setup](https://jrsoftware.org/isdl.php) (gratuito)

**Pasos:**
1. Abre Inno Setup
2. Abre el archivo `instalador.iss`
3. Haz clic en **Build → Compile**
4. El instalador `.exe` se creará en `instalador_salida/`

#### 4️⃣ Distribuir el instalador

El archivo `.exe` generado puede distribuirse e instalarse normalmente como cualquier aplicación de Windows.

---

## 🎯 Uso de la Aplicación

### Flujo Típico

```
Login
  ↓
Panel Principal
  ├─ Registrar Nueva Persona (con captura facial)
  ├─ Nueva Capacitación
  ├─ Registrar Asistencia (reconocimiento facial)
  ├─ Ver/Editar Datos
  ├─ Generar Reportes
  └─ Gestión de Usuarios (Admin)
  ↓
Logout
```

### Registro de Nueva Persona

1. **Panel Principal** → **Registrar Nueva Persona**
2. Ingresa nombre, apellido y cargo
3. Presiona **Capturar Rostro**
4. La cámara se abre automáticamente
5. El sistema captura múltiples imágenes de tu rostro
6. Presiona **Guardar** para confirmar

### Registrar Asistencia

1. **Panel Principal** → **Registrar Asistencia**
2. Selecciona la capacitación
3. Presiona **Abrir Cámara**
4. Mira a la cámara
5. El sistema reconoce automáticamente tu cara
6. Se registra tu asistencia

### Generar Reportes

1. **Panel Principal** → **Generar Reportes**
2. Selecciona la capacitación
3. Elige formato (PDF, Excel, etc.)
4. Presiona **Generar**
5. El archivo se descarga automáticamente

---

## 📂 Estructura del Proyecto

```
asistencias/
├── main.py                      # Punto de entrada principal
├── config.py                    # Configuración global, rutas, colores
├── db.py                        # Base de datos, usuarios, logs
├── ui.py                        # Interfaz gráfica (Tkinter)
├── vista.py                     # Captura facial, embeddings, DeepFace
├── exports.py                   # Generación de reportes PDF
├── diagnostico_camara.py        # Utilidad de diagnóstico de cámara
├── asistencias.spec             # Configuración PyInstaller
├── instalador.iss               # Script Inno Setup
├── Logo.ico                     # Icono de la aplicación
├── requirements.txt             # Dependencias Python
├── README.md                    # Este archivo
├── build/                       # Artefactos de compilación (PyInstaller)
├── dist/                        # Ejecutable compilado
├── plantillas/                  # Plantillas Word (.docx) para reportes
├── reportes/                    # Reportes PDF generados
└── __pycache__/                 # Cache Python (ignorar)
```

### Archivos Clave Explicados

#### `main.py`
- Punto de entrada de la aplicación
- Inicializa la base de datos
- Carga el modelo DeepFace en background
- Gestiona el loop login/logout
- Aplica tema gráfico global

#### `config.py`
- Rutas de datos (AppData, Documentos)
- Paleta de colores corporativa
- Constantes globales (thresholds, etc.)
- Detecta automáticamente si está compilado

#### `db.py`
- Inicialización de SQLite
- Funciones CRUD para usuarios, personas, capacitaciones
- Autenticación con bcrypt
- Sistema de logging de auditoría

#### `ui.py`
- Interfaz gráfica con Tkinter
- Ventana de login
- Panel principal con pestañas
- Diálogos para cada funcionalidad
- Tema corporativo azul 2026

#### `vista.py`
- Captura de video desde cámara
- Generación de embeddings con DeepFace
- Reconocimiento facial automático
- Índice FAISS para búsquedas rápidas
- Manejo de permisos de Windows

#### `exports.py`
- Generación de reportes PDF
- Conversión DOCX → PDF (3 métodos)
- Plantillas personalizables
- Exportación a Excel

---

## ⚙️ Configuración

### Variables Globales (config.py)

```python
# Rutas de datos
DB_PATH = "C:\\Users\\[usuario]\\AppData\\Local\\Asistencias\\asistencias.db"
REPORTES_DIR = "C:\\Users\\[usuario]\\Documents\\Asistencias\\reportes"

# Modelo DeepFace
MODEL_NAME = "Facenet512"           # Modelo de embeddings
THRESHOLD = 0.6                     # Similitud mínima (0-1)

# Cámara
NUM_CAPTURAS = 5                    # Imágenes por registro
ANALIZAR_CADA = 10                  # Frames para análisis
CONFIRMACIONES_NEEDED = 3            # Reconocimientos para confirmar

# Colores corporativos
PALETA = {
    "primary": "#1D4ED8",           # Azul principal
    "primary_h": "#1E40AF",         # Azul hover
    "secondary": "#64748B",         # Gris
    "white": "#FFFFFF",
    "text": "#1A2B4A",
    "border": "#CBD5E1"
}
```

### Variables de Entorno

```bash
# Windows (PowerShell)
$env:DB_PATH = "C:\Datos\asistencias.db"
$env:MODELO = "VGGFace2"
```

### Ajustes de Rendimiento (config.py)

```python
# Cámara y reconocimiento
NUM_CAPTURAS = 5            # Imágenes capturadas por persona
ANALIZAR_CADA = 10          # Frames analizados (menor = más CPU)
CONFIRMACIONES_NEEDED = 3   # Reconocimientos para confirmar asistencia
THRESHOLD = 0.6             # Sensibilidad (0.5-0.7 recomendado)
```

#### Para máquinas lentas:
```python
NUM_CAPTURAS = 3            # Menos imágenes
ANALIZAR_CADA = 20          # Menos procesamiento
CONFIRMACIONES_NEEDED = 2   # Menos confirmaciones
```

#### Para máquinas potentes / Alta precisión:
```python
NUM_CAPTURAS = 8            # Más imágenes
ANALIZAR_CADA = 5           # Análisis frecuente
CONFIRMACIONES_NEEDED = 4   # Más confirmaciones
THRESHOLD = 0.65            # Más estricto
```

### Seleccionar Modelo de IA

DeepFace soporta múltiples modelos. En `vista.py`:

```python
MODEL_NAME = "Facenet512"   # Recomendado: Rápido + preciso
# Alternativas:
# MODEL_NAME = "VGGFace2"     # Muy preciso (más lento)
# MODEL_NAME = "Facenet"      # Rápido (menos preciso)
# MODEL_NAME = "ArcFace"      # Muy preciso (muy lento)
# MODEL_NAME = "Dlib"         # Muy rápido (menos preciso)
```

### Base de Datos

La base de datos se crea automáticamente en:
- **Desarrollo:** `asistencias.db` (carpeta del proyecto)
- **Producción:** `C:\Users\[usuario]\AppData\Local\Asistencias\asistencias.db`

Tablas:
- `usuarios` - Usuarios del sistema con roles
- `personas` - Registros de personas con embeddings
- `capacitaciones` - Eventos de capacitación
- `asistencias` - Registros de asistencia
- `logs` - Auditoría de acciones

---

## 🔍 Solución de Problemas Completa

### ❌ "Cámara no disponible"

**Síntoma:** La aplicación no detecta la cámara.

**Soluciones:**

#### Paso 1: Verificar hardware
```bash
# Ejecutar diagnóstico
python diagnostico_camara.py
```

#### Paso 2: Permisos en Windows 10/11

1. Abre **Configuración**
2. Ve a **Privacidad y seguridad → Cámara**
3. Habilita "Acceso a la cámara"
4. Baja hasta esta app y verifica que esté **ACTIVADA**

#### Paso 3: Cerrar aplicaciones conflictivas

```bash
# Cierra en Task Manager:
# - Teams
# - Zoom
# - Skype
# - Discord
# - OBS
# - Cualquier app con cámara
```

#### Paso 4: Actualizar drivers de cámara

1. Abre **Administrador de dispositivos** (Win + X → Administrador de dispositivos)
2. Expande **Cámaras**
3. Click derecho en tu cámara → **Actualizar controlador**
4. **Buscar automáticamente**

#### Paso 5: Cambiar backend OpenCV

En `vista.py`, encuentra:

```python
# Por defecto
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

# Intenta estas alternativas si falla:
cap = cv2.VideoCapture(0, cv2.CAP_MSMF)      # Windows
cap = cv2.VideoCapture(0, cv2.CAP_VFW)       # Video for Windows
cap = cv2.VideoCapture(0)                     # Auto-detect
```

### ❌ "Aplicación muy lenta / congelada"

**Primera ejecución:** Es normal, tarda **30-60 segundos** cargando DeepFace.

**Después de la primera ejecución:**

**Causa:** CPU saturada durante reconocimiento facial.

**Soluciones:**

#### Opción A: Reducir carga de procesamiento
```python
# En config.py
ANALIZAR_CADA = 20          # Analiza menos frames (reduce CPU)
NUM_CAPTURAS = 3            # Menos imágenes al registrar
```

#### Opción B: Usar modelo más rápido
```python
# En vista.py
MODEL_NAME = "Facenet"      # Más rápido que Facenet512
```

#### Opción C: Aumentar RAM

Si tienes < 4GB RAM:
1. Cierra otras aplicaciones
2. Aumenta RAM si es posible

#### Opción D: Usar GPU (si tienes NVIDIA)

```bash
# Desinstala la versión CPU
pip uninstall faiss-cpu -y

# Instala versión GPU
pip install faiss-gpu
```

### ❌ "Error al generar reporte PDF"

**Error:**
```
Error: Could not convert DOCX to PDF
Could not find a suitable conversion method
```

**Causas:**
- LibreOffice/Word no instalado
- Plantilla DOCX corrupta
- Permisos insuficientes

**Soluciones:**

#### Opción 1: Instalar LibreOffice (recomendado - GRATIS)

Descarga: https://www.libreoffice.org/download/

```bash
# Después de instalar, el sistema debería detectarlo automáticamente
```

#### Opción 2: Instalar Microsoft Word

Si tienes Office 365 o Word standalone, el sistema también usa esto.

#### Opción 3: Instalar comtypes (para Word COM)

```bash
pip install comtypes
```

#### Opción 4: Verificar plantilla DOCX

1. Abre la plantilla en `plantillas/`
2. Asegúrate de que sea un documento Word válido
3. Si está corrupta, crea una nueva

### ❌ "Error de Login"

**Error:**
```
Usuario o contraseña incorrectos
```

**Soluciones:**

#### Usuario por defecto no existe

```bash
# Crea el usuario admin por defecto
python -c "from db import crear_usuario; crear_usuario('admin', 'admin', 'admin')"
```

#### Olvidé mi contraseña

```bash
# Opción 1: Reset del usuario admin
python -c "from db import reset_usuario; reset_usuario('admin', 'nuevaPassword123')"

# Opción 2: Eliminar base de datos y empezar de cero
# (Advertencia: Se perderán todos los datos)
del %LOCALAPPDATA%\Asistencias\asistencias.db
python main.py  # Crea nueva DB con admin/admin
```

### ❌ "Error de Base de Datos"

**Error:**
```
database is locked
sqlite3.OperationalError: database is locked
```

**Causa:** Dos instancias de la app usando la BD simultáneamente.

**Soluciones:**

1. Cierra todas las instancias de la aplicación
2. Espera 5 segundos
3. Ejecuta de nuevo

```bash
# Ver procesos Python
tasklist | findstr python

# Matar proceso si es necesario
taskkill /IM python.exe /F
```

### ❌ "Reconocimiento facial impreciso"

**Problema:** 
- No reconoce al usuario aunque la foto sea clara
- Reconoce al usuario incorrecto
- Demasiados falsos positivos/negativos

**Soluciones:**

#### Aumentar precisión (menos falsos positivos)
```python
# En config.py
THRESHOLD = 0.65            # Más estricto (0.6 → 0.65)
CONFIRMACIONES_NEEDED = 4   # Más confirmaciones (3 → 4)
```

#### Aumentar sensibilidad (menos falsos negativos)
```python
# En config.py
THRESHOLD = 0.55            # Menos estricto (0.6 → 0.55)
CONFIRMACIONES_NEEDED = 2   # Menos confirmaciones (3 → 2)
```

#### Usar modelo más preciso
```python
# En vista.py
MODEL_NAME = "VGGFace2"     # Muy preciso (pero lento)
# O
MODEL_NAME = "ArcFace"      # Muy preciso (pero muy lento)
```

#### Re-registrar la persona
1. Elimina el registro anterior
2. Registra de nuevo con mejor iluminación
3. Asegúrate de mirar directamente a la cámara

### ❌ "Error al compilar con PyInstaller"

**Error:**
```
ModuleNotFoundError: No module named 'deepface'
UnicodeDecodeError during compilation
```

**Soluciones:**

#### Limpiar compilaciones anteriores
```bash
rmdir /s build
rmdir /s dist
del *.egg-info
del *.pyc
```

#### Recompilar
```bash
pip install --upgrade pyinstaller
pyinstaller asistencias.spec --clean
```

#### Si falla con especificaciones
```bash
# Generar .spec nuevo (automático)
pyinstaller --onedir --windowed --icon=Logo.ico main.py
```

### ✅ Ejecutar Diagnóstico Completo

```bash
python diagnostico_camara.py
```

Este script verifica:
- Versión de Python y OpenCV
- Disponibilidad de cámara
- Backends de OpenCV
- Permisos en Windows
- Configuración guardada

---

## 👨‍💻 Para Desarrolladores: Extensiones y API

### Arquitectura del Proyecto

```
┌─────────────────────────────────────────┐
│      Interfaz Gráfica (ui.py)          │ ← Capa de Presentación
├─────────────────────────────────────────┤
│  Lógica de Negocio (vista.py)          │ ← Procesamiento de Imágenes
├─────────────────────────────────────────┤
│  Exportación (exports.py)               │ ← Generación de Reportes
├─────────────────────────────────────────┤
│  Base de Datos (db.py)                 │ ← Persistencia
├─────────────────────────────────────────┤
│  Configuración (config.py)             │ ← Constants & Setup
└─────────────────────────────────────────┘
```

### Flujo de Datos

```
Usuario → UI (tkinter)
           ↓
         db.py (CRUD, autenticación)
           ↓
         vista.py (DeepFace, OpenCV)
           ↓
         FAISS Index (búsqueda vectorial)
           ↓
         SQLite Database
```

### API Interna

#### Base de Datos (db.py)

**Usuarios:**
```python
from db import crear_usuario, verificar_login, listar_usuarios, eliminar_usuario

# Crear usuario
crear_usuario('usuario123', 'Password123!', 'operador')

# Verificar login
result = verificar_login('usuario123', 'Password123!')
# Retorna: (True, usuario_id) o (False, None)

# Listar usuarios
usuarios = listar_usuarios()

# Eliminar
eliminar_usuario(usuario_id)
```

**Personas:**
```python
from db import registrar_persona, buscar_persona, listar_personas

# Registrar con embedding
registrar_persona('Juan', 'Pérez', 'Gerente', embedding_bytes)

# Buscar por ID
persona = buscar_persona(persona_id)

# Listar todas
personas = listar_personas()
```

**Capacitaciones:**
```python
from db import crear_capacitacion, listar_capacitaciones

crear_capacitacion('Inducción 2026', 'Descripción...', '2026-05-05')

capacitaciones = listar_capacitaciones()
```

**Asistencias:**
```python
from db import registrar_asistencia, asistencias_por_capacitacion

registrar_asistencia(capacitacion_id, persona_id, timestamp)

asistencias = asistencias_por_capacitacion(capacitacion_id)
```

#### Visión (vista.py)

```python
from vista import (
    calentar_modelo,              # Pre-carga DeepFace
    capturar_embedding_multi,     # Captura y genera embedding
    reconocer_cara,               # Reconocimiento en tiempo real
    get_all_embeddings,           # Obtiene todos los embeddings de BD
    rebuild_faiss_index,          # Reconstruye índice de búsqueda
    cerrar_camara                 # Cierra dispositivo de cámara
)

# Pre-cargar modelo (ejecutar al iniciar)
calentar_modelo()

# Capturar embedding (retorna numpy array 512D)
embedding = capturar_embedding_multi(imagen_path, num_capturas=5)

# Reconocer cara en video
persona_id = reconocer_cara(threshold=0.6)
```

#### Exportación (exports.py)

```python
from exports import exportar_pdf

# Generar PDF de capacitación
exportar_pdf(
    capacitacion_id=1,
    asistencias_list=[(persona_id, timestamp), ...],
    output_path='reporte.pdf'
)
```

### Extensiones Comunes

#### Agregar un Nuevo Campo a Persona

**1. Actualizar schema (db.py)**

```python
# En init_db(), modificar CREATE TABLE personas:
CREATE TABLE IF NOT EXISTS personas (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre    TEXT NOT NULL,
    apellido  TEXT NOT NULL,
    cargo     TEXT,
    email     TEXT,                    # ← NUEVO
    telefono  TEXT,                    # ← NUEVO
    embedding BLOB NOT NULL,
    activo    INTEGER NOT NULL DEFAULT 1,
    creado_en TEXT DEFAULT (datetime('now','localtime'))
);
```

**2. Crear función de migración**

```python
# En db.py, agregar:
def migrate_add_email_telefono():
    """Migración para agregar campos email y telefono"""
    try:
        with sqlite3.connect(DB_PATH) as con:
            con.execute("ALTER TABLE personas ADD COLUMN email TEXT")
            con.execute("ALTER TABLE personas ADD COLUMN telefono TEXT")
            print("✅ Migración completada")
    except sqlite3.OperationalError:
        print("⚠️ Campos ya existen")
```

**3. Actualizar funciones CRUD**

```python
def registrar_persona(nombre: str, apellido: str, cargo: str, embedding: bytes, 
                      email: str = None, telefono: str = None):
    """Registrar nueva persona con nuevos campos"""
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute("""
            INSERT INTO personas (nombre, apellido, cargo, email, telefono, embedding)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nombre, apellido, cargo, email, telefono, embedding))
        con.commit()
        return cur.lastrowid
```

**4. Actualizar UI**

```python
# En ui.py, agregar campos Entry para email y telefono
email_entry = _entry(frame, width=32)
email_entry.pack()

telefono_entry = _entry(frame, width=32)
telefono_entry.pack()
```

#### Agregar Nuevo Módulo de Reportes

**1. Crear archivo `reportes_avanzados.py`**

```python
"""reportes_avanzados.py - Reportes personalizados"""

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import sqlite3
from config import DB_PATH

def generar_reporte_estadisticas(ruta_salida: str):
    """Genera reporte de estadísticas de asistencias"""
    
    # Obtener datos
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    
    cur.execute("""
        SELECT p.nombre, p.apellido, COUNT(a.id) as asistencias
        FROM personas p
        LEFT JOIN asistencias a ON p.id = a.persona_id
        GROUP BY p.id
        ORDER BY asistencias DESC
    """)
    datos = cur.fetchall()
    con.close()
    
    # Crear PDF
    pdf = SimpleDocTemplate(ruta_salida, pagesize=letter)
    elementos = []
    
    # Encabezado
    estilo = getSampleStyleSheet()
    titulo = Paragraph("Reporte de Estadísticas", estilo['Title'])
    elementos.append(titulo)
    elementos.append(Spacer(1, 20))
    
    # Tabla
    datos_tabla = [['Nombre', 'Apellido', 'Asistencias']] + datos
    tabla = Table(datos_tabla)
    elementos.append(tabla)
    
    # Generar
    pdf.build(elementos)
    return ruta_salida
```

**2. Usar en ui.py**

```python
from reportes_avanzados import generar_reporte_estadisticas

# En clase VentanaReportes, agregar botón:
btn_estadisticas = _btn(
    frame, 
    "Reporte Estadísticas",
    lambda: generar_reporte_estadisticas(output_path)
)
btn_estadisticas.pack()
```

#### Integrar Base de Datos Remota (PostgreSQL)

**1. Instalar psycopg2**

```bash
pip install psycopg2-binary
```

**2. Crear módulo de conexión**

```python
# db_remote.py
import psycopg2
from psycopg2.extras import RealDictCursor

class DBRemota:
    def __init__(self, host, database, user, password):
        self.conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password
        )
    
    def get_personas(self):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM personas")
            return cur.fetchall()
    
    def insertar_asistencia(self, persona_id, capacitacion_id):
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO asistencias (persona_id, capacitacion_id) VALUES (%s, %s)",
                (persona_id, capacitacion_id)
            )
            self.conn.commit()
```

### Testing

```python
# tests/test_db.py
import unittest
import sqlite3
import os
from db import crear_usuario, verificar_login

class TestDB(unittest.TestCase):
    
    def test_crear_usuario(self):
        usuario_id = crear_usuario('testuser', 'pass123', 'admin')
        self.assertIsNotNone(usuario_id)
    
    def test_verificar_login_valido(self):
        resultado, uid = verificar_login('testuser', 'pass123')
        self.assertTrue(resultado)
    
    def test_verificar_login_invalido(self):
        resultado, uid = verificar_login('testuser', 'wrongpass')
        self.assertFalse(resultado)

if __name__ == '__main__':
    unittest.main()
```

**Ejecutar:**
```bash
python -m pytest tests/
# O
python -m unittest tests.test_db
```

### Control de Versiones

```bash
# .gitignore
__pycache__/
*.pyc
venv/
build/
dist/
asistencias.db
*.log
reportes/

# Commits semánticos
git commit -m "feat: agregar reconocimiento de múltiples rostros"
git commit -m "fix: corregir bug de cámara bloqueada"
git commit -m "docs: actualizar README"
git commit -m "refactor: optimizar búsqueda FAISS"
git commit -m "perf: reducir tiempo de carga del modelo"
```

### Estándares de Código

- **Funciones:** `snake_case`
- **Clases:** `PascalCase`
- **Constantes:** `UPPER_SNAKE_CASE`
- **Privadas:** `_inicio_guion`

**Docstrings (PEP 257):**

```python
def registrar_persona(nombre: str, apellido: str, embedding: bytes) -> int:
    """
    Registra una nueva persona en la base de datos.
    
    Args:
        nombre: Nombre de la persona
        apellido: Apellido de la persona
        embedding: Array de embedding facial (bytes)
    
    Returns:
        ID de la persona registrada
    
    Raises:
        ValueError: Si el embedding es inválido
    """
```

---

## 📦 Compilación y Distribución

### Generar Ejecutable Standalone

```bash
# Activar entorno
venv\Scripts\activate

# Compilar
pyinstaller asistencias.spec

# Resultado
# → dist\asistencias\asistencias.exe (aplicación)
# → dist\asistencias\*.dll (dependencias)
```

### Crear Instalador Windows

1. Abre Inno Setup
2. Abre `instalador.iss`
3. Build → Compile
4. Resultado: `instalador_salida\asistenciasSetup.exe`

El instalador:
- Instala la aplicación en `Program Files`
- Crea acceso directo en Escritorio
- Crea entrada en Menú Inicio
- Configura rutas automáticamente

### Preparar para Producción

```bash
# 1. Limpiar
rm -rf build/ dist/ __pycache__ *.pyc

# 2. Ejecutar tests
python -m pytest tests/

# 3. Verificar seguridad
bandit -r *.py

# 4. Compilar
pyinstaller asistencias.spec

# 5. Crear instalador
# Usar Inno Setup (ver instrucciones arriba)
```

---

## 🔐 Seguridad y Buenas Prácticas

### Cambiar Contraseña del Admin

```bash
python -c "from db import cambiar_contraseña; cambiar_contraseña('admin', 'adminPassword123')"
```

### Crear Nuevo Usuario

```bash
python -c "from db import crear_usuario; crear_usuario('juan.perez', 'Password123!', 'operador')"
```

### Roles Disponibles
- `admin` - Acceso completo, gestión de usuarios
- `operador` - Uso normal, sin gestión de usuarios

### Política de Contraseñas Recomendada

```
✅ Mínimo 12 caracteres
✅ Mayúsculas + minúsculas + números + símbolos
✅ No usar el nombre de usuario
✅ Cambiar cada 90 días
❌ Evitar contraseñas comunes (123456, qwerty, etc.)
```

### Hacer Backup de Datos

```bash
# Windows CMD
copy "%LOCALAPPDATA%\Asistencias\asistencias.db" "C:\Backup\asistencias_%date:~-4,4%%date:~-10,2%%date:~-7,2%.db"

# PowerShell
Copy-Item -Path "$env:LOCALAPPDATA\Asistencias\asistencias.db" -Destination "C:\Backup\asistencias_backup.db"
```

### Restaurar desde Backup

```bash
# Primero, cierra la aplicación
# Luego:
copy "C:\Backup\asistencias_backup.db" "%LOCALAPPDATA%\Asistencias\asistencias.db"
```

### Programar Backup Automático (Windows)

1. Abre **Tareas programadas**
2. **Crear tarea básica**
3. Nombre: "Backup Asistencias"
4. Disparador: **Diario** a las 18:00
5. Acción: **Script PowerShell**

```powershell
$origen = "$env:LOCALAPPDATA\Asistencias\asistencias.db"
$destino = "C:\Backup\asistencias_$(Get-Date -Format 'yyyyMMdd_HHmmss').db"
Copy-Item -Path $origen -Destination $destino
```

### Buenas Prácticas de Seguridad

✅ **Hacer:**
- Cambiar contraseña `admin` en producción
- Usar HTTPS si se conecta a servidor remoto
- Hacer backup regular de `asistencias.db`
- Usar roles apropiados (admin/operador)

❌ **No hacer:**
- Dejar contraseña por defecto
- Compartir credenciales
- Guardar datos confidenciales en código
- Ejecutar con privilegios innecesarios

---

## 💡 Conceptos Técnicos

### Embeddings Faciales

Los embeddings son representaciones numéricas de rostros:
- DeepFace genera vectores de **512 dimensiones**
- Se comparan usando distancia euclidiana
- FAISS indexa para búsquedas O(log n)
- Threshold 0.35



### Flujo DeepFace

```
Imagen → Detección de rostro → Alineación → Extracción de características → Embedding (512D)
                                                                                ↓
                                                                        Base de datos vectorial
```

### Autenticación

```
Contraseña → bcrypt.hashpw() → Hash almacenado en DB
                                        ↓
Usuario intenta login → bcrypt.checkpw() → Match: ✅ / No match: ❌
```

### Embeddings FAISS

FAISS (Facebook AI Similarity Search) convierte embeddings en estructuras indexadas para búsquedas rápidas:

```
Embedding (512D) → FAISS Index → Búsqueda O(log n)
                      ↓
                   Personas similares
```

### Optimización de FAISS

Si tienes muchos registros:

```bash
# Reconstruir índice
python -c "from vista import rebuild_faiss_index; rebuild_faiss_index()"
```

---

## 📊 Dependencias Principales

| Librería | Versión | Propósito |
|----------|---------|-----------|
| tkinter | 3.9+ | Interfaz gráfica |
| sqlite3 | 3.9+ | Base de datos |
| deepface | 0.0.75+ | Reconocimiento facial |
| opencv-python | 4.8+ | Captura de cámara |
| numpy | 1.24+ | Cálculos numéricos |
| bcrypt | 4.0+ | Encriptación de contraseñas |
| reportlab | 4.0+ | Generación PDF |
| faiss-cpu | 1.7.4 | Búsqueda de embeddings |
| pillow | 10.0+ | Procesamiento de imágenes |
| python-docx | 0.8.11 | Lectura/escritura DOCX |

Para versiones completas: ver `requirements.txt`

---

## 🎓 Recursos de Aprendizaje

### Si quieres aprender sobre:

**Tkinter (Interfaz Gráfica)**
- Official: https://docs.python.org/3/library/tkinter.html
- Tutorial: https://www.tutorialspoint.com/python/python_tkinter.htm

**DeepFace (Reconocimiento Facial)**
- GitHub: https://github.com/serengp/deepface
- Paper: https://arxiv.org/abs/1701.07755

**OpenCV (Procesamiento de Imágenes)**
- Docs: https://docs.opencv.org/
- Tutoriales: https://docs.opencv.org/master/d9/df8/tutorial_root.html

**SQLite (Base de Datos)**
- Official: https://www.sqlite.org/docs.html
- Python: https://docs.python.org/3/library/sqlite3.html

**FAISS (Búsqueda Vectorial)**
- GitHub: https://github.com/facebookresearch/faiss
- Wiki: https://github.com/facebookresearch/faiss/wiki

**PyInstaller (Empaquetamiento)**
- Docs: https://pyinstaller.readthedocs.io/

**Inno Setup (Instaladores)**
- Docs: https://jrsoftware.org/ishelp/

---

## 📝 Historial de Cambios

### v1.0.0 (2026-05-05)
- ✅ Lanzamiento inicial
- ✅ Reconocimiento facial con DeepFace
- ✅ Generación de reportes PDF
- ✅ Interfaz tema azul corporativo
- ✅ Soporte empaquetamiento Windows

---

## 🎨 Características Detalladas

### Reconocimiento Facial Inteligente

```python
# Proceso de captura
1. Usuario presiona botón "Capturar Rostro"
2. Cámara se abre en ventana separada
3. Sistema captura 5 imágenes (configurable)
4. DeepFace genera embedding de 512 dimensiones
5. Embedding se guarda cifrado en DB
6. Índice FAISS se reconstruye

# Reconocimiento automático
1. Usuario abre cámara en módulo de asistencia
2. Sistema analiza cada 10 frames (configurable)
3. Busca rostro más cercano en índice FAISS
4. Si similitud > 0.6 (threshold), coincidencia
5. Requiere 3 confirmaciones de identidad
6. Registra asistencia automáticamente
```

### Generación de Reportes

El sistema intenta convertir plantillas DOCX a PDF mediante:

1. **docx2pdf** (más rápido, recomendado)
2. **Word COM** (si Word está instalado)
3. **LibreOffice** (alternativa gratuita)

Si falla la conversión, se exporta a Excel como fallback.

### Permisos de Cámara (Windows)

En Windows 10/11, el sistema:
1. Detecta si la cámara está bloqueada
2. Muestra diálogo con instrucciones
3. Ofrece botón directo a Configuración
4. Guarda configuración de cámara en DB para no buscar siempre

---

## 📞 Soporte y Contacto

- **Reporte de bugs:** Abre un issue en GitHub
- **Sugerencias:** Envía un pull request
- **Documentación:** Ver archivos docstrings en código

---

## 📄 Licencia

Este proyecto está bajo licencia **MIT**.

---

## 🙏 Créditos

Desarrollado con:
- **Python 3** - Lenguaje
- **Tkinter** - GUI
- **DeepFace** - Reconocimiento facial
- **OpenCV** - Procesamiento de imágenes
- **SQLite** - Base de datos
- **PyInstaller** - Empaquetamiento
- **Inno Setup** - Instalador

---

## ✅ Checklist de Instalación

- [ ] Python 3.9+ instalado
- [ ] Repositorio clonado/descargado
- [ ] Entorno virtual creado y activado
- [ ] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] Aplicación ejecutada (`python main.py`)
- [ ] Login exitoso con `admin` / `admin`
- [ ] Cámara detectada correctamente
- [ ] Primera persona registrada

---

**¡Gracias por usar Sistema de Asistencias!** 🎉

Para más información o si necesitas ayuda, revisa esta documentación.

Documentación actualizada: **2026-05-05** | Versión del proyecto: **v1.0.0**
