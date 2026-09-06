# Inyección de Fallos en el Motor de Cálculo

## Objetivo

Agregar al **Motor de Cálculo** un modo opcional que permita simular errores silenciosos en el valor de una póliza.

El motor primero debe calcular correctamente la póliza. Después, si la inyección de fallos está habilitada, podrá alterar el valor antes de construir la respuesta HTTP.

La respuesta alterada debe conservar el código HTTP 200 y el mismo formato de una respuesta correcta. El consumidor no debe poder identificar si el valor fue modificado.

## Configuración

Usar estas variables de entorno:

```text
FAULT_INJECTION_ENABLED=false
FAULT_PROBABILITY=0.10
```

- `FAULT_INJECTION_ENABLED`: activa o desactiva la simulación.
- `FAULT_PROBABILITY`: probabilidad de devolver un valor incorrecto. El valor predeterminado es `0.10`, equivalente al 10%.

Cuando `FAULT_INJECTION_ENABLED=false`, el servicio siempre devuelve el valor correcto.

## Comportamiento

Después de calcular correctamente `valor_poliza`, el servicio debe seguir estos pasos:

1. Verificar si la inyección de fallos está habilitada.
2. Generar `roll = random.random()`.
3. Si `roll < FAULT_PROBABILITY`, alterar silenciosamente `valor_poliza`.
4. Si `roll >= FAULT_PROBABILITY`, devolver `valor_poliza` sin cambios.

Con el valor predeterminado `0.10`, aproximadamente el 10% de las respuestas tendrá un valor alterado y el 90% conservará el valor correcto.

Para alterar el valor:

1. Generar un porcentaje aleatorio entre 15% y 30%.
2. Elegir aleatoriamente si el valor aumenta o disminuye.
3. Aplicar la desviación al valor correcto.
4. Redondear el resultado a dos decimales.

```text
desviacion = valor aleatorio entre 0.15 y 0.30
direccion = aumentar o disminuir

si direccion es aumentar:
    valor_devuelto = valor_correcto * (1 + desviacion)

si direccion es disminuir:
    valor_devuelto = valor_correcto * (1 - desviacion)
```

La probabilidad del 10% debe aplicarse por separado en cada petición.

## Respuesta

La estructura de la respuesta no cambia:

```json
{
  "identificacion": "990000000023",
  "producto": {
    "codigo": "VIDA_EXPERIMENTO",
    "nombre": "Seguro de vida experimental",
    "moneda": "COP",
    "anios_proteccion": 10
  },
  "valor_poliza": 291200.00
}
```

Si se inyecta un fallo, únicamente cambia `valor_poliza`. La identificación y los datos del producto deben seguir siendo correctos.

La respuesta con un valor alterado:

- Debe usar HTTP 200.
- No debe incluir campos adicionales.
- No debe incluir mensajes de advertencia.
- No debe indicar que el valor fue modificado.

## Implementación en Python

```python
import os
import random
from decimal import Decimal, ROUND_HALF_UP


FAULT_INJECTION_ENABLED = (
    os.getenv("FAULT_INJECTION_ENABLED", "false").lower() == "true"
)

FAULT_PROBABILITY = Decimal(
    os.getenv("FAULT_PROBABILITY", "0.10")
)


def aplicar_inyeccion_fallo(valor_correcto: Decimal) -> Decimal:
    if not FAULT_INJECTION_ENABLED:
        return valor_correcto

    roll = random.random()

    if roll >= float(FAULT_PROBABILITY):
        return valor_correcto

    desviacion = Decimal(
        str(random.uniform(0.15, 0.30))
    )

    direccion = random.choice((-1, 1))
    factor = Decimal("1") + Decimal(direccion) * desviacion

    valor_alterado = valor_correcto * factor

    return valor_alterado.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )
```

## Integración con el endpoint Flask

La inyección debe ejecutarse después del cálculo correcto y antes de crear la respuesta.

```python
valor_correcto = calcular_valor_poliza(
    persona,
    mortalidad,
    producto
)

valor_devuelto = aplicar_inyeccion_fallo(valor_correcto)

return {
    "identificacion": persona["identificacion"],
    "producto": {
        "codigo": producto["codigo"],
        "nombre": producto["nombre"],
        "moneda": producto["moneda"],
        "anios_proteccion": producto["anios_proteccion"]
    },
    "valor_poliza": float(valor_devuelto)
}, 200
```

## Pseudocódigo

```text
valor_correcto = calcular póliza

si FAULT_INJECTION_ENABLED es false:
    valor_devuelto = valor_correcto

si FAULT_INJECTION_ENABLED es true:
    roll = random.random()

    si roll < FAULT_PROBABILITY:
        desviacion = número aleatorio entre 0.15 y 0.30
        direccion = aumentar o disminuir aleatoriamente
        valor_devuelto = aplicar desviacion a valor_correcto
    de lo contrario:
        valor_devuelto = valor_correcto

responder HTTP 200 usando valor_devuelto
```

## Ejemplos

Si el valor correcto es `291200.00`:

- Sin fallo: `291200.00`.
- Aumento de 20%: `349440.00`.
- Disminución de 20%: `232960.00`.
- Aumento de 30%: `378560.00`.
- Disminución de 30%: `203840.00`.

## Criterios de aceptación

1. Con `FAULT_INJECTION_ENABLED=false`, todas las respuestas contienen el valor correcto.
2. Con `FAULT_INJECTION_ENABLED=true`, cada petición ejecuta `random.random()`.
3. El valor se altera cuando `roll < FAULT_PROBABILITY`.
4. `FAULT_PROBABILITY` usa `0.10` como valor predeterminado.
5. La desviación está entre 15% y 30%.
6. La desviación puede aumentar o disminuir el valor.
7. El valor alterado se redondea a dos decimales.
8. Todas las respuestas exitosas usan HTTP 200 y el mismo formato JSON.
9. Una respuesta alterada no contiene ninguna indicación de que se inyectó un fallo.
10. Solamente se modifica `valor_poliza`.
