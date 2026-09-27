"""
Restauración de datos iniciales y carga de datos de prueba (Parte 5).

Uso desde la carpeta raíz del proyecto:

    python -m src.database.datos_prueba --restaurar
        Elimina data/reservas.db y la vuelve a crear solo con los datos
        iniciales del enunciado (5 salas y 3 estudiantes).

    python -m src.database.datos_prueba --demo
        Restaura los datos iniciales y además carga reservaciones de
        demostración con fechas relativas al día actual, pasando por las
        mismas validaciones y reglas de negocio que usa la interfaz.

Los datos de demostración incluyen tildes y ñ (RNF-08), reservas
consecutivas (RN-10), una cancelación (RN-12), una modificación y una
serie recurrente (RF-14), para que el panel y el historial muestren
información desde la primera ejecución.
"""

import argparse
import os
from datetime import date, datetime, timedelta

from src.database import db


ESTUDIANTES_DEMO = [
    ("E001122334", "José Muñoz Ávila", "jose.munoz@universidad.ac.cr"),
    ("F005566778", "María Fernández Núñez", "maria.fernandez@universidad.ac.cr"),
]


def restaurar_datos_iniciales():
    """Elimina la base de datos actual y la crea con los datos iniciales."""
    for sufijo in ("", "-journal", "-wal", "-shm"):
        ruta = db.DB_PATH + sufijo
        if os.path.exists(ruta):
            os.remove(ruta)

    db.inicializar_base_datos()


def cargar_datos_demo(servicio=None):
    """
    Carga datos de demostración usando la capa de servicios.

    Devuelve un resumen con los IDs creados.
    """
    from src.services.app_service import AppService

    propio = servicio is None
    servicio = servicio or AppService()
    resumen = {"estudiantes": [], "reservaciones": [], "serie": None}

    try:
        for carne, nombre, correo in ESTUDIANTES_DEMO:
            servicio.crear_estudiante(carne, nombre, correo)
            resumen["estudiantes"].append(carne)

        d1 = (date.today() + timedelta(days=1)).isoformat()
        d2 = (date.today() + timedelta(days=2)).isoformat()
        d3 = (date.today() + timedelta(days=3)).isoformat()

        reservas = [
            ("A001234567", "S01", d1, "09:00", "2", "3"),
            ("E001122334", "S01", d1, "11:00", "1", "2"),   # consecutiva (RN-10)
            ("B009876543", "S02", d1, "11:00", "1", "5"),
            ("E001122334", "S03", d1, "14:00", "2", "8"),
            ("F005566778", "S05", d2, "10:00", "1", "1"),
            ("A001234567", "S02", d2, "08:00", "1", "4"),   # se cancelará
        ]

        # Si todavía queda horario hoy, se agrega una reserva para hoy.
        siguiente_hora = datetime.now().hour + 1
        if 8 <= siguiente_hora <= 19:
            reservas.append(
                ("F005566778", "S02", date.today().isoformat(), f"{siguiente_hora:02d}:00", "1", "3")
            )
        elif siguiente_hora < 8:
            reservas.append(("F005566778", "S02", date.today().isoformat(), "08:00", "1", "3"))

        for datos in reservas:
            resultado = servicio.crear(*datos)
            resumen["reservaciones"].append(resultado["id"])

        # Una cancelación (RN-12) y una modificación (RF-13) para el historial.
        servicio.cancelar(resumen["reservaciones"][5])
        servicio.modificar(resumen["reservaciones"][2], "S02", d1, "11:00", "1", "4")

        # Serie recurrente semanal de 4 ocurrencias (RF-14).
        serie = servicio.crear_serie_recurrente("B009876543", "S03", d3, "16:00", "2", "6", "4")
        resumen["serie"] = serie

    finally:
        if propio:
            servicio.cerrar()

    return resumen


def main():
    parser = argparse.ArgumentParser(
        description="Restaura los datos iniciales o carga datos de demostración."
    )
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--restaurar", action="store_true", help="Solo datos iniciales del enunciado.")
    grupo.add_argument("--demo", action="store_true", help="Datos iniciales + datos de demostración.")
    args = parser.parse_args()

    restaurar_datos_iniciales()
    print(f"Base de datos restaurada con los datos iniciales en: {db.DB_PATH}")

    if args.demo:
        resumen = cargar_datos_demo()
        print(
            f"Datos de demostración cargados: {len(resumen['estudiantes'])} estudiantes, "
            f"{len(resumen['reservaciones'])} reservaciones individuales y "
            f"una serie de {resumen['serie']['cantidad']} ocurrencias."
        )


if __name__ == "__main__":
    main()
