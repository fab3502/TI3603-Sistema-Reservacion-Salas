"""Punto de entrada de la aplicación.

Durante el desarrollo de la Parte 3 se utiliza un servicio temporal en memoria para
poder ejecutar la GUI. En la integración final, DemoAppService debe sustituirse
por los servicios reales que conecten con SQLite y las reglas de negocio.
"""

from src.ui.demo_services import DemoAppService
from src.ui.main_window import MainWindow


def main() -> None:
    service = DemoAppService()
    app = MainWindow(
        estudiantes_service=service,
        salas_service=service
    )
    app.mainloop()


if __name__ == "__main__":
    main()