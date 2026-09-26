"""Servicios temporales en memoria para desarrollar y demostrar la GUI.

IMPORTANTE: este archivo no reemplaza la capa de servicios/persistencia definitiva.
Se incluye únicamente para que la Parte 3 pueda ejecutarse mientras las Partes 1 y
2 implementan SQLite y las reglas de negocio. Al integrar el proyecto, ``main.py``
debe recibir las implementaciones reales.
"""

from __future__ import annotations

from copy import deepcopy

from src.ui.contracts import EstudianteDTO, SalaDTO


class DemoAppService:
    def __init__(self) -> None:
        self._estudiantes: dict[str, EstudianteDTO] = {
            "A001234567": {
                "carne": "A001234567",
                "nombre": "Andrea Solano",
                "correo": "andrea@universidad.ac.cr",
                "estado": "activo",
            },
            "B009876543": {
                "carne": "B009876543",
                "nombre": "Carlos Méndez",
                "correo": "carlos@universidad.ac.cr",
                "estado": "activo",
            },
            "C004567890": {
                "carne": "C004567890",
                "nombre": "Daniela Rojas",
                "correo": "daniela@universidad.ac.cr",
                "estado": "inactivo",
            },
        }
        self._salas: dict[str, SalaDTO] = {
            "S01": {"codigo": "S01", "nombre": "Sala Biblioteca 1", "capacidad": 4, "estado": "disponible"},
            "S02": {"codigo": "S02", "nombre": "Sala Biblioteca 2", "capacidad": 6, "estado": "disponible"},
            "S03": {"codigo": "S03", "nombre": "Laboratorio de estudio", "capacidad": 10, "estado": "disponible"},
            "S04": {"codigo": "S04", "nombre": "Sala multimedia", "capacidad": 8, "estado": "fuera_de_servicio"},
            "S05": {"codigo": "S05", "nombre": "Cubículo individual", "capacidad": 1, "estado": "disponible"},
        }

    def listar_estudiantes(self):
        return sorted((deepcopy(e) for e in self._estudiantes.values()), key=lambda e: e["nombre"].casefold())

    def crear_estudiante(self, carne: str, nombre: str, correo: str) -> None:
        carne = carne.strip().upper()
        nombre = nombre.strip()
        correo = correo.strip()
        if len(carne) != 10 or not carne.isalnum():
            raise ValueError("El carné debe contener exactamente 10 caracteres alfanuméricos.")
        if carne in self._estudiantes:
            raise ValueError("Ya existe un estudiante con ese carné.")
        if len(nombre) < 3:
            raise ValueError("El nombre debe contener al menos tres caracteres.")
        if correo.count("@") != 1 or "." not in correo.split("@", 1)[1]:
            raise ValueError("El correo electrónico no tiene un formato válido.")
        self._estudiantes[carne] = {"carne": carne, "nombre": nombre, "correo": correo, "estado": "activo"}

    def actualizar_estudiante(self, carne: str, nombre: str, correo: str) -> None:
        if carne not in self._estudiantes:
            raise ValueError("El estudiante no existe.")
        nombre = nombre.strip()
        correo = correo.strip()
        if len(nombre) < 3:
            raise ValueError("El nombre debe contener al menos tres caracteres.")
        if correo.count("@") != 1 or "." not in correo.split("@", 1)[1]:
            raise ValueError("El correo electrónico no tiene un formato válido.")
        self._estudiantes[carne]["nombre"] = nombre
        self._estudiantes[carne]["correo"] = correo

    def cambiar_estado_estudiante(self, carne: str, estado: str) -> None:
        if carne not in self._estudiantes:
            raise ValueError("El estudiante no existe.")
        if estado not in {"activo", "inactivo"}:
            raise ValueError("Estado de estudiante inválido.")
        self._estudiantes[carne]["estado"] = estado

    def listar_salas(self):
        return sorted((deepcopy(s) for s in self._salas.values()), key=lambda s: s["codigo"])

    def crear_sala(self, codigo: str, nombre: str, capacidad: str) -> None:
        codigo = codigo.strip().upper()
        nombre = nombre.strip()
        if not codigo:
            raise ValueError("El código de la sala es obligatorio.")
        if codigo in self._salas:
            raise ValueError("Ya existe una sala con ese código.")
        if not nombre:
            raise ValueError("El nombre de la sala es obligatorio.")
        try:
            capacidad_int = int(capacidad)
        except ValueError as exc:
            raise ValueError("La capacidad debe ser un número entero.") from exc
        if capacidad_int <= 0:
            raise ValueError("La capacidad debe ser mayor que cero.")
        self._salas[codigo] = {
            "codigo": codigo,
            "nombre": nombre,
            "capacidad": capacidad_int,
            "estado": "disponible",
        }

    def actualizar_sala(self, codigo: str, nombre: str, capacidad: str) -> None:
        if codigo not in self._salas:
            raise ValueError("La sala no existe.")
        nombre = nombre.strip()
        if not nombre:
            raise ValueError("El nombre de la sala es obligatorio.")
        try:
            capacidad_int = int(capacidad)
        except ValueError as exc:
            raise ValueError("La capacidad debe ser un número entero.") from exc
        if capacidad_int <= 0:
            raise ValueError("La capacidad debe ser mayor que cero.")
        self._salas[codigo]["nombre"] = nombre
        self._salas[codigo]["capacidad"] = capacidad_int

    def cambiar_estado_sala(self, codigo: str, estado: str) -> None:
        if codigo not in self._salas:
            raise ValueError("La sala no existe.")
        if estado not in {"disponible", "fuera_de_servicio"}:
            raise ValueError("Estado de sala inválido.")
        self._salas[codigo]["estado"] = estado
