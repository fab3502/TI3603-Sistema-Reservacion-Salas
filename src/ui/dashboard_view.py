"""Panel de control: ocupación, próximas reservaciones e indicadores (RF-15).

La pantalla consulta el servicio cada vez que se abre o se aplican filtros,
por lo que siempre refleja las reservaciones creadas, modificadas o
canceladas en las demás pantallas.
"""

from __future__ import annotations

import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk
from typing import Callable

from src.ui.contracts import PanelService
from src.ui.styles import COLOR_TEXTO_SECUNDARIO

OPCION_TODAS = "Todas"
OPCION_TODOS = "Todos"


def barra_ocupacion(porcentaje: int, bloques: int = 10) -> str:
    """Representa un porcentaje como una barra de texto: ██████░░░░ 60 %."""
    porcentaje = max(0, min(int(porcentaje), 100))
    llenos = round(porcentaje * bloques / 100)
    return f"{'█' * llenos}{'░' * (bloques - llenos)}  {porcentaje} %"


class DashboardView(ttk.Frame):
    def __init__(
        self,
        parent: tk.Misc,
        service: PanelService,
        volver_inicio: Callable[[], None],
    ) -> None:
        super().__init__(parent, style="App.TFrame", padding=(24, 18))
        self._service = service
        self._volver_inicio = volver_inicio
        self._kpis: dict[str, ttk.Label] = {}

        self._crear_encabezado()
        self._crear_filtros()
        self._crear_indicadores()
        self._crear_tablas_superiores()
        self._crear_tabla_reservaciones()

        self._cargar_salas()
        self.refrescar()

    # ------------------------------------------------------------------
    # Construcción de la interfaz
    # ------------------------------------------------------------------

    def _crear_encabezado(self) -> None:
        encabezado = ttk.Frame(self, style="App.TFrame")
        encabezado.pack(fill="x")
        ttk.Label(encabezado, text="Panel de control", style="Title.TLabel").pack(side="left")
        ttk.Button(encabezado, text="Volver", command=self._volver_inicio, style="Secondary.TButton").pack(
            side="right"
        )
        ttk.Button(encabezado, text="Actualizar", command=self.refrescar, style="Secondary.TButton").pack(
            side="right", padx=8
        )
        ttk.Label(
            self,
            text="Ocupación por sala, próximas reservaciones e indicadores. Los filtros se pueden combinar.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(2, 10))

    def _crear_filtros(self) -> None:
        card = ttk.Frame(self, style="Card.TFrame", padding=(14, 10))
        card.pack(fill="x", pady=(0, 10))

        ttk.Label(card, text="Fecha (AAAA-MM-DD):", style="Filter.TLabel").grid(row=0, column=0, padx=(0, 6))
        self.var_fecha = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        entry_fecha = ttk.Entry(card, textvariable=self.var_fecha, width=14)
        entry_fecha.grid(row=0, column=1, padx=(0, 16))
        entry_fecha.bind("<Return>", lambda _e: self.refrescar())

        ttk.Label(card, text="Sala:", style="Filter.TLabel").grid(row=0, column=2, padx=(0, 6))
        self.var_sala = tk.StringVar(value=OPCION_TODAS)
        self.combo_sala = ttk.Combobox(card, textvariable=self.var_sala, state="readonly", width=12)
        self.combo_sala.grid(row=0, column=3, padx=(0, 16))

        ttk.Label(card, text="Estado:", style="Filter.TLabel").grid(row=0, column=4, padx=(0, 6))
        self.var_estado = tk.StringVar(value=OPCION_TODOS)
        ttk.Combobox(
            card,
            textvariable=self.var_estado,
            values=(OPCION_TODOS, "activa", "cancelada"),
            state="readonly",
            width=12,
        ).grid(row=0, column=5, padx=(0, 16))

        ttk.Button(card, text="Aplicar filtros", command=self.refrescar, style="Primary.TButton").grid(
            row=0, column=6, padx=(0, 8)
        )
        ttk.Button(card, text="Limpiar", command=self._limpiar_filtros, style="Secondary.TButton").grid(
            row=0, column=7
        )

    def _crear_indicadores(self) -> None:
        fila = ttk.Frame(self, style="App.TFrame")
        fila.pack(fill="x", pady=(0, 10))

        indicadores = [
            ("reservas_hoy", "Reservas activas hoy"),
            ("proximas", "Próximas reservas"),
            ("activas_total", "Activas en total"),
            ("canceladas_total", "Canceladas"),
            ("salas", "Salas disponibles"),
            ("ocupacion", "Ocupación promedio"),
        ]

        for columna, (clave, texto) in enumerate(indicadores):
            fila.columnconfigure(columna, weight=1, uniform="kpi")
            tile = ttk.Frame(fila, style="Card.TFrame", padding=(12, 8))
            tile.grid(row=0, column=columna, sticky="nsew", padx=(0 if columna == 0 else 6, 0))
            valor = ttk.Label(tile, text="—", style="KpiValue.TLabel")
            valor.pack(anchor="w")
            ttk.Label(tile, text=texto, style="KpiLabel.TLabel").pack(anchor="w")
            self._kpis[clave] = valor

    def _crear_tablas_superiores(self) -> None:
        fila = ttk.Frame(self, style="App.TFrame")
        fila.pack(fill="x", pady=(0, 10))
        fila.columnconfigure(0, weight=3, uniform="sup")
        fila.columnconfigure(1, weight=2, uniform="sup")

        # Ocupación por sala
        card_ocup = ttk.Frame(fila, style="Card.TFrame", padding=(12, 8))
        card_ocup.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.lbl_ocupacion = ttk.Label(card_ocup, text="Ocupación por sala", style="Section.TLabel")
        self.lbl_ocupacion.pack(anchor="w", pady=(0, 6))

        columnas = ("codigo", "nombre", "estado", "reservas", "ocupacion")
        self.tabla_ocupacion = ttk.Treeview(card_ocup, columns=columnas, show="headings", height=5, selectmode="none")
        for col, texto, ancho, anchor in (
            ("codigo", "Sala", 60, "center"),
            ("nombre", "Nombre", 160, "w"),
            ("estado", "Estado", 125, "center"),
            ("reservas", "Reservas", 85, "center"),
            ("ocupacion", "Ocupación del día", 175, "w"),
        ):
            self.tabla_ocupacion.heading(col, text=texto)
            self.tabla_ocupacion.column(col, width=ancho, anchor=anchor, stretch=col in ("nombre", "ocupacion"))
        self.tabla_ocupacion.tag_configure("fuera", foreground=COLOR_TEXTO_SECUNDARIO)
        self.lbl_ocupacion_vacia = ttk.Label(card_ocup, text="No hay salas para mostrar.", style="Empty.TLabel")
        self.tabla_ocupacion.pack(fill="both", expand=True)

        # Próximas reservaciones
        card_prox = ttk.Frame(fila, style="Card.TFrame", padding=(12, 8))
        card_prox.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        ttk.Label(card_prox, text="Próximas reservaciones", style="Section.TLabel").pack(anchor="w", pady=(0, 6))

        columnas = ("id", "fecha", "horario", "sala", "estudiante")
        self.tabla_proximas = ttk.Treeview(card_prox, columns=columnas, show="headings", height=5, selectmode="none")
        for col, texto, ancho, anchor in (
            ("id", "ID", 58, "center"),
            ("fecha", "Fecha", 90, "center"),
            ("horario", "Horario", 102, "center"),
            ("sala", "Sala", 58, "center"),
            ("estudiante", "Estudiante", 110, "w"),
        ):
            self.tabla_proximas.heading(col, text=texto)
            self.tabla_proximas.column(col, width=ancho, anchor=anchor, stretch=col == "estudiante")
        self.lbl_proximas_vacia = ttk.Label(
            card_prox, text="No hay próximas reservaciones activas.", style="Empty.TLabel"
        )
        self.tabla_proximas.pack(fill="both", expand=True)

    def _crear_tabla_reservaciones(self) -> None:
        card = ttk.Frame(self, style="Card.TFrame", padding=(12, 8))
        card.pack(fill="both", expand=True)

        self.lbl_reservaciones = ttk.Label(card, text="Reservaciones del día", style="Section.TLabel")
        self.lbl_reservaciones.pack(anchor="w", pady=(0, 6))

        cont = ttk.Frame(card, style="Card.TFrame")
        cont.pack(fill="both", expand=True)

        columnas = ("id", "estudiante", "sala", "fecha", "inicio", "fin", "personas", "estado")
        self.tabla_reservaciones = ttk.Treeview(cont, columns=columnas, show="headings", height=6, selectmode="browse")
        for col, texto, ancho, anchor in (
            ("id", "ID", 70, "center"),
            ("estudiante", "Estudiante", 220, "w"),
            ("sala", "Sala", 170, "w"),
            ("fecha", "Fecha", 100, "center"),
            ("inicio", "Inicio", 70, "center"),
            ("fin", "Fin", 70, "center"),
            ("personas", "Personas", 85, "center"),
            ("estado", "Estado", 90, "center"),
        ):
            self.tabla_reservaciones.heading(col, text=texto)
            self.tabla_reservaciones.column(col, width=ancho, anchor=anchor, stretch=col in ("estudiante", "sala"))
        self.tabla_reservaciones.tag_configure("cancelada", foreground=COLOR_TEXTO_SECUNDARIO)

        scroll = ttk.Scrollbar(cont, orient="vertical", command=self.tabla_reservaciones.yview)
        self.tabla_reservaciones.configure(yscrollcommand=scroll.set)

        self.lbl_reservaciones_vacia = ttk.Label(
            cont,
            text="No hay reservaciones que coincidan con los filtros seleccionados.",
            style="Empty.TLabel",
        )
        self.tabla_reservaciones.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    # ------------------------------------------------------------------
    # Datos
    # ------------------------------------------------------------------

    def _cargar_salas(self) -> None:
        try:
            salas = self._service.listar_salas()
        except Exception:
            salas = []
        self.combo_sala["values"] = [OPCION_TODAS] + [sala["codigo"] for sala in salas]

    def _limpiar_filtros(self) -> None:
        self.var_fecha.set(date.today().strftime("%Y-%m-%d"))
        self.var_sala.set(OPCION_TODAS)
        self.var_estado.set(OPCION_TODOS)
        self.refrescar()

    def refrescar(self) -> None:
        """Consulta nuevamente el servicio y actualiza toda la pantalla."""
        try:
            panel = self._service.obtener_panel(
                fecha=self.var_fecha.get(),
                codigo_sala=self.var_sala.get(),
                estado=self.var_estado.get(),
            )
        except ValueError as exc:
            messagebox.showerror("Filtro inválido", str(exc), parent=self)
            return
        except Exception:
            messagebox.showerror(
                "No se pudo cargar",
                "No fue posible cargar la información del panel. Intente de nuevo.",
                parent=self,
            )
            return

        self._mostrar_indicadores(panel["indicadores"])
        self._mostrar_ocupacion(panel)
        self._mostrar_proximas(panel["proximas"])
        self._mostrar_reservaciones(panel)

    def _mostrar_indicadores(self, ind: dict) -> None:
        self._kpis["reservas_hoy"].configure(text=str(ind["reservas_hoy"]))
        self._kpis["proximas"].configure(text=str(ind["proximas"]))
        self._kpis["activas_total"].configure(text=str(ind["activas_total"]))
        self._kpis["canceladas_total"].configure(text=str(ind["canceladas_total"]))
        self._kpis["salas"].configure(text=f"{ind['salas_disponibles']}/{ind['salas_total']}")
        self._kpis["ocupacion"].configure(text=f"{ind['ocupacion_promedio']} %")

    @staticmethod
    def _vaciar(tabla: ttk.Treeview) -> None:
        for item in tabla.get_children():
            tabla.delete(item)

    @staticmethod
    def _alternar_vacio(tabla: ttk.Treeview, etiqueta: ttk.Label, vacio: bool) -> None:
        if vacio:
            etiqueta.pack(before=tabla, fill="x")
        else:
            etiqueta.pack_forget()

    def _mostrar_ocupacion(self, panel: dict) -> None:
        self._vaciar(self.tabla_ocupacion)
        self.lbl_ocupacion.configure(text=f"Ocupación por sala — {panel['fecha_consulta']}")
        for sala in panel["ocupacion"]:
            fuera = sala["estado"] != "disponible"
            self.tabla_ocupacion.insert(
                "",
                "end",
                values=(
                    sala["codigo"],
                    sala["nombre"],
                    "Fuera de servicio" if fuera else "Disponible",
                    sala["reservas"],
                    "No reservable" if fuera else barra_ocupacion(sala["porcentaje"]),
                ),
                tags=("fuera",) if fuera else (),
            )
        self._alternar_vacio(self.tabla_ocupacion, self.lbl_ocupacion_vacia, not panel["ocupacion"])

    def _mostrar_proximas(self, proximas: list) -> None:
        self._vaciar(self.tabla_proximas)
        for reserva in proximas:
            self.tabla_proximas.insert(
                "",
                "end",
                values=(
                    reserva["id"],
                    reserva["fecha"],
                    f"{reserva['hora_inicio']}–{reserva['hora_fin']}",
                    reserva["codigo_sala"],
                    reserva.get("nombre_estudiante") or reserva["carne"],
                ),
            )
        self._alternar_vacio(self.tabla_proximas, self.lbl_proximas_vacia, not proximas)

    def _mostrar_reservaciones(self, panel: dict) -> None:
        self._vaciar(self.tabla_reservaciones)

        filtros = panel["filtros"]
        detalle = [panel["fecha_consulta"]]
        if filtros["codigo_sala"]:
            detalle.append(f"sala {filtros['codigo_sala']}")
        if filtros["estado"]:
            detalle.append(f"estado {filtros['estado']}")
        self.lbl_reservaciones.configure(
            text=f"Reservaciones ({', '.join(detalle)}) — {len(panel['reservaciones'])} resultado(s)"
        )

        for reserva in panel["reservaciones"]:
            estudiante = reserva.get("nombre_estudiante") or ""
            self.tabla_reservaciones.insert(
                "",
                "end",
                values=(
                    reserva["id"],
                    f"{estudiante} ({reserva['carne']})" if estudiante else reserva["carne"],
                    f"{reserva['codigo_sala']} · {reserva.get('nombre_sala') or ''}",
                    reserva["fecha"],
                    reserva["hora_inicio"],
                    reserva["hora_fin"],
                    reserva["cantidad_personas"],
                    reserva["estado"],
                ),
                tags=(reserva["estado"],),
            )

        self._alternar_vacio(self.tabla_reservaciones, self.lbl_reservaciones_vacia, not panel["hay_resultados"])
