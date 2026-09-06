from decimal import Decimal

from app.config import Config
from app.fallos import aplicar_inyeccion_fallo

VALOR_CORRECTO = Decimal("291200.00")


def test_sin_inyeccion_devuelve_valor_correcto(monkeypatch):
    monkeypatch.setattr(Config, "FAULT_INJECTION_ENABLED", False)

    for _ in range(50):
        assert aplicar_inyeccion_fallo(VALOR_CORRECTO) == VALOR_CORRECTO


def test_con_probabilidad_uno_siempre_altera(monkeypatch):
    monkeypatch.setattr(Config, "FAULT_INJECTION_ENABLED", True)
    monkeypatch.setattr(Config, "FAULT_PROBABILITY", "1.0")

    for _ in range(50):
        resultado = aplicar_inyeccion_fallo(VALOR_CORRECTO)
        assert resultado != VALOR_CORRECTO

        desviacion = abs(resultado / VALOR_CORRECTO - 1)
        assert Decimal("0.15") <= desviacion <= Decimal("0.30")


def test_distribucion_probabilidad_por_defecto(monkeypatch):
    monkeypatch.setattr(Config, "FAULT_INJECTION_ENABLED", True)
    monkeypatch.setattr(Config, "FAULT_PROBABILITY", "0.10")

    n = 5000
    alterados = sum(
        1 for _ in range(n)
        if aplicar_inyeccion_fallo(VALOR_CORRECTO) != VALOR_CORRECTO
    )

    proporcion = alterados / n
    assert 0.07 <= proporcion <= 0.13


def test_puede_aumentar_y_disminuir(monkeypatch):
    monkeypatch.setattr(Config, "FAULT_INJECTION_ENABLED", True)
    monkeypatch.setattr(Config, "FAULT_PROBABILITY", "1.0")

    resultados = [aplicar_inyeccion_fallo(VALOR_CORRECTO) for _ in range(200)]

    assert any(r > VALOR_CORRECTO for r in resultados)
    assert any(r < VALOR_CORRECTO for r in resultados)
