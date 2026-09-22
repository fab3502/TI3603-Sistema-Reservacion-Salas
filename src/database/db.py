"""
Módulo de persistencia - Sistema de Reservación de Salas de Estudio

Este módulo centraliza toda la conexión, el esquema y las operaciones de
lectura y escritura sobre la base de datos SQLite.

Requisitos relacionados:
- RF-01: creación y carga de la base de datos.
- RN-13: identificadores de reservación no reutilizables.
- RNF-06: integridad de las operaciones de escritura.
- RNF-08: conservación correcta de tildes y ñ.
- RF-17: registro de auditoría.

Los demás módulos no deben ejecutar SQL directamente.
Deben utilizar las funciones expuestas en este módulo.
"""

import os
import sqlite3
from datetime import datetime


# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

DB_PATH = os.path.join(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
    ),
    "data",
    "reservas.db",
)


class ReservaDuplicadaError(Exception):
    """
    Se lanza cuando una reservación viola la restricción de unicidad
    de sala, fecha y hora de inicio para reservaciones activas.
    """

    pass


# ---------------------------------------------------------------------------
# Conexión
# ---------------------------------------------------------------------------

def obtener_conexion():
    """
    Abre una conexión a SQLite.

    - Crea la carpeta data si todavía no existe.
    - Activa las llaves foráneas.
    - Permite acceder a las columnas mediante su nombre.
    - Conserva los textos como str de Python.
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conexion = sqlite3.connect(DB_PATH)

    conexion.execute("PRAGMA foreign_keys = ON;")
    conexion.row_factory = sqlite3.Row
    conexion.text_factory = str

    return conexion


# ---------------------------------------------------------------------------
# Auditoría interna
# ---------------------------------------------------------------------------

def _registrar_auditoria_sin_commit(
    conexion,
    tipo_accion,
    entidad,
    identificador,
):
    """
    Inserta un registro de auditoría sin confirmar la transacción.

    Esta función se utiliza internamente para que la modificación principal
    y su registro de auditoría formen parte de una misma transacción.
    """
    cursor = conexion.cursor()

    cursor.execute(
        """
        INSERT INTO auditoria
            (fecha_hora, tipo_accion, entidad, identificador)
        VALUES (?, ?, ?, ?);
        """,
        (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            tipo_accion,
            entidad,
            identificador,
        ),
    )


# ---------------------------------------------------------------------------
# Creación e inicialización de la base de datos
# ---------------------------------------------------------------------------

def inicializar_base_datos():
    """
    Crea las tablas, índices, contador e información inicial necesaria.

    La operación es segura ante ejecuciones repetidas:
    no recrea ni duplica los registros existentes.
    """
    conexion = obtener_conexion()

    try:
        cursor = conexion.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS estudiantes (
                carne TEXT PRIMARY KEY COLLATE NOCASE,
                nombre TEXT NOT NULL,
                correo TEXT NOT NULL,
                estado TEXT NOT NULL DEFAULT 'activo'
            );
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS salas (
                codigo TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                capacidad INTEGER NOT NULL CHECK (capacidad > 0),
                estado TEXT NOT NULL DEFAULT 'disponible'
            );
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS reservaciones (
                id TEXT PRIMARY KEY,
                carne TEXT NOT NULL,
                codigo_sala TEXT NOT NULL,
                fecha TEXT NOT NULL,
                hora_inicio TEXT NOT NULL,
                duracion INTEGER NOT NULL,
                cantidad_personas INTEGER NOT NULL,
                estado TEXT NOT NULL DEFAULT 'activa',
                serie_id TEXT,
                FOREIGN KEY (carne)
                    REFERENCES estudiantes (carne),
                FOREIGN KEY (codigo_sala)
                    REFERENCES salas (codigo)
            );
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS auditoria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha_hora TEXT NOT NULL,
                tipo_accion TEXT NOT NULL,
                entidad TEXT NOT NULL,
                identificador TEXT NOT NULL
            );
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS contadores (
                nombre TEXT PRIMARY KEY,
                valor INTEGER NOT NULL
            );
            """
        )

        cursor.execute(
            """
            INSERT OR IGNORE INTO contadores
                (nombre, valor)
            VALUES ('reservacion', 0);
            """
        )

        # Evita reservaciones activas idénticas
        # en sala, fecha y hora de inicio.
        cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_unica_reserva_activa
            ON reservaciones (codigo_sala, fecha, hora_inicio)
            WHERE estado = 'activa';
            """
        )

        # Índices auxiliares para consultas frecuentes.
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_reservaciones_estudiante
            ON reservaciones (carne, fecha, hora_inicio);
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_reservaciones_sala_fecha
            ON reservaciones
                (codigo_sala, fecha, estado, hora_inicio);
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_reservaciones_serie
            ON reservaciones
                (serie_id, estado, fecha, hora_inicio);
            """
        )

        _insertar_salas_iniciales(conexion)

        conexion.commit()

    except Exception:
        conexion.rollback()
        raise

    finally:
        conexion.close()


def _insertar_salas_iniciales(conexion):
    """
    Inserta las salas iniciales requeridas por el proyecto.

    INSERT OR IGNORE permite recuperar individualmente cualquier sala
    faltante sin duplicar las que ya existen.
    """
    salas_iniciales = [
        ("S01", "Sala Biblioteca 1", 4, "disponible"),
        ("S02", "Sala Biblioteca 2", 6, "disponible"),
        ("S03", "Laboratorio de estudio", 10, "disponible"),
        ("S04", "Sala multimedia", 8, "fuera_de_servicio"),
        ("S05", "Cubículo individual", 1, "disponible"),
    ]

    conexion.executemany(
        """
        INSERT OR IGNORE INTO salas
            (codigo, nombre, capacidad, estado)
        VALUES (?, ?, ?, ?);
        """,
        salas_iniciales,
    )


# ---------------------------------------------------------------------------
# Estudiantes
# ---------------------------------------------------------------------------

def insertar_estudiante(conexion, carne, nombre, correo):
    """
    Inserta un estudiante nuevo.

    El estado inicial se asigna automáticamente como 'activo'.

    Puede lanzar sqlite3.IntegrityError si el carné ya existe.
    """
    try:
        cursor = conexion.cursor()

        cursor.execute(
            """
            INSERT INTO estudiantes
                (carne, nombre, correo)
            VALUES (?, ?, ?);
            """,
            (carne, nombre, correo),
        )

        _registrar_auditoria_sin_commit(
            conexion,
            "creacion",
            "estudiante",
            carne,
        )

        conexion.commit()

    except Exception:
        conexion.rollback()
        raise


def obtener_estudiante(conexion, carne):
    """
    Devuelve un estudiante por su carné.

    Retorna None si no existe.
    """
    cursor = conexion.cursor()

    cursor.execute(
        """
        SELECT *
        FROM estudiantes
        WHERE carne = ?;
        """,
        (carne,),
    )

    fila = cursor.fetchone()

    return dict(fila) if fila else None


def listar_estudiantes(conexion):
    """
    Devuelve todos los estudiantes ordenados alfabéticamente por nombre.
    """
    cursor = conexion.cursor()

    cursor.execute(
        """
        SELECT *
        FROM estudiantes
        ORDER BY nombre;
        """
    )

    return [dict(fila) for fila in cursor.fetchall()]


def actualizar_estudiante(
    conexion,
    carne,
    nombre,
    correo,
):
    """
    Actualiza el nombre y el correo de un estudiante.

    El carné identifica al estudiante y nunca se modifica.
    """
    cursor = conexion.cursor()

    cursor.execute(
        """
        SELECT nombre, correo
        FROM estudiantes
        WHERE carne = ?;
        """,
        (carne,),
    )

    estudiante = cursor.fetchone()

    if estudiante is None:
        raise ValueError("El estudiante no existe.")

    # No se registra auditoría si realmente no hubo ningún cambio.
    if (
        estudiante["nombre"] == nombre
        and estudiante["correo"] == correo
    ):
        return

    try:
        cursor.execute(
            """
            UPDATE estudiantes
            SET nombre = ?,
                correo = ?
            WHERE carne = ?;
            """,
            (
                nombre,
                correo,
                carne,
            ),
        )

        _registrar_auditoria_sin_commit(
            conexion,
            "actualizacion",
            "estudiante",
            carne,
        )

        conexion.commit()

    except Exception:
        conexion.rollback()
        raise


def actualizar_estado_estudiante(
    conexion,
    carne,
    nuevo_estado,
):
    """
    Activa o inactiva un estudiante existente.
    """
    cursor = conexion.cursor()

    cursor.execute(
        """
        SELECT estado
        FROM estudiantes
        WHERE carne = ?;
        """,
        (carne,),
    )

    estudiante = cursor.fetchone()

    if estudiante is None:
        raise ValueError("El estudiante no existe.")

    if estudiante["estado"] == nuevo_estado:
        return

    try:
        cursor.execute(
            """
            UPDATE estudiantes
            SET estado = ?
            WHERE carne = ?;
            """,
            (
                nuevo_estado,
                carne,
            ),
        )

        _registrar_auditoria_sin_commit(
            conexion,
            "actualizacion",
            "estudiante",
            carne,
        )

        conexion.commit()

    except Exception:
        conexion.rollback()
        raise


# ---------------------------------------------------------------------------
# Salas
# ---------------------------------------------------------------------------

def obtener_sala(conexion, codigo):
    """
    Devuelve una sala mediante su código.

    Retorna None si no existe.
    """
    cursor = conexion.cursor()

    cursor.execute(
        """
        SELECT *
        FROM salas
        WHERE codigo = ?;
        """,
        (codigo,),
    )

    fila = cursor.fetchone()

    return dict(fila) if fila else None


def listar_salas(conexion):
    """
    Devuelve todas las salas ordenadas por código.
    """
    cursor = conexion.cursor()

    cursor.execute(
        """
        SELECT *
        FROM salas
        ORDER BY codigo;
        """
    )

    return [dict(fila) for fila in cursor.fetchall()]


def insertar_sala(
    conexion,
    codigo,
    nombre,
    capacidad,
    estado="disponible",
):
    """
    Inserta una nueva sala.

    Puede lanzar sqlite3.IntegrityError si el código ya existe.
    """
    try:
        cursor = conexion.cursor()

        cursor.execute(
            """
            INSERT INTO salas
                (codigo, nombre, capacidad, estado)
            VALUES (?, ?, ?, ?);
            """,
            (
                codigo,
                nombre,
                capacidad,
                estado,
            ),
        )

        _registrar_auditoria_sin_commit(
            conexion,
            "creacion",
            "sala",
            codigo,
        )

        conexion.commit()

    except Exception:
        conexion.rollback()
        raise


def actualizar_sala(
    conexion,
    codigo,
    nombre,
    capacidad,
    estado,
):
    """
    Modifica los datos permitidos de una sala.

    El código identifica la sala y nunca se modifica.
    """
    cursor = conexion.cursor()

    cursor.execute(
        """
        SELECT nombre, capacidad, estado
        FROM salas
        WHERE codigo = ?;
        """,
        (codigo,),
    )

    sala = cursor.fetchone()

    if sala is None:
        raise ValueError("La sala no existe.")

    if (
        sala["nombre"] == nombre
        and sala["capacidad"] == capacidad
        and sala["estado"] == estado
    ):
        return

    try:
        cursor.execute(
            """
            UPDATE salas
            SET nombre = ?,
                capacidad = ?,
                estado = ?
            WHERE codigo = ?;
            """,
            (
                nombre,
                capacidad,
                estado,
                codigo,
            ),
        )

        _registrar_auditoria_sin_commit(
            conexion,
            "actualizacion",
            "sala",
            codigo,
        )

        conexion.commit()

    except Exception:
        conexion.rollback()
        raise


def actualizar_estado_sala(
    conexion,
    codigo,
    nuevo_estado,
):
    """
    Cambia el estado de una sala existente.
    """
    cursor = conexion.cursor()

    cursor.execute(
        """
        SELECT estado
        FROM salas
        WHERE codigo = ?;
        """,
        (codigo,),
    )

    sala = cursor.fetchone()

    if sala is None:
        raise ValueError("La sala no existe.")

    if sala["estado"] == nuevo_estado:
        return

    try:
        cursor.execute(
            """
            UPDATE salas
            SET estado = ?
            WHERE codigo = ?;
            """,
            (
                nuevo_estado,
                codigo,
            ),
        )

        _registrar_auditoria_sin_commit(
            conexion,
            "actualizacion",
            "sala",
            codigo,
        )

        conexion.commit()

    except Exception:
        conexion.rollback()
        raise


# ---------------------------------------------------------------------------
# Identificadores de reservación
# ---------------------------------------------------------------------------

def _generar_id_reservacion_sin_commit(conexion):
    """
    Genera el siguiente ID sin confirmar la transacción.
    """
    cursor = conexion.cursor()

    cursor.execute(
        """
        UPDATE contadores
        SET valor = valor + 1
        WHERE nombre = 'reservacion';
        """
    )

    if cursor.rowcount == 0:
        raise RuntimeError(
            "No existe el contador de reservaciones."
        )

    cursor.execute(
        """
        SELECT valor
        FROM contadores
        WHERE nombre = 'reservacion';
        """
    )

    fila = cursor.fetchone()

    if fila is None:
        raise RuntimeError(
            "No fue posible obtener el contador de reservaciones."
        )

    return f"R{fila[0]:04d}"


def generar_id_reservacion(conexion):
    """
    Genera y confirma el siguiente ID de reservación.

    Formato:
    R0001, R0002, R0003...
    """
    try:
        id_reservacion = (
            _generar_id_reservacion_sin_commit(conexion)
        )

        conexion.commit()

        return id_reservacion

    except Exception:
        conexion.rollback()
        raise


# ---------------------------------------------------------------------------
# Reservaciones
# ---------------------------------------------------------------------------

def crear_reservacion(
    conexion,
    carne,
    codigo_sala,
    fecha,
    hora_inicio,
    duracion,
    cantidad_personas,
    serie_id=None,
):
    """
    Guarda una reservación individual.

    La generación del ID, la reservación y la auditoría forman parte
    de una misma transacción.
    """
    try:
        cursor = conexion.cursor()

        id_reservacion = (
            _generar_id_reservacion_sin_commit(conexion)
        )

        cursor.execute(
            """
            INSERT INTO reservaciones (
                id,
                carne,
                codigo_sala,
                fecha,
                hora_inicio,
                duracion,
                cantidad_personas,
                estado,
                serie_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 'activa', ?);
            """,
            (
                id_reservacion,
                carne,
                codigo_sala,
                fecha,
                hora_inicio,
                duracion,
                cantidad_personas,
                serie_id,
            ),
        )

        _registrar_auditoria_sin_commit(
            conexion,
            "creacion",
            "reservacion",
            id_reservacion,
        )

        conexion.commit()

        return id_reservacion

    except sqlite3.IntegrityError as error:
        conexion.rollback()

        mensaje = str(error).upper()

        if "FOREIGN KEY" in mensaje:
            raise

        if (
            "RESERVACIONES.CODIGO_SALA" in mensaje
            and "RESERVACIONES.FECHA" in mensaje
            and "RESERVACIONES.HORA_INICIO" in mensaje
        ):
            raise ReservaDuplicadaError(
                "Ya existe una reservación activa "
                f"en {codigo_sala} el {fecha} "
                f"a las {hora_inicio}."
            ) from error

        raise

    except Exception:
        conexion.rollback()
        raise


def crear_serie_reservaciones(
    conexion,
    reservaciones,
    serie_id,
):
    """
    Guarda todas las reservaciones de una serie en una única transacción.

    Si alguna operación falla:
    - no se conserva ninguna reservación de la serie;
    - no se conservan sus registros de auditoría;
    - tampoco se consumen los IDs generados durante ese intento.
    """
    cursor = conexion.cursor()
    ids_creados = []

    try:
        for reserva in reservaciones:

            id_reservacion = (
                _generar_id_reservacion_sin_commit(conexion)
            )

            cursor.execute(
                """
                INSERT INTO reservaciones (
                    id,
                    carne,
                    codigo_sala,
                    fecha,
                    hora_inicio,
                    duracion,
                    cantidad_personas,
                    estado,
                    serie_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 'activa', ?);
                """,
                (
                    id_reservacion,
                    reserva["carne"],
                    reserva["codigo_sala"],
                    reserva["fecha"],
                    reserva["hora_inicio"],
                    reserva["duracion"],
                    reserva["cantidad_personas"],
                    serie_id,
                ),
            )

            _registrar_auditoria_sin_commit(
                conexion,
                "creacion",
                "reservacion",
                id_reservacion,
            )

            ids_creados.append(id_reservacion)

        conexion.commit()

        return ids_creados

    except sqlite3.IntegrityError as error:
        conexion.rollback()

        mensaje = str(error).upper()

        if "FOREIGN KEY" in mensaje:
            raise

        if (
            "RESERVACIONES.CODIGO_SALA" in mensaje
            and "RESERVACIONES.FECHA" in mensaje
            and "RESERVACIONES.HORA_INICIO" in mensaje
        ):
            raise ReservaDuplicadaError(
                "No se pudo crear la serie porque una "
                "de las reservaciones entra en conflicto "
                "con una reservación existente."
            ) from error

        raise

    except Exception:
        conexion.rollback()
        raise


def cancelar_reservacion(
    conexion,
    id_reservacion,
):
    """
    Cancela una reservación activa.

    La reservación permanece almacenada en el historial.
    """
    cursor = conexion.cursor()

    cursor.execute(
        """
        SELECT estado
        FROM reservaciones
        WHERE id = ?;
        """,
        (id_reservacion,),
    )

    reserva = cursor.fetchone()

    if reserva is None:
        raise ValueError(
            "La reservación no existe."
        )

    if reserva["estado"] == "cancelada":
        raise ValueError(
            "La reservación ya está cancelada."
        )

    try:
        cursor.execute(
            """
            UPDATE reservaciones
            SET estado = 'cancelada'
            WHERE id = ?;
            """,
            (id_reservacion,),
        )

        _registrar_auditoria_sin_commit(
            conexion,
            "cancelacion",
            "reservacion",
            id_reservacion,
        )

        conexion.commit()

    except Exception:
        conexion.rollback()
        raise


def listar_reservaciones_por_estudiante(
    conexion,
    carne,
):
    """
    Devuelve el historial de reservaciones de un estudiante.
    """
    cursor = conexion.cursor()

    cursor.execute(
        """
        SELECT *
        FROM reservaciones
        WHERE carne = ?
        ORDER BY fecha, hora_inicio;
        """,
        (carne,),
    )

    return [dict(fila) for fila in cursor.fetchall()]


def listar_reservaciones_por_sala_fecha(
    conexion,
    codigo_sala,
    fecha,
):
    """
    Devuelve las reservaciones activas de una sala y fecha.

    Utilizada para la validación de superposiciones.
    """
    cursor = conexion.cursor()

    cursor.execute(
        """
        SELECT *
        FROM reservaciones
        WHERE codigo_sala = ?
          AND fecha = ?
          AND estado = 'activa'
        ORDER BY hora_inicio;
        """,
        (
            codigo_sala,
            fecha,
        ),
    )

    return [dict(fila) for fila in cursor.fetchall()]


def listar_reservaciones_activas_por_sala(
    conexion,
    codigo_sala,
):
    """
    Devuelve las reservaciones activas asociadas a una sala.

    Utilizada para validar cambios de capacidad.
    """
    cursor = conexion.cursor()

    cursor.execute(
        """
        SELECT *
        FROM reservaciones
        WHERE codigo_sala = ?
          AND estado = 'activa'
        ORDER BY fecha, hora_inicio;
        """,
        (codigo_sala,),
    )

    return [dict(fila) for fila in cursor.fetchall()]


def obtener_reservacion(
    conexion,
    id_reservacion,
):
    """
    Devuelve una reservación por su ID.

    Retorna None si no existe.
    """
    cursor = conexion.cursor()

    cursor.execute(
        """
        SELECT *
        FROM reservaciones
        WHERE id = ?;
        """,
        (id_reservacion,),
    )

    fila = cursor.fetchone()

    return dict(fila) if fila else None


def cancelar_reservaciones_futuras_serie(
    conexion,
    serie_id,
    fecha_desde,
    hora_desde,
):
    """
    Cancela las reservaciones activas de una serie a partir de una
    ocurrencia determinada, incluyendo esa ocurrencia.
    """
    cursor = conexion.cursor()

    try:
        cursor.execute(
            """
            SELECT id
            FROM reservaciones
            WHERE serie_id = ?
              AND estado = 'activa'
              AND (
                    fecha > ?
                    OR (
                        fecha = ?
                        AND hora_inicio >= ?
                    )
                  )
            ORDER BY fecha, hora_inicio;
            """,
            (
                serie_id,
                fecha_desde,
                fecha_desde,
                hora_desde,
            ),
        )

        ids_cancelados = [
            fila["id"]
            for fila in cursor.fetchall()
        ]

        for id_reservacion in ids_cancelados:

            cursor.execute(
                """
                UPDATE reservaciones
                SET estado = 'cancelada'
                WHERE id = ?;
                """,
                (id_reservacion,),
            )

            _registrar_auditoria_sin_commit(
                conexion,
                "cancelacion",
                "reservacion",
                id_reservacion,
            )

        conexion.commit()

        return ids_cancelados

    except Exception:
        conexion.rollback()
        raise


# ---------------------------------------------------------------------------
# Auditoría
# ---------------------------------------------------------------------------

def registrar_auditoria(
    conexion,
    tipo_accion,
    entidad,
    identificador,
):
    """
    Registra una acción individual en el historial.

    Las funciones de escritura de este módulo utilizan internamente
    _registrar_auditoria_sin_commit() para mantener la atomicidad.
    """
    try:
        _registrar_auditoria_sin_commit(
            conexion,
            tipo_accion,
            entidad,
            identificador,
        )

        conexion.commit()

    except Exception:
        conexion.rollback()
        raise


def obtener_auditoria(
    conexion,
    limite=50,
):
    """
    Devuelve los últimos registros de auditoría,
    comenzando por el más reciente.
    """
    cursor = conexion.cursor()

    cursor.execute(
        """
        SELECT *
        FROM auditoria
        ORDER BY id DESC
        LIMIT ?;
        """,
        (limite,),
    )

    return [dict(fila) for fila in cursor.fetchall()]


# ---------------------------------------------------------------------------
# Ejecución directa
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    inicializar_base_datos()
    print(f"Base de datos lista en: {DB_PATH}")