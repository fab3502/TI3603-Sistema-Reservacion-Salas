"""Interfaz para la gestión de reservaciones."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from src.ui.recurrence_view import RecurrenceWindow

class ReservationsView(ttk.Frame):
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

        self._crear_encabezado()
        self._crear_formulario()
        self._crear_disponibilidad()
        self._crear_busqueda()
        self._crear_botones()
        self._crear_tabla()

        self._cargar_salas()
        self._cargar_reservaciones()

        

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
            text="Gestión de reservaciones",
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
            text=(
                "Cree, consulte, modifique y cancele "
                "reservaciones de salas."
            ),
            style="Subtitle.TLabel",
        ).pack(
            anchor="w",
            pady=(0, 15),
        )

    # ---------------------------------------------------------
    # Formulario
    # ---------------------------------------------------------

    def _crear_formulario(self) -> None:
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
            text="Datos de la reservación",
            style="CardTitle.TLabel",
        ).grid(
            row=0,
            column=0,
            columnspan=4,
            sticky="w",
            pady=(0, 15),
        )

        # ID
        ttk.Label(
            card,
            text="ID:",
            style="CardText.TLabel",
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=5,
            pady=5,
        )

        self.entry_id = ttk.Entry(
            card,
            width=25,
            state="readonly",
        )
        self.entry_id.grid(
            row=1,
            column=1,
            padx=5,
            pady=5,
        )

        # Carné
        ttk.Label(
            card,
            text="Carné:",
            style="CardText.TLabel",
        ).grid(
            row=1,
            column=2,
            sticky="w",
            padx=5,
            pady=5,
        )

        self.entry_carne = ttk.Entry(
            card,
            width=25,
        )
        self.entry_carne.grid(
            row=1,
            column=3,
            padx=5,
            pady=5,
        )

        # Sala
        ttk.Label(
            card,
            text="Sala:",
            style="CardText.TLabel",
        ).grid(
            row=2,
            column=0,
            sticky="w",
            padx=5,
            pady=5,
        )

        self.combo_sala = ttk.Combobox(
            card,
            state="readonly",
            width=22,
        )
        self.combo_sala.grid(
            row=2,
            column=1,
            padx=5,
            pady=5,
        )

        # Fecha
        ttk.Label(
            card,
            text="Fecha (AAAA-MM-DD):",
            style="CardText.TLabel",
        ).grid(
            row=2,
            column=2,
            sticky="w",
            padx=5,
            pady=5,
        )

        self.entry_fecha = ttk.Entry(
            card,
            width=25,
        )
        self.entry_fecha.grid(
            row=2,
            column=3,
            padx=5,
            pady=5,
        )

        # Hora
        ttk.Label(
            card,
            text="Hora de inicio:",
            style="CardText.TLabel",
        ).grid(
            row=3,
            column=0,
            sticky="w",
            padx=5,
            pady=5,
        )

        self.combo_hora = ttk.Combobox(
            card,
            values=[
                "08:00",
                "09:00",
                "10:00",
                "11:00",
                "12:00",
                "13:00",
                "14:00",
                "15:00",
                "16:00",
                "17:00",
                "18:00",
                "19:00",
            ],
            state="readonly",
            width=22,
        )
        self.combo_hora.grid(
            row=3,
            column=1,
            padx=5,
            pady=5,
        )

        # Duración
        ttk.Label(
            card,
            text="Duración:",
            style="CardText.TLabel",
        ).grid(
            row=3,
            column=2,
            sticky="w",
            padx=5,
            pady=5,
        )

        self.combo_duracion = ttk.Combobox(
            card,
            values=[1, 2],
            state="readonly",
            width=22,
        )
        self.combo_duracion.grid(
            row=3,
            column=3,
            padx=5,
            pady=5,
        )

        # Personas
        ttk.Label(
            card,
            text="Cantidad de personas:",
            style="CardText.TLabel",
        ).grid(
            row=4,
            column=0,
            sticky="w",
            padx=5,
            pady=5,
        )

        self.entry_personas = ttk.Entry(
            card,
            width=25,
        )
        self.entry_personas.grid(
            row=4,
            column=1,
            padx=5,
            pady=5,
        )


    # ---------------------------------------------------------
    # Disponibilidad
    # ---------------------------------------------------------

    def _crear_disponibilidad(self) -> None:
        frame = ttk.Frame(
            self,
            style="App.TFrame",
        )

        frame.pack(
            fill="x",
            pady=(0, 10),
        )

        ttk.Label(
            frame,
            text="Disponibilidad:",
            style="Subtitle.TLabel",
        ).pack(
            side="left"
        )

        ttk.Button(
            frame,
            text="Consultar horario seleccionado",
            command=self._consultar_disponibilidad,
            style="Secondary.TButton",
        ).pack(
            side="left",
            padx=8,
        )

        self.label_disponibilidad = ttk.Label(
            frame,
            text="",
            style="CardText.TLabel",
        )

        self.label_disponibilidad.pack(
            side="left",
            padx=8,
        )


    # ---------------------------------------------------------
    # Búsqueda
    # ---------------------------------------------------------

    def _crear_busqueda(self) -> None:
        frame = ttk.Frame(
            self,
            style="App.TFrame",
        )
        frame.pack(
            fill="x",
            pady=(0, 10),
        )

        ttk.Label(
            frame,
            text="Buscar por carné:",
            style="Subtitle.TLabel",
        ).pack(side="left")

        self.entry_busqueda = ttk.Entry(
            frame,
            width=25,
        )
        self.entry_busqueda.pack(
            side="left",
            padx=8,
        )

        ttk.Button(
            frame,
            text="Buscar",
            command=self._buscar,
            style="Secondary.TButton",
        ).pack(
            side="left",
            padx=4,
        )

        ttk.Button(
            frame,
            text="Mostrar todas",
            command=self._cargar_reservaciones,
            style="Secondary.TButton",
        ).pack(
            side="left",
            padx=4,
        )

    # ---------------------------------------------------------
    # Botones
    # ---------------------------------------------------------

    def _crear_botones(self) -> None:
        frame = ttk.Frame(
            self,
            style="App.TFrame",
        )
        frame.pack(
            fill="x",
            pady=(0, 10),
        )

        ttk.Button(
            frame,
            text="Crear reservación",
            command=self._crear,
            style="Primary.TButton",
        ).pack(
            side="left",
            padx=4,
        )

        ttk.Button(
            frame,
            text="Recurrencia",
            command=self._abrir_recurrencia,
            style="Secondary.TButton",
        ).pack(
            side="left",
            padx=4,
        )

        ttk.Button(
            frame,
            text="Modificar",
            command=self._modificar,
            style="Secondary.TButton",
        ).pack(
            side="left",
            padx=4,
        )

        ttk.Button(
            frame,
            text="Cancelar reservación",
            command=self._cancelar,
            style="Danger.TButton",
        ).pack(
            side="left",
            padx=4,
        )

        ttk.Button(
            frame,
            text="Limpiar",
            command=self._limpiar_formulario,
            style="Secondary.TButton",
        ).pack(
            side="left",
            padx=4,
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
            "inicio",
            "fin",
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
            "inicio": "Inicio",
            "fin": "Fin",
            "duracion": "Duración",
            "personas": "Personas",
            "estado": "Estado",
        }

        for columna, texto in encabezados.items():
            self.tabla.heading(
                columna,
                text=texto,
            )

        self.tabla.column("id", width=75)
        self.tabla.column("carne", width=110)
        self.tabla.column("sala", width=70)
        self.tabla.column("fecha", width=100)
        self.tabla.column("inicio", width=70)
        self.tabla.column("fin", width=70)
        self.tabla.column("duracion", width=75)
        self.tabla.column("personas", width=80)
        self.tabla.column("estado", width=90)

        self.tabla.pack(
            fill="both",
            expand=True,
        )

        self.tabla.bind(
            "<<TreeviewSelect>>",
            self._seleccionar_reserva,
        )

    # ---------------------------------------------------------
    # Cargas
    # ---------------------------------------------------------

    def _cargar_salas(self) -> None:
        try:
            salas = (
                self._service
                .listar_salas_disponibles()
            )

            self.combo_sala["values"] = [
                sala["codigo"]
                for sala in salas
            ]

        except Exception:
            messagebox.showerror(
                "Error",
                "No fue posible cargar las salas.",
                parent=self,
            )

    def _cargar_reservaciones(self) -> None:
        try:
            reservaciones = (
                self._service.listar()
            )

            self._mostrar_reservaciones(
                reservaciones
            )

        except Exception:
            messagebox.showerror(
                "Error",
                "No fue posible consultar las reservaciones.",
                parent=self,
            )

    def _mostrar_reservaciones(
        self,
        reservaciones,
    ) -> None:

        for item in self.tabla.get_children():
            self.tabla.delete(item)

        for reserva in reservaciones:
            self.tabla.insert(
                "",
                "end",
                values=(
                    reserva["id"],
                    reserva["carne"],
                    reserva["codigo_sala"],
                    reserva["fecha"],
                    reserva["hora_inicio"],
                    reserva["hora_fin"],
                    reserva["duracion"],
                    reserva["cantidad_personas"],
                    reserva["estado"],
                ),
            )

    # ---------------------------------------------------------
    # Consultar disponibilidad
    # ---------------------------------------------------------

    def _consultar_disponibilidad(self) -> None:
        try:
            resultado = self._service.consultar_disponibilidad(
                self.combo_sala.get(),
                self.entry_fecha.get(),
                self.combo_hora.get(),
                self.combo_duracion.get(),
            )

            if resultado["disponible"]:
                self.label_disponibilidad.configure(
                    text="Disponible"
                )
            else:
                self.label_disponibilidad.configure(
                    text="No disponible"
                )

            messagebox.showinfo(
                "Disponibilidad",
                resultado["mensaje"],
                parent=self,
            )

        except ValueError as error:
            self.label_disponibilidad.configure(
                text=""
            )

            messagebox.showwarning(
                "Datos inválidos",
                str(error),
                parent=self,
            )

        except Exception:
            self.label_disponibilidad.configure(
                text=""
            )

            messagebox.showerror(
                "Error",
                "No fue posible consultar la disponibilidad.",
                parent=self,
            )

    # ---------------------------------------------------------
    # Recurrencia
    # ---------------------------------------------------------

    def _abrir_recurrencia(self) -> None:
        RecurrenceWindow(
            self,
            self._service,
        )

    # ---------------------------------------------------------
    # Crear
    # ---------------------------------------------------------

    def _crear(self) -> None:
        try:
            resultado = self._service.crear(
                self.entry_carne.get(),
                self.combo_sala.get(),
                self.entry_fecha.get(),
                self.combo_hora.get(),
                self.combo_duracion.get(),
                self.entry_personas.get(),
            )

            messagebox.showinfo(
                "Reservación creada",
                resultado["mensaje"],
                parent=self,
            )

            self._limpiar_formulario()
            self._cargar_reservaciones()

        except ValueError as error:
            messagebox.showwarning(
                "Datos inválidos",
                str(error),
                parent=self,
            )

        except Exception:
            messagebox.showerror(
                "Error",
                "No fue posible crear la reservación.",
                parent=self,
            )

    # ---------------------------------------------------------
    # Buscar
    # ---------------------------------------------------------

    def _buscar(self) -> None:
        carne = (
            self.entry_busqueda
            .get()
            .strip()
        )

        if not carne:
            messagebox.showwarning(
                "Búsqueda",
                "Ingrese un carné para buscar.",
                parent=self,
            )
            return

        try:
            reservaciones = (
                self._service
                .buscar_por_estudiante(carne)
            )

            if not reservaciones:
                messagebox.showinfo(
                    "Búsqueda",
                    "El estudiante no posee reservaciones.",
                    parent=self,
                )

            self._mostrar_reservaciones(
                reservaciones
            )

        except ValueError as error:
            messagebox.showwarning(
                "Búsqueda",
                str(error),
                parent=self,
            )

    # ---------------------------------------------------------
    # Modificar
    # ---------------------------------------------------------

    def _modificar(self) -> None:
        id_reservacion = (
            self.entry_id
            .get()
            .strip()
        )

        if not id_reservacion:
            messagebox.showwarning(
                "Modificar reservación",
                "Seleccione una reservación.",
                parent=self,
            )
            return

        try:
            resultado = self._service.modificar(
                id_reservacion,
                self.combo_sala.get(),
                self.entry_fecha.get(),
                self.combo_hora.get(),
                self.combo_duracion.get(),
                self.entry_personas.get(),
            )

            messagebox.showinfo(
                "Reservación modificada",
                resultado["mensaje"],
                parent=self,
            )

            self._limpiar_formulario()
            self._cargar_reservaciones()

        except ValueError as error:
            messagebox.showwarning(
                "Datos inválidos",
                str(error),
                parent=self,
            )

        except Exception:
            messagebox.showerror(
                "Error",
                "No fue posible modificar la reservación.",
                parent=self,
            )

    # ---------------------------------------------------------
    # Cancelar
    # ---------------------------------------------------------

    def _cancelar(self) -> None:
        id_reservacion = (
            self.entry_id
            .get()
            .strip()
        )

        if not id_reservacion:
            messagebox.showwarning(
                "Cancelar reservación",
                "Seleccione una reservación.",
                parent=self,
            )
            return

        confirmar = messagebox.askyesno(
            "Cancelar reservación",
            (
                "¿Desea cancelar la reservación "
                f"{id_reservacion}?"
            ),
            parent=self,
        )

        if not confirmar:
            return

        try:
            resultado = self._service.cancelar(
                id_reservacion
            )

            messagebox.showinfo(
                "Reservación cancelada",
                resultado["mensaje"],
                parent=self,
            )

            self._limpiar_formulario()
            self._cargar_reservaciones()

        except ValueError as error:
            messagebox.showwarning(
                "Cancelar reservación",
                str(error),
                parent=self,
            )

    # ---------------------------------------------------------
    # Selección
    # ---------------------------------------------------------

    def _seleccionar_reserva(
        self,
        event=None,
    ) -> None:

        seleccion = self.tabla.selection()

        if not seleccion:
            return

        valores = self.tabla.item(
            seleccion[0],
            "values",
        )

        self._limpiar_formulario()

        self.entry_id.configure(
            state="normal"
        )
        self.entry_id.insert(
            0,
            valores[0],
        )
        self.entry_id.configure(
            state="readonly"
        )

        self.entry_carne.insert(
            0,
            valores[1],
        )

        self.combo_sala.set(
            valores[2]
        )

        self.entry_fecha.insert(
            0,
            valores[3],
        )

        self.combo_hora.set(
            valores[4]
        )

        self.combo_duracion.set(
            valores[6]
        )

        self.entry_personas.insert(
            0,
            valores[7],
        )

    # ---------------------------------------------------------
    # Limpiar
    # ---------------------------------------------------------

    def _limpiar_formulario(self) -> None:
        self.entry_id.configure(
            state="normal"
        )
        self.entry_id.delete(
            0,
            tk.END,
        )
        self.entry_id.configure(
            state="readonly"
        )

        self.entry_carne.delete(
            0,
            tk.END,
        )
        self.entry_fecha.delete(
            0,
            tk.END,
        )
        self.entry_personas.delete(
            0,
            tk.END,
        )
        self.label_disponibilidad.configure(
            text=""
        )

        self.combo_sala.set("")
        self.combo_hora.set("")
        self.combo_duracion.set("")