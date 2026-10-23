"""Regresión Fase 6, Parte 1: inicio con SQLite dañado y solapamiento directo.

Se utilizan bases temporales mediante conftest.py. No se toca data/reservas.db.
"""
import sqlite3
from unittest.mock import Mock
from tkinter import messagebox

import pytest

from src.database import db
from src import main as entrada
from tests.utilidades import fecha_futura


def test_fase6_rf01_archivo_danado_error_amigable_y_sin_borrado(ruta_bd, monkeypatch):
    """H-01 Persistencia: la GUI avisa, no inicia ni reemplaza datos dañados."""
    contenido = b"NO ES SQLITE\x00RESERVAS DE PRUEBA\x01"
    ruta_bd.write_bytes(contenido)
    dialogo = Mock()
    ventana = Mock()
    monkeypatch.setattr(messagebox, "showerror", dialogo)
    monkeypatch.setattr(entrada, "MainWindow", ventana)

    assert entrada.main() == 1
    dialogo.assert_called_once()
    titulo, mensaje = dialogo.call_args.args[:2]
    assert "base de datos" in mensaje.lower()
    assert "sqlite" not in mensaje.lower()  # sin error técnico
    assert "error" in titulo.lower()
    ventana.assert_not_called()
    assert ruta_bd.read_bytes() == contenido  # no se borra ni sustituye


def test_fase6_rf01_base_nueva_permite_inicio_normal(ruta_bd, monkeypatch):
    """La corrección no impide la primera ejecución con datos iniciales."""
    dialogo = Mock()
    ventana = Mock()
    monkeypatch.setattr(messagebox, "showerror", dialogo)
    monkeypatch.setattr(entrada, "MainWindow", ventana)

    # La versión anterior devolvía None en un inicio exitoso; ambas son válidas.
    assert entrada.main() in (None, 0)
    ventana.assert_called_once()
    ventana.return_value.mainloop.assert_called_once()
    dialogo.assert_not_called()
    con = db.obtener_conexion()
    try:
        assert con.execute("SELECT COUNT(*) FROM salas").fetchone()[0] == 5
        assert con.execute("SELECT COUNT(*) FROM estudiantes").fetchone()[0] == 3
    finally:
        con.close()


def _insertar_directo(con, rid, sala, fecha, hora, duracion, estado="activa"):
    con.execute(
        """INSERT INTO reservaciones
           (id, carne, codigo_sala, fecha, hora_inicio, duracion, cantidad_personas, estado)
           VALUES (?, 'A001234567', ?, ?, ?, ?, 1, ?)""",
        (rid, sala, fecha, hora, duracion, estado),
    )


def test_fase6_rn09_solape_parcial_directo_bloqueado(conexion):
    """H-03 Creación: SQLite rechaza un solape que omite la lógica de servicio."""
    fecha = fecha_futura(2)
    _insertar_directo(conexion, "R8001", "S01", fecha, "10:00", 2)
    conexion.commit()
    with pytest.raises(sqlite3.IntegrityError):
        _insertar_directo(conexion, "R8002", "S01", fecha, "11:00", 1)
    conexion.rollback()
    assert conexion.execute("SELECT COUNT(*) FROM reservaciones").fetchone()[0] == 1


def test_fase6_rn09_solape_en_modificacion_directa_bloqueado(conexion):
    fecha = fecha_futura(2)
    _insertar_directo(conexion, "R8001", "S01", fecha, "10:00", 2)
    _insertar_directo(conexion, "R8002", "S01", fecha, "12:00", 1)
    conexion.commit()
    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute("UPDATE reservaciones SET hora_inicio='11:00' WHERE id='R8002'")
    conexion.rollback()
    assert conexion.execute("SELECT hora_inicio FROM reservaciones WHERE id='R8002'").fetchone()[0] == "12:00"


def test_fase6_rn10_consecutivas_canceladas_y_otra_sala_permitidas(conexion):
    fecha = fecha_futura(2)
    _insertar_directo(conexion, "R8001", "S01", fecha, "10:00", 2)
    _insertar_directo(conexion, "R8002", "S01", fecha, "12:00", 1)
    _insertar_directo(conexion, "R8003", "S01", fecha, "10:00", 1, estado="cancelada")
    _insertar_directo(conexion, "R8004", "S02", fecha, "11:00", 1)
    conexion.commit()
    assert conexion.execute("SELECT COUNT(*) FROM reservaciones").fetchone()[0] == 4
