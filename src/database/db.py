"""
Módulo de persistencia - Sistema de Reservación de Salas de Estudio
Curso: TI3603 Calidad en Sistemas de Información

Este módulo centraliza toda la conexión y creación de la base de datos
SQLite, así como los datos iniciales requeridos por el proyecto (RF-01)

La base de datos se crea automáticamente en data/reservas.db
"""

import os
import sqlite3
from datetime import datetime


DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "reservas.db",
)


def obtener_conexion():
    """
    Abre una conexión a la base de datos SQLite
    Activa las llaves foráneas que SQLite trae desactivadas por defecto y permite acceder a las columnas de los resultados por nombre
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conexion = sqlite3.connect(DB_PATH)
    conexion.execute("PRAGMA foreign_keys = ON;")
    conexion.row_factory = sqlite3.Row
    return conexion


def inicializar_base_datos():
    """
    Crea las tablas si no existen todavía (RF-01)
    Si la base de datos ya existe y es válida no duplica nada porque todas las sentencias usan "IF NOT EXISTS"
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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auditoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_hora TEXT NOT NULL,
            tipo_accion TEXT NOT NULL,
            entidad TEXT NOT NULL,
            identificador TEXT NOT NULL
        );
    """)

    # Tabla auxiliar que garantiza IDs de reservación consecutivos con el formato "R0001" que nunca se reutilizan, ni siquiera después de reiniciar la aplicación (RN-13)
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

    #Inserta las salas iniciales del enunciado solo si la tabla todavía está vacía para no duplicar datos en ejecuciones posteriores
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM salas;")
    cantidad = cursor.fetchone()[0]

    if cantidad == 0:
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


def generar_id_reservacion(conexion):
    """
    Genera el siguiente ID de reservación en formato: R0001, R0002, etc
    Nunca reutiliza un número, incluso si la reservación se cancela
    """
    cursor = conexion.cursor()
    cursor.execute("UPDATE contadores SET valor = valor + 1 WHERE nombre = 'reservacion';")
    cursor.execute("SELECT valor FROM contadores WHERE nombre = 'reservacion';")
    numero = cursor.fetchone()[0]
    conexion.commit()
    return f"R{numero:04d}"


def registrar_auditoria(conexion, tipo_accion, entidad, identificador):
    """
    Guarda una acción en el historial de auditoría (RF-17).
    Solo debe llamarse cuando la operación ya se completó con éxito. Un intento fallido no debe registrarse como un cambio exitoso
    """
    cursor = conexion.cursor()
    cursor.execute(
        """
        INSERT INTO auditoria (fecha_hora, tipo_accion, entidad, identificador)
        VALUES (?, ?, ?, ?);
        """,
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), tipo_accion, entidad, identificador),
    )
    conexion.commit()


if __name__ == "__main__":
    # Permite ejecutar este archivo directamente para creary verificar la base de datos:
    # python db.py
    inicializar_base_datos()
    print(f"Base de datos lista en: {DB_PATH}")
