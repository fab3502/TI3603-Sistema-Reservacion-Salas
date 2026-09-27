"""Utilidades compartidas por las pruebas (fechas, reloj simulado, inserciones directas)."""

from datetime import date, datetime, timedelta


# ---------------------------------------------------------------------------
# Utilidades de fechas
# ---------------------------------------------------------------------------

def fecha_futura(dias=1):
    """Fecha AAAA-MM-DD a 'dias' días de hoy."""
    return (date.today() + timedelta(days=dias)).strftime("%Y-%m-%d")


def fecha_pasada(dias=1):
    return (date.today() - timedelta(days=dias)).strftime("%Y-%m-%d")


def insertar_reserva_directa(con, id_reserva, carne, sala, fecha, hora, duracion=1,
                             personas=1, estado="activa", serie_id=None):
    """
    Inserta una reservación directamente en SQLite, sin validaciones.

    Se usa solo para preparar escenarios imposibles de crear por la interfaz,
    por ejemplo reservaciones en el pasado.
    """
    con.execute(
        """
        INSERT INTO reservaciones
            (id, carne, codigo_sala, fecha, hora_inicio, duracion,
             cantidad_personas, estado, serie_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (id_reserva, carne, sala, fecha, hora, duracion, personas, estado, serie_id),
    )
    con.commit()


class RelojFijo:
    """
    Permite simular la fecha y hora del sistema en un módulo que hace
    ``from datetime import datetime, date``.
    """

    def __init__(self, momento: datetime):
        self.momento = momento

        reloj = self

        class _DateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                return reloj.momento

        class _Date(date):
            @classmethod
            def today(cls):
                return reloj.momento.date()

        self.datetime = _DateTime
        self.date = _Date
