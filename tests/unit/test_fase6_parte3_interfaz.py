"""Regresión Fase 6, Parte 3: interfaz gráfica y navegación.

Estas pruebas cubren las reglas de presentación que pueden validarse sin abrir
ventanas Tkinter. Los flujos visuales se reejecutan manualmente para las capturas
antes/después del entregable.
"""

import pytest

from src.ui.dashboard_view import cantidad_proximas_visibles
from src.ui.recurrence_view import RecurrenceWindow
from src.ui.reports_view import validar_rango_fechas


# ---------------------------------------------------------------------------
# Reportes H-01 (RF-16): validar formato y orden del rango antes de consultar
# ---------------------------------------------------------------------------

def test_reporte_acepta_rango_valido():
    assert validar_rango_fechas("2026-10-20", "2026-10-27") == (
        "2026-10-20",
        "2026-10-27",
    )


@pytest.mark.parametrize(
    "inicio,fin",
    [
        ("abc", "xyz"),
        ("20/10/2026", "27/10/2026"),
        ("2026-2-03", "2026-10-27"),
    ],
)
def test_reporte_rechaza_formato_invalido(inicio, fin):
    with pytest.raises(ValueError, match="AAAA-MM-DD"):
        validar_rango_fechas(inicio, fin)


def test_reporte_rechaza_fecha_final_anterior():
    with pytest.raises(ValueError, match="fecha final"):
        validar_rango_fechas("2026-10-27", "2026-10-20")


# ---------------------------------------------------------------------------
# Panel H-01 (RF-15): el KPI de próximas debe coincidir con la tabla visible
# ---------------------------------------------------------------------------

def test_indicador_proximas_usa_resultado_filtrado_y_limitado():
    panel = {"proximas": [{"id": f"R{i:04d}"} for i in range(1, 11)]}
    assert cantidad_proximas_visibles(panel) == 10


def test_indicador_proximas_refleja_filtro_de_sala():
    assert cantidad_proximas_visibles({"proximas": [{"id": "R1"}, {"id": "R2"}]}) == 2
    assert cantidad_proximas_visibles({"proximas": []}) == 0


# ---------------------------------------------------------------------------
# Recurrencia H-03 (RF-14): resumen explícito antes de confirmar
# ---------------------------------------------------------------------------

def test_confirmacion_recurrencia_muestra_fechas_y_conflictos():
    texto = RecurrenceWindow._texto_confirmacion(
        [
            {"ocurrencia": 1, "fecha": "2026-11-01", "disponible": True},
            {"ocurrencia": 2, "fecha": "2026-11-08", "disponible": False},
        ]
    )
    assert "2026-11-01" in texto
    assert "Disponible" in texto
    assert "2026-11-08" in texto
    assert "Conflicto" in texto
    assert "confirmar" in texto.lower()
