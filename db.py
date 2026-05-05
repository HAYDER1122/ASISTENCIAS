"""
db.py — Inicialización de base de datos, autenticación, logs y configuración.
"""

import sqlite3
import bcrypt
from config import DB_PATH

# ─────────────────────────────────────────────
#  SESIÓN ACTIVA
# ─────────────────────────────────────────────
_session_user = "sistema"

def set_session_user(username: str):
    global _session_user
    _session_user = username

def get_session_user() -> str:
    return _session_user

# ─────────────────────────────────────────────
#  INICIALIZACIÓN
# ─────────────────────────────────────────────
def init_db():
    with sqlite3.connect(DB_PATH) as con:
        con.executescript("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                rol           TEXT NOT NULL DEFAULT 'operador',
                activo        INTEGER NOT NULL DEFAULT 1,
                creado_en     TEXT DEFAULT (datetime('now','localtime'))
            );
            CREATE TABLE IF NOT EXISTS personas (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre    TEXT NOT NULL,
                apellido  TEXT NOT NULL,
                cargo     TEXT,
                embedding BLOB NOT NULL,
                activo    INTEGER NOT NULL DEFAULT 1,
                creado_en TEXT DEFAULT (datetime('now','localtime'))
            );
            CREATE TABLE IF NOT EXISTS capacitaciones (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre            TEXT NOT NULL,
                descripcion       TEXT,
                fecha             TEXT DEFAULT (date('now','localtime')),
                firma_responsable TEXT,
                firma_png         TEXT
            );
            CREATE TABLE IF NOT EXISTS asistencias (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                persona_id      INTEGER REFERENCES personas(id),
                capacitacion_id INTEGER REFERENCES capacitaciones(id),
                hora_registro   TEXT DEFAULT (datetime('now','localtime')),
                fecha_dia       TEXT DEFAULT (date('now','localtime')),
                UNIQUE(persona_id, capacitacion_id, fecha_dia)
            );
            CREATE TABLE IF NOT EXISTS logs (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT,
                accion  TEXT NOT NULL,
                detalle TEXT,
                nivel   TEXT NOT NULL DEFAULT 'INFO',
                fecha   TEXT DEFAULT (datetime('now','localtime'))
            );
            CREATE TABLE IF NOT EXISTS config (
                clave TEXT PRIMARY KEY,
                valor TEXT
            );
        """)

        # Migraciones seguras
        for sql in [
            "ALTER TABLE personas ADD COLUMN cargo TEXT",
            "ALTER TABLE personas ADD COLUMN activo INTEGER NOT NULL DEFAULT 1",
            "ALTER TABLE capacitaciones ADD COLUMN firma_responsable TEXT",
            "ALTER TABLE asistencias ADD COLUMN fecha_dia TEXT DEFAULT (date('now','localtime'))",
        ]:
            try:
                con.execute(sql)
            except Exception:
                pass

        # Migración: recrear asistencias con nuevo UNIQUE si no tiene fecha_dia
        try:
            cols = [r[1] for r in con.execute("PRAGMA table_info(asistencias)").fetchall()]
            if "fecha_dia" not in cols:
                con.executescript("""
                    ALTER TABLE asistencias RENAME TO asistencias_old;
                    CREATE TABLE asistencias (
                        id              INTEGER PRIMARY KEY AUTOINCREMENT,
                        persona_id      INTEGER REFERENCES personas(id),
                        capacitacion_id INTEGER REFERENCES capacitaciones(id),
                        hora_registro   TEXT DEFAULT (datetime('now','localtime')),
                        fecha_dia       TEXT DEFAULT (date('now','localtime')),
                        UNIQUE(persona_id, capacitacion_id, fecha_dia)
                    );
                    INSERT INTO asistencias (id, persona_id, capacitacion_id, hora_registro, fecha_dia)
                    SELECT id, persona_id, capacitacion_id, hora_registro,
                            substr(hora_registro, 1, 10)
                    FROM asistencias_old;
                    DROP TABLE asistencias_old;
                """)
        except Exception as e:
            print(f"⚠ Migración asistencias: {e}")

        # Usuario admin por defecto
        row = con.execute("SELECT id FROM usuarios WHERE username='admin'").fetchone()
        if not row:
            h = bcrypt.hashpw("camara26*".encode(), bcrypt.gensalt()).decode()
            con.execute(
                "INSERT INTO usuarios (username, password_hash, rol) VALUES (?,?,?)",
                ("admin", h, "admin"))
            con.commit()

# ─────────────────────────────────────────────
#  CONFIGURACIÓN CLAVE-VALOR
# ─────────────────────────────────────────────
def config_get(clave: str, default=None):
    with sqlite3.connect(DB_PATH) as con:
        row = con.execute("SELECT valor FROM config WHERE clave=?", (clave,)).fetchone()
    return row[0] if row else default

def config_set(clave: str, valor: str):
    with sqlite3.connect(DB_PATH) as con:
        con.execute("INSERT OR REPLACE INTO config (clave, valor) VALUES (?,?)",
                    (clave, valor))
        con.commit()

# ─────────────────────────────────────────────
#  LOGS
# ─────────────────────────────────────────────
def log(accion: str, detalle: str = "", nivel: str = "INFO"):
    try:
        with sqlite3.connect(DB_PATH) as con:
            con.execute(
                "INSERT INTO logs (usuario, accion, detalle, nivel) VALUES (?,?,?,?)",
                (_session_user, accion, detalle, nivel))
    except Exception:
        pass

# ─────────────────────────────────────────────
#  AUTENTICACIÓN
# ─────────────────────────────────────────────
def verificar_login(username: str, password: str):
    with sqlite3.connect(DB_PATH) as con:
        row = con.execute(
            "SELECT password_hash, rol, activo FROM usuarios WHERE username=?",
            (username,)).fetchone()
    if not row:
        return None, None
    h, rol, activo = row
    if not activo:
        return None, None
    if bcrypt.checkpw(password.encode(), h.encode()):
        return username, rol
    return None, None