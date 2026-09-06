# Guía de despliegue: 3 instancias en Vercel

Este proyecto no tiene un repositorio Git remoto, así que el camino más simple es desplegar la carpeta local directamente con el CLI de Vercel (no requiere GitHub). Cada instancia es un **proyecto Vercel independiente**, con el mismo código, para que la táctica de voting tenga 3 réplicas reales.

## 0. Requisitos previos

```bash
npm install -g vercel
vercel login
```

`vercel login` abre un flujo interactivo (código por correo o navegador). Corre este paso tú directamente en tu terminal.

## 1. Desplegar la primera instancia (`motor-calculo-1`)

Desde la raíz del proyecto (`C:\repo\motorCalculo`):

```bash
vercel link
```

- Cuando pregunte "Link to existing project?" → **No**.
- Te pedirá un nombre de proyecto → escribe `motor-calculo-1`.
- Esto crea una carpeta local `.vercel/` que asocia esta carpeta con ese proyecto.

Configura las variables de entorno (una vez por variable, elige el ambiente **Production**):

```bash
vercel env add DATABASE_URL production
vercel env add JWT_SECRET_KEY production
vercel env add FAULT_INJECTION_ENABLED production
vercel env add FAULT_PROBABILITY production
vercel env add FLASK_DEBUG production
```

Valores a pegar cuando lo pida:

| Variable | Valor |
|---|---|
| `DATABASE_URL` | tu cadena de Supabase completa (con `?pgbouncer=true`) |
| `JWT_SECRET_KEY` | `llave-secreta-jwt-componente-votacion-2026` |
| `FAULT_INJECTION_ENABLED` | `true` |
| `FAULT_PROBABILITY` | `0.10` |
| `FLASK_DEBUG` | `false` |

Despliega a producción:

```bash
vercel --prod
```

Al terminar te da una URL como `https://motor-calculo-1.vercel.app`. Pruébala:

```bash
curl https://motor-calculo-1.vercel.app/health
```

Si falla el build por `psycopg2-binary` (dependencia nativa), revisa los logs con `vercel logs <url>` — la alternativa es cambiar esa dependencia por `psycopg[binary]` en `requirements.txt`, pero primero confirmemos si realmente falla.

Prueba también el endpoint protegido con un JWT firmado con el mismo secreto (puedes generarlo con `jwt.io` pegando el `JWT_SECRET_KEY`, algoritmo HS256, o con un script Python local):

```bash
curl -H "Authorization: Bearer <token>" https://motor-calculo-1.vercel.app/motor-calculo/990000000023
```

## 2. Desligar la carpeta y desplegar la segunda instancia (`motor-calculo-2`)

El CLI solo permite un proyecto vinculado por carpeta a la vez. Para crear la segunda instancia desde el mismo código:

```bash
rm -rf .vercel
vercel link
```

- "Link to existing project?" → **No**.
- Nombre de proyecto → `motor-calculo-2`.

Repite exactamente los mismos pasos de variables de entorno y despliegue:

```bash
vercel env add DATABASE_URL production
vercel env add JWT_SECRET_KEY production
vercel env add FAULT_INJECTION_ENABLED production
vercel env add FAULT_PROBABILITY production
vercel env add FLASK_DEBUG production
vercel --prod
```

## 3. Repetir para la tercera instancia (`motor-calculo-3`)

Mismo procedimiento:

```bash
rm -rf .vercel
vercel link
# nombre: motor-calculo-3
vercel env add DATABASE_URL production
vercel env add JWT_SECRET_KEY production
vercel env add FAULT_INJECTION_ENABLED production
vercel env add FAULT_PROBABILITY production
vercel env add FLASK_DEBUG production
vercel --prod
```

## 4. Verificación final

Al terminar deberías tener 3 URLs independientes, por ejemplo:

- `https://motor-calculo-1.vercel.app`
- `https://motor-calculo-2.vercel.app`
- `https://motor-calculo-3.vercel.app`

Cada una:

- Responde `/health` sin token.
- Responde `/motor-calculo/{identificacion}` solo con un JWT válido firmado con `JWT_SECRET_KEY`.
- Consulta la misma base de datos en Supabase (los datos son compartidos; lo que varía entre instancias es el resultado aleatorio de la inyección de fallos, ya que cada una tiene su propio proceso y su propio generador aleatorio).

Estas 3 URLs son las que el servicio votante (fuera de este proyecto) va a consumir para aplicar la táctica de voting.

## Notas

- No subas `.env` ni el `JWT_SECRET_KEY` a ningún repositorio público — aquí se configuran solo como variables de entorno de Vercel.
- Si más adelante conectas este proyecto a un repositorio Git, Vercel puede auto-desplegar en cada push; con 3 proyectos apuntando al mismo repo, tendrías las 3 instancias actualizándose juntas.
