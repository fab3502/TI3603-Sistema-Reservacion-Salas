"""Diálogos reutilizables para formularios de estudiantes y salas."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable


class FormDialog(tk.Toplevel):
    """Ventana modal pequeña para capturar campos de texto."""

    def __init__(
        self,
        parent: tk.Misc,
        titulo: str,
        campos: list[tuple[str, str, str]],
        on_submit: Callable[[dict[str, str]], None],
        campo_bloqueado: str | None = None,
    ) -> None:
        super().__init__(parent)
        self.title(titulo)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self._on_submit = on_submit
        self._vars: dict[str, tk.StringVar] = {}

        cont = ttk.Frame(self, padding=18)
        cont.grid(row=0, column=0, sticky="nsew")

        for fila, (clave, etiqueta, valor) in enumerate(campos):
            ttk.Label(cont, text=etiqueta).grid(row=fila, column=0, sticky="w", padx=(0, 12), pady=7)
            var = tk.StringVar(value=valor)
            entry = ttk.Entry(cont, textvariable=var, width=38)
            entry.grid(row=fila, column=1, sticky="ew", pady=7)
            if clave == campo_bloqueado:
                entry.state(["disabled"])
            self._vars[clave] = var

        botones = ttk.Frame(cont)
        botones.grid(row=len(campos), column=0, columnspan=2, sticky="e", pady=(16, 0))
        ttk.Button(botones, text="Cancelar", command=self.destroy, style="Secondary.TButton").pack(side="right")
        ttk.Button(botones, text="Guardar", command=self._guardar, style="Primary.TButton").pack(
            side="right", padx=(0, 8)
        )

        self.bind("<Escape>", lambda _event: self.destroy())
        self.bind("<Return>", lambda _event: self._guardar())
        self.after(20, self._centrar)

    def _centrar(self) -> None:
        self.update_idletasks()
        parent = self.master.winfo_toplevel()
        x = parent.winfo_rootx() + max((parent.winfo_width() - self.winfo_width()) // 2, 0)
        y = parent.winfo_rooty() + max((parent.winfo_height() - self.winfo_height()) // 2, 0)
        self.geometry(f"+{x}+{y}")

    def _guardar(self) -> None:
        datos = {clave: var.get() for clave, var in self._vars.items()}
        self._on_submit(datos)
