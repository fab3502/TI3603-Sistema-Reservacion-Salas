"""
Pruebas unitarias de src/database/db.py (persistencia en SQLite).

Cobertura 14.1: persistencia, reinicio y continuidad de identificadores,
persistencia e integridad en SQLite, datos iniciales (RF-01), RN-13
(IDs no reutilizables) y RNF-08 (tildes y ñ).
"""

import sqlite3

import pytest

from src.database import db
from tests.utilidades import fecha_futura


def _contar(con, tabla):
    return con.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]


# ---------------------------------------------------------------------------
# RF-01: creación y carga
# ---------------------------------------------------------------------------

class TestCreacionBaseDatos:
    def test_crea_archivo_y_tablas_si_no_existe(self, ruta_bd):
        assert not ruta_bd.exists()
        db.inicializar_base_datos()
        assert ruta_bd.exists()
        con = db.obtener_conexion()
        tablas = {f[0] for f in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        con.close()
        assert {"estudiantes", "salas", "reservaciones", "auditoria", "contadores"} <= tablas

    def test_salas_iniciales_desde_primera_ejecucion(self, conexion):
        salas = db.listar_salas(conexion)
        assert [s["codigo"] for s in salas] == ["S01", "S02", "S03", "S04", "S05"]
        assert db.obtener_sala(conexion, "S04")["estado"] == "fuera_de_servicio"
        assert db.obtener_sala(conexion, "S05")["nombre"] == "Cubículo individual"

    def test_estudiantes_iniciales(self, conexion):
        estudiantes = {e["carne"]: e for e in db.listar_estudiantes(conexion)}
        assert set(estudiantes) == {"A001234567", "B009876543", "C004567890"}
        assert estudiantes["C004567890"]["estado"] == "inactivo"
        assert estudiantes["B009876543"]["nombre"] == "Carlos Méndez"

    def test_inicializar_dos_veces_no_duplica(self, conexion):
        db.inicializar_base_datos()
        db.inicializar_base_datos()
        assert _contar(conexion, "salas") == 5
        assert _contar(conexion, "estudiantes") == 3
        assert _contar(conexion, "contadores") == 1

    def test_reinicializar_respeta_cambios_de_la_persona_usuaria(self, conexion):
        db.actualizar_estado_estudiante(conexion, "A001234567", "inactivo")
        db.actualizar_estado_sala(conexion, "S04", "disponible")
        db.inicializar_base_datos()
        assert db.obtener_estudiante(conexion, "A001234567")["estado"] == "inactivo"
        assert db.obtener_sala(conexion, "S04")["estado"] == "disponible"

    def test_datos_iniciales_no_generan_auditoria(self, conexion):
        assert _contar(conexion, "auditoria") == 0


# ---------------------------------------------------------------------------
# Identificadores (sección 9, RN-13)
# ---------------------------------------------------------------------------

class TestIdentificadores:
    def test_formato_y_secuencia(self, conexion):
        f = fecha_futura(2)
        ids = [db.crear_reservacion(conexion, "A001234567", "S01", f, h, 1, 2) for h in ("08:00", "09:00", "10:00")]
        assert ids == ["R0001", "R0002", "R0003"]

    def test_ids_cancelados_no_se_reutilizan(self, conexion):
        f = fecha_futura(2)
        primero = db.crear_reservacion(conexion, "A001234567", "S01", f, "08:00", 1, 2)
        db.cancelar_reservacion(conexion, primero)
        segundo = db.crear_reservacion(conexion, "A001234567", "S01", f, "08:00", 1, 2)
        assert (primero, segundo) == ("R0001", "R0002")

    def test_continuidad_despues_de_reiniciar(self, conexion):
        f = fecha_futura(2)
        db.crear_reservacion(conexion, "A001234567", "S01", f, "08:00", 1, 2)
        db.crear_reservacion(conexion, "A001234567", "S01", f, "09:00", 1, 2)
        conexion.close()

        # Simula cerrar y volver a abrir la aplicación.
        db.inicializar_base_datos()
        nueva = db.obtener_conexion()
        try:
            assert db.crear_reservacion(nueva, "B009876543", "S02", f, "08:00", 1, 2) == "R0003"
            assert len(db.listar_reservaciones(nueva)) == 3
        finally:
            nueva.close()


# ---------------------------------------------------------------------------
# Integridad (RNF-06) y codificación (RNF-08)
# ---------------------------------------------------------------------------

class TestIntegridad:
    def test_carne_duplicado_con_otra_capitalizacion(self, conexion):
        with pytest.raises(sqlite3.IntegrityError):
            db.insertar_estudiante(conexion, "a001234567", "Otra Persona", "otra@universidad.ac.cr")
        assert _contar(conexion, "estudiantes") == 3

    def test_codigo_de_sala_duplicado(self, conexion):
        with pytest.raises(sqlite3.IntegrityError):
            db.insertar_sala(conexion, "S01", "Repetida", 3)
        assert _contar(conexion, "salas") == 5

    def test_llave_foranea_estudiante_inexistente(self, conexion):
        with pytest.raises(sqlite3.IntegrityError):
            db.crear_reservacion(conexion, "Z999999999", "S01", fecha_futura(1), "10:00", 1, 1)
        assert _contar(conexion, "reservaciones") == 0

    def test_insercion_fallida_no_consume_id_ni_audita(self, conexion):
        with pytest.raises(sqlite3.IntegrityError):
            db.crear_reservacion(conexion, "Z999999999", "S01", fecha_futura(1), "10:00", 1, 1)
        assert _contar(conexion, "auditoria") == 0
        assert db.crear_reservacion(conexion, "A001234567", "S01", fecha_futura(1), "10:00", 1, 1) == "R0001"

    def test_indice_unico_evita_reserva_activa_identica(self, conexion):
        f = fecha_futura(1)
        db.crear_reservacion(conexion, "A001234567", "S01", f, "10:00", 1, 1)
        with pytest.raises(db.ReservaDuplicadaError):
            db.crear_reservacion(conexion, "B009876543", "S01", f, "10:00", 1, 1)
        assert _contar(conexion, "reservaciones") == 1

    def test_serie_es_atomica(self, conexion):
        f1, f2 = fecha_futura(7), fecha_futura(14)
        db.crear_reservacion(conexion, "B009876543", "S02", f2, "10:00", 1, 1)   # R0001 bloquea
        serie = [
            {"carne": "A001234567", "codigo_sala": "S02", "fecha": f1, "hora_inicio": "10:00",
             "duracion": 1, "cantidad_personas": 2},
            {"carne": "A001234567", "codigo_sala": "S02", "fecha": f2, "hora_inicio": "10:00",
             "duracion": 1, "cantidad_personas": 2},
        ]
        with pytest.raises(db.ReservaDuplicadaError):
            db.crear_serie_reservaciones(conexion, serie, "SER-TEST")
        # No quedó ninguna ocurrencia parcial, ni auditoría, ni IDs consumidos.
        assert _contar(conexion, "reservaciones") == 1
        assert _contar(conexion, "auditoria") == 1
        assert db.crear_reservacion(conexion, "A001234567", "S03", f1, "10:00", 1, 1) == "R0002"

    def test_tildes_y_enie_se_conservan(self, conexion):
        db.insertar_estudiante(conexion, "N001234567", "Íñigo Muñoz Peñaranda", "inigo@universidad.ac.cr")
        db.insertar_sala(conexion, "S06", "Sala de reunión Ñandú", 3)
        conexion.close()
        nueva = db.obtener_conexion()
        try:
            assert db.obtener_estudiante(nueva, "N001234567")["nombre"] == "Íñigo Muñoz Peñaranda"
            assert db.obtener_sala(nueva, "S06")["nombre"] == "Sala de reunión Ñandú"
        finally:
            nueva.close()

    def test_cancelacion_persiste_y_conserva_historial(self, conexion):
        rid = db.crear_reservacion(conexion, "A001234567", "S01", fecha_futura(1), "10:00", 1, 1)
        db.cancelar_reservacion(conexion, rid)
        conexion.close()
        nueva = db.obtener_conexion()
        try:
            assert db.obtener_reservacion(nueva, rid)["estado"] == "cancelada"
        finally:
            nueva.close()

    def test_consultas_ordenadas(self, conexion):
        db.crear_reservacion(conexion, "A001234567", "S01", fecha_futura(3), "08:00", 1, 1)
        db.crear_reservacion(conexion, "A001234567", "S01", fecha_futura(1), "15:00", 1, 1)
        db.crear_reservacion(conexion, "B009876543", "S02", fecha_futura(1), "09:00", 1, 1)
        orden = [(r["fecha"], r["hora_inicio"]) for r in db.listar_reservaciones(conexion)]
        assert orden == sorted(orden)
        nombres = [e["nombre"] for e in db.listar_estudiantes(conexion)]
        assert nombres == sorted(nombres)
