"""
RNF-09: con 1 000 estudiantes y 5 000 reservaciones, cada consulta debe
responder en menos de 2 segundos. Cobertura 14.1: carga mínima.
"""

import time
from datetime import date, timedelta

import pytest

from src.services import panel_service as ps
from src.services import reservaciones_service as rs
from src.validators import reglas_negocio as rn
from src.validators.validaciones import ValidacionError

LIMITE_SEGUNDOS = 2.0

pytestmark = pytest.mark.rendimiento


@pytest.fixture
def bd_con_carga(conexion):
    estudiantes = [(f"P{i:09d}", f"Estudiante de carga {i}", f"e{i}@universidad.ac.cr") for i in range(1000)]
    conexion.executemany("INSERT INTO estudiantes (carne, nombre, correo) VALUES (?, ?, ?)", estudiantes)

    salas = ["S01", "S02", "S03", "S05"]
    reservas = []
    for i in range(5000):
        dia = date.today() + timedelta(days=1 + i // 48)     # 48 reservas por día
        indice_dia = i % 48
        sala = salas[indice_dia % 4]
        hora = 8 + indice_dia // 4                           # 08:00 a 19:00
        reservas.append((
            f"R{i + 1:04d}", f"P{i % 1000:09d}", sala, dia.isoformat(), f"{hora:02d}:00",
            1, 1, "cancelada" if i % 10 == 0 else "activa",
        ))
    conexion.executemany(
        """INSERT INTO reservaciones
           (id, carne, codigo_sala, fecha, hora_inicio, duracion, cantidad_personas, estado)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        reservas,
    )
    conexion.execute("UPDATE contadores SET valor = 5000 WHERE nombre = 'reservacion'")
    conexion.commit()
    return conexion


def _sin_error(funcion, *args):
    """En la carga cada estudiante tiene 5 reservas: interesa el tiempo, no el resultado."""
    try:
        return funcion(*args)
    except ValidacionError:
        return False


def _medir(funcion):
    inicio = time.perf_counter()
    resultado = funcion()
    return resultado, time.perf_counter() - inicio


def test_volumen_cargado(bd_con_carga):
    assert bd_con_carga.execute("SELECT COUNT(*) FROM estudiantes").fetchone()[0] == 1003
    assert bd_con_carga.execute("SELECT COUNT(*) FROM reservaciones").fetchone()[0] == 5000


@pytest.mark.parametrize("nombre, consulta", [
    ("RF-06 historial completo", lambda c: rs.consultar_reservaciones(c)),
    ("RF-07 buscar por estudiante", lambda c: rs.buscar_por_estudiante(c, "P000000007")),
    ("RF-08 disponibilidad", lambda c: rs.consultar_disponibilidad(
        c, "S01", (date.today() + timedelta(days=3)).isoformat(), "08:00", "1")),
    ("RF-15 panel con filtros", lambda c: ps.obtener_panel(
        c, fecha=(date.today() + timedelta(days=5)).isoformat(), codigo_sala="S02", estado="activa")),
    ("RF-15 panel del día", lambda c: ps.obtener_panel(c)),
    ("RF-17 historial de acciones", lambda c: ps.consultar_historial(c)),
    ("RN-11 límite por estudiante", lambda c: _sin_error(rn.validar_limite_reservas, c, "P000000999")),
])
def test_consulta_menor_a_dos_segundos(bd_con_carga, nombre, consulta):
    _, segundos = _medir(lambda: consulta(bd_con_carga))
    assert segundos < LIMITE_SEGUNDOS, f"{nombre} tardó {segundos:.3f} s"


def test_crear_reservacion_con_carga(bd_con_carga):
    fecha = (date.today() + timedelta(days=200)).isoformat()
    resultado, segundos = _medir(
        lambda: rs.crear_reservacion(bd_con_carga, "A001234567", "S01", fecha, "10:00", "1", "2")
    )
    assert resultado["id"] == "R5001"
    assert segundos < LIMITE_SEGUNDOS
