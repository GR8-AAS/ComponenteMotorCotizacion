from datetime import date
from decimal import Decimal, ROUND_HALF_UP


def calcular_edad(fecha_nacimiento: date) -> int:
    hoy = date.today()
    return (
        hoy.year
        - fecha_nacimiento.year
        - ((hoy.month, hoy.day) <
           (fecha_nacimiento.month, fecha_nacimiento.day))
    )


def calcular_valor_poliza(persona: dict, mortalidad: dict, producto: dict) -> Decimal:
    cobertura_base = (
        persona["deuda_total"]
        + persona["gastos_mensuales"]
        * Decimal("12")
        * Decimal(producto["anios_proteccion"])
        - persona["activos_liquidos"]
    )

    cobertura_recomendada = max(
        cobertura_base,
        producto["cobertura_minima"]
    )

    prima_pura = (
        cobertura_recomendada
        * mortalidad["probabilidad_mortalidad_anual"]
    )

    valor_poliza = (
        prima_pura
        * producto["factor_gastos_margen"]
    )

    return valor_poliza.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )
