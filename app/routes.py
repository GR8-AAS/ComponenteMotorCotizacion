from flask import Blueprint, jsonify

from app.auth import requiere_jwt
from app.calculo import calcular_edad, calcular_valor_poliza
from app.db import obtener_mortalidad, obtener_persona, obtener_producto
from app.fallos import aplicar_inyeccion_fallo

motor_calculo_bp = Blueprint("motor_calculo", __name__)


@motor_calculo_bp.get("/health")
def health():
    return jsonify({"status": "ok"})


@motor_calculo_bp.get("/motor-calculo/<identificacion>")
@requiere_jwt
def motor_calculo(identificacion):
    persona = obtener_persona(identificacion)
    if persona is None:
        return jsonify({"error": "identificacion no encontrada"}), 404

    edad = calcular_edad(persona["fecha_nacimiento"])
    mortalidad = obtener_mortalidad(edad)
    if mortalidad is None:
        return jsonify({"error": "identificacion no encontrada"}), 404

    producto = obtener_producto()

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
