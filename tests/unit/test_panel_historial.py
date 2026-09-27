"""
Pruebas unitarias de src/services/panel_service.py (Parte 5).

Cobertura 14.1: combinación de filtros en el panel, actualización del panel
después de una operación, estado vacío comprensible, registro y consulta de
auditoría, y "un error de validación no se registra como cambio exitoso".
"""

from datetime import datetime, timedelta

import pytest

from src.database import db
from src.services import panel_service as ps
from src.services import reservaciones_service as rs
from src.validators.validaciones import ValidacionError
from tests.utilidades import fecha_futura, fecha_pasada, insertar_reserva_directa

ANDREA, CARLOS = "A001234567", "B009876543"


@pytest.fixture
def escenario(conexion):
    """
    Reservaciones de prueba en dos fechas futuras:
      F1: S01 08-10 Andrea (activa), S01 10-11 Carlos (cancelada), S02 09-10 Carlos (activa)
      F2: S03 14-16 Andrea (activa)
    """
    f1, f2 = fecha_futura(2), fecha_futura(3)
    insertar_reserva_directa(conexion, "R0001", ANDREA, "S01", f1, "08:00", 2, 3)
    insertar_reserva_directa(conexion, "R0002", CARLOS, "S01", f1, "10:00", 1, 2, estado="cancelada")
    insertar_reserva_directa(conexion, "R0003", CARLOS, "S02", f1, "09:00", 1, 5)
    insertar_reserva_directa(conexion, "R0004", ANDREA, "S03", f2, "14:00", 2, 8)
    return {"f1": f1, "f2": f2}


# ---------------------------------------------------------------------------
# Validación de filtros
# ---------------------------------------------------------------------------

class TestFiltros:
    @pytest.mark.parametrize("fecha, sala, estado, esperado", [
        (None, None, None, (None, None, None)),
        ("", "Todas", "Todos", (None, None, None)),
        ("  2030-01-15 ", " s02 ", " ACTIVA ", ("2030-01-15", "S02", "activa")),
    ])
    def test_normalizacion(self, fecha, sala, estado, esperado):
        f = ps.validar_filtros_panel(fecha, sala, estado)
        assert (f["fecha"], f["codigo_sala"], f["estado"]) == esperado

    def test_fecha_pasada_permitida_como_filtro(self):
        assert ps.validar_filtros_panel(fecha_pasada(30))["fecha"] == fecha_pasada(30)

    @pytest.mark.parametrize("fecha", ["2030-02-30", "15/01/2030", "hoy"])
    def test_fecha_invalida(self, fecha):
        with pytest.raises(ValidacionError, match="AAAA-MM-DD"):
            ps.validar_filtros_panel(fecha=fecha)

    def test_estado_invalido(self):
        with pytest.raises(ValidacionError, match="activa' o 'cancelada"):
            ps.validar_filtros_panel(estado="pendiente")


# ---------------------------------------------------------------------------
# Panel (RF-15)
# ---------------------------------------------------------------------------

class TestPanel:
    @pytest.mark.parametrize("sala, estado, ids", [
        (None, None, ["R0001", "R0003", "R0002"]),          # solo fecha
        ("S01", None, ["R0001", "R0002"]),                  # fecha + sala
        (None, "activa", ["R0001", "R0003"]),               # fecha + estado
        ("S01", "cancelada", ["R0002"]),                    # fecha + sala + estado
        ("S01", "activa", ["R0001"]),
        ("S05", None, []),                                  # sin resultados
    ])
    def test_combinacion_de_filtros(self, conexion, escenario, sala, estado, ids):
        panel = ps.obtener_panel(conexion, fecha=escenario["f1"], codigo_sala=sala, estado=estado)
        assert [r["id"] for r in panel["reservaciones"]] == ids
        assert panel["hay_resultados"] is bool(ids)

    def test_orden_por_fecha_y_hora(self, conexion, escenario):
        panel = ps.obtener_panel(conexion, fecha=escenario["f1"])
        horas = [r["hora_inicio"] for r in panel["reservaciones"]]
        assert horas == sorted(horas)

    def test_incluye_nombres_y_hora_fin(self, conexion, escenario):
        r = ps.obtener_panel(conexion, fecha=escenario["f1"], codigo_sala="S01")["reservaciones"][0]
        assert r["nombre_estudiante"] == "Andrea Solano"
        assert r["nombre_sala"] == "Sala Biblioteca 1"
        assert r["hora_fin"] == "10:00"

    def test_sin_fecha_usa_el_dia_actual(self, conexion, escenario):
        panel = ps.obtener_panel(conexion)
        assert panel["fecha_consulta"] == datetime.now().strftime("%Y-%m-%d")
        assert panel["reservaciones"] == []
        assert panel["hay_resultados"] is False

    def test_estado_vacio_sin_datos(self, conexion):
        panel = ps.obtener_panel(conexion, fecha=fecha_futura(1))
        assert panel["hay_resultados"] is False
        assert panel["proximas"] == []
        assert panel["indicadores"]["activas_total"] == 0
        assert all(s["porcentaje"] == 0 for s in panel["ocupacion"])

    def test_ocupacion_por_sala(self, conexion, escenario):
        ocupacion = {s["codigo"]: s for s in ps.obtener_panel(conexion, fecha=escenario["f1"])["ocupacion"]}
        # S01: 2 h activas (la cancelada no cuenta) de 12 h -> 17 %
        assert ocupacion["S01"]["horas_reservadas"] == 2
        assert ocupacion["S01"]["reservas"] == 1
        assert ocupacion["S01"]["porcentaje"] == 17
        assert ocupacion["S02"]["porcentaje"] == 8
        assert ocupacion["S04"]["estado"] == "fuera_de_servicio"   # se muestra aunque no se reserve
        assert len(ocupacion) == 5

    def test_ocupacion_completa_es_100(self, conexion):
        f = fecha_futura(4)
        for i, hora in enumerate(range(8, 20, 2)):
            insertar_reserva_directa(conexion, f"R05{i:02d}", ANDREA, "S03", f, f"{hora:02d}:00", 2, 1)
        ocupacion = {s["codigo"]: s for s in ps.obtener_panel(conexion, fecha=f)["ocupacion"]}
        assert ocupacion["S03"]["porcentaje"] == 100

    def test_filtro_de_sala_limita_ocupacion(self, conexion, escenario):
        panel = ps.obtener_panel(conexion, fecha=escenario["f1"], codigo_sala="S02")
        assert [s["codigo"] for s in panel["ocupacion"]] == ["S02"]

    def test_proximas_excluyen_canceladas_y_pasadas(self, conexion, escenario):
        insertar_reserva_directa(conexion, "R0009", ANDREA, "S05", fecha_pasada(1), "10:00", 1, 1)
        proximas = [r["id"] for r in ps.obtener_panel(conexion)["proximas"]]
        assert proximas == ["R0001", "R0003", "R0004"]

    def test_proximas_usa_la_hora_actual(self, conexion):
        hoy = datetime(2030, 3, 4, 12, 0)
        insertar_reserva_directa(conexion, "R0001", ANDREA, "S01", "2030-03-04", "10:00", 1, 1)
        insertar_reserva_directa(conexion, "R0002", ANDREA, "S01", "2030-03-04", "15:00", 1, 1)
        panel = ps.obtener_panel(conexion, ahora=hoy)
        assert [r["id"] for r in panel["proximas"]] == ["R0002"]
        assert panel["indicadores"]["reservas_hoy"] == 2
        assert panel["indicadores"]["proximas"] == 1

    def test_limite_de_proximas(self, conexion):
        for i in range(12):
            insertar_reserva_directa(conexion, f"R06{i:02d}", ANDREA, "S01", fecha_futura(i + 1), "10:00", 1, 1)
        assert len(ps.obtener_panel(conexion)["proximas"]) == 10

    def test_indicadores(self, conexion, escenario):
        ind = ps.obtener_panel(conexion, fecha=escenario["f1"])["indicadores"]
        assert ind["activas_total"] == 3
        assert ind["canceladas_total"] == 1
        assert (ind["salas_disponibles"], ind["salas_total"]) == (4, 5)
        assert ind["estudiantes_activos"] == 2
        # Promedio de salas disponibles en F1: (17 + 8 + 0 + 0) / 4 = 6
        assert ind["ocupacion_promedio"] == 6

    def test_panel_no_modifica_la_base_de_datos(self, conexion, escenario):
        antes = conexion.total_changes
        ps.obtener_panel(conexion, fecha=escenario["f1"], codigo_sala="S01", estado="activa")
        assert conexion.total_changes == antes

    def test_panel_se_actualiza_despues_de_crear_modificar_y_cancelar(self, conexion):
        f = fecha_futura(2)
        assert ps.obtener_panel(conexion, fecha=f)["indicadores"]["activas_total"] == 0

        rid = rs.crear_reservacion(conexion, ANDREA, "S01", f, "10:00", "1", "2")["id"]
        panel = ps.obtener_panel(conexion, fecha=f)
        assert [r["id"] for r in panel["reservaciones"]] == [rid]
        assert panel["indicadores"]["activas_total"] == 1

        rs.actualizar_reservacion(conexion, rid, "S02", f, "12:00", "2", "3")
        panel = ps.obtener_panel(conexion, fecha=f, codigo_sala="S02")
        assert panel["reservaciones"][0]["hora_fin"] == "14:00"
        assert {s["codigo"]: s["horas_reservadas"] for s in panel["ocupacion"]}["S02"] == 2

        rs.cancelar_reservacion(conexion, rid)
        panel = ps.obtener_panel(conexion, fecha=f)
        assert panel["indicadores"]["activas_total"] == 0
        assert panel["indicadores"]["canceladas_total"] == 1
        assert panel["reservaciones"][0]["estado"] == "cancelada"
        assert panel["proximas"] == []


# ---------------------------------------------------------------------------
# Historial / auditoría (RF-17)
# ---------------------------------------------------------------------------

class TestHistorial:
    def test_creacion_modificacion_y_cancelacion_se_registran(self, conexion):
        f = fecha_futura(2)
        rid = rs.crear_reservacion(conexion, ANDREA, "S01", f, "10:00", "1", "2")["id"]
        rs.actualizar_reservacion(conexion, rid, "S01", f, "11:00", "1", "2")
        rs.cancelar_reservacion(conexion, rid)

        registros = ps.consultar_historial(conexion)
        assert [(r["tipo_accion"], r["entidad"], r["identificador"]) for r in registros] == [
            ("cancelacion", "reservacion", rid),
            ("actualizacion", "reservacion", rid),
            ("creacion", "reservacion", rid),
        ]

    def test_cada_registro_tiene_los_campos_requeridos(self, conexion):
        db.insertar_estudiante(conexion, "N001234567", "Nuevo Estudiante", "nuevo@universidad.ac.cr")
        registro = ps.consultar_historial(conexion)[0]
        datetime.strptime(registro["fecha_hora"], "%Y-%m-%d %H:%M:%S")
        assert registro["tipo_accion"] == "creacion"
        assert registro["entidad"] == "estudiante"
        assert registro["identificador"] == "N001234567"

    def test_error_de_validacion_no_se_registra(self, conexion):
        with pytest.raises(ValidacionError):
            rs.crear_reservacion(conexion, "C004567890", "S01", fecha_futura(1), "10:00", "1", "2")
        with pytest.raises(ValidacionError):
            rs.cancelar_reservacion(conexion, "R9999")
        assert ps.consultar_historial(conexion) == []

    def test_actualizacion_sin_cambios_no_se_registra(self, conexion):
        db.actualizar_estudiante(conexion, ANDREA, "Andrea Solano", "andrea@universidad.ac.cr")
        db.actualizar_estado_sala(conexion, "S01", "disponible")
        assert ps.consultar_historial(conexion) == []

    @pytest.mark.parametrize("entidad, accion, esperados", [
        ("reservacion", None, 3),
        ("Estudiante", None, 1),
        ("sala", None, 1),
        (None, "creacion", 3),
        (None, "cancelacion", 1),
        ("reservacion", "creacion", 2),
        ("Todas", "Todas", 5),
    ])
    def test_filtros_de_historial(self, conexion, entidad, accion, esperados):
        f = fecha_futura(2)
        db.insertar_estudiante(conexion, "N001234567", "Nuevo Estudiante", "nuevo@universidad.ac.cr")
        db.actualizar_estado_sala(conexion, "S04", "disponible")
        r1 = rs.crear_reservacion(conexion, ANDREA, "S01", f, "10:00", "1", "2")["id"]
        rs.crear_reservacion(conexion, ANDREA, "S01", f, "11:00", "1", "2")
        rs.cancelar_reservacion(conexion, r1)
        assert len(ps.consultar_historial(conexion, entidad=entidad, tipo_accion=accion)) == esperados

    def test_filtro_por_fecha(self, conexion):
        db.insertar_estudiante(conexion, "N001234567", "Nuevo Estudiante", "nuevo@universidad.ac.cr")
        hoy = datetime.now().strftime("%Y-%m-%d")
        assert len(ps.consultar_historial(conexion, fecha=hoy)) == 1
        assert ps.consultar_historial(conexion, fecha=fecha_pasada(1)) == []

    @pytest.mark.parametrize("kwargs", [
        {"entidad": "usuario"},
        {"tipo_accion": "eliminacion"},
        {"fecha": "2030/01/01"},
    ])
    def test_filtros_invalidos(self, conexion, kwargs):
        with pytest.raises(ValidacionError):
            ps.consultar_historial(conexion, **kwargs)

    def test_consulta_es_solo_lectura(self, conexion):
        db.insertar_estudiante(conexion, "N001234567", "Nuevo Estudiante", "nuevo@universidad.ac.cr")
        antes = conexion.total_changes
        ps.consultar_historial(conexion, entidad="estudiante")
        assert conexion.total_changes == antes
