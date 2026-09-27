"""
Pruebas de integración de pantallas Tkinter (sin automatizar clics sobre la
pantalla real: se invocan los métodos de las vistas y se simulan los diálogos).

Cobertura 14.1: exportación CSV y cancelación del selector de archivo (RF-16),
actualización del panel después de una operación (RF-15), historial no
editable desde la interfaz (RF-17).

Si el equipo no tiene pantalla disponible (por ejemplo, un servidor sin
entorno gráfico), estas pruebas se omiten automáticamente.
"""

import csv

import pytest

tk = pytest.importorskip("tkinter", reason="Esta instalación de Python no incluye Tkinter.")
from tkinter import ttk  # noqa: E402

from src.ui import dashboard_view, history_view, reports_view
from src.ui.styles import configurar_estilos
from tests.utilidades import fecha_futura

pytestmark = pytest.mark.gui


@pytest.fixture(scope="module")
def _ventana_principal():
    """
    Una sola ventana Tk para todo el módulo.

    Crear y destruir muchas ventanas tk.Tk() seguidas puede fallar de forma
    intermitente en Windows, así que se reutiliza una sola.
    """
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"No hay pantalla disponible para crear ventanas Tkinter: {exc}")
    root.withdraw()
    configurar_estilos(root)
    yield root
    root.destroy()


@pytest.fixture
def raiz(_ventana_principal):
    """Contenedor nuevo y aislado para cada prueba dentro de la ventana única."""
    marco = tk.Frame(_ventana_principal)
    yield marco
    marco.destroy()


@pytest.fixture
def sin_dialogos(monkeypatch):
    """Registra los mensajes en lugar de mostrar ventanas modales."""
    mensajes = []
    for modulo in (reports_view, dashboard_view, history_view):
        for tipo in ("showinfo", "showwarning", "showerror"):
            monkeypatch.setattr(
                modulo.messagebox, tipo,
                lambda titulo, texto, parent=None, _t=tipo: mensajes.append((_t, titulo, texto)),
            )
    return mensajes


def _reporte_generado(raiz, servicio, f):
    vista = reports_view.ReportsView(raiz, servicio, lambda: None)
    vista.entry_fecha_inicio.insert(0, f)
    vista.entry_fecha_fin.insert(0, f)
    vista._generar_reporte()
    return vista


# ---------------------------------------------------------------------------
# RF-16: exportación CSV
# ---------------------------------------------------------------------------

def test_exportar_csv_utf8_con_encabezados(raiz, servicio, sin_dialogos, tmp_path, monkeypatch):
    f = fecha_futura(2)
    servicio.crear_estudiante("N001234567", "Íñigo Muñoz", "inigo@universidad.ac.cr")
    servicio.crear("N001234567", "S05", f, "10:00", "1", "1")
    servicio.crear("A001234567", "S01", f, "11:00", "2", "4")
    servicio.cancelar("R0002")

    vista = _reporte_generado(raiz, servicio, f)
    assert len(vista.tabla.get_children()) == 2

    destino = tmp_path / "reporte ñandú.csv"
    monkeypatch.setattr(reports_view.filedialog, "asksaveasfilename", lambda **kw: str(destino))
    vista._exportar_csv()

    with open(destino, encoding="utf-8-sig", newline="") as archivo:
        filas = list(csv.reader(archivo))
    assert filas[0][:4] == ["ID", "Carné", "Sala", "Fecha"]
    assert [fila[0] for fila in filas[1:]] == ["R0001", "R0002"]
    assert filas[2][-1] == "cancelada"
    assert destino.read_bytes().decode("utf-8-sig")        # decodifica sin errores
    assert ("showinfo", "Exportación completada", "El archivo CSV se exportó correctamente.") in sin_dialogos


def test_cancelar_selector_no_crea_archivo(raiz, servicio, sin_dialogos, tmp_path, monkeypatch):
    f = fecha_futura(2)
    servicio.crear("A001234567", "S01", f, "10:00", "1", "2")
    vista = _reporte_generado(raiz, servicio, f)

    monkeypatch.setattr(reports_view.filedialog, "asksaveasfilename", lambda **kw: "")
    vista._exportar_csv()

    assert list(tmp_path.iterdir()) == [tmp_path / "prueba.db"]    # solo la BD temporal
    assert not any(tipo == "showinfo" for tipo, *_ in sin_dialogos)


def test_exportar_sin_reporte_advierte(raiz, servicio, sin_dialogos):
    vista = reports_view.ReportsView(raiz, servicio, lambda: None)
    vista._exportar_csv()
    assert sin_dialogos[-1][0] == "showwarning"


def test_reporte_rango_obligatorio(raiz, servicio, sin_dialogos):
    vista = reports_view.ReportsView(raiz, servicio, lambda: None)
    vista._generar_reporte()
    assert sin_dialogos[-1] == ("showwarning", "Reporte", "Ingrese la fecha inicial y la fecha final.")


# ---------------------------------------------------------------------------
# RF-15: panel en la interfaz
# ---------------------------------------------------------------------------

def test_panel_muestra_estado_vacio_y_se_actualiza(raiz, servicio, sin_dialogos):
    f = fecha_futura(2)
    vista = dashboard_view.DashboardView(raiz, servicio, lambda: None)
    vista.pack()
    vista.var_fecha.set(f)
    vista.refrescar()
    raiz.update_idletasks()
    assert vista.tabla_reservaciones.get_children() == ()
    assert vista.lbl_reservaciones_vacia.winfo_manager() == "pack"      # estado vacío visible

    servicio.crear("A001234567", "S01", f, "10:00", "2", "3")
    vista.refrescar()
    raiz.update_idletasks()
    filas = [vista.tabla_reservaciones.item(i, "values") for i in vista.tabla_reservaciones.get_children()]
    assert filas[0][0] == "R0001"
    assert vista.lbl_reservaciones_vacia.winfo_manager() == ""          # estado vacío oculto
    assert vista._kpis["activas_total"].cget("text") == "1"


def test_panel_combina_filtros_desde_la_interfaz(raiz, servicio, sin_dialogos):
    f = fecha_futura(2)
    servicio.crear("A001234567", "S01", f, "10:00", "1", "3")
    servicio.crear("B009876543", "S02", f, "10:00", "1", "3")
    servicio.cancelar("R0002")

    vista = dashboard_view.DashboardView(raiz, servicio, lambda: None)
    vista.var_fecha.set(f)
    vista.var_sala.set("S02")
    vista.var_estado.set("cancelada")
    vista.refrescar()
    ids = [vista.tabla_reservaciones.item(i, "values")[0] for i in vista.tabla_reservaciones.get_children()]
    assert ids == ["R0002"]


def test_panel_filtro_invalido_muestra_mensaje(raiz, servicio, sin_dialogos):
    vista = dashboard_view.DashboardView(raiz, servicio, lambda: None)
    vista.var_fecha.set("31/12/2030")
    vista.refrescar()
    assert sin_dialogos[-1][0] == "showerror"
    assert "AAAA-MM-DD" in sin_dialogos[-1][2]


def test_barra_de_ocupacion():
    assert dashboard_view.barra_ocupacion(0) == "░░░░░░░░░░  0 %"
    assert dashboard_view.barra_ocupacion(50) == "█████░░░░░  50 %"
    assert dashboard_view.barra_ocupacion(150).endswith("100 %")


# ---------------------------------------------------------------------------
# RF-17: historial en la interfaz
# ---------------------------------------------------------------------------

def test_historial_se_muestra_y_no_es_editable(raiz, servicio, sin_dialogos):
    servicio.crear("A001234567", "S01", fecha_futura(2), "10:00", "1", "2")
    servicio.cancelar("R0001")

    vista = history_view.HistoryView(raiz, servicio, lambda: None)
    filas = [vista.tabla.item(i, "values") for i in vista.tabla.get_children()]
    assert [(f[1], f[2], f[3]) for f in filas] == [
        ("Cancelación", "Reservación", "R0001"),
        ("Creación", "Reservación", "R0001"),
    ]

    # La vista no ofrece botones de edición ni eliminación.
    textos = set()
    pendientes = [vista]
    while pendientes:
        widget = pendientes.pop()
        pendientes.extend(widget.winfo_children())
        if isinstance(widget, ttk.Button):
            textos.add(widget.cget("text"))
    assert textos == {"Volver", "Buscar", "Limpiar"}

    vista.var_accion.set("Creación")
    vista.refrescar()
    assert len(vista.tabla.get_children()) == 1
