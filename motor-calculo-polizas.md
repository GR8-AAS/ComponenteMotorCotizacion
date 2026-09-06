# Motor de Cálculo de Pólizas de Vida

## Objetivo

Construir un servicio simple en **Python con Flask** para un experimento educativo de cálculo de pólizas de vida.

El servicio debe:

1. Recibir un número de identificación.
2. Recuperar de PostgreSQL/Supabase los datos financieros y la fecha de nacimiento del cliente.
3. Calcular la edad en Python.
4. Recuperar de la base de datos la mortalidad correspondiente a esa edad.
5. Recuperar de la base de datos los datos del producto.
6. Calcular en Python la cobertura, la prima pura y el valor anual de la póliza.
7. Devolver el valor, la identificación y los datos básicos del producto.

La base de datos solo almacena los datos. Las fórmulas deben ejecutarse en el código Python.

## Datos usados

### Cliente

- `identificacion`
- `fecha_nacimiento`
- `gastos_mensuales`
- `deuda_total`
- `activos_liquidos`

### Mortalidad

- `edad`
- `probabilidad_mortalidad_anual`

### Producto

- `codigo`
- `nombre`
- `moneda`
- `anios_proteccion`
- `cobertura_minima`
- `factor_gastos_margen`

## Base de datos

La semilla se encuentra en `semilla-motor-calculo.sql` y crea estas tres tablas:

- `personas_finanzas`
- `mortalidad`
- `producto_seguro`

También carga:

- 1.000 clientes sintéticos.
- Mortalidad para todas las edades entre 18 y 80 años.
- Un producto llamado `VIDA_EXPERIMENTO`.

Las identificaciones generadas van desde:

```text
990000000001
```

hasta:

```text
990000001000
```

Las fechas de nacimiento se generan en relación con `CURRENT_DATE`. Por eso, cada cliente siempre queda asociado a una edad existente en la tabla `mortalidad` al cargar la semilla.

## Fórmulas ejecutadas en Python

### Edad

Calcular los años cumplidos usando `fecha_nacimiento` y la fecha actual.

```text
edad = años cumplidos entre fecha_nacimiento y fecha_actual
```

No calcular la edad dividiendo días entre 365.

### Cobertura recomendada

```text
cobertura_base =
    deuda_total
    + gastos_mensuales * 12 * anios_proteccion
    - activos_liquidos

cobertura_recomendada =
    max(cobertura_base, cobertura_minima)
```

### Prima pura anual

```text
prima_pura =
    cobertura_recomendada
    * probabilidad_mortalidad_anual
```

### Valor anual de la póliza

```text
valor_poliza =
    prima_pura
    * factor_gastos_margen
```

El resultado se redondea a dos decimales.

## Endpoint

```http
GET /motor-calculo/{identificacion}
```

Ejemplo:

```http
GET /motor-calculo/990000000023
```

## Consultas que debe hacer Flask

### 1. Recuperar el cliente

```sql
SELECT
  identificacion,
  fecha_nacimiento,
  gastos_mensuales,
  deuda_total,
  activos_liquidos
FROM public.personas_finanzas
WHERE identificacion = %s;
```

### 2. Recuperar la mortalidad

La edad usada en esta consulta debe haber sido calculada previamente en Python.

```sql
SELECT
  edad,
  probabilidad_mortalidad_anual
FROM public.mortalidad
WHERE edad = %s;
```

### 3. Recuperar el producto

```sql
SELECT
  codigo,
  nombre,
  moneda,
  anios_proteccion,
  cobertura_minima,
  factor_gastos_margen
FROM public.producto_seguro
WHERE codigo = 'VIDA_EXPERIMENTO';
```

La consulta SQL no debe calcular la cobertura ni la prima.

## Respuesta del servicio

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

`valor_poliza` corresponde al valor anual de la póliza.

Si la identificación no existe, el servicio debe responder `404`.

## Lógica en Python

La implementación debe usar `Decimal` para los valores monetarios y las probabilidades.

```python
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


def calcular_valor_poliza(persona, mortalidad, producto) -> Decimal:
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
```

## Flujo del endpoint Flask

```text
recibir identificacion

consultar personas_finanzas
si no existe:
    responder 404

calcular edad en Python

consultar mortalidad usando la edad

consultar producto_seguro usando VIDA_EXPERIMENTO

calcular cobertura recomendada en Python
calcular prima pura en Python
calcular valor de la póliza en Python

responder:
    identificacion
    codigo del producto
    nombre del producto
    moneda
    años de protección
    valor_poliza
```

## Ejemplo con la semilla

La identificación `990000000023` se genera con estos datos:

```text
edad = 40
gastos_mensuales = 1,500,000
deuda_total = 220,000,000
activos_liquidos = 176,000,000
anios_proteccion = 10
cobertura_minima = 50,000,000
probabilidad_mortalidad_anual = 0.001
factor_gastos_margen = 1.30
```

Cobertura:

```text
220,000,000 + (1,500,000 * 12 * 10) - 176,000,000
= 224,000,000
```

Prima pura:

```text
224,000,000 * 0.001
= 224,000
```

Valor anual de la póliza:

```text
224,000 * 1.30
= 291,200 COP
```

## Criterios de aceptación

1. El endpoint recibe solo la identificación.
2. Los datos del cliente, mortalidad y producto se recuperan desde la base de datos.
3. La edad y todos los valores de la póliza se calculan en Python.
4. No se guardan los resultados del cálculo.
5. La respuesta contiene `identificacion`, `producto` y `valor_poliza`.
6. Las 1.000 identificaciones de la semilla tienen una mortalidad correspondiente y devuelven un valor válido.
7. Para `990000000023`, el resultado es `291200.00`.

El experimento usa únicamente datos sintéticos y no es un modelo actuarial para producción.
