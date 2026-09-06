from datetime import date
from decimal import Decimal

from app.calculo import calcular_edad, calcular_valor_poliza


def test_calcular_edad_cumpleanios_ya_paso():
    hoy = date.today()
    fecha_nacimiento = date(hoy.year - 40, hoy.month, max(hoy.day - 1, 1))
    assert calcular_edad(fecha_nacimiento) == 40


def test_calcular_edad_cumpleanios_no_ha_llegado():
    hoy = date.today()
    anio_nacimiento = hoy.year - 40
    mes_nacimiento = 12 if hoy.month == 1 else hoy.month - 1
    assert calcular_edad(date(anio_nacimiento, mes_nacimiento, 1)) == 40


def test_calcular_valor_poliza_ejemplo_documentado():
    persona = {
        "gastos_mensuales": Decimal("1500000"),
        "deuda_total": Decimal("220000000"),
        "activos_liquidos": Decimal("176000000"),
    }
    mortalidad = {
        "probabilidad_mortalidad_anual": Decimal("0.001"),
    }
    producto = {
        "anios_proteccion": 10,
        "cobertura_minima": Decimal("50000000"),
        "factor_gastos_margen": Decimal("1.30"),
    }

    valor = calcular_valor_poliza(persona, mortalidad, producto)

    assert valor == Decimal("291200.00")


def test_calcular_valor_poliza_usa_cobertura_minima():
    persona = {
        "gastos_mensuales": Decimal("0"),
        "deuda_total": Decimal("0"),
        "activos_liquidos": Decimal("0"),
    }
    mortalidad = {
        "probabilidad_mortalidad_anual": Decimal("0.001"),
    }
    producto = {
        "anios_proteccion": 10,
        "cobertura_minima": Decimal("50000000"),
        "factor_gastos_margen": Decimal("1.30"),
    }

    valor = calcular_valor_poliza(persona, mortalidad, producto)

    # cobertura_base seria negativa, debe usarse cobertura_minima
    assert valor == Decimal("65000.00")
