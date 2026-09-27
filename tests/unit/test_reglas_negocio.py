"""
Pruebas unitarias de src/validators/reglas_negocio.py y de la creación de
reservaciones en src/services/reservaciones_service.py

Técnicas: tabla de decisión para las reglas de reservación y partición de
equivalencia. Cobertura 14.1: estudiante inexistente/inactivo, sala
inexistente/fuera de servicio, conflicto total/parcial/envolvente, horario
consecutivo, máximo de tres reservaciones activas.
"""

import pytest

from src.services import reservaciones_service as rs
from src.validators import reglas_negocio as rn
from src.validators.validaciones import ValidacionError
from tests.utilidades import fecha_futura, fecha_pasada, insertar_reserva_directa

ANDREA = "A001234567"      # activo
CARLOS = "B009876543"      # activo
DANIELA = "C004567890"     # inactivo


# ---------------------------------------------------------------------------
# RN-01 y RN-08: existencia y estado
# ---------------------------------------------------------------------------

class TestEstudianteYSala:
    def test_estudiante_activo(self, conexion):
        assert rn.validar_estudiante_activo(conexion, ANDREA)["nombre"] == "Andrea Solano"

    def test_estudiante_inexistente(self, conexion):
        with pytest.raises(ValidacionError, match="no se encuentra registrado"):
            rn.validar_estudiante_activo(conexion, "Z999999999")

    def test_estudiante_inactivo(self, conexion):
        with pytest.raises(ValidacionError, match="inactivo"):
            rn.validar_estudiante_activo(conexion, DANIELA)

    def test_sala_disponible(self, conexion):
        assert rn.validar_sala_disponible(conexion, "S01")["capacidad"] == 4

    def test_sala_inexistente(self, conexion):
        with pytest.raises(ValidacionError, match="no existe"):
            rn.validar_sala_disponible(conexion, "S99")

    def test_sala_fuera_de_servicio(self, conexion):
        with pytest.raises(ValidacionError, match="fuera de servicio"):
            rn.validar_sala_disponible(conexion, "S04")


# ---------------------------------------------------------------------------
# RN-09 / RN-10 / RN-12: superposición (tabla de la sección 6.1)
# ---------------------------------------------------------------------------

class TestSuperposicion:
    @pytest.fixture
    def con_reserva(self, conexion):
        def _crear(hora, duracion):
            fecha = fecha_futura(5)
            insertar_reserva_directa(conexion, "R9001", ANDREA, "S03", fecha, hora, duracion)
            return fecha
        return _crear

    @pytest.mark.parametrize("existente, nueva, hay_conflicto", [
        (("10:00", 1), ("10:00", 1), True),    # conflicto total
        (("10:00", 2), ("11:00", 1), True),    # conflicto parcial (dentro)
        (("10:00", 2), ("09:00", 2), True),    # conflicto parcial (inicio)
        (("10:00", 1), ("09:00", 2), True),    # nueva envuelve a la existente
        (("10:00", 1), ("11:00", 1), False),   # consecutiva (RN-10)
        (("10:00", 2), ("12:00", 1), False),   # consecutiva (RN-10)
        (("10:00", 1), ("09:00", 1), False),   # consecutiva antes
        (("10:00", 1), ("14:00", 1), False),   # sin relación
    ])
    def test_tabla_de_superposicion(self, conexion, con_reserva, existente, nueva, hay_conflicto):
        fecha = con_reserva(*existente)
        if hay_conflicto:
            with pytest.raises(ValidacionError, match="superpone"):
                rn.validar_superposicion(conexion, "S03", fecha, nueva[0], nueva[1])
        else:
            assert rn.validar_superposicion(conexion, "S03", fecha, nueva[0], nueva[1]) is True

    def test_otra_sala_no_genera_conflicto(self, conexion, con_reserva):
        fecha = con_reserva("10:00", 2)
        assert rn.validar_superposicion(conexion, "S01", fecha, "10:00", 2) is True

    def test_otra_fecha_no_genera_conflicto(self, conexion, con_reserva):
        con_reserva("10:00", 2)
        assert rn.validar_superposicion(conexion, "S03", fecha_futura(6), "10:00", 2) is True

    def test_reserva_cancelada_no_bloquea(self, conexion):
        fecha = fecha_futura(5)
        insertar_reserva_directa(conexion, "R9001", ANDREA, "S03", fecha, "10:00", 2, estado="cancelada")
        assert rn.validar_superposicion(conexion, "S03", fecha, "10:00", 2) is True

    def test_id_excluido_no_choca_consigo_misma(self, conexion, con_reserva):
        fecha = con_reserva("10:00", 2)
        assert rn.validar_superposicion(conexion, "S03", fecha, "10:00", 2, id_excluir="R9001") is True


# ---------------------------------------------------------------------------
# RN-11: máximo tres reservaciones activas presentes o futuras
# ---------------------------------------------------------------------------

class TestLimiteReservas:
    def _reservas(self, conexion, cantidad, estado="activa", pasada=False):
        for i in range(cantidad):
            fecha = fecha_pasada(i + 1) if pasada else fecha_futura(i + 1)
            insertar_reserva_directa(conexion, f"R80{i:02d}{estado[0]}{int(pasada)}", ANDREA, "S01",
                                     fecha, "10:00", 1, estado=estado)

    @pytest.mark.parametrize("existentes", [0, 1, 2])
    def test_hasta_tres_permitidas(self, conexion, existentes):
        self._reservas(conexion, existentes)
        assert rn.validar_limite_reservas(conexion, ANDREA) is True

    def test_cuarta_reserva_rechazada(self, conexion):
        self._reservas(conexion, 3)
        with pytest.raises(ValidacionError, match="máximo de tres"):
            rn.validar_limite_reservas(conexion, ANDREA)

    def test_canceladas_no_cuentan(self, conexion):
        self._reservas(conexion, 2)
        self._reservas(conexion, 3, estado="cancelada")
        assert rn.validar_limite_reservas(conexion, ANDREA) is True

    def test_reservas_pasadas_no_cuentan(self, conexion):
        self._reservas(conexion, 2)
        self._reservas(conexion, 3, pasada=True)
        assert rn.validar_limite_reservas(conexion, ANDREA) is True

    def test_serie_cuenta_como_una_reserva(self, conexion):
        for i in range(4):
            insertar_reserva_directa(conexion, f"R70{i:02d}", ANDREA, "S02", fecha_futura(7 * (i + 1)),
                                     "10:00", 1, serie_id="SER-PRUEBA")
        self._reservas(conexion, 1)
        # Serie (1) + individual (1) = 2 -> se permite una tercera.
        assert rn.validar_limite_reservas(conexion, ANDREA) is True

    def test_limite_es_por_estudiante(self, conexion):
        self._reservas(conexion, 3)
        assert rn.validar_limite_reservas(conexion, CARLOS) is True


# ---------------------------------------------------------------------------
# RF-12: reducción de capacidad de sala
# ---------------------------------------------------------------------------

class TestReduccionCapacidad:
    def test_reducir_por_debajo_de_reserva_futura(self, conexion):
        insertar_reserva_directa(conexion, "R9100", ANDREA, "S03", fecha_futura(2), "10:00", 1, personas=8)
        with pytest.raises(ValidacionError, match="No se puede reducir"):
            rn.validar_reduccion_capacidad_sala(conexion, "S03", 7)

    def test_reducir_hasta_la_cantidad_exacta(self, conexion):
        insertar_reserva_directa(conexion, "R9100", ANDREA, "S03", fecha_futura(2), "10:00", 1, personas=8)
        assert rn.validar_reduccion_capacidad_sala(conexion, "S03", 8) is True

    def test_reserva_pasada_no_impide_reducir(self, conexion):
        insertar_reserva_directa(conexion, "R9100", ANDREA, "S03", fecha_pasada(2), "10:00", 1, personas=8)
        assert rn.validar_reduccion_capacidad_sala(conexion, "S03", 2) is True

    def test_reserva_cancelada_no_impide_reducir(self, conexion):
        insertar_reserva_directa(conexion, "R9100", ANDREA, "S03", fecha_futura(2), "10:00", 1,
                                 personas=8, estado="cancelada")
        assert rn.validar_reduccion_capacidad_sala(conexion, "S03", 2) is True


# ---------------------------------------------------------------------------
# Tabla de decisión completa para crear una reservación (RF-05)
# ---------------------------------------------------------------------------

class TestTablaDecisionCrearReservacion:
    """
    Condiciones: estudiante (activo/inactivo/inexistente), sala
    (disponible/fuera/inexistente), capacidad, horario, conflicto, límite.
    Acción: crear (R####) o rechazar con el motivo.
    """

    @pytest.mark.parametrize("carne, sala, hora, duracion, personas, motivo", [
        # regla 1: todas las condiciones se cumplen -> se crea
        (ANDREA, "S01", "10:00", "1", "4", None),
        # reglas 2-8: una condición falla cada vez -> se rechaza
        (DANIELA, "S01", "10:00", "1", "2", "inactivo"),
        ("Z999999999", "S01", "10:00", "1", "2", "no se encuentra registrado"),
        (ANDREA, "S04", "10:00", "1", "2", "fuera de servicio"),
        (ANDREA, "S99", "10:00", "1", "2", "no existe"),
        (ANDREA, "S01", "10:00", "1", "5", "superar la capacidad"),
        (ANDREA, "S01", "19:00", "2", "2", "después de las 20:00"),
        (ANDREA, "S01", "07:00", "1", "2", "antes de las 08:00"),
        (ANDREA, "S01", "10:00", "3", "2", "1 o 2 horas"),
    ])
    def test_decision(self, conexion, carne, sala, hora, duracion, personas, motivo):
        fecha = fecha_futura(3)
        if motivo is None:
            resultado = rs.crear_reservacion(conexion, carne, sala, fecha, hora, duracion, personas)
            assert resultado["id"] == "R0001"
            assert "R0001" in resultado["mensaje"]
        else:
            with pytest.raises(ValidacionError, match=motivo):
                rs.crear_reservacion(conexion, carne, sala, fecha, hora, duracion, personas)
            assert rs.consultar_reservaciones(conexion) == []

    def test_conflicto_rechazado_y_consecutiva_aceptada(self, conexion):
        fecha = fecha_futura(3)
        rs.crear_reservacion(conexion, ANDREA, "S02", fecha, "10:00", "2", "3")
        with pytest.raises(ValidacionError, match="superpone"):
            rs.crear_reservacion(conexion, CARLOS, "S02", fecha, "11:00", "1", "2")
        assert rs.crear_reservacion(conexion, CARLOS, "S02", fecha, "12:00", "1", "2")["id"] == "R0002"

    def test_cuarta_reserva_del_estudiante_rechazada(self, conexion):
        for dia in (1, 2, 3):
            rs.crear_reservacion(conexion, ANDREA, "S01", fecha_futura(dia), "10:00", "1", "2")
        with pytest.raises(ValidacionError, match="máximo de tres"):
            rs.crear_reservacion(conexion, ANDREA, "S01", fecha_futura(4), "10:00", "1", "2")
        assert len(rs.consultar_reservaciones(conexion)) == 3
