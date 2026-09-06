import random
from decimal import Decimal, ROUND_HALF_UP

from app.config import Config


def aplicar_inyeccion_fallo(valor_correcto: Decimal) -> Decimal:
    if not Config.FAULT_INJECTION_ENABLED:
        return valor_correcto

    roll = random.random()

    if roll >= float(Config.FAULT_PROBABILITY):
        return valor_correcto

    desviacion = Decimal(str(random.uniform(0.15, 0.30)))
    direccion = random.choice((-1, 1))
    factor = Decimal("1") + Decimal(direccion) * desviacion

    valor_alterado = valor_correcto * factor

    return valor_alterado.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )
