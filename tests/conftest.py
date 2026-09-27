"""
Configuración compartida de la suite de pruebas (Parte 5).

Cada prueba usa una base de datos SQLite temporal y aislada: nunca se toca
data/reservas.db. Las fechas se calculan relativas al día actual para que la
suite siga siendo válida sin importar cuándo se ejecute.
"""

import pytest

from src.database import db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def ruta_bd(tmp_path, monkeypatch):
    """Redirige la base de datos del sistema a un archivo temporal."""
    ruta = tmp_path / "prueba.db"
    monkeypatch.setattr(db, "DB_PATH", str(ruta))
    return ruta


@pytest.fixture
def conexion(ruta_bd):
    """Base de datos temporal inicializada con los datos del enunciado."""
    db.inicializar_base_datos()
    con = db.obtener_conexion()
    yield con
    con.close()


@pytest.fixture
def servicio(ruta_bd):
    """AppService real (la misma capa que usa la GUI) sobre la BD temporal."""
    from src.services.app_service import AppService

    srv = AppService()
    yield srv
    srv.cerrar()
