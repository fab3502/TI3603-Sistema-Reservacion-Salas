"""Historial de acciones / auditoría (RF-17, parte visual).

La pantalla es de solo lectura: no ofrece botones para crear, editar ni
eliminar registros de auditoría.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from src.ui.contracts import PanelService

OPCION_TODAS = "Todas"

ETIQUETAS_ACCION = {
    "creacion": "Creación",
    "actualizacion": "Modificación",
    "cancelacion": "Cancelación",
}

ETIQUETAS_ENTIDAD = {
    "estudiante": "Estudiante",
    "sala": "Sala",
    "reservacion": "Reservación",
}


class HistoryView(ttk.Frame):
    def __init__(
        self,
        parent: tk.Misc,
        service: PanelService,
        volver_inicio: Callable[[], None],
    ) -> None:
        super().__init__(parent, style="App.TFrame", padding=24)
        self._service = service
        self._volver_inicio = volver_inicio
        self._crear_contenido()
        self.refrescar()

    def _crear_contenido(self) -> None:
        encabezado = ttk.Frame(self, style="App.TFrame")
        encabezado.pack(fill="x")
        ttk.Label(encabezado, text="Historial de acciones", style="Title.TLabel").pack(side="left")
        ttk.Button(encabezado, text="Volver", command=self._volver_inicio, style="Secondary.TButton").pack(
            side="right"
        )
        ttk.Label(
            self,
            text="Registro de creaciones, modificaciones y cancelaciones. Solo consulta: los registros no se pueden editar.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(4, 12))

        filtros = ttk.Frame(self, style="Card.TFrame", padding=(14, 10))
        filtros.pack(fill="x", pady=(0, 12))

        ttk.Label(filtros, text="Entidad:", style="Filter.TLabel").grid(row=0, column=0, padx=(0, 6))
        self.var_entidad = tk.StringVar(value=OPCION_TODAS)
        ttk.Combobox(
            filtros,
            textvariable=self.var_entidad,
            values=(OPCION_TODAS, *ETIQUETAS_ENTIDAD.values()),
            state="readonly",
            width=14,
        ).grid(row=0, column=1, padx=(0, 16))

        ttk.Label(filtros, text="Acción:", style="Filter.TLabel").grid(row=0, column=2, padx=(0, 6))
        self.var_accion = tk.StringVar(value=OPCION_TODAS)
        ttk.Combobox(
            filtros,
            textvariable=self.var_accion,
            values=(OPCION_TODAS, *ETIQUETAS_ACCION.values()),
            state="readonly",
            width=14,
        ).grid(row=0, column=3, padx=(0, 16))

        ttk.Label(filtros, text="Fecha (AAAA-MM-DD):", style="Filter.TLabel").grid(row=0, column=4, padx=(0, 6))
        self.var_fecha = tk.StringVar()
        entry = ttk.Entry(filtros, textvariable=self.var_fecha, width=14)
        entry.grid(row=0, column=5, padx=(0, 16))
        entry.bind("<Return>", lambda _e: self.refrescar())

        ttk.Button(filtros, text="Buscar", command=self.refrescar, style="Primary.TButton").grid(
            row=0, column=6, padx=(0, 8)
        )
        ttk.Button(filtros, text="Limpiar", command=self._limpiar, style="Secondary.TButton").grid(row=0, column=7)

        card = ttk.Frame(self, style="Card.TFrame", padding=(12, 8))
        card.pack(fill="both", expand=True)

        self.lbl_total = ttk.Label(card, text="", style="Section.TLabel")
        self.lbl_total.pack(anchor="w", pady=(0, 6))

        cont = ttk.Frame(card, style="Card.TFrame")
        cont.pack(fill="both", expand=True)

        columnas = ("fecha_hora", "accion", "entidad", "identificador")
        # selectmode="browse" permite leer una fila, pero no existe ninguna
        # acción de edición asociada (RF-17: no editable desde la interfaz).
        self.tabla = ttk.Treeview(cont, columns=columnas, show="headings", selectmode="browse")
        for col, texto, ancho in (
            ("fecha_hora", "Fecha y hora", 200),
            ("accion", "Tipo de acción", 180),
            ("entidad", "Entidad", 180),
            ("identificador", "Identificador afectado", 220),
        ):
            self.tabla.heading(col, text=texto)
            self.tabla.column(col, width=ancho, anchor="w" if col != "fecha_hora" else "center")

        scroll = ttk.Scrollbar(cont, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll.set)

        self.lbl_vacio = ttk.Label(
            cont,
            text="No hay acciones registradas que coincidan con los filtros.",
            style="Empty.TLabel",
        )
        self.tabla.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    @staticmethod
    def _clave(etiquetas: dict[str, str], texto: str) -> str | None:
        for clave, etiqueta in etiquetas.items():
            if etiqueta == texto:
                return clave
        return None

    def _limpiar(self) -> None:
        self.var_entidad.set(OPCION_TODAS)
        self.var_accion.set(OPCION_TODAS)
        self.var_fecha.set("")
        self.refrescar()

    def refrescar(self) -> None:
        try:
            registros = self._service.listar_historial(
                entidad=self._clave(ETIQUETAS_ENTIDAD, self.var_entidad.get()),
                tipo_accion=self._clave(ETIQUETAS_ACCION, self.var_accion.get()),
                fecha=self.var_fecha.get(),
            )
        except ValueError as exc:
            messagebox.showerror("Filtro inválido", str(exc), parent=self)
            return
        except Exception:
            messagebox.showerror(
                "No se pudo cargar",
                "No fue posible consultar el historial. Intente de nuevo.",
                parent=self,
            )
            return

        for item in self.tabla.get_children():
            self.tabla.delete(item)

        for registro in registros:
            self.tabla.insert(
                "",
                "end",
                values=(
                    registro["fecha_hora"],
                    ETIQUETAS_ACCION.get(registro["tipo_accion"], registro["tipo_accion"]),
                    ETIQUETAS_ENTIDAD.get(registro["entidad"], registro["entidad"]),
                    registro["identificador"],
                ),
            )

        self.lbl_total.configure(text=f"{len(registros)} registro(s), del más reciente al más antiguo")

        if registros:
            self.lbl_vacio.pack_forget()
        else:
            self.lbl_vacio.pack(before=self.tabla, fill="x")
