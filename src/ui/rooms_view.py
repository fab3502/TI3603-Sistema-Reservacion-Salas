"""Pantalla de gestión de salas (RF-04 y RF-12)."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from src.ui.contracts import SalaDTO, SalasService
from src.ui.dialogs import FormDialog


class RoomsView(ttk.Frame):
    def __init__(
        self,
        parent: tk.Misc,
        service: SalasService,
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
        ttk.Label(encabezado, text="Gestión de salas", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            encabezado,
            text="Consulte, registre y modifique las salas disponibles para reservación.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        barra = ttk.Frame(self, style="App.TFrame")
        barra.pack(fill="x", pady=(18, 10))
        ttk.Button(barra, text="Nueva sala", command=self._nueva, style="Primary.TButton").pack(side="left")
        ttk.Button(barra, text="Editar", command=self._editar, style="Secondary.TButton").pack(side="left", padx=8)
        ttk.Button(barra, text="Cambiar estado", command=self._cambiar_estado, style="Secondary.TButton").pack(side="left")
        ttk.Button(barra, text="Actualizar", command=self.refrescar, style="Secondary.TButton").pack(side="left", padx=8)
        ttk.Button(barra, text="Volver", command=self._volver_inicio, style="Secondary.TButton").pack(side="right")

        cont_tabla = ttk.Frame(self, style="Card.TFrame", padding=1)
        cont_tabla.pack(fill="both", expand=True)

        columnas = ("codigo", "nombre", "capacidad", "estado")
        self.tabla = ttk.Treeview(cont_tabla, columns=columnas, show="headings", selectmode="browse")
        self.tabla.heading("codigo", text="Código")
        self.tabla.heading("nombre", text="Nombre")
        self.tabla.heading("capacidad", text="Capacidad")
        self.tabla.heading("estado", text="Estado")
        self.tabla.column("codigo", width=110, anchor="w")
        self.tabla.column("nombre", width=350, anchor="w")
        self.tabla.column("capacidad", width=110, anchor="center")
        self.tabla.column("estado", width=160, anchor="center")

        scroll = ttk.Scrollbar(cont_tabla, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll.set)
        self.tabla.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tabla.bind("<Double-1>", lambda _event: self._editar())

    def refrescar(self) -> None:
        for item in self.tabla.get_children():
            self.tabla.delete(item)
        try:
            salas = self._service.listar_salas()
        except Exception as exc:
            messagebox.showerror("No se pudo cargar", str(exc), parent=self)
            return

        for sala in salas:
            self.tabla.insert(
                "",
                "end",
                iid=sala["codigo"],
                values=(sala["codigo"], sala["nombre"], sala["capacidad"], sala["estado"]),
            )

    def _seleccionada(self) -> SalaDTO | None:
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showinfo("Seleccione una sala", "Seleccione una sala para continuar.", parent=self)
            return None
        valores = self.tabla.item(seleccion[0], "values")
        return {
            "codigo": str(valores[0]),
            "nombre": str(valores[1]),
            "capacidad": int(valores[2]),
            "estado": str(valores[3]),
        }

    def _nueva(self) -> None:
        def guardar(datos: dict[str, str]) -> None:
            try:
                self._service.crear_sala(datos["codigo"], datos["nombre"], datos["capacidad"])
            except (ValueError, RuntimeError) as exc:
                messagebox.showerror("No se pudo registrar", str(exc), parent=self)
                return
            dialog.destroy()
            self.refrescar()
            messagebox.showinfo("Registro exitoso", "La sala fue registrada correctamente.", parent=self)

        dialog = FormDialog(
            self,
            "Nueva sala",
            [("codigo", "Código", ""), ("nombre", "Nombre", ""), ("capacidad", "Capacidad", "")],
            guardar,
        )

    def _editar(self) -> None:
        sala = self._seleccionada()
        if sala is None:
            return

        def guardar(datos: dict[str, str]) -> None:
            try:
                self._service.actualizar_sala(sala["codigo"], datos["nombre"], datos["capacidad"])
            except (ValueError, RuntimeError) as exc:
                messagebox.showerror("No se pudo actualizar", str(exc), parent=self)
                return
            dialog.destroy()
            self.refrescar()
            messagebox.showinfo("Actualización exitosa", "Los datos de la sala fueron actualizados.", parent=self)

        dialog = FormDialog(
            self,
            "Editar sala",
            [
                ("codigo", "Código", sala["codigo"]),
                ("nombre", "Nombre", sala["nombre"]),
                ("capacidad", "Capacidad", str(sala["capacidad"])),
            ],
            guardar,
            campo_bloqueado="codigo",
        )

    def _cambiar_estado(self) -> None:
        sala = self._seleccionada()
        if sala is None:
            return
        nuevo_estado = "fuera_de_servicio" if sala["estado"] == "disponible" else "disponible"
        confirmar = messagebox.askyesno(
            "Confirmar cambio de estado",
            f"¿Desea cambiar el estado de {sala['nombre']} a '{nuevo_estado}'?",
            parent=self,
        )
        if not confirmar:
            return
        try:
            self._service.cambiar_estado_sala(sala["codigo"], nuevo_estado)
        except (ValueError, RuntimeError) as exc:
            messagebox.showerror("No se pudo cambiar el estado", str(exc), parent=self)
            return
        self.refrescar()
