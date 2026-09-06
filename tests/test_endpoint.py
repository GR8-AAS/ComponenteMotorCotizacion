from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import jwt
import pytest

from app import create_app
from app.config import Config


@pytest.fixture
def client():
    app = create_app()
    app.testing = True
    return app.test_client()


def token_valido(**claims_extra):
    return jwt.encode({"servicio": "voter-test", **claims_extra}, Config.JWT_SECRET_KEY, algorithm="HS256")


def auth_headers(token=None):
    return {"Authorization": f"Bearer {token or token_valido()}"}


PERSONA = {
    "identificacion": "990000000023",
    "fecha_nacimiento": date(1986, 9, 5),
    "gastos_mensuales": Decimal("1500000"),
    "deuda_total": Decimal("220000000"),
    "activos_liquidos": Decimal("176000000"),
}

MORTALIDAD = {"edad": 40, "probabilidad_mortalidad_anual": Decimal("0.001")}

PRODUCTO = {
    "codigo": "VIDA_EXPERIMENTO",
    "nombre": "Seguro de vida experimental",
    "moneda": "COP",
    "anios_proteccion": 10,
    "cobertura_minima": Decimal("50000000"),
    "factor_gastos_margen": Decimal("1.30"),
}


def test_motor_calculo_devuelve_valor_correcto(client, monkeypatch):
    monkeypatch.setattr(Config, "FAULT_INJECTION_ENABLED", False)
    monkeypatch.setattr("app.routes.obtener_persona", lambda ident: PERSONA)
    monkeypatch.setattr("app.routes.calcular_edad", lambda fecha: 40)
    monkeypatch.setattr("app.routes.obtener_mortalidad", lambda edad: MORTALIDAD)
    monkeypatch.setattr("app.routes.obtener_producto", lambda: PRODUCTO)

    resp = client.get("/motor-calculo/990000000023", headers=auth_headers())

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["identificacion"] == "990000000023"
    assert body["producto"]["codigo"] == "VIDA_EXPERIMENTO"
    assert body["producto"]["anios_proteccion"] == 10
    assert body["valor_poliza"] == 291200.00


def test_motor_calculo_404_si_no_existe(client, monkeypatch):
    monkeypatch.setattr("app.routes.obtener_persona", lambda ident: None)

    resp = client.get("/motor-calculo/000000000000", headers=auth_headers())

    assert resp.status_code == 404


def test_motor_calculo_404_si_no_hay_mortalidad_para_la_edad(client, monkeypatch):
    monkeypatch.setattr("app.routes.obtener_persona", lambda ident: PERSONA)
    monkeypatch.setattr("app.routes.calcular_edad", lambda fecha: 17)
    monkeypatch.setattr("app.routes.obtener_mortalidad", lambda edad: None)

    resp = client.get("/motor-calculo/990000000001", headers=auth_headers())

    assert resp.status_code == 404


def test_motor_calculo_401_sin_token(client):
    resp = client.get("/motor-calculo/990000000023")

    assert resp.status_code == 401


def test_motor_calculo_401_token_con_firma_invalida(client):
    token = jwt.encode({"servicio": "impostor"}, "llave-incorrecta", algorithm="HS256")

    resp = client.get("/motor-calculo/990000000023", headers=auth_headers(token))

    assert resp.status_code == 401


def test_motor_calculo_401_token_expirado(client):
    exp = datetime.now(timezone.utc) - timedelta(minutes=1)
    token = token_valido(exp=exp)

    resp = client.get("/motor-calculo/990000000023", headers=auth_headers(token))

    assert resp.status_code == 401


def test_motor_calculo_200_token_sin_expiracion(client, monkeypatch):
    monkeypatch.setattr("app.routes.obtener_persona", lambda ident: PERSONA)
    monkeypatch.setattr("app.routes.calcular_edad", lambda fecha: 40)
    monkeypatch.setattr("app.routes.obtener_mortalidad", lambda edad: MORTALIDAD)
    monkeypatch.setattr("app.routes.obtener_producto", lambda: PRODUCTO)

    resp = client.get("/motor-calculo/990000000023", headers=auth_headers())

    assert resp.status_code == 200


def test_health_no_requiere_token(client):
    resp = client.get("/health")

    assert resp.status_code == 200


def test_motor_calculo_con_fallo_mantiene_formato_y_200(client, monkeypatch):
    monkeypatch.setattr(Config, "FAULT_INJECTION_ENABLED", True)
    monkeypatch.setattr(Config, "FAULT_PROBABILITY", "1.0")
    monkeypatch.setattr("app.routes.obtener_persona", lambda ident: PERSONA)
    monkeypatch.setattr("app.routes.calcular_edad", lambda fecha: 40)
    monkeypatch.setattr("app.routes.obtener_mortalidad", lambda edad: MORTALIDAD)
    monkeypatch.setattr("app.routes.obtener_producto", lambda: PRODUCTO)

    resp = client.get("/motor-calculo/990000000023", headers=auth_headers())

    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == {"identificacion", "producto", "valor_poliza"}
    assert body["identificacion"] == "990000000023"
    assert body["valor_poliza"] != 291200.00
