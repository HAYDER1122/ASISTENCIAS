"""
ui.py — Interfaz gráfica — Tema Corporativo Azul Oscuro 2026
Fixes aplicados:
- App ahora es tk.Toplevel (no tk.Tk) → permite loop login/logout en main.py
- _logout() pone _pedir_logout=True antes de destroy → main.py abre login de nuevo
- VentanaUsuarios: botón "Eliminar Usuario" añadido
- FIX CRÍTICO: uso de queue.Queue para comunicación hilo→tkinter (Python 3.13 compatible)
  self.after() y winfo_exists() NO pueden llamarse desde hilos secundarios en Python 3.13
- Resto de funcionalidad sin cambios
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import os
import shutil
import datetime
import threading
import queue
import bcrypt

from config import C, DB_PATH, PLANTILLA_DIR, NUM_CAPTURAS
from db import (verificar_login, set_session_user, log,
                config_get, config_set)
from vista import (capturar_embedding_multi, reconocer_cara,get_all_embeddings, persona_ya_existe,rebuild_faiss_index, cerrar_camara)
from exports import exportar_pdf


# ─────────────────────────────────────────────
#  SONIDO DE FEEDBACK
# ─────────────────────────────────────────────
def _beep(exitoso: bool):
    try:
        import winsound
        if exitoso:
            winsound.Beep(880, 150)
            winsound.Beep(1100, 150)
        else:
            winsound.Beep(400, 200)
    except ImportError:
        try:
            import subprocess
            if exitoso:
                subprocess.Popen(
                    ["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.Popen(
                    ["paplay", "/usr/share/sounds/freedesktop/stereo/dialog-warning.oga"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
    except Exception:
        pass


# ─────────────────────────────────────────────
#  HELPERS UI
# ─────────────────────────────────────────────
def _entry(parent, width=32, show=None, **kw):
    e = tk.Entry(parent,
                bg=C["white"], fg=C["text"],
                insertbackground=C["primary"],
                relief="flat", bd=0, font=("Segoe UI", 10),
                highlightthickness=1,
                highlightcolor=C["primary"],
                highlightbackground=C["border"],
                width=width, **kw)
    if show:
        e.config(show=show)
    return e


def _btn(parent, text, command, bg=None, fg=None, pad_x=18, pad_y=9):
    bg = bg or C["primary"]
    fg = fg or C["white"]
    hover = C["primary_h"] if bg == C["primary"] else bg
    b = tk.Button(parent, text=text, command=command,
                font=("Segoe UI", 10, "bold"),
                bg=bg, fg=fg,
                activebackground=hover,
                activeforeground=fg,
                relief="flat", bd=0,
                padx=pad_x, pady=pad_y,
                cursor="hand2")
    b.bind("<Enter>", lambda e, b=b, h=hover: b.config(bg=h))
    b.bind("<Leave>", lambda e, b=b, o=bg:    b.config(bg=o))
    return b


def _sep(parent, bg=None):
    return tk.Frame(parent, bg=bg or C["border"], height=1)


# ─────────────────────────────────────────────
#  VENTANA LOGIN
# ─────────────────────────────────────────────
class VentanaLogin(tk.Toplevel):
    def __init__(self, root):
        super().__init__(root)
        self.title("Iniciar Sesión")
        self.resizable(False, False)
        self.configure(bg=C["sidebar"])
        self.resultado = None
        ancho, alto = 420, 500
        self.withdraw()
        self.update_idletasks()

        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x  = (sw - ancho) // 2
        y  = (sh - alto)  // 2
        self.geometry(f"{ancho}x{alto}+{x}+{y}")
        self.deiconify()

        try:
            import os as _os, sys as _sys
            _base = _sys._MEIPASS if getattr(_sys, "frozen", False) else \
                    _os.path.dirname(_os.path.abspath(__file__))
            _ico = _os.path.join(_base, "Logo.ico")
            root.iconbitmap(_ico)
            self.iconbitmap(_ico)
        except Exception:
            pass

        self.grab_set()
        self._build()
        self.protocol("WM_DELETE_WINDOW", self._cerrar)

    def _cerrar(self):
        self.resultado = None
        self.destroy()

    def _build(self):
        logo_fr = tk.Frame(self, bg=C["sidebar"])
        logo_fr.pack(fill="x", pady=(28, 8))

        icon_box = tk.Frame(logo_fr, bg=C["primary"], width=56, height=56)
        icon_box.pack()
        icon_box.pack_propagate(False)
        tk.Label(icon_box, text="🎓", font=("Segoe UI", 26),
                 fg=C["white"], bg=C["primary"]).place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(logo_fr, text="SISTEMA DE ASISTENCIAS",
                 font=("Segoe UI", 13, "bold"),
                 fg=C["white"], bg=C["sidebar"]).pack(pady=(12, 2))
        tk.Label(logo_fr, text="Control de Capacitaciones",
                 font=("Segoe UI", 9), fg="#4A6090", bg=C["sidebar"]).pack(pady=(2, 0))

        card = tk.Frame(self, bg="#1A2B4A", padx=32, pady=24)
        card.pack(fill="x", padx=32, pady=(20, 0))

        tk.Label(card, text="Usuario", font=("Segoe UI", 9, "bold"),
                 fg="#7A90B8", bg="#1A2B4A", anchor="w").pack(fill="x", pady=(0, 4))
        self.ent_user = _entry(card, width=28)
        self.ent_user.pack(fill="x", ipady=8)

        tk.Label(card, text="Contraseña", font=("Segoe UI", 9, "bold"),
                 fg="#7A90B8", bg="#1A2B4A", anchor="w").pack(fill="x", pady=(14, 4))

        pass_fr = tk.Frame(card, bg="#1A2B4A")
        pass_fr.pack(fill="x")
        self.ent_pass = _entry(pass_fr, width=24, show="•")
        self.ent_pass.pack(side="left", fill="x", expand=True, ipady=8)

        self._pass_visible = False

        def _toggle_pass():
            self._pass_visible = not self._pass_visible
            self.ent_pass.config(show="" if self._pass_visible else "•")
            btn_ojo.config(text="🙈" if self._pass_visible else "👁")

        btn_ojo = tk.Button(pass_fr, text="👁", command=_toggle_pass,
                            font=("Segoe UI", 11),
                            bg="#1A2B4A", fg="#7A90B8",
                            activebackground="#1A2B4A", activeforeground=C["white"],
                            relief="flat", bd=0, cursor="hand2", padx=6)
        btn_ojo.pack(side="left", ipady=8)

        self.lbl_error = tk.Label(card, text="", font=("Segoe UI", 9),
                                  fg="#FF6B6B", bg="#1A2B4A")
        self.lbl_error.pack(pady=(8, 0))

        tk.Button(card, text="  Iniciar Sesión  →", command=self._login,
                  font=("Segoe UI", 11, "bold"),
                  bg=C["primary"], fg=C["white"],
                  activebackground=C["primary_h"], activeforeground=C["white"],
                  relief="flat", bd=0, pady=12, cursor="hand2").pack(fill="x", pady=(16, 0))

        self.ent_user.focus()
        self.ent_pass.bind("<Return>", lambda e: self._login())
        self.ent_user.bind("<Return>", lambda e: self.ent_pass.focus())

    def _login(self):
        user = self.ent_user.get().strip()
        pwd  = self.ent_pass.get()
        if not user or not pwd:
            self.lbl_error.config(text="Completa usuario y contraseña.")
            return
        username, rol = verificar_login(user, pwd)
        if username:
            set_session_user(username)
            log("LOGIN", f"Usuario '{username}' inició sesión", "INFO")
            self.resultado = (username, rol)
            self.destroy()
        else:
            self.lbl_error.config(text="❌  Usuario o contraseña incorrectos.")
            log("LOGIN_FAIL", f"Intento fallido para '{user}'", "WARNING")
            self.ent_pass.delete(0, "end")


# ─────────────────────────────────────────────
#  VENTANA CRUD PERSONAS
# ─────────────────────────────────────────────
class VentanaPersonas(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Gestión de Personas")
        self.geometry("820x640")
        self.resizable(False, False)
        self.configure(bg=C["bg"])
        self.grab_set()
        self._build()
        self._cargar()

    def _build(self):
        top = tk.Frame(self, bg=C["sidebar"])
        top.pack(fill="x")
        tk.Frame(top, bg=C["primary"], width=4).pack(side="left", fill="y")
        tk.Label(top, text="  👥  Gestión de Personas Registradas",
                 font=("Segoe UI", 12, "bold"),
                 fg=C["white"], bg=C["sidebar"], pady=14).pack(side="left")

        btn_fr = tk.Frame(self, bg=C["bg"], pady=10)
        btn_fr.pack(side="bottom", fill="x", padx=20)
        _btn(btn_fr, "✏️  Editar",
             self._editar, C["primary"], pad_x=14).pack(side="left", padx=(0, 8))
        self.btn_toggle = _btn(btn_fr, "⛔  Desactivar",
                               self._toggle_activo, C["warning"], pad_x=14)
        self.btn_toggle.pack(side="left", padx=(0, 8))
        _btn(btn_fr, "🗑️  Eliminar",
             self._eliminar, C["danger"], pad_x=14).pack(side="left")
        _btn(btn_fr, "🔄  Actualizar",
             self._cargar, C["border2"], fg=C["text2"], pad_x=14).pack(side="right")

        body = tk.Frame(self, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=20, pady=(12, 4))

        buscar_fr = tk.Frame(body, bg=C["bg"])
        buscar_fr.pack(fill="x", pady=(0, 8))
        tk.Label(buscar_fr, text="🔍", font=("Segoe UI", 11),
                 fg=C["text2"], bg=C["bg"]).pack(side="left", padx=(0, 6))
        self.ent_buscar = _entry(buscar_fr, width=30)
        self.ent_buscar.pack(side="left", fill="x", expand=True, ipady=5)
        self.ent_buscar.bind("<KeyRelease>", lambda e: self._cargar())
        _btn(buscar_fr, "✖",
             lambda: (self.ent_buscar.delete(0, "end"), self._cargar()),
             C["border2"], fg=C["text2"], pad_x=8, pad_y=5).pack(side="left", padx=(6, 0))

        filtro_fr = tk.Frame(body, bg=C["bg"])
        filtro_fr.pack(fill="x", pady=(0, 10))
        tk.Label(filtro_fr, text="Filtrar:", font=("Segoe UI", 9, "bold"),
                 fg=C["text2"], bg=C["bg"]).pack(side="left", padx=(0, 10))
        self._filtro = tk.StringVar(value="todos")
        for val, txt in [("todos", "Todos"),
                         ("activos", "Solo activos"),
                         ("inactivos", "Solo inactivos")]:
            tk.Radiobutton(filtro_fr, text=txt, variable=self._filtro, value=val,
                           command=self._cargar, font=("Segoe UI", 9),
                           fg=C["text2"], bg=C["bg"],
                           selectcolor=C["primary_l"],
                           activebackground=C["bg"],
                           activeforeground=C["primary"]).pack(side="left", padx=8)

        style = ttk.Style()
        style.configure("Corp.Treeview",
                         background=C["white"], foreground=C["text"],
                         fieldbackground=C["white"], rowheight=32,
                         font=("Segoe UI", 9), borderwidth=0)
        style.configure("Corp.Treeview.Heading",
                         background=C["sidebar"], foreground=C["white"],
                         font=("Segoe UI", 9, "bold"), relief="raised", padding=10)
        style.map("Corp.Treeview",
                  background=[("selected", C["primary"]), ("active", C["primary_l"])],
                  foreground=[("selected", C["white"]),   ("active", C["primary"])])

        tree_fr = tk.Frame(body, bg=C["border"], bd=1)
        tree_fr.pack(fill="both", expand=True)
        inner = tk.Frame(tree_fr, bg=C["white"])
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        cols = ("ID", "Estado", "Nombre", "Apellido", "Cargo", "Registrado")
        self.tree = ttk.Treeview(inner, columns=cols, show="headings",
                                 selectmode="browse", style="Corp.Treeview", height=13)
        for col, ancho in zip(cols, [38, 90, 150, 150, 150, 200]):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=ancho,
                             anchor="center" if col in ("ID", "Estado") else "w")

        self.tree.tag_configure("activo_par",     background=C["primary_l"], foreground=C["text"])
        self.tree.tag_configure("activo_impar",   background=C["white"],     foreground=C["text"])
        self.tree.tag_configure("inactivo_par",   background="#FFF5F5",      foreground="#9CA3AF")
        self.tree.tag_configure("inactivo_impar", background=C["white"],     foreground="#9CA3AF")

        sc = ttk.Scrollbar(inner, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sc.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sc.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def _on_select(self, _e):
        sel = self.tree.selection()
        if not sel:
            return
        with sqlite3.connect(DB_PATH) as con:
            row = con.execute("SELECT activo FROM personas WHERE id=?", (int(sel[0]),)).fetchone()
        if not row:
            return
        self.btn_toggle.config(
            text="⛔  Desactivar" if row[0] else "✅  Activar",
            bg=C["warning"] if row[0] else C["success"])

    def _cargar(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        buscar = self.ent_buscar.get().strip().lower() if hasattr(self, "ent_buscar") else ""
        filtro = self._filtro.get()
        where  = "" if filtro == "todos" else f" WHERE activo={'1' if filtro == 'activos' else '0'}"
        with sqlite3.connect(DB_PATH) as con:
            rows = con.execute(
                f"SELECT id,nombre,apellido,cargo,activo,creado_en "
                f"FROM personas{where} ORDER BY nombre,apellido").fetchall()
        if buscar:
            rows = [r for r in rows
                    if buscar in r[1].lower()
                    or buscar in r[2].lower()
                    or (r[3] and buscar in r[3].lower())]
        for i, (pid, nombre, apellido, cargo, activo, creado) in enumerate(rows):
            estado = "● Activo" if activo else "○ Inactivo"
            base   = "activo" if activo else "inactivo"
            tag    = f"{base}_par" if i % 2 == 0 else f"{base}_impar"
            self.tree.insert("", "end", iid=str(pid), tags=(tag,),
                             values=(pid, estado, nombre, apellido,
                                     cargo or "—",
                                     creado[:16] if creado else ""))

    def _get_sel(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Sin selección", "Selecciona una persona.", parent=self)
            return None
        return int(sel[0])

    def _editar(self):
        pid = self._get_sel()
        if pid is None:
            return
        with sqlite3.connect(DB_PATH) as con:
            row = con.execute("SELECT nombre,apellido,cargo FROM personas WHERE id=?", (pid,)).fetchone()
        if not row:
            return
        win = tk.Toplevel(self)
        win.title("Editar Persona")
        win.geometry("420x340")
        win.resizable(False, False)
        win.configure(bg=C["bg"])
        win.grab_set()
        hdr = tk.Frame(win, bg=C["sidebar"])
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=C["primary"], width=4).pack(side="left", fill="y")
        tk.Label(hdr, text="  ✏️  Editar datos del Trabajador",
                 font=("Segoe UI", 11, "bold"), fg=C["white"], bg=C["sidebar"], pady=12).pack(side="left")
        form_fr = tk.Frame(win, bg=C["bg"])
        form_fr.pack(fill="both", expand=True, padx=24, pady=16)
        entradas = []
        for lbl, val in [("Nombre *", row[0]), ("Apellido *", row[1]), ("Cargo", row[2] or "")]:
            tk.Label(form_fr, text=lbl, font=("Segoe UI", 9), fg=C["text2"],
                     bg=C["bg"], anchor="w").pack(fill="x", pady=(8, 2))
            ent = _entry(form_fr, width=40)
            ent.insert(0, val)
            ent.pack(fill="x", ipady=6)
            entradas.append(ent)

        def guardar():
            n, a, c = [x.get().strip() for x in entradas]
            if not n or not a:
                messagebox.showwarning("Requerido", "Nombre y Apellido son obligatorios.", parent=win)
                return
            try:
                with sqlite3.connect(DB_PATH) as con:
                    con.execute("UPDATE personas SET nombre=?,apellido=?,cargo=? WHERE id=?",
                                (n, a, c or None, pid))
                log("EDITAR_PERSONA", f"ID={pid} actualizado a '{n} {a}'")
                win.destroy()
                self._cargar()
                messagebox.showinfo("✅ Actualizado", f"{n} {a} actualizado.", parent=self)
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=win)

        _btn(form_fr, "💾  Guardar cambios", guardar).pack(fill="x", pady=(16, 0), ipady=4)

    def _toggle_activo(self):
        pid = self._get_sel()
        if pid is None:
            return
        with sqlite3.connect(DB_PATH) as con:
            row = con.execute("SELECT nombre||' '||apellido, activo FROM personas WHERE id=?", (pid,)).fetchone()
        if not row:
            return
        nombre, activo = row
        if activo and not messagebox.askyesno("Desactivar", f"¿Desactivar a {nombre}?", parent=self):
            return
        nuevo = 0 if activo else 1
        with sqlite3.connect(DB_PATH) as con:
            con.execute("UPDATE personas SET activo=? WHERE id=?", (nuevo, pid))
        log("DESACTIVAR_PERSONA" if nuevo == 0 else "ACTIVAR_PERSONA", f"'{nombre}' ID={pid}")
        rebuild_faiss_index()
        self._cargar()

    def _eliminar(self):
        pid = self._get_sel()
        if pid is None:
            return
        with sqlite3.connect(DB_PATH) as con:
            row   = con.execute("SELECT nombre||' '||apellido FROM personas WHERE id=?", (pid,)).fetchone()
            asist = con.execute("SELECT COUNT(*) FROM asistencias WHERE persona_id=?", (pid,)).fetchone()[0]
        nombre = row[0] if row else "esta persona"

        if asist > 0:
            msg = (f"⚠️  ADVERTENCIA\n\n"
                   f"'{nombre}' tiene {asist} asistencia(s) registrada(s).\n\n"
                   f"Si eliminas esta persona, sus registros de asistencia\n"
                   f"también serán eliminados permanentemente.\n\n"
                   f"¿Estás seguro de que deseas eliminar a '{nombre}'\n"
                   f"junto con todas sus asistencias?")
            if not messagebox.askyesno("⚠️  Confirmar eliminación permanente", msg, parent=self):
                return
            with sqlite3.connect(DB_PATH) as con:
                con.execute("DELETE FROM asistencias WHERE persona_id=?", (pid,))
                con.execute("DELETE FROM personas WHERE id=?", (pid,))
            log("ELIMINAR_PERSONA", f"'{nombre}' ID={pid} eliminado con {asist} asistencias", "WARNING")
        else:
            if not messagebox.askyesno(
                    "Confirmar eliminación",
                    f"¿Eliminar permanentemente a '{nombre}'?\n\n"
                    f"(No tiene asistencias registradas.)",
                    parent=self):
                return
            with sqlite3.connect(DB_PATH) as con:
                con.execute("DELETE FROM personas WHERE id=?", (pid,))
            log("ELIMINAR_PERSONA", f"'{nombre}' ID={pid} eliminado (sin asistencias)", "WARNING")

        rebuild_faiss_index()
        self._cargar()
        messagebox.showinfo("Eliminado", f"'{nombre}' fue eliminado del sistema.", parent=self)


# ─────────────────────────────────────────────
#  VENTANA GESTIÓN DE USUARIOS
# ─────────────────────────────────────────────
class VentanaUsuarios(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Gestión de Usuarios del Sistema")
        self.geometry("700x480")
        self.resizable(False, False)
        self.configure(bg=C["bg"])
        self.grab_set()
        self._build()
        self._cargar()

    def _build(self):
        top = tk.Frame(self, bg=C["sidebar"])
        top.pack(fill="x")
        tk.Frame(top, bg=C["primary"], width=4).pack(side="left", fill="y")
        tk.Label(top, text="  🔐  Usuarios del Sistema",
                 font=("Segoe UI", 12, "bold"), fg=C["white"], bg=C["sidebar"], pady=14).pack(side="left")

        body = tk.Frame(self, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=20, pady=12)

        style = ttk.Style()
        style.configure("User.Treeview", background=C["white"], foreground=C["text"],
                         fieldbackground=C["white"], rowheight=32, font=("Segoe UI", 9), borderwidth=0)
        style.configure("User.Treeview.Heading", background=C["sidebar"], foreground=C["white"],
                         font=("Segoe UI", 9, "bold"), relief="raised", padding=10)
        style.map("User.Treeview",
                  background=[("selected", C["primary"]),  ("active", C["primary_l"])],
                  foreground=[("selected", C["white"]),     ("active", C["primary"])])

        tree_fr = tk.Frame(body, bg=C["border"], bd=1)
        tree_fr.pack(fill="both", expand=True)
        inner = tk.Frame(tree_fr, bg=C["white"])
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        cols = ("ID", "Usuario", "Rol", "Estado", "Creado")
        self.tree = ttk.Treeview(inner, columns=cols, show="headings", selectmode="browse",
                                 style="User.Treeview", height=10)
        for col, w in zip(cols, [40, 160, 100, 90, 140]):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center" if col in ("ID", "Estado") else "w")
        sc = ttk.Scrollbar(inner, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sc.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sc.pack(side="right", fill="y")

        bot = tk.Frame(self, bg=C["bg"])
        bot.pack(fill="x", padx=20, pady=8)
        _btn(bot, "➕  Nuevo",      self._nuevo_usuario, C["success"],  pad_x=12).pack(side="left", padx=(0, 6))
        _btn(bot, "🔑  Contraseña", self._cambiar_pass,  C["primary"],  pad_x=12).pack(side="left", padx=(0, 6))
        _btn(bot, "⛔  Act/Desact", self._toggle,        C["warning"],  pad_x=12).pack(side="left", padx=(0, 6))
        _btn(bot, "🗑️  Eliminar",   self._eliminar,      C["danger"],   pad_x=12).pack(side="left")
        _btn(bot, "🔄",             self._cargar,        C["border2"], fg=C["text2"], pad_x=8).pack(side="right")

    def _cargar(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        with sqlite3.connect(DB_PATH) as con:
            rows = con.execute("SELECT id,username,rol,activo,creado_en FROM usuarios ORDER BY id").fetchall()
        for uid, username, rol, activo, creado in rows:
            self.tree.insert("", "end", iid=str(uid),
                             values=(uid, username, rol,
                                     "● Activo" if activo else "○ Inactivo",
                                     creado[:16] if creado else ""))

    def _get_sel(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Sin selección", "Selecciona un usuario.", parent=self)
            return None
        return int(sel[0])

    def _nuevo_usuario(self):
        win = tk.Toplevel(self)
        win.title("Nuevo Usuario")
        win.geometry("380x340")
        win.resizable(False, False)
        win.configure(bg=C["bg"])
        win.grab_set()
        hdr = tk.Frame(win, bg=C["sidebar"])
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=C["primary"], width=4).pack(side="left", fill="y")
        tk.Label(hdr, text="  ➕  Crear nuevo usuario",
                 font=("Segoe UI", 11, "bold"), fg=C["white"], bg=C["sidebar"], pady=12).pack(side="left")
        fr = tk.Frame(win, bg=C["bg"])
        fr.pack(fill="both", expand=True, padx=24, pady=16)

        def lf(t):
            tk.Label(fr, text=t, font=("Segoe UI", 9), fg=C["text2"],
                     bg=C["bg"], anchor="w").pack(fill="x", pady=(8, 2))

        lf("Usuario *")
        ent_u = _entry(fr, width=36)
        ent_u.pack(fill="x", ipady=6)
        lf("Contraseña *")
        ent_p = _entry(fr, width=36, show="•")
        ent_p.pack(fill="x", ipady=6)
        lf("Rol")
        rol_var = tk.StringVar(value="operador")
        rol_fr  = tk.Frame(fr, bg=C["bg"])
        rol_fr.pack(anchor="w", pady=(4, 0))
        for r in ("admin", "operador"):
            tk.Radiobutton(rol_fr, text=r.capitalize(), variable=rol_var, value=r,
                           font=("Segoe UI", 9), fg=C["text2"], bg=C["bg"],
                           selectcolor=C["primary_l"],
                           activebackground=C["bg"]).pack(side="left", padx=(0, 16))

        def crear():
            u = ent_u.get().strip()
            p = ent_p.get()
            if not u or not p:
                messagebox.showwarning("Requerido", "Usuario y contraseña requeridos.", parent=win)
                return
            if len(p) < 6:
                messagebox.showwarning("Contraseña débil", "Mínimo 6 caracteres.", parent=win)
                return
            h = bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()
            try:
                with sqlite3.connect(DB_PATH) as con:
                    con.execute("INSERT INTO usuarios (username,password_hash,rol) VALUES (?,?,?)",
                                (u, h, rol_var.get()))
                log("CREAR_USUARIO", f"Usuario '{u}' creado con rol '{rol_var.get()}'")
                win.destroy()
                self._cargar()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Ese nombre de usuario ya existe.", parent=win)

        _btn(fr, "💾  Crear usuario", crear, C["success"]).pack(fill="x", pady=(14, 0), ipady=4)

    def _cambiar_pass(self):
        uid = self._get_sel()
        if uid is None:
            return
        with sqlite3.connect(DB_PATH) as con:
            row = con.execute("SELECT username FROM usuarios WHERE id=?", (uid,)).fetchone()
        if not row:
            return
        username = row[0]
        win = tk.Toplevel(self)
        win.title("Cambiar Contraseña")
        win.geometry("340x240")
        win.resizable(False, False)
        win.configure(bg=C["bg"])
        win.grab_set()
        hdr = tk.Frame(win, bg=C["sidebar"])
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=C["primary"], width=4).pack(side="left", fill="y")
        tk.Label(hdr, text=f"  🔑  Cambiar contraseña: {username}",
                 font=("Segoe UI", 11, "bold"), fg=C["white"], bg=C["sidebar"], pady=12).pack(side="left")
        fr = tk.Frame(win, bg=C["bg"])
        fr.pack(fill="both", expand=True, padx=24, pady=16)
        tk.Label(fr, text="Nueva contraseña *", font=("Segoe UI", 9), fg=C["text2"],
                 bg=C["bg"], anchor="w").pack(fill="x", pady=(8, 2))
        ent_p = _entry(fr, width=36, show="•")
        ent_p.pack(fill="x", ipady=6)
        tk.Label(fr, text="Repetir contraseña *", font=("Segoe UI", 9), fg=C["text2"],
                 bg=C["bg"], anchor="w").pack(fill="x", pady=(8, 2))
        ent_p2 = _entry(fr, width=36, show="•")
        ent_p2.pack(fill="x", ipady=6)

        def cambiar():
            p1 = ent_p.get()
            p2 = ent_p2.get()
            if not p1:
                messagebox.showwarning("Requerido", "Ingresa la contraseña.", parent=win)
                return
            if p1 != p2:
                messagebox.showwarning("Error", "Las contraseñas no coinciden.", parent=win)
                return
            if len(p1) < 6:
                messagebox.showwarning("Débil", "Mínimo 6 caracteres.", parent=win)
                return
            h = bcrypt.hashpw(p1.encode(), bcrypt.gensalt()).decode()
            with sqlite3.connect(DB_PATH) as con:
                con.execute("UPDATE usuarios SET password_hash=? WHERE id=?", (h, uid))
            log("CAMBIAR_CONTRASEÑA", f"Contraseña de '{username}' actualizada")
            win.destroy()
            messagebox.showinfo("✅ Actualizado", "Contraseña cambiada.", parent=self)

        _btn(fr, "💾  Guardar", cambiar, C["primary"]).pack(fill="x", pady=(12, 0), ipady=4)

    def _toggle(self):
        uid = self._get_sel()
        if uid is None:
            return
        with sqlite3.connect(DB_PATH) as con:
            row = con.execute("SELECT username,activo FROM usuarios WHERE id=?", (uid,)).fetchone()
        if not row:
            return
        username, activo = row
        if username == "admin" and activo:
            messagebox.showwarning("Protegido",
                                   "No se puede desactivar al usuario 'admin'.", parent=self)
            return
        nuevo = 0 if activo else 1
        with sqlite3.connect(DB_PATH) as con:
            con.execute("UPDATE usuarios SET activo=? WHERE id=?", (nuevo, uid))
        log("DESACTIVAR_USUARIO" if nuevo == 0 else "ACTIVAR_USUARIO", f"Usuario '{username}'")
        self._cargar()

    def _eliminar(self):
        uid = self._get_sel()
        if uid is None:
            return
        with sqlite3.connect(DB_PATH) as con:
            row = con.execute("SELECT username FROM usuarios WHERE id=?", (uid,)).fetchone()
        if not row:
            return
        username = row[0]
        if username == "admin":
            messagebox.showwarning("Protegido",
                                   "No se puede eliminar al usuario 'admin'.", parent=self)
            return
        if not messagebox.askyesno(
                "Confirmar eliminación",
                f"¿Eliminar permanentemente al usuario '{username}'?\n\n"
                f"Esta acción no se puede deshacer.",
                parent=self):
            return
        with sqlite3.connect(DB_PATH) as con:
            con.execute("DELETE FROM usuarios WHERE id=?", (uid,))
        log("ELIMINAR_USUARIO", f"Usuario '{username}' eliminado", "WARNING")
        self._cargar()
        messagebox.showinfo("Eliminado", f"Usuario '{username}' eliminado.", parent=self)


# ─────────────────────────────────────────────
#  VENTANA PRINCIPAL  —  ahora es tk.Toplevel
# ─────────────────────────────────────────────
class App(tk.Toplevel):
    """
    Ventana principal del sistema.
    Es tk.Toplevel (no tk.Tk) para que main.py pueda hacer
    root.wait_window(app) y reabrir el login tras el logout.
    """

    def __init__(self, root, username, rol):
        super().__init__(root)
        self._username      = username
        self._rol           = rol
        self._camara_activa = False
        self._pedir_logout  = False

        # ── FIX: cola thread-safe para recibir resultados de hilos de cámara ──
        self._resultado_queue = queue.Queue()

        import os as _os, sys as _sys
        _base = _sys._MEIPASS if getattr(_sys, "frozen", False) else \
                _os.path.dirname(_os.path.abspath(__file__))
        self._logo_path = _os.path.join(_base, "Logo.ico")

        try:
            self.iconbitmap(self._logo_path)
        except Exception:
            pass

        _style = ttk.Style(self)
        _style.theme_use("clam")
        self.configure(bg=C["sidebar"])

        self.title("Sistema de Asistencias a Capacitaciones")
        self.state("zoomed")
        self.minsize(980, 620)
        self._frames = {}
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._confirmar_salida)

        self._TIMEOUT_MS    = 10 * 60 * 1000
        self._ultimo_evento = datetime.datetime.now()
        self.bind_all("<Any-KeyPress>",    self._resetear_timeout)
        self.bind_all("<Any-ButtonPress>", self._resetear_timeout)
        self._check_timeout()

        # ── FIX: iniciar el procesador de cola en el hilo principal ──
        self._procesar_queue()

    # ─────────────────────────────────────────
    #  FIX: PROCESADOR DE COLA (hilo principal)
    # ─────────────────────────────────────────
    def _procesar_queue(self):
        """
        Corre cada 100ms en el hilo principal de tkinter.
        Procesa resultados enviados por los hilos de cámara via queue.
        NUNCA llames self.after() o self.winfo_exists() desde un hilo secundario
        en Python 3.13 — usa esta cola en su lugar.
        """
        try:
            while True:
                tipo, datos = self._resultado_queue.get_nowait()
                if tipo == "registro":
                    emb, nombre, apellido, cargo, n_capturas = datos
                    self._finalizar_registro(emb, nombre, apellido, cargo, n_capturas)
                elif tipo == "asistencia":
                    ids_registrados, sel = datos
                    self._finalizar_asistencia(ids_registrados, sel)
                elif tipo == "modelo_listo":
                    self._btn_capturar.config(
                        state="normal",
                        text="📷   Capturar y Registrar",
                        bg=C["primary"], fg=C["white"], cursor="hand2")
                    self.btn_registrar_asistencia.config(
                        state="normal",
                        text="🎯\n\nRegistrar Asistencia\n",
                        bg=C["primary"], fg=C["white"], cursor="hand2")

                elif tipo == "diagnostico":
                    try:
                        txt = getattr(self, "_txt_diagnostico", None)
                        if txt is not None and txt.winfo_exists():
                            txt.config(state="normal")
                            txt.delete("1.0", "end")
                            txt.insert("end", datos)
                            txt.see("end")
                    except Exception as e:
                        print("Error UI diagnóstico:", e)
                

        except queue.Empty:
            pass
        except Exception as e:
            print(f"[ERROR] _procesar_queue: {e}")
        # Reprogramar solo si la ventana sigue viva
        try:
            self.after(100, self._procesar_queue)
        except Exception:
            pass

    # ── Timeout de inactividad ────────────────
    def _resetear_timeout(self, event=None):
        self._ultimo_evento = datetime.datetime.now()

    def _check_timeout(self):
        if not self.winfo_exists():
            return
        if self._camara_activa:
            self.after(30_000, self._check_timeout)
            return
        inactivo_s = (datetime.datetime.now() - self._ultimo_evento).total_seconds()
        if inactivo_s * 1000 >= self._TIMEOUT_MS:
            log("TIMEOUT", f"Sesión de '{self._username}' cerrada por inactividad")
            cerrar_camara()
            self._pedir_logout = True
            self.destroy()
        else:
            self.after(30_000, self._check_timeout)

    # ── Logout y salida ───────────────────────
    def _logout(self):
        log("LOGOUT", f"Usuario '{self._username}' cerró sesión")
        cerrar_camara()
        self._pedir_logout = True
        self.destroy()

    def _confirmar_salida(self):
        if messagebox.askyesno(
                "¿Salir del sistema?",
                "¿Seguro que quieres cerrar el Sistema de Asistencias?\n\n"
                "Asegúrate de haber registrado todas las asistencias."):
            log("SALIDA", f"Usuario '{self._username}' cerró la aplicación")
            cerrar_camara()
            self.destroy()

    def _iniciar_faiss(self):
        ok = rebuild_faiss_index()
        if ok:
            log("FAISS", "Índice facial construido al iniciar", "INFO")
        # Esperar modelo en hilo separado y deshabilitar botones hasta que esté listo
        self._btn_capturar.config(state="disabled", text="⏳  Cargando modelo...")
        self.btn_registrar_asistencia.config(state="disabled", text="⏳\n\nCargando modelo...\n")
        threading.Thread(target=self._esperar_modelo_listo, daemon=True).start()

    def _esperar_modelo_listo(self):
        from vista import _modelo_evento
        print(">>> _esperar_modelo_listo iniciado")
        _modelo_evento.wait(timeout=30)
        print(">>> _esperar_modelo_listo terminado, poniendo en queue")
        self._resultado_queue.put(("modelo_listo", None))


    # ── Construcción de la UI ─────────────────
    def _build_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        sidebar = tk.Frame(self, bg=C["sidebar"], width=C["sidebar_w"])
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.grid_propagate(False)

        tk.Frame(sidebar, bg=C["primary"], height=4).pack(fill="x")

        logo_inner = tk.Frame(sidebar, bg=C["sidebar"])
        logo_inner.pack(fill="x", pady=(18, 16), padx=16)
        try:
            from PIL import Image, ImageTk
            _ico_top = Image.open(self._logo_path)
            _ico_top = _ico_top.resize((52, 52), Image.LANCZOS)
            self._logo_top_img = ImageTk.PhotoImage(_ico_top)
            tk.Label(logo_inner, image=self._logo_top_img,
                     bg=C["sidebar"]).pack()
        except Exception:
            icon_box = tk.Frame(logo_inner, bg=C["primary"], width=44, height=44)
            icon_box.pack()
            icon_box.pack_propagate(False)
            tk.Label(icon_box, text="🎓", font=("Segoe UI", 20),
                     fg=C["white"], bg=C["primary"]).place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(logo_inner, text="ASISTENCIAS",
                 font=("Segoe UI", 11, "bold"), fg=C["white"], bg=C["sidebar"]).pack(pady=(10, 2))
        tk.Label(logo_inner, text="Sistema de Control",
                 font=("Segoe UI", 8), fg="#4A6090", bg=C["sidebar"]).pack()

        tk.Frame(sidebar, bg="#1E2E4A", height=1).pack(fill="x", padx=16)

        def _nav_section(text):
            tk.Label(sidebar, text=text,
                     font=("Segoe UI", 7, "bold"), fg="#374E7A",
                     bg=C["sidebar"], anchor="w", padx=20).pack(fill="x", pady=(10, 2))

        nav_items = [
            ("dashboard",      "📊", "Dashboard"),
            ("registro",       "👤", "Registrar Persona"),
            ("capacitaciones", "📋", "Capacitaciones"),
            ("asistencia",     "✅", "Asistencia"),
            ("admin",          "⚙️", "Gestión"),
        ]
        if self._rol == "admin":
            nav_items.append(("logs", "📜", "Logs del Sistema"))

        _nav_section("PRINCIPAL")
        self._nav_btns = {}
        for key, icon, label in nav_items:
            if key == "logs":
                _nav_section("SISTEMA")
            btn = self._make_nav_btn(sidebar, icon, label, key)
            btn.pack(fill="x", padx=10, pady=1)
            self._nav_btns[key] = btn

        tk.Frame(sidebar, bg=C["sidebar"]).pack(fill="both", expand=True)

        tk.Frame(sidebar, bg="#1E2E4A", height=1).pack(fill="x", padx=16)
        dev_fr = tk.Frame(sidebar, bg=C["sidebar"])
        dev_fr.pack(fill="x", padx=12, pady=(6, 4))
        tk.Label(dev_fr, text="Desarrollado por",
                 font=("Segoe UI", 7), fg="#374E7A", bg=C["sidebar"]).pack(anchor="center")
        tk.Label(dev_fr, text="HOPD",
                 font=("Segoe UI", 8, "bold"), fg="#4A6090", bg=C["sidebar"]).pack(anchor="center")

        tk.Frame(sidebar, bg="#1E2E4A", height=1).pack(fill="x", padx=16)
        footer = tk.Frame(sidebar, bg=C["sidebar"])
        footer.pack(fill="x", padx=12, pady=8)
        av = tk.Frame(footer, bg=C["primary"], width=32, height=32)
        av.pack(side="left")
        av.pack_propagate(False)
        tk.Label(av, text=self._username[0].upper(),
                 font=("Segoe UI", 11, "bold"), fg=C["white"],
                 bg=C["primary"]).place(relx=0.5, rely=0.5, anchor="center")
        info_fr = tk.Frame(footer, bg=C["sidebar"])
        info_fr.pack(side="left", padx=(8, 0))
        tk.Label(info_fr, text=self._username,
                 font=("Segoe UI", 9, "bold"), fg="#B8C8E0",
                 bg=C["sidebar"]).pack(anchor="w")
        tk.Label(info_fr, text=f"[{self._rol}]",
                 font=("Segoe UI", 8), fg="#4A6090",
                 bg=C["sidebar"]).pack(anchor="w")
        tk.Button(sidebar, text="🚪  Cerrar sesión", command=self._logout,
                  font=("Segoe UI", 8), fg="#FF6B6B", bg=C["sidebar"],
                  activebackground=C["sidebar_h"], activeforeground="#FF6B6B",
                  relief="flat", bd=0, cursor="hand2").pack(pady=(2, 8))

        main = tk.Frame(self, bg=C["bg"])
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_rowconfigure(1, weight=1)
        main.grid_columnconfigure(0, weight=1)

        self.topbar = tk.Frame(main, bg=C["topbar"], height=60)
        self.topbar.grid(row=0, column=0, sticky="ew")
        self.topbar.grid_propagate(False)
        tk.Frame(self.topbar, bg=C["primary"], width=4).pack(side="left", fill="y")
        title_fr = tk.Frame(self.topbar, bg=C["topbar"])
        title_fr.pack(side="left", padx=20, fill="y", pady=10)
        self.lbl_titulo = tk.Label(title_fr, text="",
                                   font=("Segoe UI", 15, "bold"),
                                   fg=C["text"], bg=C["topbar"], anchor="w")
        self.lbl_titulo.pack(anchor="w")
        self.lbl_subtitulo = tk.Label(title_fr, text="",
                                      font=("Segoe UI", 8),
                                      fg=C["text3"], bg=C["topbar"], anchor="w")
        self.lbl_subtitulo.pack(anchor="w")
        date_pill = tk.Frame(self.topbar, bg=C["primary_l"], padx=12, pady=5)
        date_pill.pack(side="right", padx=20)
        tk.Label(date_pill,
                 text=f"📅  {datetime.datetime.now().strftime('%d/%m/%Y')}",
                 font=("Segoe UI", 9, "bold"),
                 fg=C["primary"], bg=C["primary_l"]).pack()
        _sep(self.topbar, C["border"]).pack(fill="x", side="bottom")

        self.page_area = tk.Frame(main, bg=C["bg"])
        self.page_area.grid(row=1, column=0, sticky="nsew")

        self._frames["dashboard"]      = self._build_page_dashboard(self.page_area)
        self._frames["registro"]       = self._build_page_registro(self.page_area)
        self._frames["capacitaciones"] = self._build_page_capacitaciones(self.page_area)
        self._frames["asistencia"]     = self._build_page_asistencia(self.page_area)
        self._frames["admin"]          = self._build_page_admin(self.page_area)
        if self._rol == "admin":
            self._frames["logs"]       = self._build_page_logs(self.page_area)

        self._ir_a("dashboard")
        self.after(200, self._iniciar_faiss)

    # ── Navegación ────────────────────────────
    def _make_nav_btn(self, parent, icon, label, key):
        fr = tk.Frame(parent, bg=C["sidebar"], cursor="hand2")
        fr.bind("<Button-1>", lambda e: self._ir_a(key))
        fr.bind("<Enter>",    lambda e: self._nav_hover(fr, key, True))
        fr.bind("<Leave>",    lambda e: self._nav_hover(fr, key, False))
        indicator = tk.Frame(fr, bg=C["sidebar"], width=3)
        indicator.pack(side="left", fill="y")
        icon_lbl = tk.Label(fr, text=icon, font=("Segoe UI", 12),
                            fg="#4A6090", bg=C["sidebar"], width=3, pady=10)
        icon_lbl.pack(side="left", padx=(6, 0))
        text_lbl = tk.Label(fr, text=label, font=("Segoe UI", 10),
                            fg="#B8C8E0", bg=C["sidebar"])
        text_lbl.pack(side="left", padx=4)
        for child in fr.winfo_children():
            child.bind("<Button-1>", lambda e: self._ir_a(key))
            child.bind("<Enter>",    lambda e: self._nav_hover(fr, key, True))
            child.bind("<Leave>",    lambda e: self._nav_hover(fr, key, False))
        fr._indicator = indicator
        fr._icon_lbl  = icon_lbl
        fr._text_lbl  = text_lbl
        return fr

    def _nav_hover(self, fr, key, entering):
        if self._active_key == key:
            return
        bg = C["sidebar_h"] if entering else C["sidebar"]
        fr.configure(bg=bg)
        for child in fr.winfo_children():
            child.configure(bg=bg)

    _active_key = ""

    _REFRESH_MAP = {
        "dashboard":      "_refresh_dashboard",
        "registro":       None,
        "capacitaciones": "_refresh_caps_list",
        "asistencia":     "_refresh_asistencias_list",
        "admin":          "_refresh_personas_list",
        "logs":           "_refresh_logs",
    }

    def _refresh_all(self):
        self._refresh_caps_combo()
        fn_name = self._REFRESH_MAP.get(self._active_key)
        if fn_name:
            getattr(self, fn_name)()

    def _ir_a(self, key):
        titles = {
            "dashboard":      ("Dashboard",            "Resumen general del sistema"),
            "registro":       ("Registrar Persona",    "Captura facial de los trabajadores"),
            "capacitaciones": ("Capacitaciones",       "Gestión de eventos y cursos"),
            "asistencia":     ("Registrar Asistencia", "Identificación automática por reconocimiento facial"),
            "admin":          ("Administrador",        "Gestión de personas y exportación de reportes"),
            "logs":           ("Logs del Sistema",     "Historial de actividad y auditoría"),
        }
        for f in self._frames.values():
            f.pack_forget()
        for k, btn in self._nav_btns.items():
            active = (k == key)
            bg = C["sidebar_h"] if active else C["sidebar"]
            btn.configure(bg=bg)
            btn._indicator.configure(bg=C["primary"] if active else C["sidebar"])
            btn._icon_lbl.configure(bg=bg, fg=C["primary_l"] if active else "#4A6090")
            btn._text_lbl.configure(bg=bg,
                                    fg=C["white"] if active else "#B8C8E0",
                                    font=("Segoe UI", 10, "bold") if active else ("Segoe UI", 10))
        self._active_key = key
        t, s = titles[key]
        self.lbl_titulo.config(text=t)
        self.lbl_subtitulo.config(text=s)
        self._frames[key].pack(fill="both", expand=True)
        self._refresh_all()

    # ── Helpers de layout ─────────────────────
    def _form_field(self, parent, label, row=None, width=32, bg=None):
        bg = bg or C["card"]
        if row is not None:
            tk.Label(parent, text=label, font=("Segoe UI", 9), fg=C["text2"],
                     bg=bg, anchor="w").grid(row=row * 2, column=0, sticky="w", pady=(10, 2))
            ent = _entry(parent, width=width)
            ent.grid(row=row * 2 + 1, column=0, sticky="ew", ipady=6)
        else:
            tk.Label(parent, text=label, font=("Segoe UI", 9), fg=C["text2"],
                     bg=bg, anchor="w").pack(fill="x", pady=(10, 2))
            ent = _entry(parent, width=width)
            ent.pack(fill="x", ipady=6)
        return ent

    def _card_frame(self, parent, title=None, icon="", accent=None):
        outer = tk.Frame(parent, bg=C["border"], bd=0)
        inner = tk.Frame(outer, bg=C["card"])
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        if title:
            hdr = tk.Frame(inner, bg=C["card"])
            hdr.pack(fill="x", padx=20, pady=(16, 0))
            tk.Frame(hdr, bg=accent or C["primary"], width=4).pack(side="left", fill="y", padx=(0, 10))
            tk.Label(hdr, text=f"{icon}  {title}" if icon else title,
                     font=("Segoe UI", 11, "bold"), fg=C["text"], bg=C["card"]).pack(side="left")
            _sep(inner).pack(fill="x", padx=20, pady=(10, 0))
        return outer, inner

    def _refresh_caps_combo(self):
        with sqlite3.connect(DB_PATH) as con:
            names = [r[0] for r in con.execute(
                "SELECT nombre FROM capacitaciones ORDER BY id DESC").fetchall()]
        if hasattr(self, "combo_caps"):
            cur = self.combo_caps.get()
            self.combo_caps["values"] = names
            if cur in names:
                self.combo_caps.set(cur)
        if hasattr(self, "combo_export"):
            cur = self.combo_export.get()
            self.combo_export["values"] = names
            if cur in names:
                self.combo_export.set(cur)

    def _get_cap_id(self, nombre):
        with sqlite3.connect(DB_PATH) as con:
            row = con.execute(
                "SELECT id FROM capacitaciones WHERE nombre=? ORDER BY id DESC LIMIT 1",
                (nombre,)).fetchone()
        return row[0] if row else None

    # ── PÁGINA: DASHBOARD ─────────────────────
    def _build_page_dashboard(self, parent):
        page = tk.Frame(parent, bg=C["bg"])
        body = tk.Frame(page, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=24, pady=20)

        kpi_row = tk.Frame(body, bg=C["bg"])
        kpi_row.pack(fill="x", pady=(0, 16))
        self._kpi_frames = {}
        for key, icon, label, color, bg_l in [
            ("total_personas", "👤", "Personas",        C["primary"],   C["primary_l"]),
            ("total_caps",     "📋", "Capacitaciones",  C["secondary"], "#E0F2FE"),
            ("total_asist",    "✅", "Asistencias",     C["success"],   C["success_l"]),
            ("asist_hoy",      "📅", "Asistencias Hoy", C["warning"],   C["warning_l"]),
        ]:
            card = tk.Frame(kpi_row, bg=C["card"],
                            highlightthickness=1, highlightbackground=C["border"])
            card.pack(side="left", fill="both", expand=True, padx=(0, 12))
            tk.Frame(card, bg=color, height=4).pack(fill="x")
            icon_row = tk.Frame(card, bg=C["card"])
            icon_row.pack(fill="x", padx=16, pady=(12, 0))
            icon_box = tk.Frame(icon_row, bg=bg_l, width=38, height=38)
            icon_box.pack(side="left")
            icon_box.pack_propagate(False)
            tk.Label(icon_box, text=icon, font=("Segoe UI", 16),
                     fg=color, bg=bg_l).place(relx=0.5, rely=0.5, anchor="center")
            lv = tk.Label(card, text="—", font=("Segoe UI", 26, "bold"), fg=color, bg=C["card"])
            lv.pack(padx=16, pady=(6, 2), anchor="w")
            tk.Label(card, text=label, font=("Segoe UI", 9), fg=C["text3"], bg=C["card"]).pack(
                padx=16, anchor="w", pady=(0, 14))
            self._kpi_frames[key] = lv

        bot_row = tk.Frame(body, bg=C["bg"])
        bot_row.pack(fill="both", expand=True)

        outer_tc, card_tc = self._card_frame(bot_row, "Top Capacitaciones", "🏆", accent=C["warning"])
        outer_tc.pack(side="left", fill="both", expand=True, padx=(0, 12))
        tc_wrap = tk.Frame(card_tc, bg=C["card"])
        tc_wrap.pack(fill="both", expand=True, padx=16, pady=(8, 16))
        tc_canvas = tk.Canvas(tc_wrap, bg=C["card"], highlightthickness=0)
        tc_scroll = ttk.Scrollbar(tc_wrap, orient="vertical", command=tc_canvas.yview)
        self._tc_inner = tk.Frame(tc_canvas, bg=C["card"])
        self._tc_inner.bind("<Configure>",
                            lambda e: tc_canvas.configure(scrollregion=tc_canvas.bbox("all")))
        tc_canvas.create_window((0, 0), window=self._tc_inner, anchor="nw")
        tc_canvas.configure(yscrollcommand=tc_scroll.set)
        tc_canvas.pack(side="left", fill="both", expand=True)
        tc_scroll.pack(side="right", fill="y")
        self._tc_canvas = tc_canvas

        outer_ur, card_ur = self._card_frame(bot_row, "Últimos Registros", "🕐", accent=C["secondary"])
        outer_ur.pack(side="left", fill="both", expand=True)
        ur_wrap = tk.Frame(card_ur, bg=C["card"])
        ur_wrap.pack(fill="both", expand=True, padx=16, pady=(8, 16))
        ur_canvas = tk.Canvas(ur_wrap, bg=C["card"], highlightthickness=0)
        ur_scroll = ttk.Scrollbar(ur_wrap, orient="vertical", command=ur_canvas.yview)
        self._ur_inner = tk.Frame(ur_canvas, bg=C["card"])
        self._ur_inner.bind("<Configure>",
                            lambda e: ur_canvas.configure(scrollregion=ur_canvas.bbox("all")))
        ur_canvas.create_window((0, 0), window=self._ur_inner, anchor="nw")
        ur_canvas.configure(yscrollcommand=ur_scroll.set)
        ur_canvas.pack(side="left", fill="both", expand=True)
        ur_scroll.pack(side="right", fill="y")
        self._ur_canvas = ur_canvas
        return page

    def _refresh_dashboard(self):
        if not hasattr(self, "_kpi_frames"):
            return
        with sqlite3.connect(DB_PATH) as con:
            total_p  = con.execute("SELECT COUNT(*) FROM personas WHERE activo=1").fetchone()[0]
            total_c  = con.execute("SELECT COUNT(*) FROM capacitaciones").fetchone()[0]
            total_a  = con.execute("SELECT COUNT(*) FROM asistencias").fetchone()[0]
            hoy      = datetime.date.today().isoformat()
            asist_h  = con.execute("SELECT COUNT(*) FROM asistencias WHERE hora_registro LIKE ?",
                                   (f"{hoy}%",)).fetchone()[0]
            top_caps = con.execute("""
                SELECT c.nombre, COUNT(a.id) FROM capacitaciones c
                LEFT JOIN asistencias a ON a.capacitacion_id=c.id
                GROUP BY c.id ORDER BY 2 DESC LIMIT 8""").fetchall()
            ultimos  = con.execute("""
                SELECT p.nombre||' '||p.apellido, c.nombre, a.hora_registro
                FROM asistencias a JOIN personas p ON p.id=a.persona_id
                JOIN capacitaciones c ON c.id=a.capacitacion_id
                ORDER BY a.hora_registro DESC LIMIT 10""").fetchall()

        self._kpi_frames["total_personas"].config(text=str(total_p))
        self._kpi_frames["total_caps"].config(text=str(total_c))
        self._kpi_frames["total_asist"].config(text=str(total_a))
        self._kpi_frames["asist_hoy"].config(text=str(asist_h))

        if hasattr(self, "_tc_inner"):
            for w in self._tc_inner.winfo_children():
                w.destroy()
            max_total    = max((t for _, t in top_caps), default=1) or 1
            badge_colors = [C["primary"], C["secondary"], C["success"],
                            C["warning"], C["danger"], C["purple"],
                            C["primary"], C["secondary"]]
            for i, (nombre, total) in enumerate(top_caps):
                row = tk.Frame(self._tc_inner, bg=C["white"],
                               highlightthickness=1, highlightbackground=C["border"])
                row.pack(fill="x", pady=3, ipady=6)
                bc    = badge_colors[i % len(badge_colors)]
                badge = tk.Frame(row, bg=bc, width=26, height=26)
                badge.pack(side="left", padx=(10, 10))
                badge.pack_propagate(False)
                tk.Label(badge, text=str(i + 1), font=("Segoe UI", 9, "bold"),
                         fg=C["white"], bg=bc).place(relx=0.5, rely=0.5, anchor="center")
                tk.Label(row, text=nombre[:30], font=("Segoe UI", 9, "bold"),
                         fg=C["text"], bg=C["white"], anchor="w").pack(side="left", fill="x", expand=True)
                right  = tk.Frame(row, bg=C["white"])
                right.pack(side="right", padx=10)
                bar_bg = tk.Frame(right, bg=C["border"], width=60, height=6)
                bar_bg.pack(side="left", padx=(0, 6))
                bar_bg.pack_propagate(False)
                bar_w  = max(4, int(60 * total / max_total))
                tk.Frame(bar_bg, bg=bc, width=bar_w, height=6).place(x=0, y=0)
                tk.Label(right, text=str(total), font=("Segoe UI", 9, "bold"),
                         fg=bc, bg=C["white"], width=3).pack(side="left")
            if not top_caps:
                tk.Label(self._tc_inner, text="Sin capacitaciones aún",
                         font=("Segoe UI", 9), fg=C["text3"], bg=C["card"]).pack(pady=20)
            self._tc_canvas.update_idletasks()
            self._tc_canvas.configure(scrollregion=self._tc_canvas.bbox("all"))

        if hasattr(self, "_ur_inner"):
            for w in self._ur_inner.winfo_children():
                w.destroy()
            av_colors = [C["primary"], C["secondary"], C["success"],
                         C["warning"], C["purple"], C["danger"]]
            for i, (nombre, cap, hora) in enumerate(ultimos):
                row = tk.Frame(self._ur_inner, bg=C["white"],
                               highlightthickness=1, highlightbackground=C["border"])
                row.pack(fill="x", pady=3, ipady=5)
                ac  = av_colors[i % len(av_colors)]
                av  = tk.Frame(row, bg=ac, width=28, height=28)
                av.pack(side="left", padx=(10, 10))
                av.pack_propagate(False)
                inicial = nombre[0].upper() if nombre else "?"
                tk.Label(av, text=inicial, font=("Segoe UI", 9, "bold"),
                         fg=C["white"], bg=ac).place(relx=0.5, rely=0.5, anchor="center")
                txt = tk.Frame(row, bg=C["white"])
                txt.pack(side="left", fill="x", expand=True)
                tk.Label(txt, text=nombre, font=("Segoe UI", 9, "bold"),
                         fg=C["text"], bg=C["white"], anchor="w").pack(anchor="w")
                tk.Label(txt, text=cap[:28], font=("Segoe UI", 8),
                         fg=C["text3"], bg=C["white"], anchor="w").pack(anchor="w")
                hora_str  = hora[11:16] if hora and len(hora) > 11 else ""
                hora_pill = tk.Frame(row, bg=C["primary_l"], padx=6, pady=2)
                hora_pill.pack(side="right", padx=10)
                tk.Label(hora_pill, text=hora_str, font=("Segoe UI", 8, "bold"),
                         fg=C["primary"], bg=C["primary_l"]).pack()
            if not ultimos:
                tk.Label(self._ur_inner, text="Sin asistencias aún",
                         font=("Segoe UI", 9), fg=C["text3"], bg=C["card"]).pack(pady=20)
            self._ur_canvas.update_idletasks()
            self._ur_canvas.configure(scrollregion=self._ur_canvas.bbox("all"))

    # ── PÁGINA: REGISTRO ──────────────────────
    def _build_page_registro(self, parent):
        page = tk.Frame(parent, bg=C["bg"])
        body = tk.Frame(page, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=24, pady=20)
        outer, card = self._card_frame(body, "Datos del Trabajador", "👤")
        outer.pack(side="left", fill="y", padx=(0, 16))
        form = tk.Frame(card, bg=C["card"])
        form.pack(padx=20, pady=10, fill="x")
        self.ent_nombre   = self._form_field(form, "Nombres *",   0, width=30)
        self.ent_apellido = self._form_field(form, "Apellidos *", 1, width=30)
        self.ent_cargo    = self._form_field(form, "Cargo",       2, width=30)
        form.columnconfigure(0, weight=1)
        num_fr = tk.Frame(card, bg=C["card"])
        num_fr.pack(fill="x", padx=20, pady=(8, 0))
        tk.Label(num_fr, text="Capturas faciales para el registro:",
                 font=("Segoe UI", 9), fg=C["text2"], bg=C["card"]).pack(side="left")
        self.spin_capturas = ttk.Spinbox(num_fr, from_=1, to=10, width=4, font=("Segoe UI", 10))
        self.spin_capturas.set(NUM_CAPTURAS)
        self.spin_capturas.pack(side="left", padx=(8, 0))
        tk.Label(num_fr, text="(más capturas = mayor precisión)",
                 font=("Segoe UI", 8), fg=C["text3"], bg=C["card"]).pack(side="left", padx=8)
        btn_fr = tk.Frame(card, bg=C["card"])
        btn_fr.pack(fill="x", padx=20, pady=(14, 20))
        self._btn_capturar = tk.Button(
            btn_fr,
            text="📷   Capturar y Registrar",
            command=self._registrar_persona,
            font=("Segoe UI", 10, "bold"),
            bg=C["primary"], fg=C["white"],
            activebackground=C["primary_h"], activeforeground=C["white"],
            relief="flat", bd=0, padx=18, pady=9, cursor="hand2")
        self._btn_capturar.pack(fill="x", ipady=6)

        outer2, card2 = self._card_frame(body, "¿Cómo registrarse?", "📌", accent=C["secondary"])
        outer2.pack(side="left", fill="both", expand=True)
        for num, col, texto in [
            ("1", C["primary"],   "Completa nombres, apellidos y cargo."),
            ("2", C["secondary"], "Selecciona el número de capturas (recomendado: 5)."),
            ("3", C["success"],   "Haz clic en 'Capturar y Registrar'."),
            ("4", C["warning"],   "Presiona ESPACIO para cada captura desde\nángulos ligeramente distintos."),
            ("5", C["purple"],    "El sistema promedia los embeddings para\nmayor robustez en el reconocimiento."),
        ]:
            fr = tk.Frame(card2, bg=C["card"])
            fr.pack(fill="x", padx=20, pady=5)
            tk.Label(fr, text=num, font=("Segoe UI", 9, "bold"), fg=C["white"], bg=col,
                     width=2, pady=2).pack(side="left", padx=(0, 12))
            tk.Label(fr, text=texto, font=("Segoe UI", 9), fg=C["text2"],
                     bg=C["card"], justify="left").pack(side="left", anchor="nw")
        nota = tk.Frame(card2, bg=C["primary_l"])
        nota.pack(fill="x", padx=20, pady=(10, 20))
        tk.Label(nota, text="  ℹ️  Se almacena el vector facial promedio,\n  no se guardan fotografías.",
                 font=("Segoe UI", 8), fg=C["primary"], bg=C["primary_l"],
                 justify="left", pady=8).pack(anchor="w")
        return page

    #  registrar persona 
    def _registrar_persona(self):
        if self._camara_activa:
            messagebox.showwarning("Cámara en uso",
                                "Ya hay una sesión de cámara activa.")
            return
        nombre   = self.ent_nombre.get().strip()
        apellido = self.ent_apellido.get().strip()
        cargo    = self.ent_cargo.get().strip()
        if not nombre or not apellido:
            messagebox.showwarning("Campos requeridos",
                                "Nombres y Apellidos son obligatorios.")
            return
        try:
            n_capturas = max(1, min(10, int(self.spin_capturas.get())))
        except Exception:
            n_capturas = NUM_CAPTURAS


        self._camara_activa = True
        self._btn_capturar.config(state="disabled", text="📷   Capturando...",
                                bg=C["border2"], fg=C["text3"], cursor="arrow")

        _queue    = self._resultado_queue
        _nombre   = nombre
        _apellido = apellido
        _cargo    = cargo
        _n        = n_capturas

        def _tarea():
            try:
                # Sin parent_tk — el diálogo ya se manejó arriba
                emb = capturar_embedding_multi(_n, parent_tk=None)
            except Exception as e:
                emb = None
                print(f"[ERROR] capturar_embedding_multi: {e}")
            _queue.put(("registro", (emb, _nombre, _apellido, _cargo, _n)))

        threading.Thread(target=_tarea, daemon=True).start()


    def _finalizar_registro(self, emb, nombre, apellido, cargo, n_capturas):
        """Siempre se llama desde el hilo principal via _procesar_queue."""
        self._camara_activa = False
        self._btn_capturar.config(state="normal", text="📷   Capturar y Registrar", bg=C["primary"], fg=C["white"], cursor="hand2")
        if emb is None:
            messagebox.showwarning("Cancelado", "No se capturó ninguna cara o se canceló.")
            return

        try:
            pid_dup, nombre_dup, activo_dup = persona_ya_existe(emb)
        except Exception as e:
            print(f"[ERROR] persona_ya_existe: {e}")
            pid_dup = None

        if pid_dup is not None:
            messagebox.showwarning(
                "⚠️  Persona ya registrada",
                f"Esta cara ya existe en el sistema:\n\n  👤  {nombre_dup}  "
                f"[{'activo' if activo_dup else 'inactivo'}]\n\n"
                f"Si necesitas actualizar sus datos, ve a\nAdministrador → Gestionar Personas.")
            return

        try:
            with sqlite3.connect(DB_PATH) as con:
                con.execute(
                    "INSERT INTO personas (nombre,apellido,cargo,embedding) VALUES (?,?,?,?)",
                    (nombre, apellido, cargo or None, emb.tobytes()))
            log("REGISTRAR_PERSONA", f"'{nombre} {apellido}' registrado con {n_capturas} capturas")
            rebuild_faiss_index()
            messagebox.showinfo("✅ Registro exitoso",
                                f"{nombre} {apellido} registrado correctamente.")
            for e in (self.ent_nombre, self.ent_apellido, self.ent_cargo):
                e.delete(0, "end")
            self._refresh_personas_list()
        except sqlite3.IntegrityError as e:
            print(f"[ERROR] IntegrityError al registrar persona: {e}")
            messagebox.showerror("Error", "Error de integridad al registrar la persona.")
        except Exception as e:
            print(f"[ERROR] Error al registrar persona: {e}")
            messagebox.showerror("Error", f"No se pudo registrar:\n{e}")

    # ── PÁGINA: CAPACITACIONES ────────────────
    def _build_page_capacitaciones(self, parent):
        page = tk.Frame(parent, bg=C["bg"])
        body = tk.Frame(page, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=24, pady=20)
        outer, card = self._card_frame(body, "Nueva capacitación", "➕")
        outer.pack(side="left", fill="y", padx=(0, 16))
        form_fr = tk.Frame(card, bg=C["card"])
        form_fr.pack(padx=20, pady=10, fill="x")
        self.ent_cap_nombre = self._form_field(form_fr, "Nombre *",          width=34)
        self.ent_cap_desc   = self._form_field(form_fr, "Descripción",       width=34)
        self.ent_cap_firma  = self._form_field(form_fr, "Firma Responsable", width=34)

        self._firma_png_ruta = ""
        firma_png_fr = tk.Frame(card, bg=C["card"])
        firma_png_fr.pack(fill="x", padx=20, pady=(6, 0))
        tk.Label(firma_png_fr, text="Imagen de firma (PNG, opcional):",
                 font=("Segoe UI", 9), fg=C["text2"], bg=C["card"]).pack(anchor="w", pady=(4, 2))
        self.lbl_firma_png = tk.Label(firma_png_fr, text="Sin imagen cargada",
                                      font=("Segoe UI", 8), fg=C["text3"], bg=C["card"], anchor="w")
        self.lbl_firma_png.pack(fill="x")
        firma_btns = tk.Frame(card, bg=C["card"])
        firma_btns.pack(fill="x", padx=20, pady=(6, 4))
        _btn(firma_btns, "🖼️  Cargar PNG", self._cargar_firma_png,
             C["secondary"], pad_x=10, pad_y=5).pack(side="left", padx=(0, 6))
        _btn(firma_btns, "✖  Quitar", self._quitar_firma_png,
             C["border2"], fg=C["text2"], pad_x=10, pad_y=5).pack(side="left")

        btn_fr = tk.Frame(card, bg=C["card"])
        btn_fr.pack(fill="x", padx=20, pady=(10, 20))
        _btn(btn_fr, "➕   Crear Capacitación", self._crear_capacitacion, C["success"]).pack(fill="x", ipady=6)

        outer2, card2 = self._card_frame(body, "Capacitaciones registradas", "📋", accent=C["secondary"])
        outer2.pack(side="left", fill="both", expand=True)
        caps_wrap = tk.Frame(card2, bg=C["card"])
        caps_wrap.pack(fill="both", expand=True, padx=16, pady=(8, 4))
        caps_canvas = tk.Canvas(caps_wrap, bg=C["card"], highlightthickness=0)
        caps_sc = ttk.Scrollbar(caps_wrap, orient="vertical", command=caps_canvas.yview)
        self._caps_inner = tk.Frame(caps_canvas, bg=C["card"])
        self._caps_inner.bind("<Configure>",
                              lambda e: caps_canvas.configure(scrollregion=caps_canvas.bbox("all")))
        caps_canvas.create_window((0, 0), window=self._caps_inner, anchor="nw")
        caps_canvas.configure(yscrollcommand=caps_sc.set)
        caps_canvas.pack(side="left", fill="both", expand=True)
        caps_sc.pack(side="right", fill="y")
        self._caps_canvas = caps_canvas
        self._cap_sel_id  = None
        btn_del_fr = tk.Frame(card2, bg=C["card"])
        btn_del_fr.pack(fill="x", padx=20, pady=(6, 16))
        _btn(btn_del_fr, "🗑️  Eliminar capacitación seleccionada",
             self._eliminar_capacitacion, C["danger"], pad_x=12).pack(fill="x", ipady=5)
        self._refresh_caps_list()
        return page

    def _cargar_firma_png(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar imagen de firma",
            filetypes=[("Imágenes PNG", "*.png"), ("Todos los archivos", "*.*")])
        if not ruta:
            return
        self._firma_png_ruta = ruta
        self.lbl_firma_png.config(text=f"🖼️  {os.path.basename(ruta)}", fg=C["success"])

    def _quitar_firma_png(self):
        self._firma_png_ruta = ""
        self.lbl_firma_png.config(text="Sin imagen cargada", fg=C["text3"])

    def _crear_capacitacion(self):
        nombre    = self.ent_cap_nombre.get().strip()
        desc      = self.ent_cap_desc.get().strip()
        firma     = self.ent_cap_firma.get().strip()
        firma_png = self._firma_png_ruta or None
        if not nombre:
            messagebox.showwarning("Campo requerido", "Ingresa el nombre.")
            return
        if firma_png and os.path.isfile(firma_png):
            nombre_png  = os.path.basename(firma_png)
            destino_png = os.path.abspath(os.path.join(PLANTILLA_DIR, nombre_png))
            try:
                shutil.copy2(firma_png, destino_png)
                firma_png = destino_png
            except Exception:
                pass
        with sqlite3.connect(DB_PATH) as con:
            con.execute(
                "INSERT INTO capacitaciones (nombre,descripcion,firma_responsable,firma_png) VALUES (?,?,?,?)",
                (nombre, desc or None, firma or None, firma_png))
        log("CREAR_CAPACITACION", f"'{nombre}'" + (" con firma PNG" if firma_png else ""))
        messagebox.showinfo("✅ Creada", f"Capacitación '{nombre}' creada.")
        self.ent_cap_nombre.delete(0, "end")
        self.ent_cap_desc.delete(0, "end")
        self.ent_cap_firma.delete(0, "end")
        self._quitar_firma_png()
        self._refresh_caps_list()
        self._refresh_caps_combo()

    def _eliminar_capacitacion(self):
        if not hasattr(self, "_cap_sel_id") or self._cap_sel_id is None:
            messagebox.showwarning("Sin selección", "Selecciona una capacitación de la lista.")
            return
        cap_id = self._cap_sel_id
        with sqlite3.connect(DB_PATH) as con:
            row         = con.execute("SELECT nombre FROM capacitaciones WHERE id=?", (cap_id,)).fetchone()
            total_asist = con.execute("SELECT COUNT(*) FROM asistencias WHERE capacitacion_id=?",
                                      (cap_id,)).fetchone()[0]
        if not row:
            messagebox.showerror("Error", "No se encontró la capacitación.")
            return
        nombre = row[0]
        msg    = f"¿Eliminar permanentemente la capacitación:\n\n  📋  {nombre}?"
        if total_asist > 0:
            msg += f"\n\nEsta acción eliminará también {total_asist} asistencia(s) asociadas."
        if not messagebox.askyesno("Confirmar eliminación", msg):
            return
        with sqlite3.connect(DB_PATH) as con:
            con.execute("DELETE FROM asistencias WHERE capacitacion_id=?", (cap_id,))
            con.execute("DELETE FROM capacitaciones WHERE id=?", (cap_id,))
        log("ELIMINAR_CAPACITACION",
            f"'{nombre}' ID={cap_id} eliminada con {total_asist} asistencias", "WARNING")
        self._cap_sel_id = None
        self._refresh_caps_list()
        self._refresh_caps_combo()
        messagebox.showinfo("Eliminado", f"Capacitación '{nombre}' eliminada correctamente.")

    def _refresh_caps_list(self):
        if not hasattr(self, "_caps_inner"):
            return
        for w in self._caps_inner.winfo_children():
            w.destroy()
        with sqlite3.connect(DB_PATH) as con:
            rows = con.execute("""
                SELECT id, nombre, fecha, firma_responsable,
                       (SELECT COUNT(*) FROM asistencias WHERE capacitacion_id=c.id)
                FROM capacitaciones c ORDER BY id DESC""").fetchall()
        for i, (cid, nombre, fecha, firma, total) in enumerate(rows):
            is_sel = (cid == self._cap_sel_id)
            row_bg = C["primary_l"] if is_sel else (C["card_alt"] if i % 2 == 0 else C["white"])
            row    = tk.Frame(self._caps_inner, bg=row_bg,
                              highlightthickness=1,
                              highlightbackground=C["primary"] if is_sel else C["border"])
            row.pack(fill="x", pady=2)

            def _select(e, cid=cid):
                self._cap_sel_id = cid
                self._refresh_caps_list()

            row.bind("<Button-1>", _select)
            ic = tk.Frame(row, bg=C["secondary"], width=28, height=28)
            ic.pack(side="left", padx=(10, 8), pady=8)
            ic.pack_propagate(False)
            tk.Label(ic, text="📋", font=("Segoe UI", 12),
                     bg=C["secondary"]).place(relx=0.5, rely=0.5, anchor="center")
            ic.bind("<Button-1>", _select)
            txt = tk.Frame(row, bg=row_bg)
            txt.pack(side="left", fill="x", expand=True)
            txt.bind("<Button-1>", _select)
            tk.Label(txt, text=nombre[:36], font=("Segoe UI", 9, "bold"),
                     fg=C["primary"] if is_sel else C["text"],
                     bg=row_bg, anchor="w").pack(anchor="w")
            meta = f"{fecha or ''}  ·  {total} asistentes"
            if firma:
                meta += f"  ·  {firma[:20]}"
            tk.Label(txt, text=meta, font=("Segoe UI", 8),
                     fg=C["primary"] if is_sel else C["text3"],
                     bg=row_bg, anchor="w").pack(anchor="w")
            for child in txt.winfo_children():
                child.bind("<Button-1>", _select)
            pill = tk.Frame(row, bg=C["primary"] if is_sel else C["primary_l"], padx=8, pady=3)
            pill.pack(side="right", padx=10)
            pill.bind("<Button-1>", _select)
            tk.Label(pill, text=str(total), font=("Segoe UI", 9, "bold"),
                     fg=C["white"] if is_sel else C["primary"],
                     bg=C["primary"] if is_sel else C["primary_l"]).pack()

        if not rows:
            tk.Label(self._caps_inner, text="Sin capacitaciones registradas",
                     font=("Segoe UI", 9), fg=C["text3"], bg=C["card"]).pack(pady=20)
        self._caps_canvas.update_idletasks()
        self._caps_canvas.configure(scrollregion=self._caps_canvas.bbox("all"))

    # ── PÁGINA: ASISTENCIA ────────────────────
    def _build_page_asistencia(self, parent):
        page = tk.Frame(parent, bg=C["bg"])
        body = tk.Frame(page, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=24, pady=20)
        outer, card = self._card_frame(body, "Registrar asistencia", "✅")
        outer.pack(side="left", fill="y", padx=(0, 16), ipadx=10)
        tk.Label(card, text="Capacitación:", font=("Segoe UI", 9), fg=C["text2"],
                 bg=C["card"]).pack(anchor="w", padx=20, pady=(14, 2))
        combo_fr = tk.Frame(card, bg=C["card"])
        combo_fr.pack(fill="x", padx=20, pady=(0, 16))
        self.combo_caps = ttk.Combobox(combo_fr, state="readonly", font=("Segoe UI", 10), width=30)
        self.combo_caps.pack(fill="x")
        self.btn_registrar_asistencia = tk.Button(
            card,
            text="🎯\n\nRegistrar Asistencia\n",
            command=self._registrar_asistencia,
            font=("Segoe UI", 13, "bold"),
            bg=C["primary"], fg=C["white"],
            activebackground=C["primary_h"], activeforeground=C["white"],
            relief="flat", bd=0, pady=14, cursor="hand2")
        self.btn_registrar_asistencia.pack(fill="x", padx=20)
        tk.Label(card, text="La cámara identificará al trabajador automáticamente.",
                 font=("Segoe UI", 8), fg=C["text3"], bg=C["card"],
                 justify="center").pack(pady=(10, 20))

        outer2, card2 = self._card_frame(body, "Últimas asistencias", "🕐", accent=C["secondary"])
        outer2.pack(side="left", fill="both", expand=True)
        asist_wrap = tk.Frame(card2, bg=C["card"])
        asist_wrap.pack(fill="both", expand=True, padx=16, pady=(8, 20))
        asist_canvas = tk.Canvas(asist_wrap, bg=C["card"], highlightthickness=0)
        asist_sc = ttk.Scrollbar(asist_wrap, orient="vertical", command=asist_canvas.yview)
        self._asist_inner = tk.Frame(asist_canvas, bg=C["card"])
        self._asist_inner.bind("<Configure>",
                               lambda e: asist_canvas.configure(scrollregion=asist_canvas.bbox("all")))
        asist_canvas.create_window((0, 0), window=self._asist_inner, anchor="nw")
        asist_canvas.configure(yscrollcommand=asist_sc.set)
        asist_canvas.pack(side="left", fill="both", expand=True)
        asist_sc.pack(side="right", fill="y")
        self._asist_canvas = asist_canvas
        self._refresh_asistencias_list()
        self._refresh_caps_combo()
        return page

    # ─ registrar   asistencia ───
    def _registrar_asistencia(self):
        if self._camara_activa:
            return
        sel = self.combo_caps.get()
        if not sel:
            messagebox.showwarning("Sin selección", "Selecciona una capacitación.")
            return
        cap_id = self._get_cap_id(sel)
        if cap_id is None:
            messagebox.showerror("Error", "Capacitación no encontrada.")
            return
        known = get_all_embeddings()
        if not known:
            messagebox.showwarning("Sin personas", "Registra personas primero.")
            return


        self._camara_activa = True
        self.btn_registrar_asistencia.config(
            state="disabled", text="🎯\n\n⏳  Cámara activa...\n",
            bg=C["border2"], fg=C["text3"], cursor="arrow")
        self.combo_caps.config(state="disabled")

        _queue  = self._resultado_queue
        _known  = known
        _cap_id = cap_id
        _sel    = sel

        def _tarea():
            try:
                # Sin parent_tk — el diálogo ya se manejó arriba
                ids_registrados = reconocer_cara(_known, _cap_id, parent_tk=None)
            except Exception as e:
                ids_registrados = []
                print(f"[ERROR] reconocer_cara: {e}")
            _queue.put(("asistencia", (ids_registrados, _sel)))

        threading.Thread(target=_tarea, daemon=True).start()


    def _finalizar_asistencia(self, ids_registrados, sel):
        """Siempre se llama desde el hilo principal via _procesar_queue."""
        self._camara_activa = False
        self.btn_registrar_asistencia.config(
            state="normal", text="🎯\n\nRegistrar Asistencia\n",
            bg=C["primary"], fg=C["white"], cursor="hand2")
        self.combo_caps.config(state="readonly")

        if not ids_registrados:
            messagebox.showwarning("Sin registros", "No se registró ninguna asistencia.")
            return

        with sqlite3.connect(DB_PATH) as con:
            nombres = []
            for pid in ids_registrados:
                row = con.execute(
                    "SELECT nombre||' '||apellido FROM personas WHERE id=?", (pid,)).fetchone()
                if row:
                    nombres.append(row[0])

        log("REGISTRAR_ASISTENCIA",
            f"{len(ids_registrados)} asistencia(s) en '{sel}': {', '.join(nombres)}")
        _beep(True)
        resumen = "\n".join(f"  ✓ {n}" for n in nombres)
        messagebox.showinfo(
            "✅ Sesión finalizada",
            f"Se registraron {len(ids_registrados)} asistencia(s) en '{sel}':\n\n{resumen}")
        self._refresh_asistencias_list()
        self._refresh_caps_list()
        self._refresh_dashboard()

    def _refresh_asistencias_list(self):
        if not hasattr(self, "_asist_inner"):
            return
        for w in self._asist_inner.winfo_children():
            w.destroy()
        with sqlite3.connect(DB_PATH) as con:
            rows = con.execute("""
                SELECT p.nombre||' '||p.apellido, c.nombre, a.hora_registro
                FROM asistencias a JOIN personas p ON p.id=a.persona_id
                JOIN capacitaciones c ON c.id=a.capacitacion_id
                ORDER BY a.hora_registro DESC LIMIT 30""").fetchall()
        av_colors = [C["primary"], C["secondary"], C["success"],
                     C["warning"], C["purple"], C["danger"]]
        for i, (nombre, cap, hora) in enumerate(rows):
            row_bg = C["card_alt"] if i % 2 == 0 else C["white"]
            row    = tk.Frame(self._asist_inner, bg=row_bg,
                              highlightthickness=1, highlightbackground=C["border"])
            row.pack(fill="x", pady=2)
            ac = av_colors[i % len(av_colors)]
            av = tk.Frame(row, bg=ac, width=28, height=28)
            av.pack(side="left", padx=(10, 8), pady=7)
            av.pack_propagate(False)
            tk.Label(av, text=nombre[0].upper(), font=("Segoe UI", 9, "bold"),
                     fg=C["white"], bg=ac).place(relx=0.5, rely=0.5, anchor="center")
            txt = tk.Frame(row, bg=row_bg)
            txt.pack(side="left", fill="x", expand=True)
            tk.Label(txt, text=nombre, font=("Segoe UI", 9, "bold"),
                     fg=C["text"], bg=row_bg, anchor="w").pack(anchor="w")
            tk.Label(txt, text=cap[:32], font=("Segoe UI", 8),
                     fg=C["text3"], bg=row_bg, anchor="w").pack(anchor="w")
            hora_str = hora[11:16] if hora and len(hora) > 11 else hora or ""
            pill     = tk.Frame(row, bg=C["success_l"], padx=7, pady=3)
            pill.pack(side="right", padx=10)
            tk.Label(pill, text=hora_str, font=("Segoe UI", 8, "bold"),
                     fg=C["success"], bg=C["success_l"]).pack()
        if not rows:
            tk.Label(self._asist_inner, text="Sin asistencias registradas",
                     font=("Segoe UI", 9), fg=C["text3"], bg=C["card"]).pack(pady=20)
        self._asist_canvas.update_idletasks()
        self._asist_canvas.configure(scrollregion=self._asist_canvas.bbox("all"))

    # ── PÁGINA: ADMINISTRADOR ─────────────────
    def _build_page_admin(self, parent):
        page = tk.Frame(parent, bg=C["bg"])
        body = tk.Frame(page, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=24, pady=20)

        col_izq = tk.Frame(body, bg=C["bg"])
        col_izq.pack(side="left", fill="both", expand=True, padx=(0, 14))
        outer, card = self._card_frame(col_izq, "Trabajadores registrados", "👥")
        outer.pack(fill="both", expand=True)
        pers_wrap = tk.Frame(card, bg=C["card"])
        pers_wrap.pack(fill="both", expand=True, padx=16, pady=(8, 8))
        pers_canvas = tk.Canvas(pers_wrap, bg=C["card"], highlightthickness=0)
        pers_sc = ttk.Scrollbar(pers_wrap, orient="vertical", command=pers_canvas.yview)
        self._pers_inner = tk.Frame(pers_canvas, bg=C["card"])
        self._pers_inner.bind("<Configure>",
                              lambda e: pers_canvas.configure(scrollregion=pers_canvas.bbox("all")))
        pers_canvas.create_window((0, 0), window=self._pers_inner, anchor="nw")
        pers_canvas.configure(yscrollcommand=pers_sc.set)
        pers_canvas.pack(side="left", fill="both", expand=True)
        pers_sc.pack(side="right", fill="y")
        self._pers_canvas = pers_canvas
        self._refresh_personas_list()
        
        btn_fr = tk.Frame(card, bg=C["card"])
        btn_fr.pack(fill="x", padx=20, pady=(4, 12))
        _btn(btn_fr, "👥  Gestionar Personas", self._abrir_crud, C["primary"]).pack(
            side="left", fill="x", expand=True, ipady=5, padx=(0, 8))
        if self._rol == "admin":
            _btn(btn_fr, "🔐  Usuarios", self._abrir_usuarios, C["purple"]).pack(
                side="left", fill="x", expand=True, ipady=5, padx=(0, 8))
            _btn(btn_fr, "📷  Diagnóstico cámara", self._diagnosticar_camara, C["secondary"]).pack(
                side="left", fill="x", expand=True, ipady=5)

        col_der = tk.Frame(body, bg=C["bg"], width=320)
        col_der.pack(side="left", fill="both")
        col_der.pack_propagate(False)
        scroll_frame = tk.Frame(col_der, bg=C["bg"])
        scroll_frame.pack(fill="both", expand=True)

        outer_pdf, card_pdf = self._card_frame(scroll_frame, "Plantilla PDF (.docx)", "📝", accent=C["danger"])
        outer_pdf.pack(fill="x", pady=(0, 10), padx=2)
        plnt_pdf_fr = tk.Frame(card_pdf, bg=C["card"])
        plnt_pdf_fr.pack(padx=14, pady=(8, 0), fill="x")
        ruta_pdf_actual   = config_get("plantilla_pdf_docx") or ""
        nombre_pdf_actual = (os.path.basename(ruta_pdf_actual)
                             if ruta_pdf_actual and os.path.isfile(ruta_pdf_actual)
                             else "Sin plantilla (PDF corporativo)")
        self.lbl_plantilla_pdf = tk.Label(
            plnt_pdf_fr,
            text=f"📝  {nombre_pdf_actual}",
            font=("Segoe UI", 8),
            fg=C["success"] if ruta_pdf_actual and os.path.isfile(ruta_pdf_actual) else C["text3"],
            bg=C["card"], anchor="w", wraplength=260)
        self.lbl_plantilla_pdf.pack(fill="x", pady=(0, 6))
        btns_pdf = tk.Frame(card_pdf, bg=C["card"])
        btns_pdf.pack(fill="x", padx=14, pady=(0, 10))
        _btn(btns_pdf, "📂  Cargar .docx", self._cargar_plantilla_pdf,
             C["danger"], pad_x=8, pad_y=6).pack(side="left", padx=(0, 6))
        _btn(btns_pdf, "✖  Quitar", self._quitar_plantilla_pdf,
             C["border2"], fg=C["text2"], pad_x=8, pad_y=6).pack(side="left")
        tk.Label(card_pdf,
                 text="  ℹ️  Usa marcadores {{...}} en tu .docx.\n"
                      "  Requiere: pip install python-docx docx2pdf",
                 font=("Segoe UI", 7), fg=C["text3"], bg=C["card"],
                 justify="left").pack(anchor="w", padx=14, pady=(0, 8))

        outer2, card2 = self._card_frame(scroll_frame, "Exportar reporte", "📥", accent=C["success"])
        outer2.pack(fill="x", pady=(0, 10), padx=2)
        exp_fr = tk.Frame(card2, bg=C["card"])
        exp_fr.pack(padx=14, pady=(8, 0), fill="x")
        tk.Label(exp_fr, text="Capacitación:",
                 font=("Segoe UI", 9), fg=C["text2"], bg=C["card"]).pack(anchor="w", pady=(0, 4))
        self.combo_export = ttk.Combobox(exp_fr, state="readonly", font=("Segoe UI", 9), width=28)
        self.combo_export.pack(fill="x")
        btn_pdf_fr = tk.Frame(card2, bg=C["card"])
        btn_pdf_fr.pack(fill="x", padx=14, pady=(10, 14))
        _btn(btn_pdf_fr, "📄   Exportar a PDF", self._exportar_pdf, C["danger"]).pack(fill="x", ipady=5)
        return page

    def _cargar_plantilla_pdf(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar plantilla PDF (.docx)",
            filetypes=[("Documentos Word", "*.docx"), ("Todos los archivos", "*.*")])
        if not ruta:
            return
        nombre_archivo = os.path.basename(ruta)
        destino = os.path.abspath(os.path.join(PLANTILLA_DIR, nombre_archivo))
        try:
            shutil.copy2(ruta, destino)
            config_set("plantilla_pdf_docx", destino)
            log("CARGAR_PLANTILLA_PDF", f"Plantilla PDF '{nombre_archivo}' cargada")
            self.lbl_plantilla_pdf.config(text=f"📝  {nombre_archivo}", fg=C["success"])
            messagebox.showinfo("✅ Plantilla PDF cargada",
                                f"Plantilla '{nombre_archivo}' configurada para PDF.\n\n"
                                f"Usa marcadores como {{{{nombre_completo}}}},\n"
                                f"{{{{cap_nombre}}}}, {{{{firma_responsable}}}}, etc.\n\n"
                                f"La fila de la tabla con marcadores de persona\n"
                                f"se repetirá por cada asistente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo copiar la plantilla:\n{e}")

    def _quitar_plantilla_pdf(self):
        config_set("plantilla_pdf_docx", "")
        log("QUITAR_PLANTILLA_PDF", "Plantilla PDF removida")
        self.lbl_plantilla_pdf.config(
            text="📝  Sin plantilla (PDF corporativo por defecto)", fg=C["text3"])
        messagebox.showinfo("Plantilla removida", "Se usará el PDF corporativo por defecto.")

    def _abrir_crud(self):
        VentanaPersonas(self)
        self.wait_window(self.winfo_children()[-1])
        self._refresh_personas_list()

    def _abrir_usuarios(self):
        VentanaUsuarios(self)
        self.wait_window(self.winfo_children()[-1])







    def _diagnosticar_camara(self):
        """
        Muestra diagnóstico completo de cámaras disponibles.
        Limpia la config guardada para forzar re-detección en el próximo uso.
        """
        from vista import diagnosticar_camaras, _limpiar_config_camara
        

        win = tk.Toplevel(self)
        win.title("Diagnóstico de Cámara")
        win.geometry("520x440")
        win.resizable(False, False)
        win.configure(bg=C["bg"])
        win.grab_set()

        # ── Header ──
        hdr = tk.Frame(win, bg=C["sidebar"])
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=C["secondary"], width=4).pack(side="left", fill="y")
        tk.Label(hdr,
                text="  📷  Diagnóstico de Cámara",
                font=("Segoe UI", 11, "bold"),
                fg=C["white"], bg=C["sidebar"], pady=12).pack(side="left")

        # ── Descripción ──
        body = tk.Frame(win, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=20, pady=(14, 0))
        tk.Label(body,
                text="Probando todas las configuraciones de cámara disponibles…",
                font=("Segoe UI", 9), fg=C["text2"], bg=C["bg"]).pack(anchor="w", pady=(0, 10))

        # ── Área de texto con scrollbar ──
        txt_fr = tk.Frame(body, bg=C["border"], bd=1)
        txt_fr.pack(fill="both", expand=True)
        txt = tk.Text(
            txt_fr,
            font=("Courier New", 9),
            bg=C["sidebar"], fg="#B8C8E0",
            relief="flat", bd=0,
            wrap="word",
            padx=12, pady=10)
        self._txt_diagnostico = txt
        sc = ttk.Scrollbar(txt_fr, command=txt.yview)
        txt.configure(yscrollcommand=sc.set)
        sc.pack(side="right", fill="y")
        txt.pack(fill="both", expand=True)
        txt.insert("end", "⏳ Probando cámaras... esto puede tardar 20-30 segundos.\n\n")
        def _ejecutar():
            resultado = diagnosticar_camaras()
            self._resultado_queue.put(("diagnostico", resultado))

        threading.Thread(target=_ejecutar, daemon=True).start()





        # ── Botones ──
        bot = tk.Frame(win, bg=C["bg"])
        bot.pack(fill="x", padx=20, pady=(10, 0))

        def _re_ejecutar():
            txt.delete("1.0", "end")
            txt.insert("end", "⏳ Re-ejecutando diagnóstico...\n")
            txt.update()
            _limpiar_config_camara()
            threading.Thread(target=_ejecutar, daemon=True).start()

        _btn(bot, "🔄  Volver a probar", _re_ejecutar,
            C["secondary"], pad_x=12).pack(side="left", padx=(0, 8))
        _btn(bot, "✖  Cerrar", win.destroy,
            C["border2"], fg=C["text2"], pad_x=12).pack(side="left")

        # ── Nota al pie ──
        tk.Label(win,
                text="ℹ️  La configuración que funcione se guardará automáticamente al usar la cámara.",
                font=("Segoe UI", 8), fg=C["text3"], bg=C["bg"]).pack(
            anchor="w", padx=20, pady=(8, 14))


















    def _exportar_pdf(self):
        sel = self.combo_export.get()
        if not sel:
            messagebox.showwarning("Sin selección", "Selecciona una capacitación.")
            return
        cap_id = self._get_cap_id(sel)
        if cap_id is None:
            return
        try:
            fname = exportar_pdf(cap_id, sel)
            if fname:
                log("EXPORTAR_PDF", f"Capacitación '{sel}' → {fname}")
                messagebox.showinfo("✅ PDF generado",
                                    f"Archivo guardado:\n{os.path.abspath(fname)}")
        except Exception as e:
            messagebox.showerror("Error al exportar PDF", f"Ocurrió un error:\n\n{e}")

    def _refresh_personas_list(self):
        if not hasattr(self, "_pers_inner"):
            return
        for w in self._pers_inner.winfo_children():
            w.destroy()
        with sqlite3.connect(DB_PATH) as con:
            rows = con.execute(
                "SELECT nombre, apellido, cargo, activo FROM personas ORDER BY nombre"
            ).fetchall()
        av_colors = [C["primary"], C["secondary"], C["success"], C["purple"],
                     C["warning"], C["danger"]]
        for i, (nombre, apellido, cargo, activo) in enumerate(rows):
            row_bg = C["card_alt"] if i % 2 == 0 else C["white"]
            row    = tk.Frame(self._pers_inner, bg=row_bg,
                              highlightthickness=1, highlightbackground=C["border"])
            row.pack(fill="x", pady=2)
            ac = av_colors[i % len(av_colors)] if activo else C["text3"]
            av = tk.Frame(row, bg=ac, width=28, height=28)
            av.pack(side="left", padx=(10, 8), pady=7)
            av.pack_propagate(False)
            tk.Label(av, text=nombre[0].upper(), font=("Segoe UI", 9, "bold"),
                     fg=C["white"], bg=ac).place(relx=0.5, rely=0.5, anchor="center")
            txt = tk.Frame(row, bg=row_bg)
            txt.pack(side="left", fill="x", expand=True)
            tk.Label(txt, text=f"{nombre} {apellido}"[:30], font=("Segoe UI", 9, "bold"),
                     fg=C["text"] if activo else C["text3"],
                     bg=row_bg, anchor="w").pack(anchor="w")
            tk.Label(txt, text=cargo or "Sin cargo", font=("Segoe UI", 8),
                     fg=C["text3"], bg=row_bg, anchor="w").pack(anchor="w")
            pill_bg, pill_fg, pill_txt = (
                (C["success_l"], C["success"], "Activo") if activo
                else (C["danger_l"], C["danger"], "Inactivo"))
            pill = tk.Frame(row, bg=pill_bg, padx=7, pady=3)
            pill.pack(side="right", padx=10)
            tk.Label(pill, text=pill_txt, font=("Segoe UI", 8, "bold"),
                     fg=pill_fg, bg=pill_bg).pack()
        if not rows:
            tk.Label(self._pers_inner, text="Sin personas registradas",
                     font=("Segoe UI", 9), fg=C["text3"], bg=C["card"]).pack(pady=20)
        self._pers_canvas.update_idletasks()
        self._pers_canvas.configure(scrollregion=self._pers_canvas.bbox("all"))

    # ── PÁGINA: LOGS ──────────────────────────
    def _build_page_logs(self, parent):
        page = tk.Frame(parent, bg=C["bg"])
        body = tk.Frame(page, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=24, pady=20)
        outer, card = self._card_frame(body, "Historial de actividad del sistema", "📜")
        outer.pack(fill="both", expand=True)
        filtros_fr = tk.Frame(card, bg=C["card"])
        filtros_fr.pack(fill="x", padx=20, pady=(12, 0))
        tk.Label(filtros_fr, text="Nivel:", font=("Segoe UI", 9), fg=C["text2"],
                 bg=C["card"]).pack(side="left", padx=(0, 8))
        self._log_nivel = tk.StringVar(value="TODOS")
        for val in ("TODOS", "INFO", "WARNING", "ERROR"):
            col = {"TODOS": C["text2"], "INFO": C["primary"],
                   "WARNING": C["warning"], "ERROR": C["danger"]}.get(val, C["text2"])
            tk.Radiobutton(filtros_fr, text=val, variable=self._log_nivel, value=val,
                           command=self._refresh_logs, font=("Segoe UI", 9, "bold"),
                           fg=col, bg=C["card"], selectcolor=C["primary_l"],
                           activebackground=C["card"],
                           activeforeground=col).pack(side="left", padx=8)
        tk.Label(filtros_fr, text="  Buscar:", font=("Segoe UI", 9),
                 fg=C["text2"], bg=C["card"]).pack(side="left", padx=(16, 6))
        self.ent_log_buscar = _entry(filtros_fr, width=20)
        self.ent_log_buscar.pack(side="left")
        self.ent_log_buscar.bind("<KeyRelease>", lambda e: self._refresh_logs())
        _btn(filtros_fr, "🔄", self._refresh_logs, C["border2"],
             fg=C["text2"], pad_x=8, pad_y=5).pack(side="right")

        style = ttk.Style()
        style.configure("Log.Treeview", background=C["white"], foreground=C["text"],
                         fieldbackground=C["white"], rowheight=28, font=("Segoe UI", 9), borderwidth=0)
        style.configure("Log.Treeview.Heading", background=C["sidebar"], foreground=C["white"],
                         font=("Segoe UI", 9, "bold"), relief="raised", padding=10)
        style.map("Log.Treeview",
                  background=[("selected", C["primary"]),  ("active", C["primary_l"])],
                  foreground=[("selected", C["white"]),     ("active", C["primary"])])

        tree_fr = tk.Frame(card, bg=C["border"], bd=1)
        tree_fr.pack(fill="both", expand=True, padx=20, pady=(10, 20))
        inner = tk.Frame(tree_fr, bg=C["white"])
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        cols = ("Fecha", "Usuario", "Nivel", "Acción", "Detalle")
        self.tree_logs = ttk.Treeview(inner, columns=cols, show="headings",
                                      selectmode="browse", style="Log.Treeview")
        for col, ancho in zip(cols, [140, 90, 80, 160, 320]):
            self.tree_logs.heading(col, text=col)
            self.tree_logs.column(col, width=ancho,
                                  anchor="center" if col == "Nivel" else "w")
        self.tree_logs.tag_configure("INFO",        background=C["primary_l"], foreground=C["text"])
        self.tree_logs.tag_configure("INFO_alt",    background=C["white"],     foreground=C["text"])
        self.tree_logs.tag_configure("WARNING",     background=C["warning_l"], foreground="#7C3E05")
        self.tree_logs.tag_configure("WARNING_alt", background="#FFFBF0",      foreground="#7C3E05")
        self.tree_logs.tag_configure("ERROR",       background=C["danger_l"],  foreground=C["danger"])
        self.tree_logs.tag_configure("ERROR_alt",   background="#FFF8F8",      foreground=C["danger"])
        sc_v = ttk.Scrollbar(inner, orient="vertical",   command=self.tree_logs.yview)
        sc_h = ttk.Scrollbar(inner, orient="horizontal", command=self.tree_logs.xview)
        self.tree_logs.configure(yscrollcommand=sc_v.set, xscrollcommand=sc_h.set)
        sc_v.pack(side="right", fill="y")
        sc_h.pack(side="bottom", fill="x")
        self.tree_logs.pack(fill="both", expand=True)
        return page

    def _refresh_logs(self):
        if not hasattr(self, "tree_logs"):
            return
        for r in self.tree_logs.get_children():
            self.tree_logs.delete(r)
        nivel  = self._log_nivel.get() if hasattr(self, "_log_nivel") else "TODOS"
        buscar = self.ent_log_buscar.get().strip().lower() if hasattr(self, "ent_log_buscar") else ""
        query  = "SELECT fecha,usuario,nivel,accion,detalle FROM logs"
        params = []
        if nivel != "TODOS":
            query += " WHERE nivel=?"
            params.append(nivel)
        query += " ORDER BY id DESC LIMIT 500"
        with sqlite3.connect(DB_PATH) as con:
            rows = con.execute(query, params).fetchall()
        for i, (fecha, usuario, niv, accion, detalle) in enumerate(rows):
            if buscar and buscar not in f"{usuario} {accion} {detalle or ''}".lower():
                continue
            suffix = "" if i % 2 == 0 else "_alt"
            icono  = {"INFO": "ℹ️", "WARNING": "⚠️", "ERROR": "❌"}.get(niv, "•")
            self.tree_logs.insert("", "end", tags=(f"{niv}{suffix}",),
                                values=(fecha, usuario or "—",
                                        f"{icono} {niv}", accion, detalle or ""))