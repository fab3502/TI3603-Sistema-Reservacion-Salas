"""Ventana principal y navegación base de la aplicación (RF-10 / RNF-04)."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from src.ui.contracts import EstudiantesService, PanelService, SalasService, ReservacionesService
from src.ui.dashboard_view import DashboardView
from src.ui.history_view import HistoryView
from src.ui.reservations_view import ReservationsView
from src.ui.reports_view import ReportsView
from src.ui.rooms_view import RoomsView
from src.ui.students_view import StudentsView
from src.ui.styles import configurar_estilos


class MainWindow(tk.Tk):
    def __init__(
        self,
        estudiantes_service: EstudiantesService,
        salas_service: SalasService,
        reservaciones_service: ReservacionesService,
        panel_service: PanelService | None = None,
    ) -> None:
        super().__init__()
        self.title("Sistema de reservación de salas de estudio")
        self.geometry("1120x700")
        self.minsize(900, 580)
        self._estudiantes_service = estudiantes_service
        self._salas_service = salas_service
        self._reservaciones_service = reservaciones_service
        # Parte 5: si no se indica, se usa el mismo servicio de reservaciones.
        self._panel_service = panel_service or reservaciones_service
        configurar_estilos(self)

        self._contenedor = ttk.Frame(self, style="App.TFrame")
        self._contenedor.pack(fill="both", expand=True)
        self.protocol("WM_DELETE_WINDOW", self._salir)
        self.mostrar_inicio()

    def _limpiar(self) -> None:
        for widget in self._contenedor.winfo_children():
            widget.destroy()

    def mostrar_inicio(self) -> None:
        """Pantalla principal (RF-15): resumen del día y acceso a los módulos."""
        self._limpiar()
        vista = ttk.Frame(self._contenedor, style="App.TFrame", padding=(28, 22))
        vista.pack(fill="both", expand=True)

        ttk.Label(vista, text="Sistema de reservación de salas", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            vista,
            text="Resumen de hoy. Seleccione un módulo para continuar.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(4, 14))

        self._resumen_inicio(vista)

        grid = ttk.Frame(vista, style="App.TFrame")
        grid.pack(fill="both", expand=True)
        for columna in range(3):
            grid.columnconfigure(columna, weight=1, uniform="modulos")

        modulos = [
            ("Panel de control", "Ocupación por sala, próximas reservaciones e indicadores con filtros.", self._mostrar_panel),
            ("Reservaciones", "Creación, consulta, modificación, cancelación y recurrencia.", self._mostrar_reservaciones),
            ("Estudiantes", "Registro, consulta, modificación, activación e inactivación.", self._mostrar_estudiantes),
            ("Salas", "Consulta, registro, edición de capacidad y cambio de estado.", self._mostrar_salas),
            ("Reportes", "Reservaciones por rango de fechas y exportación a CSV.", self._mostrar_reportes),
            ("Historial de acciones", "Consulta de creaciones, modificaciones y cancelaciones.", self._mostrar_historial),
        ]
        for indice, (titulo, descripcion, comando) in enumerate(modulos):
            self._tarjeta(grid, indice // 3, indice % 3, titulo, descripcion, comando)

        pie = ttk.Frame(vista, style="App.TFrame")
        pie.pack(fill="x", pady=(14, 0))
        ttk.Button(pie, text="Salir", command=self._salir, style="Secondary.TButton").pack(side="right")

    def _resumen_inicio(self, parent) -> None:
        """Indicadores rápidos del día; si fallan, la pantalla sigue funcionando."""
        fila = ttk.Frame(parent, style="App.TFrame")
        fila.pack(fill="x", pady=(0, 10))
        try:
            ind = self._panel_service.obtener_panel()["indicadores"]
            valores = [
                (str(ind["reservas_hoy"]), "Reservas activas hoy"),
                (str(ind["proximas"]), "Próximas reservas"),
                (f"{ind['salas_disponibles']}/{ind['salas_total']}", "Salas disponibles"),
                (f"{ind['ocupacion_promedio']} %", "Ocupación promedio hoy"),
            ]
        except Exception:
            valores = [("—", "Indicadores no disponibles")]

        for columna, (valor, texto) in enumerate(valores):
            fila.columnconfigure(columna, weight=1, uniform="resumen")
            tile = ttk.Frame(fila, style="Card.TFrame", padding=(14, 8))
            tile.grid(row=0, column=columna, sticky="nsew", padx=(0 if columna == 0 else 8, 0))
            ttk.Label(tile, text=valor, style="KpiValue.TLabel").pack(anchor="w")
            ttk.Label(tile, text=texto, style="KpiLabel.TLabel").pack(anchor="w")

    def _tarjeta(self, parent, fila: int, columna: int, titulo: str, descripcion: str, command) -> None:
        card = ttk.Frame(parent, style="Card.TFrame", padding=18)
        card.grid(row=fila, column=columna, sticky="nsew", padx=6, pady=6)
        ttk.Label(card, text=titulo, style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(card, text=descripcion, style="CardText.TLabel", wraplength=280).pack(anchor="w", pady=(8, 14))
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

    def _mostrar_panel(self) -> None:
        self._limpiar()
        DashboardView(self._contenedor, self._panel_service, self.mostrar_inicio).pack(fill="both", expand=True)

    def _mostrar_historial(self) -> None:
        self._limpiar()
        HistoryView(self._contenedor, self._panel_service, self.mostrar_inicio).pack(fill="both", expand=True)

    def _salir(self) -> None:
        if messagebox.askyesno("Salir", "¿Desea cerrar la aplicación?", parent=self):
            self.destroy()
