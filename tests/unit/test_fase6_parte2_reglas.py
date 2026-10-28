"""Regresión Fase 6, Parte 2: reglas de negocio y validaciones.

Cada prueba reproduce un hallazgo recibido del equipo evaluador. Se escribieron
antes de corregir el código para comprobar que el fallo existía, y se mantienen
como pruebas de regresión. Usan bases temporales mediante conftest.py.
"""
import pytest

from src.services import reservaciones_service as rs
from src.validators import validaciones as v
from src.validators.validaciones import ValidacionError
from tests.utilidades import fecha_futura, fecha_pasada, insertar_reserva_directa

ANDREA = "A001234567"


# ---------------------------------------------------------------------------
# Modificación H-01 (RF-13, RN-11): la modificación no puede superar el límite
# ---------------------------------------------------------------------------

def _tres_futuras_y_una_pasada(servicio):
    for dias in (1, 2, 3):
        servicio.crear(ANDREA, "S01", fecha_futura(dias), "10:00", "1", "2")
    insertar_reserva_directa(servicio._conexion, "R0100", ANDREA, "S02", fecha_pasada(2), "10:00")


def test_modificar_reserva_pasada_a_futura_supera_limite(servicio):
    _tres_futuras_y_una_pasada(servicio)

    with pytest.raises(ValueError, match="máximo de tres"):
        servicio.modificar("R0100", "S02", fecha_futura(4), "10:00", "1", "2")

    original = rs.obtener_reservacion(servicio._conexion, "R0100")
    assert original["fecha"] == fecha_pasada(2)          # se conservan los datos originales


def test_modificar_reserva_vigente_sigue_permitido_con_tres(servicio):
    """Caso cercano: cambiar una de las tres vigentes no aumenta el total."""
    _tres_futuras_y_una_pasada(servicio)
    servicio.modificar("R0001", "S01", fecha_futura(5), "11:00", "1", "2")
    assert rs.obtener_reservacion(servicio._conexion, "R0001")["fecha"] == fecha_futura(5)


def test_modificar_ocurrencia_de_serie_no_cuenta_doble(servicio):
    """Caso cercano: la serie cuenta como una sola reserva (política del equipo)."""
    servicio.crear_serie_recurrente(ANDREA, "S03", fecha_futura(1), "14:00", "1", "2", "3")
    servicio.crear(ANDREA, "S01", fecha_futura(2), "10:00", "1", "2")
    servicio.crear(ANDREA, "S01", fecha_futura(3), "10:00", "1", "2")
    servicio.modificar("R0001", "S03", fecha_futura(1), "15:00", "1", "2")
    assert rs.obtener_reservacion(servicio._conexion, "R0001")["hora_inicio"] == "15:00"


# ---------------------------------------------------------------------------
# Recurrencia H-01 (RF-14): cancelar la serie solo afecta ocurrencias futuras
# ---------------------------------------------------------------------------

def test_cancelar_serie_desde_ocurrencia_pasada_conserva_las_pasadas(servicio):
    con = servicio._conexion
    insertar_reserva_directa(con, "R0101", ANDREA, "S03", fecha_pasada(14), "10:00", serie_id="SER-T")
    insertar_reserva_directa(con, "R0102", ANDREA, "S03", fecha_pasada(7), "10:00", serie_id="SER-T")
    insertar_reserva_directa(con, "R0103", ANDREA, "S03", fecha_futura(7), "10:00", serie_id="SER-T")

    resultado = servicio.cancelar_serie_desde_ocurrencia("R0101")

    assert resultado["reservaciones_canceladas"] == ["R0103"]
    assert rs.obtener_reservacion(con, "R0101")["estado"] == "activa"
    assert rs.obtener_reservacion(con, "R0102")["estado"] == "activa"
    assert rs.obtener_reservacion(con, "R0103")["estado"] == "cancelada"


def test_cancelar_serie_desde_ocurrencia_futura_sigue_igual(servicio):
    """Caso cercano: desde una ocurrencia futura se cancelan esa y las siguientes."""
    servicio.crear_serie_recurrente(ANDREA, "S03", fecha_futura(1), "14:00", "1", "2", "3")
    resultado = servicio.cancelar_serie_desde_ocurrencia("R0002")
    assert resultado["reservaciones_canceladas"] == ["R0002", "R0003"]
    assert rs.obtener_reservacion(servicio._conexion, "R0001")["estado"] == "activa"


# ---------------------------------------------------------------------------
# Salas H-01 y H-02 (RF-12): capacidad muy grande y formato del código
# ---------------------------------------------------------------------------

def test_capacidad_muy_grande_muestra_mensaje_claro(servicio):
    with pytest.raises(ValueError, match="capacidad"):
        servicio.crear_sala("S06", "Sala grande", str(10 ** 30))


@pytest.mark.parametrize("codigo", ["S" * 200, "S/<>;'", "S 06"],
                         ids=["200_caracteres", "simbolos", "espacio_interno"])
def test_codigo_de_sala_con_formato_invalido(codigo):
    with pytest.raises(ValidacionError, match="código"):
        v.validar_codigo_sala(codigo)


@pytest.mark.parametrize("codigo", ["S01", "s06", "LAB10"])
def test_codigo_de_sala_valido(codigo):
    assert v.validar_codigo_sala(codigo) == codigo.upper()


# ---------------------------------------------------------------------------
# Creación H-04 (RN-09): una sola regla de superposición para crear y modificar
# ---------------------------------------------------------------------------

def test_modificar_con_superposicion_usa_la_misma_regla(servicio):
    f = fecha_futura(2)
    servicio.crear(ANDREA, "S03", f, "10:00", "2", "2")
    servicio.crear("B009876543", "S03", f, "13:00", "1", "2")
    with pytest.raises(ValueError, match="se superpone con el horario solicitado"):
        servicio.modificar("R0002", "S03", f, "11:00", "1", "2")
    assert rs.obtener_reservacion(servicio._conexion, "R0002")["hora_inicio"] == "13:00"
