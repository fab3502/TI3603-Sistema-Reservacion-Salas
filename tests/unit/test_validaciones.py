"""
Pruebas unitarias de src/validators/validaciones.py

Técnicas: partición de equivalencia y análisis de valores límite.
Cobertura 14.1: campos vacíos y espacios periféricos, tipos y formatos
inválidos, fechas pasadas/inexistentes, fecha actual con hora pasada,
horario fuera de rango, duración inválida, capacidad exacta/excedida/cero/decimal.
"""

from datetime import date, datetime, time, timedelta

import pytest

from src.validators import validaciones as v
from src.validators.validaciones import ValidacionError
from tests.utilidades import RelojFijo, fecha_futura, fecha_pasada


# ---------------------------------------------------------------------------
# Carné (RF-02, 5.1)
# ---------------------------------------------------------------------------

class TestCarne:
    @pytest.mark.parametrize("entrada, esperado", [
        ("A001234567", "A001234567"),          # válido
        ("a001234567", "A001234567"),          # minúsculas -> se normaliza
        ("  B009876543  ", "B009876543"),      # espacios periféricos se eliminan
        ("1234567890", "1234567890"),          # solo dígitos
    ])
    def test_carne_valido(self, entrada, esperado):
        assert v.validar_carne(entrada) == esperado

    @pytest.mark.parametrize("entrada", [
        "",                 # vacío
        "   ",              # solo espacios
        "A00123456",        # 9 caracteres (límite inferior - 1)
        "A0012345678",      # 11 caracteres (límite superior + 1)
    ])
    def test_carne_longitud_invalida(self, entrada):
        with pytest.raises(ValidacionError, match="exactamente 10"):
            v.validar_carne(entrada)

    @pytest.mark.parametrize("entrada", ["A00 234567", "A00-234567", "A00_234567", "A00123456@"])
    def test_carne_con_espacios_internos_o_simbolos(self, entrada):
        with pytest.raises(ValidacionError):
            v.validar_carne(entrada)

    @pytest.mark.parametrize("entrada", [None, 1234567890, 12.5])
    def test_carne_tipo_invalido(self, entrada):
        with pytest.raises(ValidacionError, match="texto"):
            v.validar_carne(entrada)


# ---------------------------------------------------------------------------
# Nombre y correo (RF-02, 5.1)
# ---------------------------------------------------------------------------

class TestNombreCorreo:
    @pytest.mark.parametrize("entrada", ["Ana", "  Ana  ", "José Muñoz", "A n a"])
    def test_nombre_valido(self, entrada):
        assert v.validar_nombre(entrada) == entrada.strip()

    @pytest.mark.parametrize("entrada", ["", "   ", "Al", "A b", "  A  b  "])
    def test_nombre_con_menos_de_tres_caracteres_no_espacio(self, entrada):
        with pytest.raises(ValidacionError, match="tres caracteres"):
            v.validar_nombre(entrada)

    @pytest.mark.parametrize("entrada", [
        "andrea@universidad.ac.cr",
        "  andrea@universidad.ac.cr  ",
        "a@b.c",
    ])
    def test_correo_valido(self, entrada):
        assert v.validar_correo(entrada) == entrada.strip()

    @pytest.mark.parametrize("entrada, mensaje", [
        ("", "exactamente un símbolo @"),
        ("andrea.universidad.ac.cr", "exactamente un símbolo @"),
        ("an@drea@universidad.ac.cr", "exactamente un símbolo @"),
        ("andrea@universidad", "punto"),
        ("@universidad.ac.cr", "texto antes del @"),
        ("andrea.x@universidad", "punto"),     # punto solo antes del @
    ])
    def test_correo_invalido(self, entrada, mensaje):
        with pytest.raises(ValidacionError, match=mensaje):
            v.validar_correo(entrada)


# ---------------------------------------------------------------------------
# Fecha (RN-02)
# ---------------------------------------------------------------------------

class TestFecha:
    def test_fecha_hoy_es_valida(self):
        hoy = date.today().strftime("%Y-%m-%d")
        assert v.validar_fecha(hoy) == date.today()

    def test_fecha_futura_valida(self):
        assert v.validar_fecha(fecha_futura(30)) == date.today() + timedelta(days=30)

    def test_fecha_con_espacios_perifericos(self):
        assert v.validar_fecha(f"  {fecha_futura(1)}  ") == date.today() + timedelta(days=1)

    def test_fecha_ayer_es_pasada(self):
        with pytest.raises(ValidacionError, match="pasado"):
            v.validar_fecha(fecha_pasada(1))

    @pytest.mark.parametrize("entrada", [
        "2030-02-30",     # fecha inexistente
        "2030-13-01",     # mes inexistente
        "2031-02-29",     # año no bisiesto
        "30/01/2030",     # formato distinto
        "2030-1-5",       # sin ceros a la izquierda
        "",               # vacío
        "mañana",         # texto
    ])
    def test_fecha_formato_o_inexistente(self, entrada):
        with pytest.raises(ValidacionError, match="AAAA-MM-DD"):
            v.validar_fecha(entrada)


# ---------------------------------------------------------------------------
# Hora (RN-04) y horario (RN-05)
# ---------------------------------------------------------------------------

class TestHoraYHorario:
    @pytest.mark.parametrize("entrada", ["08:00", "19:00", "  10:00 "])
    def test_hora_completa_valida(self, entrada):
        assert v.validar_hora(entrada).minute == 0

    @pytest.mark.parametrize("entrada", ["08:30", "10:01", "19:59"])
    def test_hora_no_completa(self, entrada):
        with pytest.raises(ValidacionError, match="hora completa"):
            v.validar_hora(entrada)

    @pytest.mark.parametrize("entrada", ["8:00", "25:00", "10", "10:00:00", "", "diez"])
    def test_hora_formato_invalido(self, entrada):
        with pytest.raises(ValidacionError, match="HH:MM"):
            v.validar_hora(entrada)

    @pytest.mark.parametrize("hora, duracion", [
        (8, 1), (8, 2),        # límite de apertura
        (18, 2), (19, 1),      # terminan exactamente a las 20:00
    ])
    def test_horario_dentro_de_rango(self, hora, duracion):
        assert v.validar_horario(time(hora, 0), duracion) is True

    @pytest.mark.parametrize("hora, duracion, mensaje", [
        (7, 1, "antes de las 08:00"),
        (0, 1, "antes de las 08:00"),
        (19, 2, "terminar después de las 20:00"),
        (20, 1, "iniciar antes de las 20:00"),
        (21, 1, "iniciar antes de las 20:00"),
    ])
    def test_horario_fuera_de_rango(self, hora, duracion, mensaje):
        with pytest.raises(ValidacionError, match=mensaje):
            v.validar_horario(time(hora, 0), duracion)


# ---------------------------------------------------------------------------
# RN-03: reservación para hoy con hora pasada
# ---------------------------------------------------------------------------

class TestReservaHoy:
    def _con_reloj(self, monkeypatch, momento):
        reloj = RelojFijo(momento)
        monkeypatch.setattr(v, "datetime", reloj.datetime)
        monkeypatch.setattr(v, "date", reloj.date)
        return momento.date()

    def test_hoy_hora_pasada_rechazada(self, monkeypatch):
        hoy = self._con_reloj(monkeypatch, datetime(2030, 5, 10, 14, 30))
        with pytest.raises(ValidacionError, match="después de la hora actual"):
            v.validar_reserva_hoy(hoy, time(10, 0))

    def test_hoy_hora_actual_exacta_rechazada(self, monkeypatch):
        hoy = self._con_reloj(monkeypatch, datetime(2030, 5, 10, 14, 0))
        with pytest.raises(ValidacionError):
            v.validar_reserva_hoy(hoy, time(14, 0))

    def test_hoy_hora_futura_aceptada(self, monkeypatch):
        hoy = self._con_reloj(monkeypatch, datetime(2030, 5, 10, 14, 30))
        assert v.validar_reserva_hoy(hoy, time(15, 0)) is True

    def test_otro_dia_no_aplica_rn03(self, monkeypatch):
        hoy = self._con_reloj(monkeypatch, datetime(2030, 5, 10, 14, 30))
        assert v.validar_reserva_hoy(hoy + timedelta(days=1), time(8, 0)) is True


# ---------------------------------------------------------------------------
# Duración (RN-06), cantidad de personas (RN-07) y ocurrencias (RF-14)
# ---------------------------------------------------------------------------

class TestNumericos:
    @pytest.mark.parametrize("entrada, esperado", [(1, 1), (2, 2), ("1", 1), ("2", 2), (2.0, 2)])
    def test_duracion_valida(self, entrada, esperado):
        assert v.validar_duracion(entrada) == esperado

    @pytest.mark.parametrize("entrada", [0, 3, -1, "3"])
    def test_duracion_fuera_de_rango(self, entrada):
        with pytest.raises(ValidacionError, match="1 o 2 horas"):
            v.validar_duracion(entrada)

    @pytest.mark.parametrize("entrada", [1.5, "1.5", "uno", "", None, True])
    def test_duracion_tipo_invalido(self, entrada):
        with pytest.raises(ValidacionError, match="entero"):
            v.validar_duracion(entrada)

    def test_capacidad_exacta_aceptada(self):
        assert v.validar_cantidad_personas("4", 4) == 4

    def test_capacidad_minima_aceptada(self):
        assert v.validar_cantidad_personas(1, 4) == 1

    def test_capacidad_excedida(self):
        with pytest.raises(ValidacionError, match="superar la capacidad"):
            v.validar_cantidad_personas(5, 4)

    @pytest.mark.parametrize("entrada", [0, "0", -1])
    def test_capacidad_cero_o_negativa(self, entrada):
        with pytest.raises(ValidacionError, match="mayor que cero"):
            v.validar_cantidad_personas(entrada, 4)

    @pytest.mark.parametrize("entrada", [2.5, "2.5", "dos", "", None, True])
    def test_capacidad_decimal_o_no_numerica(self, entrada):
        with pytest.raises(ValidacionError, match="entero"):
            v.validar_cantidad_personas(entrada, 4)

    @pytest.mark.parametrize("entrada", [2, 8, "5"])
    def test_ocurrencias_en_limites(self, entrada):
        assert v.validar_cantidad_ocurrencias(entrada) == int(entrada)

    @pytest.mark.parametrize("entrada", [1, 9, 0])
    def test_ocurrencias_fuera_de_limites(self, entrada):
        with pytest.raises(ValidacionError, match="entre 2 y 8"):
            v.validar_cantidad_ocurrencias(entrada)


# ---------------------------------------------------------------------------
# Salas y estados (RF-11, RF-12)
# ---------------------------------------------------------------------------

class TestSalasYEstados:
    def test_codigo_sala_normalizado(self):
        assert v.validar_codigo_sala("  s06 ") == "S06"

    def test_codigo_sala_vacio(self):
        with pytest.raises(ValidacionError, match="obligatorio"):
            v.validar_codigo_sala("   ")

    def test_nombre_sala_vacio(self):
        with pytest.raises(ValidacionError, match="obligatorio"):
            v.validar_nombre_sala("")

    @pytest.mark.parametrize("entrada", [1, "1", "12"])
    def test_capacidad_sala_valida(self, entrada):
        assert v.validar_capacidad_sala(entrada) == int(entrada)

    @pytest.mark.parametrize("entrada", [0, -3, "0"])
    def test_capacidad_sala_no_positiva(self, entrada):
        with pytest.raises(ValidacionError, match="mayor que cero"):
            v.validar_capacidad_sala(entrada)

    @pytest.mark.parametrize("entrada", [2.5, "2.5", "diez", ""])
    def test_capacidad_sala_no_entera(self, entrada):
        with pytest.raises(ValidacionError, match="entero"):
            v.validar_capacidad_sala(entrada)

    @pytest.mark.parametrize("entrada", ["disponible", "FUERA_DE_SERVICIO", " disponible "])
    def test_estado_sala_valido(self, entrada):
        assert v.validar_estado_sala(entrada) in ("disponible", "fuera_de_servicio")

    def test_estado_sala_invalido(self):
        with pytest.raises(ValidacionError):
            v.validar_estado_sala("cerrada")

    @pytest.mark.parametrize("entrada", ["activo", "Inactivo"])
    def test_estado_estudiante_valido(self, entrada):
        assert v.validar_estado_estudiante(entrada) == entrada.lower()

    def test_estado_estudiante_invalido(self):
        with pytest.raises(ValidacionError):
            v.validar_estado_estudiante("suspendido")
