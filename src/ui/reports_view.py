from __future__ import annotations

import csv
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


class ReportsView(ttk.Frame):
    def __init__(
        self,
        parent,
        reservaciones_service,
        volver_inicio,
    ) -> None:
        super().__init__(
            parent,
            style="App.TFrame",
            padding=28,
        )

        self._service = reservaciones_service
        self._volver_inicio = volver_inicio
        self._reservaciones_actuales = []

        self._crear_encabezado()
        self._crear_filtros()
        self._crear_tabla()

    # ---------------------------------------------------------
    # Encabezado
    # ---------------------------------------------------------

    def _crear_encabezado(self) -> None:
        encabezado = ttk.Frame(
            self,
            style="App.TFrame",
        )
        encabezado.pack(
            fill="x",
            pady=(0, 20),
        )

        ttk.Label(
            encabezado,
            text="Reportes de reservaciones",
            style="Title.TLabel",
        ).pack(side="left")

        ttk.Button(
            encabezado,
            text="Volver",
            command=self._volver_inicio,
            style="Secondary.TButton",
        ).pack(side="right")

        ttk.Label(
            self,
            text="Consulte reservaciones por rango de fechas y expórtelas a CSV.",
            style="Subtitle.TLabel",
        ).pack(
            anchor="w",
            pady=(0, 15),
        )

    # ---------------------------------------------------------
    # Filtros
    # ---------------------------------------------------------

    def _crear_filtros(self) -> None:
        card = ttk.Frame(
            self,
            style="Card.TFrame",
            padding=20,
        )
        card.pack(
            fill="x",
            pady=(0, 15),
        )

        ttk.Label(
            card,
            text="Fecha inicial (AAAA-MM-DD):",
            style="CardText.TLabel",
        ).grid(
            row=0,
            column=0,
            padx=5,
            pady=5,
            sticky="w",
        )

        self.entry_fecha_inicio = ttk.Entry(
            card,
            width=20,
        )
        self.entry_fecha_inicio.grid(
            row=0,
            column=1,
            padx=5,
            pady=5,
        )

        ttk.Label(
            card,
            text="Fecha final (AAAA-MM-DD):",
            style="CardText.TLabel",
        ).grid(
            row=0,
            column=2,
            padx=5,
            pady=5,
            sticky="w",
        )

        self.entry_fecha_fin = ttk.Entry(
            card,
            width=20,
        )
        self.entry_fecha_fin.grid(
            row=0,
            column=3,
            padx=5,
            pady=5,
        )

        ttk.Button(
            card,
            text="Generar reporte",
            command=self._generar_reporte,
            style="Primary.TButton",
        ).grid(
            row=0,
            column=4,
            padx=8,
            pady=5,
        )

        ttk.Button(
            card,
            text="Exportar CSV",
            command=self._exportar_csv,
            style="Secondary.TButton",
        ).grid(
            row=0,
            column=5,
            padx=8,
            pady=5,
        )

    # ---------------------------------------------------------
    # Tabla
    # ---------------------------------------------------------

    def _crear_tabla(self) -> None:
        card = ttk.Frame(
            self,
            style="Card.TFrame",
            padding=15,
        )
        card.pack(
            fill="both",
            expand=True,
        )

        columnas = (
            "id",
            "carne",
            "sala",
            "fecha",
            "hora",
            "duracion",
            "personas",
            "estado",
        )

        self.tabla = ttk.Treeview(
            card,
            columns=columnas,
            show="headings",
        )

        encabezados = {
            "id": "ID",
            "carne": "Carné",
            "sala": "Sala",
            "fecha": "Fecha",
            "hora": "Hora",
            "duracion": "Duración",
            "personas": "Personas",
            "estado": "Estado",
        }

        for columna, texto in encabezados.items():
            self.tabla.heading(
                columna,
                text=texto,
            )

        self.tabla.column("id", width=80)
        self.tabla.column("carne", width=110)
        self.tabla.column("sala", width=80)
        self.tabla.column("fecha", width=100)
        self.tabla.column("hora", width=80)
        self.tabla.column("duracion", width=80)
        self.tabla.column("personas", width=80)
        self.tabla.column("estado", width=90)

        self.tabla.pack(
            fill="both",
            expand=True,
        )

    # ---------------------------------------------------------
    # Generar reporte
    # ---------------------------------------------------------

    def _generar_reporte(self) -> None:
        fecha_inicio = self.entry_fecha_inicio.get().strip()
        fecha_fin = self.entry_fecha_fin.get().strip()

        if not fecha_inicio or not fecha_fin:
            messagebox.showwarning(
                "Reporte",
                "Ingrese la fecha inicial y la fecha final.",
                parent=self,
            )
            return

        try:
            reservaciones = self._service.listar_por_rango_fechas(
                fecha_inicio,
                fecha_fin,
            )

            self._reservaciones_actuales = list(reservaciones)

            for item in self.tabla.get_children():
                self.tabla.delete(item)

            for reserva in self._reservaciones_actuales:
                self.tabla.insert(
                    "",
                    "end",
                    values=(
                        reserva["id"],
                        reserva["carne"],
                        reserva["codigo_sala"],
                        reserva["fecha"],
                        reserva["hora_inicio"],
                        reserva["duracion"],
                        reserva["cantidad_personas"],
                        reserva["estado"],
                    ),
                )

        except Exception as error:
            messagebox.showerror(
                "Error",
                f"No fue posible generar el reporte.\n{error}",
                parent=self,
            )

    # ---------------------------------------------------------
    # Exportar CSV
    # ---------------------------------------------------------

    def _exportar_csv(self) -> None:
        if not self._reservaciones_actuales:
            messagebox.showwarning(
                "Exportar CSV",
                "Primero genere un reporte.",
                parent=self,
            )
            return

        ruta = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=".csv",
            filetypes=[
                ("Archivo CSV", "*.csv"),
            ],
            title="Guardar reporte",
        )

        if not ruta:
            return

        try:
            with open(
                ruta,
                "w",
                newline="",
                encoding="utf-8-sig",
            ) as archivo:
                escritor = csv.writer(archivo)

                escritor.writerow(
                    [
                        "ID",
                        "Carné",
                        "Sala",
                        "Fecha",
                        "Hora de inicio",
                        "Duración",
                        "Cantidad de personas",
                        "Estado",
                    ]
                )

                for reserva in self._reservaciones_actuales:
                    escritor.writerow(
                        [
                            reserva["id"],
                            reserva["carne"],
                            reserva["codigo_sala"],
                            reserva["fecha"],
                            reserva["hora_inicio"],
                            reserva["duracion"],
                            reserva["cantidad_personas"],
                            reserva["estado"],
                        ]
                    )

            messagebox.showinfo(
                "Exportación completada",
                "El archivo CSV se exportó correctamente.",
                parent=self,
            )

        except OSError as error:
            messagebox.showerror(
                "Error",
                f"No fue posible guardar el archivo.\n{error}",
                parent=self,
            )