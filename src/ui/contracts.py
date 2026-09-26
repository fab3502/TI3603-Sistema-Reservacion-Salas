"""Contratos mínimos que la interfaz gráfica espera de la capa de servicios.

Estos protocolos permiten desarrollar y probar la GUI sin acoplarla a SQLite ni a
las reglas de negocio. La implementación definitiva debe ser provista por las
capas ``services`` y ``database`` del proyecto.
"""

from __future__ import annotations

from typing import Protocol, Sequence, TypedDict


class EstudianteDTO(TypedDict):
    carne: str
    nombre: str
    correo: str
    estado: str


class SalaDTO(TypedDict):
    codigo: str
    nombre: str
    capacidad: int
    estado: str

class ReservacionDTO(TypedDict):
    id: str
    carne: str
    codigo_sala: str
    fecha: str
    hora_inicio: str
    hora_fin: str
    duracion: int
    cantidad_personas: int
    estado: str


class EstudiantesService(Protocol):
    def listar_estudiantes(self) -> Sequence[EstudianteDTO]: ...

    def crear_estudiante(self, carne: str, nombre: str, correo: str) -> None: ...

    def actualizar_estudiante(self, carne: str, nombre: str, correo: str) -> None: ...

    def cambiar_estado_estudiante(self, carne: str, estado: str) -> None: ...


class SalasService(Protocol):
    def listar_salas(self) -> Sequence[SalaDTO]: ...

    def crear_sala(self, codigo: str, nombre: str, capacidad: str) -> None: ...

    def actualizar_sala(self, codigo: str, nombre: str, capacidad: str) -> None: ...

    def cambiar_estado_sala(self, codigo: str, estado: str) -> None: ...

class ReservacionesService(Protocol):
    def listar(self) -> Sequence[ReservacionDTO]: ...

    def listar_por_rango_fechas(
        self,
        fecha_inicio: str,
        fecha_fin: str,
    ) -> Sequence[ReservacionDTO]: ...

    def crear(
        self,
        carne: str,
        codigo_sala: str,
        fecha: str,
        hora_inicio: str,
        duracion: str,
        cantidad_personas: str,
    ) -> dict: ...

    def buscar_por_estudiante(
        self,
        carne: str,
    ) -> Sequence[ReservacionDTO]: ...

    def modificar(
        self,
        id_reservacion: str,
        codigo_sala: str,
        fecha: str,
        hora_inicio: str,
        duracion: str,
        cantidad_personas: str,
    ) -> dict: ...

    def cancelar(
        self,
        id_reservacion: str,
    ) -> dict: ...

    def listar_salas_disponibles(
        self,
    ) -> Sequence[SalaDTO]: ...

    def consultar_disponibilidad(
        self,
        codigo_sala: str,
        fecha: str,
        hora_inicio: str,
        duracion: str,
    ) -> dict: ...

    def validar_recurrencia(
        self,
        carne: str,
        codigo_sala: str,
        fecha_inicial: str,
        hora_inicio: str,
        duracion: str,
        cantidad_personas: str,
        cantidad_ocurrencias: str,
    ) -> dict: ...

    def crear_serie_recurrente(
        self,
        carne: str,
        codigo_sala: str,
        fecha_inicial: str,
        hora_inicio: str,
        duracion: str,
        cantidad_personas: str,
        cantidad_ocurrencias: str,
    ) -> dict: ...

    def crear_serie_recurrente(
        self,
        carne: str,
        codigo_sala: str,
        fecha_inicial: str,
        hora_inicio: str,
        duracion: str,
        cantidad_personas: str,
        cantidad_ocurrencias: str,
    ) -> dict: ...

    def cancelar_ocurrencia(
        self,
        id_reservacion: str,
    ) -> dict: ...

    def cancelar_serie_desde_ocurrencia(
        self,
        id_reservacion: str,
    ) -> dict: ...