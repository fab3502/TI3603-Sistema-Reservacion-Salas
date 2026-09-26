"""Punto de entrada de la aplicación."""

from src.services.app_service import AppService
from src.ui.main_window import MainWindow


def main() -> None:
    service = AppService()

    try:
        app = MainWindow(
            estudiantes_service=service,
            salas_service=service,
            reservaciones_service=service,
        )
        app.mainloop()

    finally:
        service.cerrar()


if __name__ == "__main__":
    main()