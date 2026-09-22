"""Configuración visual compartida por las pantallas de la aplicación."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


COLOR_FONDO = "#F5F7FA"
COLOR_PANEL = "#FFFFFF"
COLOR_PRIMARIO = "#0B6E99"
COLOR_PRIMARIO_OSCURO = "#075779"
COLOR_TEXTO = "#1F2937"
COLOR_TEXTO_SECUNDARIO = "#5B6472"
COLOR_BORDE = "#D9DEE7"
COLOR_PELIGRO = "#B42318"
COLOR_EXITO = "#067647"


def configurar_estilos(root: tk.Misc) -> None:
    """Aplica una apariencia consistente usando únicamente Tkinter/ttk."""
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    root.configure(bg=COLOR_FONDO)

    style.configure("App.TFrame", background=COLOR_FONDO)
    style.configure("Card.TFrame", background=COLOR_PANEL)
    style.configure(
        "Title.TLabel",
        background=COLOR_FONDO,
        foreground=COLOR_TEXTO,
        font=("Segoe UI", 20, "bold"),
    )
    style.configure(
        "Subtitle.TLabel",
        background=COLOR_FONDO,
        foreground=COLOR_TEXTO_SECUNDARIO,
        font=("Segoe UI", 10),
    )
    style.configure(
        "CardTitle.TLabel",
        background=COLOR_PANEL,
        foreground=COLOR_TEXTO,
        font=("Segoe UI", 12, "bold"),
    )
    style.configure(
        "CardText.TLabel",
        background=COLOR_PANEL,
        foreground=COLOR_TEXTO_SECUNDARIO,
        font=("Segoe UI", 10),
    )
    style.configure(
        "Primary.TButton",
        font=("Segoe UI", 10, "bold"),
        padding=(14, 8),
        background=COLOR_PRIMARIO,
        foreground="white",
    )
    style.map(
        "Primary.TButton",
        background=[("active", COLOR_PRIMARIO_OSCURO)],
        foreground=[("disabled", "#E5E7EB")],
    )
    style.configure("Secondary.TButton", font=("Segoe UI", 10), padding=(12, 8))
    style.configure("Danger.TButton", font=("Segoe UI", 10), padding=(12, 8))

    style.configure(
        "Treeview",
        font=("Segoe UI", 10),
        rowheight=30,
        background="white",
        fieldbackground="white",
        foreground=COLOR_TEXTO,
        bordercolor=COLOR_BORDE,
    )
    style.configure(
        "Treeview.Heading",
        font=("Segoe UI", 10, "bold"),
        background="#EAF2F7",
        foreground=COLOR_TEXTO,
        padding=(8, 8),
    )
    style.map("Treeview", background=[("selected", "#D8EDF7")], foreground=[("selected", COLOR_TEXTO)])
