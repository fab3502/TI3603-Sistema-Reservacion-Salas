# TI3603-Sistema-Reservacion-Salas

Proyecto del curso TI3603 Calidad en Sistemas de Información.

## Descripción

Aplicación de escritorio en Python (Tkinter + SQLite) para administrar estudiantes, salas y reservaciones de espacios de estudio universitarios.

## Integrantes

- Mirka Araya
- Brandon Badilla
- Fabián Granados
- Sharon Sánchez
- Angélica Granados

## Requisitos

- Python 3.10 o superior, con Tkinter (incluido en el instalador oficial de Windows y macOS; en Linux: `sudo apt install python3-tk`).
- La aplicación no usa paquetes externos. `pytest` y `pytest-cov` solo se necesitan para las pruebas.

## Estructura de carpetas

```
src/
  main.py              Punto de entrada
  database/db.py       Esquema, datos iniciales y operaciones SQLite
  database/datos_prueba.py  Restauración de datos iniciales y datos de demostración
  validators/          Validaciones de campos y reglas de negocio RN-01 a RN-13
  services/            Lógica de estudiantes, salas, reservaciones, panel e historial
  ui/                  Pantallas Tkinter
tests/
  unit/                Pruebas unitarias (validaciones, reglas, persistencia, panel, historial)
  integration/         Flujos completos, rendimiento (RNF-09) y pantallas (CSV, panel, historial)
data/reservas.db       Base de datos (se crea sola en la primera ejecución)
```

## Instalación

Desde la carpeta raíz del proyecto.

**Windows (PowerShell)**

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Si PowerShell bloquea la activación, ejecute una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Ejecución

```bash
python -m src.main
```

La primera ejecución crea `data/reservas.db` con las 5 salas y los 3 estudiantes iniciales del enunciado.

## Restaurar datos iniciales

```bash
python -m src.database.datos_prueba --restaurar   # solo datos iniciales
python -m src.database.datos_prueba --demo        # datos iniciales + reservaciones de demostración
```

Ambos comandos eliminan la base de datos actual. Los datos de demostración usan fechas relativas al día en que se ejecutan y pasan por las mismas reglas de negocio que la interfaz.

## Pruebas automatizadas

```bash
python -m pytest                          # toda la suite
python -m pytest tests/unit               # solo unitarias
python -m pytest --cov=src --cov-report=term   # con cobertura
```

Cada prueba usa una base de datos temporal; nunca modifica `data/reservas.db`. Las pruebas de pantallas se omiten automáticamente si el equipo no tiene entorno gráfico.

## Opciones del menú

| Opción | Qué permite |
|---|---|
| Resumen (pantalla principal) | Reservas activas de hoy, próximas reservas, salas disponibles y ocupación promedio del día (RF-15). |
| Panel de control | Ocupación por sala, próximas reservaciones, indicadores y reservaciones del día con filtros combinables por fecha, sala y estado (RF-15). |
| Reservaciones | Crear, consultar, buscar por carné, modificar, cancelar, consultar disponibilidad y gestionar series recurrentes (RF-05 a RF-09, RF-13, RF-14). |
| Estudiantes | Registrar, consultar, editar, activar e inactivar (RF-02, RF-03, RF-11). |
| Salas | Registrar, consultar, editar nombre y capacidad, cambiar estado (RF-04, RF-12). |
| Reportes | Reservaciones por rango de fechas y exportación a CSV UTF-8 (RF-16). |
| Historial de acciones | Consulta de solo lectura de creaciones, modificaciones y cancelaciones, con filtros por entidad, acción y fecha (RF-17). |
| Salir | Cierra la aplicación con confirmación (RF-10). |
