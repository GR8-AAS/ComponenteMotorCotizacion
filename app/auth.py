from functools import wraps

import jwt
from flask import jsonify, request

from app.config import Config


def requiere_jwt(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "token no provisto"}), 401

        token = auth_header[len("Bearer "):]

        try:
            jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "token expirado"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "token inválido"}), 401

        return view_func(*args, **kwargs)

    return wrapper
