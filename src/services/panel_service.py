"""
Servicio del panel de control y del historial de acciones (Parte 5).

Requisitos relacionados:
- RF-15: reservaciones del día, próximas reservaciones, ocupación por sala,
  indicadores y filtros combinables por fecha, sala y estado.
- RF-17: consulta de solo lectura del historial de auditoría.
- RNF-10: toda la lógica puede probarse sin la interfaz gráfica.

Las funciones reciben la conexión y, opcionalmente, el momento actual
(``ahora``) para que las pruebas sean deterministas.
"""

from datetime import datetime, timedelta

from src.database import db
from src.validators.validaciones import ValidacionError


HORA_APERTURA = 8
HORA_CIERRE = 20
HORAS_OPERACION = HORA_CIERRE - HORA_APERTURA

ESTADOS_RESERVACION = ("activa", "cancelada")
ENTIDADES_AUDITORIA = ("estudiante", "sala", "reservacion")
ACCIONES_AUDITORIA = ("creacion", "actualizacion", "cancelacion")

# Valores que la interfaz usa para indicar "sin filtro".
_SIN_FILTRO = ("", "todas", "todos")


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def _texto_opcional(valor):
    """Normaliza un filtro opcional: None, vacío o 'Todas' equivalen a None."""
    if valor is None:
        return None

    if not isinstance(valor, str):
        raise ValidacionError("Los filtros deben ser texto.")

    valor = valor.strip()

    if valor.lower() in _SIN_FILTRO:
        return None

    return valor


def _validar_fecha_filtro(fecha):
    """
    Valida una fecha usada como filtro.

    A diferencia de una reservación, un filtro sí puede consultar fechas
    pasadas, por lo que solo se valida el formato AAAA-MM-DD.
    """
    fecha = _texto_opcional(fecha)

    if fecha is None:
        return None

    try:
        fecha_validada = datetime.strptime(fecha, "%Y-%m-%d").date()
    except ValueError:
        raise ValidacionError(
            "La fecha del filtro debe utilizar el formato AAAA-MM-DD."
        )

    if fecha_validada.strftime("%Y-%m-%d") != fecha:
        raise ValidacionError(
            "La fecha del filtro debe utilizar el formato AAAA-MM-DD."
        )

    return fecha


def _hora_fin(hora_inicio, duracion):
    inicio = datetime.strptime(hora_inicio, "%H:%M")
    return (inicio + timedelta(hours=int(duracion))).strftime("%H:%M")


def _agregar_hora_fin(reservaciones):
    for reservacion in reservaciones:
        reservacion["hora_fin"] = _hora_fin(
            reservacion["hora_inicio"],
            reservacion["duracion"],
        )
    return reservaciones


def validar_filtros_panel(fecha=None, codigo_sala=None, estado=None):
    """
    Normaliza y valida los filtros del panel.

    Devuelve un diccionario con valores normalizados o None cuando
    el filtro no se aplica.
    """
    fecha = _validar_fecha_filtro(fecha)

    codigo_sala = _texto_opcional(codigo_sala)
    if codigo_sala is not None:
        codigo_sala = codigo_sala.upper()

    estado = _texto_opcional(estado)
    if estado is not None:
        estado = estado.lower()
        if estado not in ESTADOS_RESERVACION:
            raise ValidacionError(
                "El estado del filtro debe ser 'activa' o 'cancelada'."
            )

    return {
        "fecha": fecha,
        "codigo_sala": codigo_sala,
        "estado": estado,
    }


# ---------------------------------------------------------------------------
# Panel de control (RF-15)
# ---------------------------------------------------------------------------

def calcular_ocupacion(conexion, fecha, codigo_sala=None):
    """
    Calcula la ocupación de cada sala en una fecha.

    La ocupación es el porcentaje de horas reservadas (solo reservaciones
    activas) sobre las 12 horas del horario de uso (08:00 a 20:00).
    Las salas fuera de servicio se incluyen con su estado visible.
    """
    salas = db.listar_salas(conexion)

    if codigo_sala:
        salas = [sala for sala in salas if sala["codigo"] == codigo_sala]

    ocupacion = []

    for sala in salas:
        activas = db.listar_reservaciones_por_sala_fecha(
            conexion,
            sala["codigo"],
            fecha,
        )

        horas = sum(int(reserva["duracion"]) for reserva in activas)
        porcentaje = round(horas * 100 / HORAS_OPERACION)

        ocupacion.append({
            "codigo": sala["codigo"],
            "nombre": sala["nombre"],
            "capacidad": sala["capacidad"],
            "estado": sala["estado"],
            "reservas": len(activas),
            "horas_reservadas": horas,
            "porcentaje": min(porcentaje, 100),
        })

    return ocupacion


def obtener_panel(
    conexion,
    fecha=None,
    codigo_sala=None,
    estado=None,
    ahora=None,
    limite_proximas=10,
):
    """
    RF-15: construye toda la información del panel de control.

    - Si no se indica fecha, se usan las reservaciones del día actual.
    - Los filtros de fecha, sala y estado se combinan (AND).
    - ``hay_resultados`` permite a la interfaz mostrar un estado vacío.

    Es una operación de solo lectura: no modifica la base de datos.
    """
    filtros = validar_filtros_panel(fecha, codigo_sala, estado)

    ahora = ahora or datetime.now()
    hoy = ahora.strftime("%Y-%m-%d")
    hora_actual = ahora.strftime("%H:%M")

    fecha_consulta = filtros["fecha"] or hoy

    reservaciones = _agregar_hora_fin(
        db.listar_reservaciones_filtradas(
            conexion,
            fecha=fecha_consulta,
            codigo_sala=filtros["codigo_sala"],
            estado=filtros["estado"],
        )
    )

    proximas = _agregar_hora_fin(
        db.listar_proximas_reservaciones(
            conexion,
            hoy,
            hora_actual,
            codigo_sala=filtros["codigo_sala"],
            limite=limite_proximas,
        )
    )

    conteos = db.contar_registros_panel(conexion, hoy, hora_actual)

    ocupacion = calcular_ocupacion(
        conexion,
        fecha_consulta,
        filtros["codigo_sala"],
    )

    salas_operativas = [
        sala for sala in ocupacion if sala["estado"] == "disponible"
    ]
    if salas_operativas:
        ocupacion_promedio = round(
            sum(sala["porcentaje"] for sala in salas_operativas)
            / len(salas_operativas)
        )
    else:
        ocupacion_promedio = 0

    indicadores = {
        "reservas_hoy": conteos["activas_hoy"],
        "proximas": conteos["proximas"],
        "activas_total": conteos["activas_total"],
        "canceladas_total": conteos["canceladas_total"],
        "salas_disponibles": conteos["salas_disponibles"],
        "salas_total": conteos["salas_total"],
        "estudiantes_activos": conteos["estudiantes_activos"],
        "ocupacion_promedio": ocupacion_promedio,
    }

    return {
        "fecha_consulta": fecha_consulta,
        "filtros": filtros,
        "indicadores": indicadores,
        "reservaciones": reservaciones,
        "proximas": proximas,
        "ocupacion": ocupacion,
        "hay_resultados": bool(reservaciones),
    }


# ---------------------------------------------------------------------------
# Historial de acciones (RF-17)
# ---------------------------------------------------------------------------

def consultar_historial(conexion, entidad=None, tipo_accion=None, fecha=None):
    """
    RF-17: consulta el historial de auditoría con filtros opcionales.

    Solo lectura: la interfaz no ofrece ninguna forma de editar registros.
    """
    entidad = _texto_opcional(entidad)
    if entidad is not None:
        entidad = entidad.lower()
        if entidad not in ENTIDADES_AUDITORIA:
            raise ValidacionError(
                "La entidad debe ser estudiante, sala o reservacion."
            )

    tipo_accion = _texto_opcional(tipo_accion)
    if tipo_accion is not None:
        tipo_accion = tipo_accion.lower()
        if tipo_accion not in ACCIONES_AUDITORIA:
            raise ValidacionError(
                "La acción debe ser creacion, actualizacion o cancelacion."
            )

    fecha = _validar_fecha_filtro(fecha)

    return db.listar_auditoria(
        conexion,
        entidad=entidad,
        tipo_accion=tipo_accion,
        fecha=fecha,
    )
