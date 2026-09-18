"""
Módulo de persistencia - Sistema de Reservación de Salas de Estudio

Este módulo centraliza toda la conexión, el esquema y las operaciones de
lectura y escritura sobre la base de datos SQLite (RF-01, RN-13, RNF-06,
RNF-08, RF-17). Los demás módulos no deben escribir SQL directamente deben llamar las funciones de aquí
"""

import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "reservas.db",
)


class ReservaDuplicadaError(Exception):
    #se lanza cuando ya existe una reservación activa en la misma sala, fecha y hora de inicio
    pass


# ---------------------------------------------------------------------------
# Conexión y esquema
# ---------------------------------------------------------------------------

def obtener_conexion():
    """
    Abre una conexión a la base de datos SQLite
    Activa las llaves foráneas, permite acceder a las columnas por nombre y usa UTF-8 para que tildes y la ñ se guarden y lean correctamente (RNF-08)
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conexion = sqlite3.connect(DB_PATH)
    conexion.execute("PRAGMA foreign_keys = ON;")
    conexion.row_factory = sqlite3.Row
    conexion.text_factory = str  # esto fuerza el manejo de texto como str/UTF-8
    return conexion


def inicializar_base_datos():
    """
    Crea las tablas si no existen todavía (RF-01)
    Si la bd ya existe y es válida no duplica nada porque todas las sentencias usan "IF NOT EXISTS"
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS estudiantes (
            carne TEXT PRIMARY KEY COLLATE NOCASE,
            nombre TEXT NOT NULL,
            correo TEXT NOT NULL,
            estado TEXT NOT NULL DEFAULT 'activo'
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS salas (
            codigo TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            capacidad INTEGER NOT NULL CHECK (capacidad > 0),
            estado TEXT NOT NULL DEFAULT 'disponible'
        );
    """)

    cursor.execute("""
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
            FOREIGN KEY (carne) REFERENCES estudiantes (carne),
            FOREIGN KEY (codigo_sala) REFERENCES salas (codigo)
        );
    """)

    # evita a nivel de base de datos dos reservaciones activas en la misma sala, fecha y hora
    # cumple con el RNF-06 de "evitar duplicados"
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_unica_reserva_activa
        ON reservaciones (codigo_sala, fecha, hora_inicio)
        WHERE estado = 'activa';
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auditoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_hora TEXT NOT NULL,
            tipo_accion TEXT NOT NULL,
            entidad TEXT NOT NULL,
            identificador TEXT NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contadores (
            nombre TEXT PRIMARY KEY,
            valor INTEGER NOT NULL
        );
    """)
    cursor.execute("""
        INSERT OR IGNORE INTO contadores (nombre, valor) VALUES ('reservacion', 0);
    """)

    conexion.commit()
    _insertar_salas_iniciales(conexion)
    conexion.close()


def _insertar_salas_iniciales(conexion):
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM salas;")
    if cursor.fetchone()[0] == 0:
        salas_iniciales = [
            ("S01", "Sala Biblioteca 1", 4, "disponible"),
            ("S02", "Sala Biblioteca 2", 6, "disponible"),
            ("S03", "Laboratorio de estudio", 10, "disponible"),
            ("S04", "Sala multimedia", 8, "fuera_de_servicio"),
            ("S05", "Cubículo individual", 1, "disponible"),
        ]
        cursor.executemany(
            "INSERT INTO salas (codigo, nombre, capacidad, estado) VALUES (?, ?, ?, ?);",
            salas_iniciales,
        )
        conexion.commit()


# ---------------------------------------------------------------------------
# Estudiantes
# ---------------------------------------------------------------------------

def insertar_estudiante(conexion, carne, nombre, correo):
    #inserta un estudiante nuevo. Falla con IntegrityError si el carné ya existe
    cursor = conexion.cursor()
    cursor.execute(
        "INSERT INTO estudiantes (carne, nombre, correo) VALUES (?, ?, ?);",
        (carne, nombre, correo),
    )
    conexion.commit()
    registrar_auditoria(conexion, "creacion", "estudiante", carne)


def obtener_estudiante(conexion, carne):
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM estudiantes WHERE carne = ?;", (carne,))
    fila = cursor.fetchone()
    return dict(fila) if fila else None


def listar_estudiantes(conexion):
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM estudiantes ORDER BY nombre;")
    return [dict(f) for f in cursor.fetchall()]


def actualizar_estado_estudiante(conexion, carne, nuevo_estado):
    cursor = conexion.cursor()
    cursor.execute(
        "UPDATE estudiantes SET estado = ? WHERE carne = ?;", (nuevo_estado, carne)
    )
    conexion.commit()
    registrar_auditoria(conexion, "actualizacion", "estudiante", carne)


# ---------------------------------------------------------------------------
# Salas
# ---------------------------------------------------------------------------

def listar_salas(conexion):
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM salas ORDER BY codigo;")
    return [dict(f) for f in cursor.fetchall()]


def actualizar_estado_sala(conexion, codigo, nuevo_estado):
    cursor = conexion.cursor()
    cursor.execute(
        "UPDATE salas SET estado = ? WHERE codigo = ?;", (nuevo_estado, codigo)
    )
    conexion.commit()
    registrar_auditoria(conexion, "actualizacion", "sala", codigo)


# ---------------------------------------------------------------------------
# Reservaciones
# ---------------------------------------------------------------------------

def generar_id_reservacion(conexion):
    #genera el siguiente ID en formato R0001, R0002 y así consecutivamente. Nunca se reutiliza incluso si la reservación se cancela (RN-13)
    cursor = conexion.cursor()
    cursor.execute("UPDATE contadores SET valor = valor + 1 WHERE nombre = 'reservacion';")
    cursor.execute("SELECT valor FROM contadores WHERE nombre = 'reservacion';")
    numero = cursor.fetchone()[0]
    conexion.commit()
    return f"R{numero:04d}"


def crear_reservacion(conexion, carne, codigo_sala, fecha, hora_inicio, duracion, cantidad_personas, serie_id=None):
    #guarda una reservación de forma transaccional: si algo falla no se guarda nada a medias

    id_reservacion = generar_id_reservacion(conexion)
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO reservaciones
                (id, carne, codigo_sala, fecha, hora_inicio, duracion,
                 cantidad_personas, estado, serie_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'activa', ?);
            """,
            (id_reservacion, carne, codigo_sala, fecha, hora_inicio,
             duracion, cantidad_personas, serie_id),
        )
        conexion.commit()
    except sqlite3.IntegrityError as error:
        conexion.rollback()
        if "FOREIGN KEY" in str(error).upper():
            raise
        raise ReservaDuplicadaError(
            f"Ya existe una reservación activa en {codigo_sala} el {fecha} a las {hora_inicio}."
        )

    registrar_auditoria(conexion, "creacion", "reservacion", id_reservacion)
    return id_reservacion


def cancelar_reservacion(conexion, id_reservacion):
    cursor = conexion.cursor()
    cursor.execute(
        "UPDATE reservaciones SET estado = 'cancelada' WHERE id = ?;",
        (id_reservacion,),
    )
    conexion.commit()
    registrar_auditoria(conexion, "cancelacion", "reservacion", id_reservacion)


def listar_reservaciones_por_estudiante(conexion, carne):
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM reservaciones WHERE carne = ? ORDER BY fecha, hora_inicio;", (carne,))
    return [dict(f) for f in cursor.fetchall()]


def listar_reservaciones_por_sala_fecha(conexion, codigo_sala, fecha):
    """Usada por el módulo de validaciones para revisar superposiciones."""
    cursor = conexion.cursor()
    cursor.execute(
        """
        SELECT * FROM reservaciones
        WHERE codigo_sala = ? AND fecha = ? AND estado = 'activa'
        ORDER BY hora_inicio;
        """,
        (codigo_sala, fecha),
    )
    return [dict(f) for f in cursor.fetchall()]


# ---------------------------------------------------------------------------
# Auditoría
# ---------------------------------------------------------------------------

def registrar_auditoria(conexion, tipo_accion, entidad, identificador):
    #guarda una acción en el historial (RF-17). Solo se debe llamar cuando la operación ya se completó con éxito
    cursor = conexion.cursor()
    cursor.execute(
        """
        INSERT INTO auditoria (fecha_hora, tipo_accion, entidad, identificador)
        VALUES (?, ?, ?, ?);
        """,
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), tipo_accion, entidad, identificador),
    )
    conexion.commit()


def obtener_auditoria(conexion, limite=50):
    #devuelve las últimas acciones registradas,las más recientes primero
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT * FROM auditoria ORDER BY id DESC LIMIT ?;", (limite,)
    )
    return [dict(f) for f in cursor.fetchall()]


if __name__ == "__main__":
    inicializar_base_datos()
    print(f"Base de datos lista en: {DB_PATH}")
