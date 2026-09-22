"""Servicio de integración entre la interfaz gráfica y el backend real.

Este módulo conecta la GUI con:
- validaciones y reglas de negocio;
- operaciones de persistencia en SQLite.

La interfaz gráfica no accede directamente a SQL.
"""

import sqlite3
from src.validators.validaciones import ValidacionError
from src.database import db
from src.services.entidades_service import (
    validar_nuevo_estudiante,
    validar_modificacion_estudiante,
    validar_nueva_sala,
    validar_modificacion_sala,
)


class AppService:
    """Servicio utilizado por las pantallas de estudiantes y salas."""

    def __init__(self) -> None:
        db.inicializar_base_datos()
        self._conexion = db.obtener_conexion()

    # ------------------------------------------------------------------
    # Estudiantes
    # ------------------------------------------------------------------

    def listar_estudiantes(self):
        """Devuelve todos los estudiantes."""
        try:
            return db.listar_estudiantes(self._conexion)

        except sqlite3.Error as exc:
            raise RuntimeError(
                "No se pudieron consultar los estudiantes."
            ) from exc

    def crear_estudiante(
        self,
        carne: str,
        nombre: str,
        correo: str,
    ) -> None:
        """Valida y registra un estudiante nuevo."""
        try:
            datos = validar_nuevo_estudiante(
                self._conexion,
                carne,
                nombre,
                correo,
            )

            db.insertar_estudiante(
                self._conexion,
                datos["carne"],
                datos["nombre"],
                datos["correo"],
            )

        except ValidacionError as exc:
            raise ValueError(str(exc)) from exc

        except ValueError:
            raise

        except sqlite3.IntegrityError as exc:
            raise ValueError(
                "Ya existe un estudiante con ese carné."
            ) from exc

        except sqlite3.Error as exc:
            raise RuntimeError(
                "No se pudo registrar el estudiante."
            ) from exc

    def actualizar_estudiante(
        self,
        carne: str,
        nombre: str,
        correo: str,
    ) -> None:
        """Valida y actualiza nombre y correo."""
        try:
            estudiante = db.obtener_estudiante(
                self._conexion,
                carne,
            )

            if estudiante is None:
                raise ValueError(
                    "El estudiante no existe."
                )

            datos = validar_modificacion_estudiante(
                nombre,
                correo,
                estudiante["estado"],
            )

            db.actualizar_estudiante(
                self._conexion,
                carne,
                datos["nombre"],
                datos["correo"],
            )

        except ValidacionError as exc:
            raise ValueError(str(exc)) from exc

        except ValueError:
            raise

        except sqlite3.Error as exc:
            raise RuntimeError(
                "No se pudo actualizar el estudiante."
            ) from exc

    def cambiar_estado_estudiante(
        self,
        carne: str,
        estado: str,
    ) -> None:
        """Activa o inactiva un estudiante."""
        try:
            estudiante = db.obtener_estudiante(
                self._conexion,
                carne,
            )

            if estudiante is None:
                raise ValueError(
                    "El estudiante no existe."
                )

            datos = validar_modificacion_estudiante(
                estudiante["nombre"],
                estudiante["correo"],
                estado,
            )

            db.actualizar_estado_estudiante(
                self._conexion,
                carne,
                datos["estado"],
            )

        except ValidacionError as exc:
            raise ValueError(str(exc)) from exc

        except ValueError:
            raise

        except sqlite3.Error as exc:
            raise RuntimeError(
                "No se pudo cambiar el estado del estudiante."
            ) from exc

    # ------------------------------------------------------------------
    # Salas
    # ------------------------------------------------------------------

    def listar_salas(self):
        """Devuelve todas las salas."""
        try:
            return db.listar_salas(self._conexion)

        except sqlite3.Error as exc:
            raise RuntimeError(
                "No se pudieron consultar las salas."
            ) from exc

    def crear_sala(
        self,
        codigo: str,
        nombre: str,
        capacidad: str,
    ) -> None:
        """Valida y registra una sala nueva."""
        try:
            datos = validar_nueva_sala(
                self._conexion,
                codigo,
                nombre,
                capacidad,
            )

            db.insertar_sala(
                self._conexion,
                datos["codigo"],
                datos["nombre"],
                datos["capacidad"],
                datos["estado"],
            )

        except ValidacionError as exc:
            raise ValueError(str(exc)) from exc

        except ValueError:
            raise

        except sqlite3.IntegrityError as exc:
            raise ValueError(
                "Ya existe una sala con ese código."
            ) from exc

        except sqlite3.Error as exc:
            raise RuntimeError(
                "No se pudo registrar la sala."
            ) from exc

    def actualizar_sala(
        self,
        codigo: str,
        nombre: str,
        capacidad: str,
    ) -> None:
        """Valida y actualiza nombre y capacidad de una sala."""
        try:
            sala = db.obtener_sala(
                self._conexion,
                codigo,
            )

            if sala is None:
                raise ValueError(
                    "La sala no existe."
                )

            datos = validar_modificacion_sala(
                self._conexion,
                codigo,
                nombre,
                capacidad,
                sala["estado"],
            )

            db.actualizar_sala(
                self._conexion,
                codigo,
                datos["nombre"],
                datos["capacidad"],
                datos["estado"],
            )

        except ValidacionError as exc:
            raise ValueError(str(exc)) from exc

        except ValueError:
            raise

        except sqlite3.Error as exc:
            raise RuntimeError(
                "No se pudo actualizar la sala."
            ) from exc

    def cambiar_estado_sala(
        self,
        codigo: str,
        estado: str,
    ) -> None:
        """Cambia el estado de una sala."""
        try:
            sala = db.obtener_sala(
                self._conexion,
                codigo,
            )

            if sala is None:
                raise ValueError(
                    "La sala no existe."
                )

            datos = validar_modificacion_sala(
                self._conexion,
                codigo,
                sala["nombre"],
                sala["capacidad"],
                estado,
            )

            db.actualizar_estado_sala(
                self._conexion,
                codigo,
                datos["estado"],
            )

        except ValidacionError as exc:
            raise ValueError(str(exc)) from exc

        except ValueError:
            raise

        except sqlite3.Error as exc:
            raise RuntimeError(
                "No se pudo cambiar el estado de la sala."
            ) from exc

    # ------------------------------------------------------------------
    # Cierre
    # ------------------------------------------------------------------

    def cerrar(self) -> None:
        """Cierra la conexión SQLite utilizada por la aplicación."""
        if self._conexion is not None:
            self._conexion.close()
            self._conexion = None