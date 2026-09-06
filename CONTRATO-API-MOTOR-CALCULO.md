# Contrato de API — Motor de Cálculo de Pólizas

Documentación para el **servicio consumidor** (el componente que implementa la táctica de *voting*, fuera de este repositorio). Describe cómo llamar a las 3 instancias del motor de cálculo, cómo autenticarse y qué esperar en cada respuesta.

## Contexto

`motorCalculo` está desplegado como **3 instancias independientes**, con el mismo código y la misma base de datos, pero cada una con su propio proceso y su propio generador aleatorio de fallos. El consumidor debe llamar a las 3 y aplicar su lógica de voting sobre las 3 respuestas — eso no es responsabilidad de este servicio.

## URLs base

| Instancia | URL |
|---|---|
| motor-calculo-1 | `https://motor-calculo-1.vercel.app` |
| motor-calculo-2 | `https://motor-calculo-2.vercel.app` |
| motor-calculo-3 | `https://motor-calculo-3.vercel.app` |

## Autenticación

Todas las llamadas a `/motor-calculo/{identificacion}` requieren un JWT firmado con **HS256** usando el secreto compartido:

```text
JWT_SECRET_KEY=llave-secreta-jwt-componente-votacion-2026
```

- El consumidor **firma su propio token** con este secreto — no existe endpoint de login ni de emisión de tokens en el motor de cálculo.
- El token no requiere ningún claim específico (el motor no valida `sub`, `iss`, ni similares). Puede incluir un `exp` opcional; si lo incluye y ya venció, el motor responde `401`. Si no lo incluye, el token no expira.
- Header requerido:

```http
Authorization: Bearer <token>
```

### Ejemplo de generación del token (Python)

```python
import jwt

token = jwt.encode(
    {"servicio": "voter-experimento"},
    "llave-secreta-jwt-componente-votacion-2026",
    algorithm="HS256",
)
```

### Ejemplo de generación del token (Node.js)

```javascript
const jwt = require("jsonwebtoken");

const token = jwt.sign(
  { servicio: "voter-experimento" },
  "llave-secreta-jwt-componente-votacion-2026",
  { algorithm: "HS256" }
);
```

## Endpoints

### `GET /health`

Sin autenticación. Útil para chequeos de disponibilidad antes de votar.

**Respuesta `200`:**

```json
{ "status": "ok" }
```

### `GET /motor-calculo/{identificacion}`

Requiere `Authorization: Bearer <token>`.

**Parámetro de ruta:**

| Nombre | Tipo | Ejemplo |
|---|---|---|
| `identificacion` | string | `990000000023` |

**Respuesta `200` (éxito):**

```json
{
  "identificacion": "990000000023",
  "producto": {
    "codigo": "VIDA_EXPERIMENTO",
    "nombre": "Seguro de vida experimental",
    "moneda": "COP",
    "anios_proteccion": 10
  },
  "valor_poliza": 291200.0
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `identificacion` | string | Igual a la solicitada |
| `producto.codigo` | string | Siempre `VIDA_EXPERIMENTO` en este experimento |
| `producto.nombre` | string | Nombre comercial del producto |
| `producto.moneda` | string | Código de moneda (ISO 4217), ej. `COP` |
| `producto.anios_proteccion` | integer | Años de protección del producto |
| `valor_poliza` | number | Valor anual calculado de la póliza, con 2 decimales |

**⚠️ Importante para la lógica de voting:** `valor_poliza` puede venir **silenciosamente alterado** (±15%–30% del valor correcto) en aproximadamente el 10% de las llamadas, de forma independiente en cada instancia. Esto es intencional — es el mecanismo de inyección de fallos del experimento. El formato de la respuesta y el código `200` son idénticos con o sin alteración; no hay ningún campo que indique si el valor es correcto. Por eso el consumidor debe llamar a las 3 instancias y comparar (`voting`) en vez de confiar en una sola respuesta.

**Respuesta `404` (identificación no encontrada, o sin mortalidad asociada a la edad calculada):**

```json
{ "error": "identificacion no encontrada" }
```

**Respuestas `401` (token ausente, inválido o expirado):**

```json
{ "error": "token no provisto" }
```
```json
{ "error": "token inválido" }
```
```json
{ "error": "token expirado" }
```

## Ejemplo de llamada completa (cURL)

```bash
TOKEN="<token generado con el secreto compartido>"

curl -H "Authorization: Bearer $TOKEN" \
  https://motor-calculo-1.vercel.app/motor-calculo/990000000023
```

## Identificaciones válidas para pruebas

Las identificaciones sembradas van de `990000000001` a `990000001000` (1000 clientes sintéticos). No todas devuelven `200`: algunas de las edades más jóvenes pueden caer fuera del rango de la tabla de mortalidad (18–80 años) según la fecha en que se corrió la semilla, y en ese caso el motor responde `404` en vez de fallar. El caso `990000000023` es estable y sirve como referencia (`valor_poliza = 291200.00` cuando no hay inyección de fallo).
