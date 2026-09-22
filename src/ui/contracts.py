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
