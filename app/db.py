import psycopg2
import psycopg2.extras

from app.config import Config


def get_connection():
    dsn = Config.DATABASE_URL.split("?")[0]
    return psycopg2.connect(dsn)


def obtener_persona(conn, identificacion: str) -> dict | None:
    query = """
        SELECT
          identificacion,
          fecha_nacimiento,
          gastos_mensuales,
          deuda_total,
          activos_liquidos
        FROM public.personas_finanzas
        WHERE identificacion = %s;
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(query, (identificacion,))
        row = cur.fetchone()
        return dict(row) if row else None


def obtener_mortalidad(conn, edad: int) -> dict | None:
    query = """
        SELECT
          edad,
          probabilidad_mortalidad_anual
        FROM public.mortalidad
        WHERE edad = %s;
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(query, (edad,))
        row = cur.fetchone()
        return dict(row) if row else None


def obtener_producto(conn, codigo: str = "VIDA_EXPERIMENTO") -> dict | None:
    query = """
        SELECT
          codigo,
          nombre,
          moneda,
          anios_proteccion,
          cobertura_minima,
          factor_gastos_margen
        FROM public.producto_seguro
        WHERE codigo = %s;
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(query, (codigo,))
        row = cur.fetchone()
        return dict(row) if row else None
