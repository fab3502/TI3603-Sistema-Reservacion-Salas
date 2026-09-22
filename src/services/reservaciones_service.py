from datetime import timedelta
import uuid

from src.database.db import (crear_serie_reservaciones, obtener_reservacion, cancelar_reservacion, 
                             cancelar_reservaciones_futuras_serie)

from src.validators.validaciones import (validar_carne,validar_fecha,validar_hora,validar_duracion,
                                         validar_cantidad_personas,validar_reserva_hoy,validar_horario,
                                         ValidacionError, validar_cantidad_ocurrencias, validar_codigo_sala)

from src.validators.reglas_negocio import (validar_estudiante_activo,validar_sala_disponible,
                                           validar_superposicion,validar_limite_reservas,
                                           CONTAR_OCURRENCIAS_SERIE_INDIVIDUALMENTE)


def validar_nueva_reservacion(conexion,carne,codigo_sala,fecha,hora_inicio,duracion,cantidad_personas):
    """
    Ejecuta las reglas necesarias antes de crear una reservación.

    Si alguna validación falla, se lanza ValidacionError.
    Si todo es correcto, devuelve los datos normalizados.
    """

    # Validaciones básicas
    carne = validar_carne(carne)
    codigo_sala = validar_codigo_sala(codigo_sala)
    fecha_validada = validar_fecha(fecha)
    hora_validada = validar_hora(hora_inicio)
    duracion = validar_duracion(duracion)

    # RN-01
    validar_estudiante_activo(conexion, carne)

    # RN-08
    sala = validar_sala_disponible(conexion, codigo_sala)

    # RN-07
    cantidad_personas = validar_cantidad_personas(
        cantidad_personas,
        sala["capacidad"],
    )

    # RN-03
    validar_reserva_hoy(fecha_validada, hora_validada)

    # RN-05
    validar_horario(hora_validada, duracion)

    # Convertimos nuevamente al formato utilizado por SQLite.
    fecha_texto = fecha_validada.strftime("%Y-%m-%d")
    hora_texto = hora_validada.strftime("%H:%M")

    # RN-09 y RN-10
    validar_superposicion(conexion,codigo_sala,fecha_texto,hora_texto,duracion)

    # RN-11
    validar_limite_reservas(conexion, carne)

    return {
        "carne": carne,
        "codigo_sala": codigo_sala,
        "fecha": fecha_texto,
        "hora_inicio": hora_texto,
        "duracion": duracion,
        "cantidad_personas": cantidad_personas,
    }

def consultar_disponibilidad(conexion,codigo_sala,fecha,hora_inicio,duracion):
    """
    RF-08:
    Consulta si una sala está disponible sin crear ni modificar
    ninguna reservación.
    """

    # Validar codigo sala, fecha, hora y duración
    codigo_sala = validar_codigo_sala(codigo_sala)
    fecha_validada = validar_fecha(fecha)
    hora_validada = validar_hora(hora_inicio)
    duracion = validar_duracion(duracion)

    # RN-08: la sala debe existir y estar disponible
    validar_sala_disponible(conexion, codigo_sala)

    # RN-03: si es hoy, la hora debe ser posterior a la actual
    validar_reserva_hoy(fecha_validada, hora_validada)

    # RN-05: debe respetar el horario 08:00 - 20:00
    validar_horario(hora_validada, duracion)

    fecha_texto = fecha_validada.strftime("%Y-%m-%d")
    hora_texto = hora_validada.strftime("%H:%M")

    try:
        # RN-09 y RN-10
        validar_superposicion(conexion,codigo_sala,fecha_texto,hora_texto,duracion)

    except ValidacionError:
        return {
            "disponible": False,
            "mensaje": "La sala no está disponible en el horario solicitado.",
        }

    return {
        "disponible": True,
        "mensaje": "La sala está disponible en el horario solicitado.",
    }

def validar_recurrencia(conexion,carne,codigo_sala,fecha_inicial,hora_inicio,duracion,cantidad_personas,cantidad_ocurrencias):
    """
    RF-14:
    Genera y valida una serie semanal de reservaciones.

    No guarda información. Devuelve un resumen indicando
    cuáles ocurrencias están disponibles y cuáles presentan conflicto.
    """

    carne = validar_carne(carne)
    codigo_sala = validar_codigo_sala(codigo_sala)
    fecha_base = validar_fecha(fecha_inicial)
    hora_validada = validar_hora(hora_inicio)
    duracion = validar_duracion(duracion)
    cantidad_ocurrencias = validar_cantidad_ocurrencias(cantidad_ocurrencias)

    # RN-01
    validar_estudiante_activo(conexion, carne)

    # RN-08
    sala = validar_sala_disponible(conexion, codigo_sala)

    # RN-07
    cantidad_personas = validar_cantidad_personas(cantidad_personas,sala["capacidad"])

    # RN-05
    validar_horario(hora_validada, duracion)

    # RN-11
    if CONTAR_OCURRENCIAS_SERIE_INDIVIDUALMENTE:
        cantidad_para_limite = cantidad_ocurrencias
    else:
        cantidad_para_limite = 1

    validar_limite_reservas(conexion,carne,cantidad_nueva=cantidad_para_limite,)

    hora_texto = hora_validada.strftime("%H:%M")

    resumen = []

    for numero in range(cantidad_ocurrencias):

        fecha_ocurrencia = fecha_base + timedelta(weeks=numero)

        try:
            # RN-03: si una ocurrencia es para hoy, debe iniciar después de la hora actual
            validar_reserva_hoy(fecha_ocurrencia,hora_validada,)

            # RN-09 y RN-10
            validar_superposicion(conexion,codigo_sala,fecha_ocurrencia.strftime("%Y-%m-%d"),hora_texto,duracion)

            resumen.append({
                "ocurrencia": numero + 1,
                "fecha": fecha_ocurrencia.strftime("%Y-%m-%d"),
                "disponible": True,
                "mensaje": "Disponible",
            })

        except ValidacionError as error:
            resumen.append({
                "ocurrencia": numero + 1,
                "fecha": fecha_ocurrencia.strftime("%Y-%m-%d"),
                "disponible": False,
                "mensaje": str(error),
            })

    return {
        "carne": carne,
        "codigo_sala": codigo_sala,
        "hora_inicio": hora_texto,
        "duracion": duracion,
        "cantidad_personas": cantidad_personas,
        "cantidad_ocurrencias": cantidad_ocurrencias,
        "tiene_conflictos": any(
            not ocurrencia["disponible"]
            for ocurrencia in resumen
        ),
        "ocurrencias": resumen,
    }

def crear_serie_recurrente(conexion,carne,codigo_sala,fecha_inicial,hora_inicio,duracion,cantidad_personas,cantidad_ocurrencias):
    """
    RF-14:
    Crea una serie semanal únicamente si todas las ocurrencias
    fueron validadas previamente y no presentan conflictos.
    """

    resultado = validar_recurrencia(conexion,carne,codigo_sala,fecha_inicial,hora_inicio,
                                    duracion,cantidad_personas,cantidad_ocurrencias,)

    if resultado["tiene_conflictos"]:
        raise ValidacionError(
            "La serie contiene conflictos y no puede guardarse."
        )

    serie_id = f"SER-{uuid.uuid4().hex[:8].upper()}"

    reservaciones = []

    for ocurrencia in resultado["ocurrencias"]:
        reservaciones.append({
            "carne": resultado["carne"],
            "codigo_sala": resultado["codigo_sala"],
            "fecha": ocurrencia["fecha"],
            "hora_inicio": resultado["hora_inicio"],
            "duracion": resultado["duracion"],
            "cantidad_personas": resultado["cantidad_personas"],
        })

    ids_creados = crear_serie_reservaciones(conexion,reservaciones,serie_id,)

    return {
        "serie_id": serie_id,
        "reservaciones": ids_creados,
        "cantidad": len(ids_creados),
    }

def cancelar_ocurrencia(conexion, id_reservacion):
    """
    RF-14:
    Cancela únicamente una ocurrencia de una serie.
    También puede utilizarse con una reservación individual.
    """

    reserva = obtener_reservacion(conexion, id_reservacion)

    if reserva is None:
        raise ValidacionError("La reservación no existe.")

    if reserva["estado"] == "cancelada":
        raise ValidacionError("La reservación ya se encuentra cancelada.")

    cancelar_reservacion(conexion, id_reservacion)

    return {
        "id": id_reservacion,
        "mensaje": "La reservación fue cancelada correctamente.",
    }

def cancelar_serie_desde_ocurrencia(conexion, id_reservacion):
    """
    RF-14:
    Cancela la ocurrencia seleccionada y todas las ocurrencias
    futuras pertenecientes a la misma serie.
    """

    reserva = obtener_reservacion(conexion, id_reservacion)

    if reserva is None:
        raise ValidacionError("La reservación no existe.")

    if reserva["estado"] == "cancelada":
        raise ValidacionError("La reservación ya se encuentra cancelada.")

    if reserva["serie_id"] is None:
        raise ValidacionError(
            "La reservación seleccionada no pertenece a una serie recurrente."
        )

    ids_cancelados = cancelar_reservaciones_futuras_serie(conexion,reserva["serie_id"],reserva["fecha"],
                                                          reserva["hora_inicio"])

    return {
        "serie_id": reserva["serie_id"],
        "reservaciones_canceladas": ids_cancelados,
        "cantidad": len(ids_cancelados),
    }



