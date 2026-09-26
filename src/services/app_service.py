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
from src.services.reservaciones_service import (
    crear_reservacion,
    consultar_reservaciones,
    buscar_por_estudiante,
    actualizar_reservacion,
    cancelar_reservacion,
    consultar_disponibilidad as consultar_disponibilidad_reservacion,
    validar_recurrencia as validar_recurrencia_reservacion,
    crear_serie_recurrente as crear_serie_recurrente_reservacion,
    cancelar_ocurrencia as cancelar_ocurrencia_reservacion,
    cancelar_serie_desde_ocurrencia as cancelar_serie_desde_ocurrencia_reservacion
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
    # Reservaciones
    # ------------------------------------------------------------------

    def listar(self):
        """Devuelve todas las reservaciones."""
        try:
            return consultar_reservaciones(self._conexion)

        except sqlite3.Error as exc:
            raise RuntimeError(
                "No se pudieron consultar las reservaciones."
            ) from exc

    def listar_por_rango_fechas(
                self, 
                fecha_inicio: str,
                fecha_fin: str,
        ): 
            """Devuelve todas las reservaciones dentro de un rango de fechas."""
            try:
                return db.listar_reservaciones_por_rango_fechas(
                    self._conexion,
                    fecha_inicio,
                    fecha_fin,
                )
    
            except sqlite3.Error as exc:
                raise RuntimeError(
                    "No se pudieron consultar las reservaciones dentro del rango de fechas."
                ) from exc

    def crear(
        self,
        carne: str,
        codigo_sala: str,
        fecha: str,
        hora_inicio: str,
        duracion: str,
        cantidad_personas: str,
    ):
        """Valida y registra una reservación nueva."""
        try:
            return crear_reservacion(
                self._conexion,
                carne,
                codigo_sala,
                fecha,
                hora_inicio,
                duracion,
                cantidad_personas,
            )

        except ValidacionError as exc:
            raise ValueError(str(exc)) from exc

        except ValueError:
            raise

        except sqlite3.Error as exc:
            raise RuntimeError(
                "No se pudo registrar la reservación."
            ) from exc

    def buscar_por_estudiante(
        self,
        carne: str,
    ):
        """Devuelve todas las reservaciones de un estudiante."""
        try:
            return buscar_por_estudiante(
                self._conexion,
                carne,
            )

        except ValidacionError as exc:
            raise ValueError(str(exc)) from exc

        except ValueError:
            raise

        except sqlite3.Error as exc:
            raise RuntimeError(
                "No se pudieron consultar las reservaciones del estudiante."
            ) from exc

    def cancelar(
            self, 
            codigo: str,
    ):
        """Cancela una reservación."""
        try:
            return cancelar_reservacion(
                self._conexion,
                codigo,
            )

        except ValidacionError as exc:
            raise ValueError(str(exc)) from exc

        except ValueError:
            raise

        except sqlite3.Error as exc:
            raise RuntimeError(
                "No se pudo cancelar la reservación."
            ) from exc

    def modificar(
        self,
        id_reservacion: str,
        codigo_sala: str,
        fecha: str,
        hora_inicio: str,
        duracion: str,
        cantidad_personas: str,
    ):
        """Valida y actualiza una reservación."""
        try:
            return actualizar_reservacion(
                self._conexion,
                id_reservacion,
                codigo_sala,
                fecha,
                hora_inicio,
                duracion,
                cantidad_personas,
            )

        except ValidacionError as exc:
            raise ValueError(str(exc)) from exc

        except ValueError:
            raise

        except sqlite3.Error as exc:
            raise RuntimeError(
                "No se pudo actualizar la reservación."
            ) from exc

    def listar_salas_disponibles(self):
        """Devuelve todas las salas disponibles para reservación."""
        try:
            salas = db.listar_salas(self._conexion)

            return [sala for sala in salas if sala["estado"] == "disponible"]

        except sqlite3.Error as exc:
            raise RuntimeError(
                "No se pudieron consultar las salas disponibles."
            ) from exc

    def consultar_disponibilidad(
        self,
        codigo_sala: str,
        fecha: str,
        hora_inicio: str,
        duracion: str,
    ):
        """Consulta la disponibilidad de una sala sin crear reservaciones."""
        try:
            return consultar_disponibilidad_reservacion(
                self._conexion, 
                codigo_sala,
                fecha,
                hora_inicio,
                duracion,
            )

        except ValidacionError as exc:
            raise ValueError(str(exc)) from exc

        except ValueError:
            raise

        except sqlite3.Error as exc:
            raise RuntimeError(
                "No se pudo consultar la disponibilidad de la sala."
            ) from exc

    def validar_recurrencia(
        self,
        carne: str,
        codigo_sala: str,
        fecha_inicial: str,
        hora_inicio: str,
        duracion: str,
        cantidad_personas: str,
        cantidad_ocurrencias: str,
    ):
        """Valida una serie de reservaciones recurrentes."""
        try:
            return validar_recurrencia_reservacion(
                self._conexion,
                carne,
                codigo_sala,
                fecha_inicial,
                hora_inicio,
                duracion,
                cantidad_personas,
                cantidad_ocurrencias,
            )

        except ValidacionError as exc:
            raise ValueError(str(exc)) from exc

        except ValueError:
            raise

        except sqlite3.Error as exc:
            raise RuntimeError(
                "No se pudo validar la recurrencia de la reservación."
            ) from exc

    def crear_serie_recurrente(
        self,
        carne: str,
        codigo_sala: str,
        fecha_inicial: str,
        hora_inicio: str,
        duracion: str,
        cantidad_personas: str,
        cantidad_ocurrencias: str,
    ):
        """Crea una serie de reservaciones recurrentes."""
        try:
            return crear_serie_recurrente_reservacion(
                self._conexion,
                carne,
                codigo_sala,
                fecha_inicial,
                hora_inicio,
                duracion,
                cantidad_personas,
                cantidad_ocurrencias
            )

        except ValidacionError as exc:
            raise ValueError(str(exc)) from exc

        except ValueError:
            raise

        except sqlite3.Error as exc:
            raise RuntimeError(
                "No se pudo crear la serie de reservaciones recurrentes."
            ) from exc

    def cancelar_ocurrencia(
        self,
        id_reservacion: str,
    ):
        """Cancela una ocurrencia de una serie de reservaciones."""
        try:
            return cancelar_ocurrencia_reservacion(
                self._conexion,
                id_reservacion,
            )

        except ValidacionError as exc:
            raise ValueError(str(exc)) from exc

        except ValueError:
            raise

        except sqlite3.Error as exc:
            raise RuntimeError(
                "No se pudo cancelar la ocurrencia de la reservación."
            ) from exc  

    def cancelar_serie_desde_ocurrencia(
        self,
        id_reservacion: str,
    ):
        """Cancela una serie de reservaciones desde una ocurrencia."""
        try:
            return cancelar_serie_desde_ocurrencia_reservacion(
                self._conexion,
                id_reservacion,
            )

        except ValidacionError as exc:
            raise ValueError(str(exc)) from exc

        except ValueError:
            raise

        except sqlite3.Error as exc:
            raise RuntimeError(
                "No se pudo cancelar la serie de reservaciones desde la ocurrencia."
            ) from exc
        
    # ------------------------------------------------------------------
    # Cierre
    # ------------------------------------------------------------------

    def cerrar(self) -> None:
        """Cierra la conexión SQLite utilizada por la aplicación."""
        if self._conexion is not None:
            self._conexion.close()
            self._conexion = None