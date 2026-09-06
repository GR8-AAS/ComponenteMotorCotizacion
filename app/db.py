import psycopg2
import psycopg2.extras

from app.config import Config

_conn = None


def get_connection():
    """Reutiliza la conexión entre invocaciones "calientes" de la función
    serverless para evitar pagar el handshake TCP/TLS en cada request."""
    global _conn
    if _conn is None or _conn.closed:
        dsn = Config.DATABASE_URL.split("?")[0]
        _conn = psycopg2.connect(dsn)
        _conn.autocommit = True
    return _conn


def reset_connection():
    """Descarta la conexión cacheada cuando resultó estar rota (ej. el pooler
    la cerró por inactividad); la siguiente llamada a get_connection() abre una nueva."""
    global _conn
    if _conn is not None:
        try:
            _conn.close()
        except psycopg2.Error:
            pass
    _conn = None


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
