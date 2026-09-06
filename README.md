# Motor de Cálculo de Pólizas — Experimento de Voting

Servicio Flask que calcula el valor de una póliza de vida a partir de datos sintéticos en PostgreSQL/Supabase. Es una de **3 réplicas idénticas** desplegadas de forma independiente, usadas como experimento universitario de la **táctica de arquitectura de voting**: cada réplica puede alterar silenciosamente su resultado (inyección de fallos controlada), y un servicio externo (fuera de este repositorio) consulta las 3 y aplica votación para detectar la respuesta correcta.

## Documentos de especificación (contexto original del experimento)

- [`motor-calculo-polizas.md`](./motor-calculo-polizas.md) — reglas de negocio y fórmulas del cálculo de la póliza.
- [`inyeccion-fallos-motor-calculo.md`](./inyeccion-fallos-motor-calculo.md) — especificación del modo de inyección de fallos.
- [`semilla-motor-calculo.sql`](./semilla-motor-calculo.sql) — script que crea y puebla la base de datos.

## Documentos generados durante la construcción

- [`CONTRATO-API-MOTOR-CALCULO.md`](./CONTRATO-API-MOTOR-CALCULO.md) — contrato de API para el servicio que va a consumir este motor (autenticación, endpoints, formatos de error).
- [`DESPLIEGUE-VERCEL.md`](./DESPLIEGUE-VERCEL.md) — guía manual para desplegar las 3 instancias en Vercel desde cero.

## Estructura del proyecto

```
motorCalculo/
├── app/
│   ├── __init__.py      # factory de Flask
│   ├── config.py         # variables de entorno
│   ├── auth.py            # validación de JWT (HS256)
│   ├── db.py               # acceso a datos (solo SELECT)
│   ├── calculo.py           # fórmulas de edad y valor de póliza
│   ├── fallos.py              # inyección de fallos silenciosa
│   └── routes.py                # endpoints Flask
├── api/index.py           # entrypoint para el runtime serverless de Vercel
├── tests/                  # pytest (unitarias + endpoint)
├── run.py                   # entrypoint para desarrollo local
├── requirements.txt
├── vercel.json / .vercelignore
├── .env.example
└── semilla-motor-calculo.sql
```

## Requisitos

- Python 3.11+
- Una base de datos PostgreSQL (se usó Supabase, con el pooler en modo transacción)

## Puesta en marcha local

### 1. Entorno virtual e instalación

```bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. Variables de entorno

Copia `.env.example` a `.env` y completa los valores:

```env
DATABASE_URL=postgresql://usuario:password@host:5432/nombre_bd
FAULT_INJECTION_ENABLED=false
FAULT_PROBABILITY=0.10
FLASK_DEBUG=false
JWT_SECRET_KEY=llave-secreta-jwt-componente-votacion-2026
```

`JWT_SECRET_KEY` es un secreto compartido con el servicio consumidor (no hay endpoint de login/emisión de tokens en este proyecto — ver `CONTRATO-API-MOTOR-CALCULO.md`).

### 3. Sembrar la base de datos

Con `DATABASE_URL` ya configurado en `.env`, ejecuta:

```bash
.venv\Scripts\python.exe scripts_apply_seed.py
```

Corre `semilla-motor-calculo.sql` contra tu base y al final imprime la verificación esperada:

```text
personas = 1000, edades_mortalidad = 63, productos = 1
```

### 4. Levantar el servicio

```bash
.venv\Scripts\python.exe run.py
```

### 5. Correr las pruebas

```bash
.venv\Scripts\python.exe -m pytest -v
```

## Uso del endpoint

```http
GET /health
```

Sin autenticación, para chequeos de disponibilidad.

```http
GET /motor-calculo/{identificacion}
Authorization: Bearer <token JWT firmado con JWT_SECRET_KEY, HS256>
```

Detalle completo de request/response, códigos de error y ejemplos de generación del token en [`CONTRATO-API-MOTOR-CALCULO.md`](./CONTRATO-API-MOTOR-CALCULO.md).

## Inyección de fallos

Controlada por `FAULT_INJECTION_ENABLED` y `FAULT_PROBABILITY`. Con la inyección activa, `valor_poliza` puede venir alterado (±15%–30%) sin ninguna señal visible en la respuesta — es el comportamiento esperado del experimento, no un bug. Detalle en `inyeccion-fallos-motor-calculo.md`.

## Despliegue

El servicio está desplegado como 3 instancias independientes en Vercel:

- `https://motor-calculo-1.vercel.app`
- `https://motor-calculo-2.vercel.app`
- `https://motor-calculo-3.vercel.app`

Cada una con las mismas 5 variables de entorno configuradas en el dashboard de Vercel (nunca en el repositorio). Pasos completos para replicar el despliegue en [`DESPLIEGUE-VERCEL.md`](./DESPLIEGUE-VERCEL.md).

## Rendimiento y latencia

Al medir el endpoint en producción se detectaron tiempos de respuesta iniciales de **~1.9s**, altos para 3 consultas `SELECT` simples. Investigación y fixes aplicados:

**Índices:** revisados y descartados como causa. Las 3 tablas (`personas_finanzas`, `mortalidad`, `producto_seguro`) ya tienen índice automático en la columna consultada, porque esa columna es su `PRIMARY KEY`. No se necesitó agregar ninguno.

**Causa real — 2 fixes de conexión a la base de datos:**

| Cambio | Efecto medido |
|---|---|
| Estado inicial: cada una de las 3 consultas (`persona`, `mortalidad`, `producto`) abría y cerraba su propia conexión a Supabase | ~1.9s |
| Fix 1: reutilizar una sola conexión para las 3 consultas de un mismo request | ~1.0s |
| Fix 2: cachear la conexión a nivel de módulo para reutilizarla también entre invocaciones "calientes" de la función serverless (con reintento automático si el pooler la cerró por inactividad) | **~0.5s** en peticiones que caen en un contenedor caliente; la primera petición a un contenedor frío sigue costando ~1s |

**Causa raíz restante (no resuelta, limitación del plan):** la función de Vercel corre en `iad1` (Virginia, costa este de EE.UU.), pero la base de datos Supabase está en `aws-0-us-west-2` (Oregón, costa oeste) — cada ida y vuelta a la base paga latencia transcontinental. Fijar la región de la función cerca de la base eliminaría esto, pero requiere plan Pro de Vercel (el proyecto usa el plan free por ser un experimento). Queda documentado como limitación conocida.

## Alcance del experimento

Este repositorio implementa **solo** el motor de cálculo (las 3 réplicas). No implementa el servicio votante ni la lógica de comparación/consenso entre las 3 respuestas — eso se construye en un componente aparte. Todos los datos son sintéticos; esto no es un modelo actuarial real.
