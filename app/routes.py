import psycopg2
from flask import Blueprint, jsonify

from app.auth import requiere_jwt
from app.calculo import calcular_edad, calcular_valor_poliza
from app.db import get_connection, obtener_mortalidad, obtener_persona, obtener_producto, reset_connection
from app.fallos import aplicar_inyeccion_fallo

motor_calculo_bp = Blueprint("motor_calculo", __name__)


@motor_calculo_bp.get("/health")
def health():
    return jsonify({"status": "ok"})


def _consultar_datos(identificacion):
    conn = get_connection()
    persona = obtener_persona(conn, identificacion)
    if persona is None:
        return None, None, None

    edad = calcular_edad(persona["fecha_nacimiento"])
    mortalidad = obtener_mortalidad(conn, edad)
    if mortalidad is None:
        return persona, None, None

    producto = obtener_producto(conn)
    return persona, mortalidad, producto


@motor_calculo_bp.get("/motor-calculo/<identificacion>")
@requiere_jwt
def motor_calculo(identificacion):
    try:
        persona, mortalidad, producto = _consultar_datos(identificacion)
    except (psycopg2.OperationalError, psycopg2.InterfaceError):
        reset_connection()
        persona, mortalidad, producto = _consultar_datos(identificacion)

    if persona is None or mortalidad is None:
        return jsonify({"error": "identificacion no encontrada"}), 404

    valor_correcto = calcular_valor_poliza(persona, mortalidad, producto)
    valor_devuelto = aplicar_inyeccion_fallo(valor_correcto)

    return jsonify({
        "identificacion": persona["identificacion"],
        "producto": {
            "codigo": producto["codigo"],
            "nombre": producto["nombre"],
            "moneda": producto["moneda"],
            "anios_proteccion": producto["anios_proteccion"]
        },
        "valor_poliza": float(valor_devuelto)
    }), 200
