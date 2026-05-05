"""
main.py — Punto de entrada del Sistema de Asistencias a Capacitaciones.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk

from db import init_db
from vista import calentar_modelo
from ui import VentanaLogin, App


def _get_icon_path() -> str:
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "Logo.ico")


def aplicar_tema_global(widget):
    from config import C
    style = ttk.Style(widget)
    style.theme_use("clam")
    style.configure("Vertical.TScrollbar",
                    gripcount=0, background="#B8C8E0",
                    darkcolor="#B8C8E0", lightcolor="#B8C8E0",
                    troughcolor="#F0F4FA", bordercolor="#F0F4FA",
                    arrowcolor="#4A6090", arrowsize=12)
    style.configure("Horizontal.TScrollbar",
                    gripcount=0, background="#B8C8E0",
                    troughcolor="#F0F4FA", bordercolor="#F0F4FA",
                    arrowcolor="#4A6090", arrowsize=12)
    style.configure("TCombobox",
                    fieldbackground="white", background="white",
                    foreground="#1A2B4A", selectbackground="#1D4ED8",
                    selectforeground="white", bordercolor="#CBD5E1",
                    lightcolor="#CBD5E1", darkcolor="#CBD5E1",
                    arrowcolor="#4A6090")
    style.map("TCombobox",
                fieldbackground=[("readonly", "white")],
                foreground=[("readonly", "#1A2B4A")])
    style.configure("TSpinbox",
                    fieldbackground="white", foreground="#1A2B4A",
                    bordercolor="#CBD5E1", arrowcolor="#4A6090")


def main():
    init_db()
    calentar_modelo()

    icon_path = _get_icon_path()

    # Root invisible — existe durante toda la vida del programa
    # App y VentanaLogin son Toplevel hijos de este root
    root = tk.Tk()
    root.withdraw()
    root.title("Sistema de Asistencias")
    try:
        root.iconbitmap(default=icon_path)
    except Exception:
        pass
    aplicar_tema_global(root)

    # ── LOOP PRINCIPAL ────────────────────────────────────────────────────────
    while True:
        # 1. Login
        login = VentanaLogin(root)
        root.wait_window(login)

        if login.resultado is None:
            break                       # cerró el login → salir

        username, rol = login.resultado

        # 2. Ventana principal (Toplevel)
        app = App(root, username, rol)
        try:
            app.iconbitmap(icon_path)
        except Exception:
            pass
        aplicar_tema_global(app)
        root.wait_window(app)           # bloquea hasta que App se destruya

        # 3. ¿Logout o salida real?
        if not getattr(app, "_pedir_logout", False):
            break                       # salida confirmada → terminar

        # logout → vuelve al inicio del while → muestra login de nuevo

    root.destroy()


if __name__ == "__main__":
    main()