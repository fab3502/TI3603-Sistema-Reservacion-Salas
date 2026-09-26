"""Pantalla de gestión de estudiantes (RF-02, RF-03 y RF-11)."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from src.ui.contracts import EstudianteDTO, EstudiantesService
from src.ui.dialogs import FormDialog


class StudentsView(ttk.Frame):
    def __init__(
        self,
        parent: tk.Misc,
        service: EstudiantesService,
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
        ttk.Label(encabezado, text="Gestión de estudiantes", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            encabezado,
            text="Registre, consulte, modifique y cambie el estado de estudiantes.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        barra = ttk.Frame(self, style="App.TFrame")
        barra.pack(fill="x", pady=(18, 10))
        ttk.Button(barra, text="Nuevo estudiante", command=self._nuevo, style="Primary.TButton").pack(side="left")
        ttk.Button(barra, text="Editar", command=self._editar, style="Secondary.TButton").pack(side="left", padx=8)
        ttk.Button(barra, text="Activar / Inactivar", command=self._cambiar_estado, style="Secondary.TButton").pack(
            side="left"
        )
        ttk.Button(barra, text="Actualizar", command=self.refrescar, style="Secondary.TButton").pack(side="left", padx=8)
        ttk.Button(barra, text="Volver", command=self._volver_inicio, style="Secondary.TButton").pack(side="right")

        cont_tabla = ttk.Frame(self, style="Card.TFrame", padding=1)
        cont_tabla.pack(fill="both", expand=True)

        columnas = ("carne", "nombre", "correo", "estado")
        self.tabla = ttk.Treeview(cont_tabla, columns=columnas, show="headings", selectmode="browse")
        self.tabla.heading("carne", text="Carné")
        self.tabla.heading("nombre", text="Nombre completo")
        self.tabla.heading("correo", text="Correo electrónico")
        self.tabla.heading("estado", text="Estado")
        self.tabla.column("carne", width=135, anchor="w")
        self.tabla.column("nombre", width=260, anchor="w")
        self.tabla.column("correo", width=300, anchor="w")
        self.tabla.column("estado", width=110, anchor="center")

        scroll = ttk.Scrollbar(cont_tabla, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll.set)
        self.tabla.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tabla.bind("<Double-1>", lambda _event: self._editar())

    def refrescar(self) -> None:
        for item in self.tabla.get_children():
            self.tabla.delete(item)
        try:
            estudiantes = self._service.listar_estudiantes()
        except Exception as exc:  # la GUI traduce el error técnico a un mensaje amigable
            messagebox.showerror("No se pudo cargar", str(exc), parent=self)
            return

        for estudiante in estudiantes:
            self.tabla.insert(
                "",
                "end",
                iid=estudiante["carne"],
                values=(
                    estudiante["carne"],
                    estudiante["nombre"],
                    estudiante["correo"],
                    estudiante["estado"],
                ),
            )

    def _seleccionado(self) -> EstudianteDTO | None:
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showinfo("Seleccione un estudiante", "Seleccione un estudiante para continuar.", parent=self)
            return None
        valores = self.tabla.item(seleccion[0], "values")
        return {
            "carne": str(valores[0]),
            "nombre": str(valores[1]),
            "correo": str(valores[2]),
            "estado": str(valores[3]),
        }

    def _nuevo(self) -> None:
        def guardar(datos: dict[str, str]) -> None:
            try:
                self._service.crear_estudiante(datos["carne"], datos["nombre"], datos["correo"])
            except (ValueError, RuntimeError) as exc:
                messagebox.showerror("No se pudo registrar", str(exc), parent=self)
                return
            dialog.destroy()
            self.refrescar()
            messagebox.showinfo("Registro exitoso", "El estudiante fue registrado correctamente.", parent=self)

        dialog = FormDialog(
            self,
            "Nuevo estudiante",
            [("carne", "Carné", ""), ("nombre", "Nombre completo", ""), ("correo", "Correo electrónico", "")],
            guardar,
        )

    def _editar(self) -> None:
        estudiante = self._seleccionado()
        if estudiante is None:
            return

        def guardar(datos: dict[str, str]) -> None:
            try:
                self._service.actualizar_estudiante(estudiante["carne"], datos["nombre"], datos["correo"])
            except (ValueError, RuntimeError) as exc:
                messagebox.showerror("No se pudo actualizar", str(exc), parent=self)
                return
            dialog.destroy()
            self.refrescar()
            messagebox.showinfo("Actualización exitosa", "Los datos del estudiante fueron actualizados.", parent=self)

        dialog = FormDialog(
            self,
            "Editar estudiante",
            [
                ("carne", "Carné", estudiante["carne"]),
                ("nombre", "Nombre completo", estudiante["nombre"]),
                ("correo", "Correo electrónico", estudiante["correo"]),
            ],
            guardar,
            campo_bloqueado="carne",
        )

    def _cambiar_estado(self) -> None:
        estudiante = self._seleccionado()
        if estudiante is None:
            return
        nuevo_estado = "inactivo" if estudiante["estado"].lower() == "activo" else "activo"
        confirmar = messagebox.askyesno(
            "Confirmar cambio de estado",
            f"¿Desea cambiar el estado de {estudiante['nombre']} a '{nuevo_estado}'?",
            parent=self,
        )
        if not confirmar:
            return
        try:
            self._service.cambiar_estado_estudiante(estudiante["carne"], nuevo_estado)
        except (ValueError, RuntimeError) as exc:
            messagebox.showerror("No se pudo cambiar el estado", str(exc), parent=self)
            return
        self.refrescar()
