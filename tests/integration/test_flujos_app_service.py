"""
Pruebas de integración sobre AppService (la misma capa que usa la GUI):
servicios + reglas + SQLite trabajando juntos, sin automatizar clics (RNF-10).

Técnica: pruebas basadas en escenarios. Cobertura 14.1: flujo exitoso
completo, carné duplicado con otra capitalización, campos vacíos, recuperación
después de errores, persistencia y reinicio, creación y modificación de salas,
cambio de estado de estudiantes y salas, modificación válida e inválida,
cancelación exitosa/inexistente/repetida, series recurrentes con y sin
conflictos, cancelación de una ocurrencia y de una serie.
"""

import pytest

from src.database import db
from src.services.app_service import AppService
from tests.utilidades import fecha_futura

ANDREA, CARLOS, DANIELA = "A001234567", "B009876543", "C004567890"


# ---------------------------------------------------------------------------
# Escenario principal
# ---------------------------------------------------------------------------

def test_flujo_exitoso_completo(servicio):
    f = fecha_futura(3)

    # 1. Registrar estudiante (RF-02) y verlo en la consulta (RF-03)
    servicio.crear_estudiante("  e001122334 ", "  José Muñoz  ", " jose@universidad.ac.cr ")
    jose = next(e for e in servicio.listar_estudiantes() if e["carne"] == "E001122334")
    assert (jose["nombre"], jose["correo"], jose["estado"]) == ("José Muñoz", "jose@universidad.ac.cr", "activo")

    # 2. Consultar disponibilidad (RF-08) sin crear nada
    assert servicio.consultar_disponibilidad("S02", f, "10:00", "2")["disponible"] is True
    assert servicio.listar() == []

    # 3. Crear reservación (RF-05)
    resultado = servicio.crear("E001122334", "S02", f, "10:00", "2", "6")
    assert resultado["id"] == "R0001" and "R0001" in resultado["mensaje"]
    assert servicio.consultar_disponibilidad("S02", f, "11:00", "1")["disponible"] is False

    # 4. Consultar (RF-06) y buscar por carné sin distinguir mayúsculas (RF-07)
    reserva = servicio.listar()[0]
    assert (reserva["hora_fin"], reserva["estado"]) == ("12:00", "activa")
    assert [r["id"] for r in servicio.buscar_por_estudiante("e001122334")] == ["R0001"]

    # 5. Modificar conservando el ID (RF-13)
    servicio.modificar("R0001", "S03", f, "14:00", "1", "8")
    reserva = servicio.listar()[0]
    assert (reserva["id"], reserva["codigo_sala"], reserva["hora_inicio"]) == ("R0001", "S03", "14:00")

    # 6. Panel refleja la operación (RF-15)
    panel = servicio.obtener_panel(fecha=f)
    assert [r["id"] for r in panel["reservaciones"]] == ["R0001"]

    # 7. Cancelar (RF-09): permanece en el historial y libera el horario
    servicio.cancelar("R0001")
    assert servicio.listar()[0]["estado"] == "cancelada"
    assert servicio.consultar_disponibilidad("S03", f, "14:00", "1")["disponible"] is True
    assert servicio.obtener_panel(fecha=f)["indicadores"]["canceladas_total"] == 1

    # 8. Auditoría (RF-17): estudiante creado + reserva creada, modificada y cancelada
    acciones = [(r["tipo_accion"], r["entidad"]) for r in servicio.listar_historial()]
    assert acciones == [
        ("cancelacion", "reservacion"),
        ("actualizacion", "reservacion"),
        ("creacion", "reservacion"),
        ("creacion", "estudiante"),
    ]


# ---------------------------------------------------------------------------
# Estudiantes (RF-02, RF-03, RF-11)
# ---------------------------------------------------------------------------

class TestEstudiantes:
    def test_carne_duplicado_con_otra_capitalizacion(self, servicio):
        with pytest.raises(ValueError, match="Ya existe"):
            servicio.crear_estudiante("a001234567", "Otra Persona", "otra@universidad.ac.cr")
        assert len(servicio.listar_estudiantes()) == 3

    @pytest.mark.parametrize("carne, nombre, correo, mensaje", [
        ("", "Ana Pérez", "ana@universidad.ac.cr", "carné"),
        ("E001122334", "   ", "ana@universidad.ac.cr", "nombre"),
        ("E001122334", "Ana Pérez", "", "@"),
        ("E001122334", "Ana Pérez", "ana@universidad", "punto"),
    ])
    def test_registro_invalido_no_guarda_nada(self, servicio, carne, nombre, correo, mensaje):
        with pytest.raises(ValueError, match=mensaje):
            servicio.crear_estudiante(carne, nombre, correo)
        assert len(servicio.listar_estudiantes()) == 3
        assert servicio.listar_historial() == []

    def test_listado_incluye_activos_e_inactivos_ordenado(self, servicio):
        estudiantes = servicio.listar_estudiantes()
        assert [e["nombre"] for e in estudiantes] == ["Andrea Solano", "Carlos Méndez", "Daniela Rojas"]
        assert {e["estado"] for e in estudiantes} == {"activo", "inactivo"}

    def test_editar_estudiante_valida_y_no_cambia_carne(self, servicio):
        servicio.actualizar_estudiante(ANDREA, "Andrea Solano Mora", "andrea.solano@universidad.ac.cr")
        andrea = next(e for e in servicio.listar_estudiantes() if e["carne"] == ANDREA)
        assert andrea["nombre"] == "Andrea Solano Mora"
        with pytest.raises(ValueError):
            servicio.actualizar_estudiante(ANDREA, "An", "andrea@universidad.ac.cr")
        andrea = next(e for e in servicio.listar_estudiantes() if e["carne"] == ANDREA)
        assert andrea["nombre"] == "Andrea Solano Mora"

    def test_inactivar_impide_reservar_y_conserva_historial(self, servicio):
        f = fecha_futura(2)
        servicio.crear(CARLOS, "S01", f, "10:00", "1", "2")
        servicio.cambiar_estado_estudiante(CARLOS, "inactivo")
        with pytest.raises(ValueError, match="inactivo"):
            servicio.crear(CARLOS, "S01", f, "12:00", "1", "2")
        assert len(servicio.buscar_por_estudiante(CARLOS)) == 1

    def test_reactivar_permite_reservar(self, servicio):
        servicio.cambiar_estado_estudiante(DANIELA, "activo")
        assert servicio.crear(DANIELA, "S01", fecha_futura(2), "10:00", "1", "1")["id"] == "R0001"

    def test_buscar_estudiante_inexistente(self, servicio):
        with pytest.raises(ValueError, match="no existe"):
            servicio.buscar_por_estudiante("Z999999999")

    def test_buscar_estudiante_sin_reservaciones(self, servicio):
        assert servicio.buscar_por_estudiante(DANIELA) == []


# ---------------------------------------------------------------------------
# Salas (RF-04, RF-12)
# ---------------------------------------------------------------------------

class TestSalas:
    def test_crear_sala(self, servicio):
        servicio.crear_sala(" s06 ", "Sala de reunión", "5")
        sala = next(s for s in servicio.listar_salas() if s["codigo"] == "S06")
        assert (sala["nombre"], sala["capacidad"], sala["estado"]) == ("Sala de reunión", 5, "disponible")
        assert servicio.crear("A001234567", "S06", fecha_futura(1), "10:00", "1", "5")["id"] == "R0001"

    @pytest.mark.parametrize("codigo, nombre, capacidad", [
        ("S01", "Duplicada", "4"),
        ("S07", "", "4"),
        ("S07", "Sala", "0"),
        ("S07", "Sala", "2.5"),
        ("", "Sala", "4"),
    ])
    def test_crear_sala_invalida(self, servicio, codigo, nombre, capacidad):
        with pytest.raises(ValueError):
            servicio.crear_sala(codigo, nombre, capacidad)
        assert len(servicio.listar_salas()) == 5

    def test_modificar_nombre_y_capacidad(self, servicio):
        servicio.actualizar_sala("S01", "Sala Biblioteca Uno", "6")
        sala = servicio.listar_salas()[0]
        assert (sala["nombre"], sala["capacidad"]) == ("Sala Biblioteca Uno", 6)

    def test_no_reducir_capacidad_bajo_reserva_futura(self, servicio):
        servicio.crear(ANDREA, "S03", fecha_futura(2), "10:00", "1", "9")
        with pytest.raises(ValueError, match="No se puede reducir"):
            servicio.actualizar_sala("S03", "Laboratorio de estudio", "8")
        assert servicio.listar_salas()[2]["capacidad"] == 10

    def test_fuera_de_servicio_rechaza_y_conserva_historial(self, servicio):
        f = fecha_futura(2)
        servicio.crear(ANDREA, "S02", f, "10:00", "1", "2")
        servicio.cambiar_estado_sala("S02", "fuera_de_servicio")
        with pytest.raises(ValueError, match="fuera de servicio"):
            servicio.crear(CARLOS, "S02", f, "14:00", "1", "2")
        assert servicio.listar()[0]["codigo_sala"] == "S02"
        estados = {s["codigo"]: s["estado"] for s in servicio.listar_salas()}
        assert estados["S02"] == "fuera_de_servicio"

    def test_habilitar_sala_fuera_de_servicio(self, servicio):
        servicio.cambiar_estado_sala("S04", "disponible")
        assert servicio.crear(ANDREA, "S04", fecha_futura(1), "10:00", "1", "8")["id"] == "R0001"

    def test_estado_invalido(self, servicio):
        with pytest.raises(ValueError):
            servicio.cambiar_estado_sala("S01", "cerrada")


# ---------------------------------------------------------------------------
# Reservaciones: modificación y cancelación (RF-09, RF-13)
# ---------------------------------------------------------------------------

class TestModificacionCancelacion:
    def test_modificacion_invalida_conserva_datos_originales(self, servicio):
        f = fecha_futura(2)
        servicio.crear(ANDREA, "S01", f, "10:00", "1", "2")
        servicio.crear(CARLOS, "S01", f, "12:00", "1", "2")
        original = servicio.listar()[0]

        for args in [
            ("S01", f, "12:00", "1", "2"),     # conflicto con R0002
            ("S01", f, "10:00", "1", "9"),     # excede capacidad
            ("S04", f, "10:00", "1", "2"),     # sala fuera de servicio
            ("S01", f, "19:00", "2", "2"),     # termina después de las 20:00
            ("S01", "2020-01-01", "10:00", "1", "2"),   # fecha pasada
        ]:
            with pytest.raises(ValueError):
                servicio.modificar("R0001", *args)
            assert servicio.listar()[0] == original

    def test_modificar_en_su_mismo_horario_no_choca_consigo_misma(self, servicio):
        f = fecha_futura(2)
        servicio.crear(ANDREA, "S01", f, "10:00", "2", "2")
        servicio.modificar("R0001", "S01", f, "11:00", "1", "4")
        assert servicio.listar()[0]["cantidad_personas"] == 4

    def test_no_se_modifica_una_cancelada(self, servicio):
        f = fecha_futura(2)
        servicio.crear(ANDREA, "S01", f, "10:00", "1", "2")
        servicio.cancelar("R0001")
        with pytest.raises(ValueError, match="cancelada"):
            servicio.modificar("R0001", "S01", f, "11:00", "1", "2")

    def test_cancelacion_exitosa_inexistente_y_repetida(self, servicio):
        servicio.crear(ANDREA, "S01", fecha_futura(2), "10:00", "1", "2")
        assert "cancelada correctamente" in servicio.cancelar("r0001")["mensaje"]
        with pytest.raises(ValueError, match="ya se encuentra cancelada"):
            servicio.cancelar("R0001")
        with pytest.raises(ValueError, match="no existe"):
            servicio.cancelar("R9999")
        with pytest.raises(ValueError, match="vacío"):
            servicio.cancelar("   ")
        assert len(servicio.listar_historial(tipo_accion="cancelacion")) == 1


# ---------------------------------------------------------------------------
# Recurrencia (RF-14)
# ---------------------------------------------------------------------------

class TestRecurrencia:
    def test_serie_sin_conflictos(self, servicio):
        f = fecha_futura(1)
        resumen = servicio.validar_recurrencia(ANDREA, "S03", f, "16:00", "2", "6", "4")
        assert resumen["tiene_conflictos"] is False
        assert len(resumen["ocurrencias"]) == 4
        assert servicio.listar() == []                     # validar no guarda

        serie = servicio.crear_serie_recurrente(ANDREA, "S03", f, "16:00", "2", "6", "4")
        assert serie["reservaciones"] == ["R0001", "R0002", "R0003", "R0004"]
        fechas = [r["fecha"] for r in servicio.listar()]
        assert fechas == [fecha_futura(1 + 7 * i) for i in range(4)]

    def test_serie_con_conflicto_muestra_resumen_y_no_guarda(self, servicio):
        f = fecha_futura(1)
        servicio.crear(CARLOS, "S03", fecha_futura(8), "16:00", "1", "2")   # choca con la 2.ª
        resumen = servicio.validar_recurrencia(ANDREA, "S03", f, "16:00", "2", "6", "3")
        assert resumen["tiene_conflictos"] is True
        assert [o["disponible"] for o in resumen["ocurrencias"]] == [True, False, True]
        with pytest.raises(ValueError, match="conflictos"):
            servicio.crear_serie_recurrente(ANDREA, "S03", f, "16:00", "2", "6", "3")
        assert len(servicio.listar()) == 1

    @pytest.mark.parametrize("ocurrencias", ["1", "9", "dos"])
    def test_cantidad_de_ocurrencias_invalida(self, servicio, ocurrencias):
        with pytest.raises(ValueError):
            servicio.validar_recurrencia(ANDREA, "S03", fecha_futura(1), "16:00", "1", "2", ocurrencias)

    def test_cancelar_una_ocurrencia(self, servicio):
        servicio.crear_serie_recurrente(ANDREA, "S03", fecha_futura(1), "16:00", "1", "2", "3")
        servicio.cancelar_ocurrencia("R0002")
        assert [r["estado"] for r in servicio.listar()] == ["activa", "cancelada", "activa"]

    def test_cancelar_serie_desde_una_ocurrencia(self, servicio):
        servicio.crear_serie_recurrente(ANDREA, "S03", fecha_futura(1), "16:00", "1", "2", "4")
        resultado = servicio.cancelar_serie_desde_ocurrencia("R0002")
        assert resultado["reservaciones_canceladas"] == ["R0002", "R0003", "R0004"]
        assert [r["estado"] for r in servicio.listar()] == ["activa", "cancelada", "cancelada", "cancelada"]

    def test_cancelar_serie_de_reserva_individual(self, servicio):
        servicio.crear(ANDREA, "S01", fecha_futura(1), "10:00", "1", "2")
        with pytest.raises(ValueError, match="no pertenece a una serie"):
            servicio.cancelar_serie_desde_ocurrencia("R0001")


# ---------------------------------------------------------------------------
# Persistencia, reinicio y recuperación
# ---------------------------------------------------------------------------

class TestPersistenciaYRecuperacion:
    def test_persistencia_y_continuidad_tras_reiniciar(self, ruta_bd):
        f = fecha_futura(2)
        primero = AppService()
        primero.crear_estudiante("E001122334", "María Núñez", "maria@universidad.ac.cr")
        primero.crear(ANDREA, "S01", f, "10:00", "1", "2")
        primero.crear(CARLOS, "S02", f, "10:00", "1", "2")
        primero.cancelar("R0002")
        primero.cerrar()

        segundo = AppService()      # "reinicio" de la aplicación
        try:
            assert len(segundo.listar_estudiantes()) == 4
            assert [r["estado"] for r in segundo.listar()] == ["activa", "cancelada"]
            assert segundo.crear("E001122334", "S03", f, "10:00", "1", "2")["id"] == "R0003"
            maria = next(e for e in segundo.listar_estudiantes() if e["carne"] == "E001122334")
            assert maria["nombre"] == "María Núñez"
        finally:
            segundo.cerrar()

    def test_recuperacion_despues_de_errores(self, servicio):
        f = fecha_futura(2)
        errores = [
            lambda: servicio.crear(ANDREA, "S01", "2030-02-30", "10:00", "1", "2"),
            lambda: servicio.crear(ANDREA, "S01", f, "10:30", "1", "2"),
            lambda: servicio.crear(ANDREA, "S01", f, "10:00", "1.5", "2"),
            lambda: servicio.crear(ANDREA, "S01", f, "10:00", "1", "cero"),
            lambda: servicio.crear("", "", "", "", "", ""),
            lambda: servicio.modificar("R0404", "S01", f, "10:00", "1", "2"),
        ]
        for accion in errores:
            with pytest.raises(ValueError):
                accion()

        # Ningún dato parcial y el sistema sigue operando con normalidad.
        assert servicio.listar() == []
        assert servicio.listar_historial() == []
        assert servicio.crear(ANDREA, "S01", f, "10:00", "1", "2")["id"] == "R0001"

    def test_errores_tecnicos_se_traducen_sin_trazas(self, servicio):
        servicio._conexion.close()      # simula una falla de la base de datos
        with pytest.raises(RuntimeError, match="^No se pudo"):
            servicio.obtener_panel()
        with pytest.raises(RuntimeError, match="^No se pudo"):
            servicio.listar_historial()
        with pytest.raises(RuntimeError, match="^No se pudieron"):
            servicio.listar_estudiantes()
        servicio._conexion = db.obtener_conexion()     # para que el fixture cierre sin error
