from src.validators.validaciones import (validar_carne,validar_nombre,validar_correo,validar_estado_estudiante,
                                         validar_codigo_sala,validar_nombre_sala,validar_capacidad_sala,validar_estado_sala)

from src.validators.reglas_negocio import (validar_carne_disponible,validar_codigo_sala_disponible,
                                           validar_reduccion_capacidad_sala)


# Estudiantes

def validar_nuevo_estudiante(conexion, carne, nombre, correo):
    """
    Valida los datos necesarios para registrar un estudiante nuevo.
    """

    carne = validar_carne(carne)
    nombre = validar_nombre(nombre)
    correo = validar_correo(correo)

    # RF-02: no puede existir un carné duplicado.
    validar_carne_disponible(conexion, carne)

    return {
        "carne": carne,
        "nombre": nombre,
        "correo": correo,
        "estado": "activo",
    }

def validar_modificacion_estudiante(nombre, correo, estado):
    """
    Valida los campos que pueden modificarse de un estudiante.

    El carné no se recibe porque RF-11 establece que no puede modificarse.
    """

    nombre = validar_nombre(nombre)
    correo = validar_correo(correo)
    estado = validar_estado_estudiante(estado)

    return {
        "nombre": nombre,
        "correo": correo,
        "estado": estado,
    }


# Salas

def validar_nueva_sala(conexion, codigo, nombre, capacidad, estado="disponible"):
    """
    Valida los datos necesarios para registrar una sala nueva.
    """

    codigo = validar_codigo_sala(codigo)
    nombre = validar_nombre_sala(nombre)
    capacidad = validar_capacidad_sala(capacidad)
    estado = validar_estado_sala(estado)

    # RF-12: el código debe ser único.
    validar_codigo_sala_disponible(conexion, codigo)

    return {
        "codigo": codigo,
        "nombre": nombre,
        "capacidad": capacidad,
        "estado": estado,
    }

def validar_modificacion_sala(conexion, codigo_sala, nombre, capacidad, estado):
    """
    Valida los campos modificables de una sala.

    El código de la sala se utiliza para consultar sus reservaciones,
    pero no se modifica.
    """

    codigo_sala = validar_codigo_sala(codigo_sala)
    nombre = validar_nombre_sala(nombre)
    capacidad = validar_capacidad_sala(capacidad)
    estado = validar_estado_sala(estado)

    # RF-12: no se puede reducir la capacidad por debajo de la cantidad
    # de personas de una reservación activa futura.
    validar_reduccion_capacidad_sala(conexion,codigo_sala,capacidad)

    return {
        "nombre": nombre,
        "capacidad": capacidad,
        "estado": estado,
    }