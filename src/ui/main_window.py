"""Ventana principal y navegación base de la aplicación (RF-10 / RNF-04)."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from src.ui.contracts import EstudiantesService, SalasService, ReservacionesService
from src.ui.reservations_view import ReservationsView
from src.ui.reports_view import ReportsView
from src.ui.rooms_view import RoomsView
from src.ui.students_view import StudentsView
from src.ui.styles import configurar_estilos


class MainWindow(tk.Tk):
    def __init__(self, estudiantes_service: EstudiantesService, salas_service: SalasService, reservaciones_service: ReservacionesService) -> None:
        super().__init__()
        self.title("Sistema de reservación de salas de estudio")
        self.geometry("1120x700")
        self.minsize(900, 580)
        self._estudiantes_service = estudiantes_service
        self._salas_service = salas_service
        self._reservaciones_service = reservaciones_service
        configurar_estilos(self)

        self._contenedor = ttk.Frame(self, style="App.TFrame")
        self._contenedor.pack(fill="both", expand=True)
        self.protocol("WM_DELETE_WINDOW", self._salir)
        self.mostrar_inicio()

    def _limpiar(self) -> None:
        for widget in self._contenedor.winfo_children():
            widget.destroy()

    def mostrar_inicio(self) -> None:
        self._limpiar()
        vista = ttk.Frame(self._contenedor, style="App.TFrame", padding=28)
        vista.pack(fill="both", expand=True)

        ttk.Label(vista, text="Sistema de reservación de salas", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            vista,
            text="Seleccione un módulo para continuar.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(4, 24))

        grid = ttk.Frame(vista, style="App.TFrame")
        grid.pack(fill="both", expand=True)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        self._tarjeta(
            grid,
            0,
            0,
            "Estudiantes",
            "Registro, consulta, modificación, activación e inactivación.",
            lambda: self._mostrar_estudiantes(),
        )
        self._tarjeta(
            grid,
            0,
            1,
            "Salas",
            "Consulta, registro, edición de capacidad y cambio de estado.",
            lambda: self._mostrar_salas(),
        )
        self._tarjeta(
            grid,
            1,
            0,
            "Reservaciones",
            "Creación, consulta, modificación y cancelación de reservaciones.",
            lambda: self._mostrar_reservaciones(),
        )
        self._tarjeta(
            grid,
            1,
            1,
            "Panel, reportes e historial",
            "Consulte resportes de reservaciones por rango de fechas y el historial de reservaciones.",
            self._mostrar_reportes,
        )

        pie = ttk.Frame(vista, style="App.TFrame")
        pie.pack(fill="x", pady=(20, 0))
        ttk.Button(pie, text="Salir", command=self._salir, style="Secondary.TButton").pack(side="right")

    def _tarjeta(self, parent, fila: int, columna: int, titulo: str, descripcion: str, command) -> None:
        card = ttk.Frame(parent, style="Card.TFrame", padding=20)
        card.grid(row=fila, column=columna, sticky="nsew", padx=8, pady=8)
        ttk.Label(card, text=titulo, style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(card, text=descripcion, style="CardText.TLabel", wraplength=390).pack(anchor="w", pady=(8, 18))
        ttk.Button(card, text="Abrir", command=command, style="Primary.TButton").pack(anchor="w")

    def _mostrar_estudiantes(self) -> None:
        self._limpiar()
        StudentsView(self._contenedor, self._estudiantes_service, self.mostrar_inicio).pack(fill="both", expand=True)

    def _mostrar_salas(self) -> None:
        self._limpiar()
        RoomsView(self._contenedor, self._salas_service, self.mostrar_inicio).pack(fill="both", expand=True)

    def _mostrar_reservaciones(self) -> None:
        self._limpiar()
        ReservationsView(
            self._contenedor, 
            self._reservaciones_service, 
            self.mostrar_inicio
        ).pack(fill="both", expand=True)

    def _mostrar_reportes(self) -> None:
        self._limpiar()

        ReportsView(
            self._contenedor,
            self._reservaciones_service,
            self.mostrar_inicio
        ).pack(fill="both", expand=True)

    def _salir(self) -> None:
        if messagebox.askyesno("Salir", "¿Desea cerrar la aplicación?", parent=self):
            self.destroy()
