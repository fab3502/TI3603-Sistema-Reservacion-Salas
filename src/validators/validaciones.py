from datetime import datetime, date


class ValidacionError(Exception):
    """Error producido cuando un dato no cumple las reglas del sistema."""
    pass

MENSAJE_DURACION_ENTERA = "La duración debe ser un número entero."
MENSAJE_CANTIDAD_PERSONAS_ENTERA = "La cantidad de personas debe ser un número entero."
MENSAJE_CANTIDAD_OCURRENCIAS_ENTERA = "La cantidad de ocurrencias debe ser un número entero."
MENSAJE_CAPACIDAD_ENTERA = "La capacidad debe ser un número entero."

def limpiar_texto(valor):
    """Elimina espacios al inicio y al final."""
    if not isinstance(valor, str):
        raise ValidacionError("El valor debe ser texto.")
    return valor.strip()


# Estudiantes

def validar_carne(carne):
    carne = limpiar_texto(carne)

    if len(carne) != 10:
        raise ValidacionError("El carné debe contener exactamente 10 caracteres.")

    if not carne.isalnum():
        raise ValidacionError("El carné debe contener únicamente letras y números.")

    return carne.upper()

def validar_nombre(nombre):
    nombre = limpiar_texto(nombre)

    if sum(1 for caracter in nombre if not caracter.isspace()) < 3:
        raise ValidacionError("El nombre debe contener al menos tres caracteres distintos de espacios.")

    return nombre

def validar_correo(correo):
    correo = limpiar_texto(correo)

    if correo.count("@") != 1:
        raise ValidacionError(
            "El correo debe contener exactamente un símbolo @."
        )

    usuario, dominio = correo.split("@")

    if not usuario or "." not in dominio:
        raise ValidacionError(
            "El correo debe contener texto antes del @ y al menos un punto después."
        )

    return correo


# Reservaciones

def validar_fecha(fecha_texto):
    fecha_texto = limpiar_texto(fecha_texto)

    try:
        fecha_reserva = datetime.strptime(fecha_texto, "%Y-%m-%d").date()
    except ValueError:
        raise ValidacionError("La fecha debe utilizar el formato AAAA-MM-DD.")

    if fecha_reserva.strftime("%Y-%m-%d") != fecha_texto:
        raise ValidacionError("La fecha debe utilizar el formato AAAA-MM-DD.")

    if fecha_reserva < date.today():
        raise ValidacionError(
            "La fecha de la reservación no puede estar en el pasado."
        )

    return fecha_reserva

def validar_hora(hora_texto):
    hora_texto = limpiar_texto(hora_texto)

    try:
        hora = datetime.strptime(hora_texto, "%H:%M").time()
    except ValueError:
        raise ValidacionError("La hora debe utilizar el formato HH:MM.")

    if hora.strftime("%H:%M") != hora_texto:
        raise ValidacionError("La hora debe utilizar el formato HH:MM.")

    if hora.minute != 0:
        raise ValidacionError(
            "La reservación debe iniciar exactamente en una hora completa."
        )

    return hora

def validar_duracion(duracion):
    if isinstance(duracion, bool):
        raise ValidacionError(MENSAJE_DURACION_ENTERA)

    if isinstance(duracion, float) and not duracion.is_integer():
        raise ValidacionError(MENSAJE_DURACION_ENTERA)

    try:
        duracion = int(duracion)
    except (TypeError, ValueError):
        raise ValidacionError(MENSAJE_DURACION_ENTERA)

    if duracion not in (1, 2):
        raise ValidacionError("La duración permitida es de 1 o 2 horas.")

    return duracion

def validar_cantidad_personas(cantidad, capacidad):
    if isinstance(cantidad, bool):
        raise ValidacionError(MENSAJE_CANTIDAD_PERSONAS_ENTERA)

    if isinstance(cantidad, float) and not cantidad.is_integer():
        raise ValidacionError(MENSAJE_CANTIDAD_PERSONAS_ENTERA)

    try:
        cantidad = int(cantidad)
    except (TypeError, ValueError):
        raise ValidacionError(MENSAJE_CANTIDAD_PERSONAS_ENTERA)

    if cantidad <= 0:
        raise ValidacionError("La cantidad de personas debe ser mayor que cero.")

    if cantidad > capacidad:
        raise ValidacionError(
            "La cantidad de personas no puede superar la capacidad de la sala."
        )

    return cantidad

def validar_reserva_hoy(fecha_reserva, hora_inicio):
    """RN-03: si la reserva es para hoy, debe iniciar después de la hora actual."""
    hoy = date.today()

    if fecha_reserva == hoy:
        ahora = datetime.now().time()

        if hora_inicio <= ahora:
            raise ValidacionError(
                "Una reservación para hoy debe iniciar después de la hora actual."
            )

    return True

def validar_horario(hora_inicio, duracion):
    """RN-05: horario permitido entre 08:00 y 20:00."""
    hora_apertura = 8
    hora_cierre = 20

    inicio = hora_inicio.hour
    fin = inicio + duracion

    if inicio < hora_apertura:
        raise ValidacionError(
            "La reservación no puede iniciar antes de las 08:00."
        )

    if inicio >= hora_cierre:
        raise ValidacionError(
            "La reservación debe iniciar antes de las 20:00."
        )

    if fin > hora_cierre:
        raise ValidacionError(
            "La reservación no puede terminar después de las 20:00."
        )

    return True

def validar_cantidad_ocurrencias(cantidad):
    """RF-14: una serie recurrente debe tener entre 2 y 8 ocurrencias."""

    if isinstance(cantidad, bool):
        raise ValidacionError(MENSAJE_CANTIDAD_OCURRENCIAS_ENTERA)

    if isinstance(cantidad, float) and not cantidad.is_integer():
        raise ValidacionError(MENSAJE_CANTIDAD_OCURRENCIAS_ENTERA)

    try:
        cantidad = int(cantidad)
    except (TypeError, ValueError):
        raise ValidacionError(MENSAJE_CANTIDAD_OCURRENCIAS_ENTERA)

    if cantidad < 2 or cantidad > 8:
        raise ValidacionError("La serie debe contener entre 2 y 8 ocurrencias.")

    return cantidad



# Salas

def validar_codigo_sala(codigo):
    """Valida que el código de una sala no esté vacío."""

    codigo = limpiar_texto(codigo)

    if not codigo:
        raise ValidacionError("El código de la sala es obligatorio.")

    return codigo.upper()

def validar_nombre_sala(nombre):
    """Valida que el nombre de la sala no esté vacío."""

    nombre = limpiar_texto(nombre)

    if not nombre:
        raise ValidacionError("El nombre de la sala es obligatorio.")

    return nombre

def validar_capacidad_sala(capacidad):
    """RF-12: la capacidad debe ser un entero mayor que cero."""

    if isinstance(capacidad, bool):
        raise ValidacionError(MENSAJE_CAPACIDAD_ENTERA)

    if isinstance(capacidad, float) and not capacidad.is_integer():
        raise ValidacionError(MENSAJE_CAPACIDAD_ENTERA)

    try:
        capacidad = int(capacidad)
    except (TypeError, ValueError):
        raise ValidacionError(MENSAJE_CAPACIDAD_ENTERA)

    if capacidad <= 0:
        raise ValidacionError("La capacidad de la sala debe ser mayor que cero.")

    return capacidad

def validar_estado_sala(estado):
    """Valida los estados permitidos para una sala."""

    estado = limpiar_texto(estado).lower()

    estados_validos = ("disponible", "fuera_de_servicio")

    if estado not in estados_validos:
        raise ValidacionError("El estado de la sala debe ser 'disponible' o 'fuera_de_servicio'.")

    return estado

def validar_estado_estudiante(estado):
    """Valida los estados permitidos para un estudiante."""

    estado = limpiar_texto(estado).lower()

    if estado not in ("activo", "inactivo"):
        raise ValidacionError("El estado del estudiante debe ser 'activo' o 'inactivo'.")

    return estado