from datetime import datetime, timedelta
from src.database.db import (obtener_estudiante,listar_salas,listar_reservaciones_por_sala_fecha, 
                             listar_reservaciones_por_estudiante, listar_reservaciones_activas_por_sala)
from src.validators.validaciones import ValidacionError

# Política provisional para RN-11 + RF-14.
# False: una serie recurrente cuenta como una sola reserva.
# True: cada ocurrencia de la serie cuenta como una reserva individual.
CONTAR_OCURRENCIAS_SERIE_INDIVIDUALMENTE = False

def validar_estudiante_activo(conexion, carne):
    """RN-01: solamente un estudiante registrado y activo puede reservar."""

    estudiante = obtener_estudiante(conexion, carne)

    if estudiante is None:
        raise ValidacionError("El estudiante no se encuentra registrado.")

    if estudiante["estado"] != "activo":
        raise ValidacionError("El estudiante se encuentra inactivo.")

    return estudiante

def obtener_sala(conexion, codigo_sala):
    """Busca una sala por su código."""

    salas = listar_salas(conexion)

    for sala in salas:
        if sala["codigo"] == codigo_sala:
            return sala

    return None

def validar_sala_disponible(conexion, codigo_sala):
    """RN-08: una sala fuera de servicio no puede reservarse."""

    sala = obtener_sala(conexion, codigo_sala)

    if sala is None:
        raise ValidacionError("La sala no existe.")

    if sala["estado"] != "disponible":
        raise ValidacionError("La sala se encuentra fuera de servicio.")

    return sala

def _hora_a_minutos(hora_texto):
    """Convierte una hora HH:MM a minutos desde medianoche."""
    horas, minutos = map(int, hora_texto.split(":"))
    return horas * 60 + minutos

def validar_superposicion(conexion, codigo_sala, fecha, hora_inicio, duracion, id_excluir=None,):
    """
    RN-09 y RN-10:
    Verifica que una nueva reservación no se superponga con otra activa.

    id_excluir permite ignorar una reservación específica cuando
    posteriormente se utilice esta validación para modificar reservas.
    """

    reservaciones = listar_reservaciones_por_sala_fecha(conexion,codigo_sala,fecha,)

    inicio_nuevo = _hora_a_minutos(hora_inicio)
    fin_nuevo = inicio_nuevo + (duracion * 60)

    for reserva in reservaciones:

        if id_excluir is not None and reserva["id"] == id_excluir:
            continue

        inicio_existente = _hora_a_minutos(reserva["hora_inicio"])
        fin_existente = inicio_existente + (reserva["duracion"] * 60)

        hay_conflicto = (inicio_nuevo < fin_existente and fin_nuevo > inicio_existente)

        if hay_conflicto:
            raise ValidacionError(
                "La sala ya tiene una reservación activa "
                "que se superpone con el horario solicitado."
            )

    return True

def validar_limite_reservas(conexion,carne,cantidad_nueva=1,id_excluir=None):
    """
    RN-11:
    Cada estudiante puede tener como máximo tres reservaciones
    activas presentes o futuras.

    Las series recurrentes se contabilizan según la política definida
    en CONTAR_OCURRENCIAS_SERIE_INDIVIDUALMENTE.
    """

    reservaciones = listar_reservaciones_por_estudiante(conexion, carne)

    ahora = datetime.now()

    reservas_individuales = 0
    series_activas = set()

    for reserva in reservaciones:

        if id_excluir is not None and reserva["id"] == id_excluir:
            continue

        if reserva["estado"] != "activa":
            continue

        inicio = datetime.strptime(
            f'{reserva["fecha"]} {reserva["hora_inicio"]}',
            "%Y-%m-%d %H:%M",
        )

        fin = inicio + timedelta(hours=reserva["duracion"])

        # Las reservas que ya terminaron no cuentan para RN-11.
        if fin <= ahora:
            continue

        if (
            not CONTAR_OCURRENCIAS_SERIE_INDIVIDUALMENTE
            and reserva["serie_id"] is not None
        ):
            # Todas las ocurrencias de una misma serie cuentan como una.
            series_activas.add(reserva["serie_id"])
        else:
            # Reserva normal o política de contar cada ocurrencia.
            reservas_individuales += 1

    cantidad_actual = reservas_individuales + len(series_activas)

    if cantidad_actual + cantidad_nueva > 3:
        raise ValidacionError(
            "El estudiante superaría el máximo de tres reservaciones activas."
        )

    return True

def validar_carne_disponible(conexion, carne):
    """
    RF-02:
    Verifica que no exista otro estudiante con el mismo carné.
    La BD ya realiza la comparación sin distinguir mayúsculas y minúsculas.
    """

    estudiante = obtener_estudiante(conexion, carne)

    if estudiante is not None:
        raise ValidacionError("Ya existe un estudiante registrado con ese carné.")

    return True

def validar_codigo_sala_disponible(conexion, codigo_sala):
    """
    RF-12:
    Verifica que el código de una nueva sala no esté registrado.
    """

    sala = obtener_sala(conexion, codigo_sala)

    if sala is not None:
        raise ValidacionError("Ya existe una sala registrada con ese código.")

    return True

def validar_reduccion_capacidad_sala(conexion, codigo_sala, nueva_capacidad):
    """
    RF-12:
    Impide reducir la capacidad de una sala por debajo de la cantidad
    de personas de alguna reservación activa futura.
    """

    reservaciones = listar_reservaciones_activas_por_sala(
        conexion,
        codigo_sala,
    )

    ahora = datetime.now()

    for reserva in reservaciones:
        inicio = datetime.strptime(
            f'{reserva["fecha"]} {reserva["hora_inicio"]}',
            "%Y-%m-%d %H:%M",
        )

        if (
            inicio >= ahora
            and reserva["cantidad_personas"] > nueva_capacidad
        ):
            raise ValidacionError(
                "No se puede reducir la capacidad de la sala porque "
                "existe una reservación activa futura con una cantidad "
                "de personas superior a la nueva capacidad."
            )

    return True



# NOTA PARA PERSONA 4:
# Al implementar RF-13 (modificar reservación), pasar el ID actual en
# id_excluir para que la reserva no se cuente contra sí misma en RN-11.
# Si la reservación pertenece a una serie, conservar el manejo de serie_id
# según la política definida arriba.