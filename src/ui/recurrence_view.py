"""Interfaz para reservaciones recurrentes (RF-14)."""

import tkinter as tk
from tkinter import messagebox, ttk


class RecurrenceWindow(tk.Toplevel):
    def __init__(
        self,
        parent,
        reservaciones_service,
    ) -> None:
        super().__init__(parent)

        self._service = reservaciones_service

        self.title("Reservaciones recurrentes")
        self.geometry("850x620")
        self.minsize(750, 550)

        self._crear_formulario()
        self._crear_acciones()
        self._crear_resumen()
        self._crear_cancelacion()

        self.transient(parent.winfo_toplevel())
        self.grab_set()

    def _crear_formulario(self) -> None:
        contenedor = ttk.Frame(
            self,
            style="App.TFrame",
            padding=24,
        )
        contenedor.pack(
            fill="both",
            expand=True,
        )

        self._contenedor = contenedor

        ttk.Label(
            contenedor,
            text="Reservaciones recurrentes",
            style="Title.TLabel",
        ).pack(
            anchor="w",
            pady=(0, 5),
        )

        ttk.Label(
            contenedor,
            text="Cree una serie semanal de 2 a 8 ocurrencias.",
            style="Subtitle.TLabel",
        ).pack(
            anchor="w",
            pady=(0, 15),
        )

        card = ttk.Frame(
            contenedor,
            style="Card.TFrame",
            padding=15,
        )
        card.pack(
            fill="x",
            pady=(0, 12),
        )

        ttk.Label(
            card,
            text="Carné:",
            style="CardText.TLabel",
        ).grid(
            row=0,
            column=0,
            padx=5,
            pady=5,
            sticky="w",
        )

        self.entry_carne = ttk.Entry(
            card,
            width=22,
        )
        self.entry_carne.grid(
            row=0,
            column=1,
            padx=5,
            pady=5,
        )

        ttk.Label(
            card,
            text="Sala:",
            style="CardText.TLabel",
        ).grid(
            row=0,
            column=2,
            padx=5,
            pady=5,
            sticky="w",
        )

        self.combo_sala = ttk.Combobox(
            card,
            state="readonly",
            width=20,
        )
        self.combo_sala.grid(
            row=0,
            column=3,
            padx=5,
            pady=5,
        )

        ttk.Label(
            card,
            text="Fecha inicial:",
            style="CardText.TLabel",
        ).grid(
            row=1,
            column=0,
            padx=5,
            pady=5,
            sticky="w",
        )

        self.entry_fecha = ttk.Entry(
            card,
            width=22,
        )
        self.entry_fecha.grid(
            row=1,
            column=1,
            padx=5,
            pady=5,
        )

        ttk.Label(
            card,
            text="Hora:",
            style="CardText.TLabel",
        ).grid(
            row=1,
            column=2,
            padx=5,
            pady=5,
            sticky="w",
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
            width=20,
        )
        self.combo_hora.grid(
            row=1,
            column=3,
            padx=5,
            pady=5,
        )

        ttk.Label(
            card,
            text="Duración:",
            style="CardText.TLabel",
        ).grid(
            row=2,
            column=0,
            padx=5,
            pady=5,
            sticky="w",
        )

        self.combo_duracion = ttk.Combobox(
            card,
            values=[1, 2],
            state="readonly",
            width=20,
        )
        self.combo_duracion.grid(
            row=2,
            column=1,
            padx=5,
            pady=5,
        )

        ttk.Label(
            card,
            text="Personas:",
            style="CardText.TLabel",
        ).grid(
            row=2,
            column=2,
            padx=5,
            pady=5,
            sticky="w",
        )

        self.entry_personas = ttk.Entry(
            card,
            width=22,
        )
        self.entry_personas.grid(
            row=2,
            column=3,
            padx=5,
            pady=5,
        )

        ttk.Label(
            card,
            text="Ocurrencias:",
            style="CardText.TLabel",
        ).grid(
            row=3,
            column=0,
            padx=5,
            pady=5,
            sticky="w",
        )

        self.combo_ocurrencias = ttk.Combobox(
            card,
            values=[2, 3, 4, 5, 6, 7, 8],
            state="readonly",
            width=20,
        )
        self.combo_ocurrencias.grid(
            row=3,
            column=1,
            padx=5,
            pady=5,
        )

        self._cargar_salas()

    def _crear_acciones(self) -> None:
        frame = ttk.Frame(
            self._contenedor,
            style="App.TFrame",
        )
        frame.pack(
            fill="x",
            pady=(0, 12),
        )

        ttk.Button(
            frame,
            text="Revisar conflictos",
            command=self._validar,
            style="Secondary.TButton",
        ).pack(
            side="left",
            padx=(0, 8),
        )

        ttk.Button(
            frame,
            text="Crear serie",
            command=self._crear_serie,
            style="Primary.TButton",
        ).pack(side="left")

    def _crear_resumen(self) -> None:
        card = ttk.Frame(
            self._contenedor,
            style="Card.TFrame",
            padding=15,
        )
        card.pack(
            fill="both",
            expand=True,
            pady=(0, 12),
        )

        ttk.Label(
            card,
            text="Resumen de ocurrencias",
            style="CardTitle.TLabel",
        ).pack(
            anchor="w",
            pady=(0, 8),
        )

        columnas = (
            "numero",
            "fecha",
            "estado",
            "mensaje",
        )

        self.tabla = ttk.Treeview(
            card,
            columns=columnas,
            show="headings",
            height=7,
        )

        self.tabla.heading(
            "numero",
            text="#",
        )
        self.tabla.heading(
            "fecha",
            text="Fecha",
        )
        self.tabla.heading(
            "estado",
            text="Estado",
        )
        self.tabla.heading(
            "mensaje",
            text="Detalle",
        )

        self.tabla.column(
            "numero",
            width=50,
        )
        self.tabla.column(
            "fecha",
            width=110,
        )
        self.tabla.column(
            "estado",
            width=100,
        )
        self.tabla.column(
            "mensaje",
            width=400,
        )

        self.tabla.pack(
            fill="both",
            expand=True,
        )

    def _crear_cancelacion(self) -> None:
        frame = ttk.Frame(
            self._contenedor,
            style="App.TFrame",
        )
        frame.pack(fill="x")

        ttk.Label(
            frame,
            text="ID de ocurrencia:",
            style="Subtitle.TLabel",
        ).pack(side="left")

        self.entry_id = ttk.Entry(
            frame,
            width=15,
        )
        self.entry_id.pack(
            side="left",
            padx=8,
        )

        ttk.Button(
            frame,
            text="Cancelar ocurrencia",
            command=self._cancelar_ocurrencia,
            style="Danger.TButton",
        ).pack(
            side="left",
            padx=4,
        )

        ttk.Button(
            frame,
            text="Cancelar futuras",
            command=self._cancelar_futuras,
            style="Danger.TButton",
        ).pack(
            side="left",
            padx=4,
        )

    def _cargar_salas(self) -> None:
        try:
            salas = self._service.listar_salas_disponibles()

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

    def _validar(self) -> None:
        try:
            resultado = self._service.validar_recurrencia(
                self.entry_carne.get(),
                self.combo_sala.get(),
                self.entry_fecha.get(),
                self.combo_hora.get(),
                self.combo_duracion.get(),
                self.entry_personas.get(),
                self.combo_ocurrencias.get(),
            )

            self._mostrar_resultado(
                resultado["ocurrencias"]
            )

            if resultado["tiene_conflictos"]:
                messagebox.showwarning(
                    "Conflictos",
                    "La serie contiene conflictos.",
                    parent=self,
                )
            else:
                messagebox.showinfo(
                    "Disponibilidad",
                    "Todas las ocurrencias están disponibles.",
                    parent=self,
                )

        except ValueError as error:
            messagebox.showwarning(
                "Datos inválidos",
                str(error),
                parent=self,
            )

        except Exception:
            messagebox.showerror(
                "Error",
                "No fue posible validar la recurrencia.",
                parent=self,
            )

    def _mostrar_resultado(
        self,
        ocurrencias,
    ) -> None:
        for item in self.tabla.get_children():
            self.tabla.delete(item)

        for ocurrencia in ocurrencias:
            estado = (
                "Disponible"
                if ocurrencia["disponible"]
                else "Conflicto"
            )

            self.tabla.insert(
                "",
                "end",
                values=(
                    ocurrencia["ocurrencia"],
                    ocurrencia["fecha"],
                    estado,
                    ocurrencia["mensaje"],
                ),
            )

    def _crear_serie(self) -> None:
        try:
            resultado = (
                self._service.crear_serie_recurrente(
                    self.entry_carne.get(),
                    self.combo_sala.get(),
                    self.entry_fecha.get(),
                    self.combo_hora.get(),
                    self.combo_duracion.get(),
                    self.entry_personas.get(),
                    self.combo_ocurrencias.get(),
                )
            )

            messagebox.showinfo(
                "Serie creada",
                (
                    f"Serie {resultado['serie_id']} creada correctamente.\n"
                    f"Reservaciones creadas: {resultado['cantidad']}."
                ),
                parent=self,
            )

            for item in self.tabla.get_children():
                self.tabla.delete(item)

            
        except ValueError as error:
            messagebox.showwarning(
                "No se pudo crear la serie",
                str(error),
                parent=self,
            )

        except Exception as error:
            messagebox.showerror(
                "Error",
                f"No fue posible crear la serie recurrente.\n{error}",
                parent=self,
            )

    def _cancelar_ocurrencia(self) -> None:
        id_reservacion = (
            self.entry_id.get().strip()
        )

        if not id_reservacion:
            messagebox.showwarning(
                "Cancelar ocurrencia",
                "Ingrese un ID de reservación.",
                parent=self,
            )
            return

        try:
            resultado = (
                self._service.cancelar_ocurrencia(
                    id_reservacion
                )
            )

            messagebox.showinfo(
                "Ocurrencia cancelada",
                resultado["mensaje"],
                parent=self,
            )

        except ValueError as error:
            messagebox.showwarning(
                "Cancelar ocurrencia",
                str(error),
                parent=self,
            )

    def _cancelar_futuras(self) -> None:
        id_reservacion = (
            self.entry_id.get().strip()
        )

        if not id_reservacion:
            messagebox.showwarning(
                "Cancelar serie",
                "Ingrese un ID de reservación.",
                parent=self,
            )
            return

        confirmar = messagebox.askyesno(
            "Cancelar futuras",
            (
                "¿Desea cancelar esta ocurrencia "
                "y las futuras de la serie?"
            ),
            parent=self,
        )

        if not confirmar:
            return

        try:
            resultado = (
                self._service
                .cancelar_serie_desde_ocurrencia(
                    id_reservacion
                )
            )

            messagebox.showinfo(
                "Serie actualizada",
                (
                    "Reservaciones canceladas: "
                    f"{resultado['cantidad']}."
                ),
                parent=self,
            )

        except ValueError as error:
            messagebox.showwarning(
                "Cancelar serie",
                str(error),
                parent=self,
            )