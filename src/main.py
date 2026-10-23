"""Punto de entrada de la aplicación (RF-01: inicio seguro de SQLite)."""

import sqlite3
import sys
import tkinter as tk
from tkinter import messagebox

from src.services.app_service import AppService
from src.ui.main_window import MainWindow


_MENSAJE_BD = (
    "No se pudo abrir o inicializar la base de datos de reservaciones.\n\n"
    "La aplicación se cerrará para evitar cambios en los datos. "
    "Conserve el archivo data/reservas.db y solicite ayuda para "
    "revisarlo o restaurar una copia de seguridad."
)


def main() -> int:
    try:
        service = AppService()
    except (sqlite3.DatabaseError, OSError):
        # La base puede no ser SQLite, estar dañada, inaccesible o bloqueada.
        # No se elimina ni se reemplaza: evitar pérdida de datos (RNF-06).
        try:
            messagebox.showerror("Error al iniciar la base de datos", _MENSAJE_BD)
        except tk.TclError:
            # Para ambientes sin pantalla: mensaje legible, sin traceback técnico.
            print(_MENSAJE_BD, file=sys.stderr)
        return 1

    try:
        app = MainWindow(
            estudiantes_service=service,
            salas_service=service,
            reservaciones_service=service,
            panel_service=service,
        )
        app.mainloop()
    finally:
        service.cerrar()

    return 0


if __name__ == "__main__":
    sys.exit(main())
