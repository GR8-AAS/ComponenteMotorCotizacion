BEGIN;

DROP TABLE IF EXISTS public.cotizaciones;
DROP TABLE IF EXISTS public.producto_seguro;
DROP TABLE IF EXISTS public.mortalidad;
DROP TABLE IF EXISTS public.personas_finanzas;

CREATE TABLE public.personas_finanzas (
  identificacion varchar(20) PRIMARY KEY,
  fecha_nacimiento date NOT NULL,
  gastos_mensuales numeric(18,2) NOT NULL CHECK (gastos_mensuales >= 0),
  deuda_total numeric(18,2) NOT NULL CHECK (deuda_total >= 0),
  activos_liquidos numeric(18,2) NOT NULL CHECK (activos_liquidos >= 0)
);

CREATE TABLE public.mortalidad (
  edad smallint PRIMARY KEY CHECK (edad BETWEEN 18 AND 80),
  probabilidad_mortalidad_anual numeric(12,10) NOT NULL
    CHECK (
      probabilidad_mortalidad_anual > 0
      AND probabilidad_mortalidad_anual < 1
    )
);

CREATE TABLE public.producto_seguro (
  codigo varchar(30) PRIMARY KEY,
  nombre varchar(100) NOT NULL,
  moneda char(3) NOT NULL,
  anios_proteccion smallint NOT NULL CHECK (anios_proteccion > 0),
  cobertura_minima numeric(18,2) NOT NULL CHECK (cobertura_minima >= 0),
  factor_gastos_margen numeric(8,4) NOT NULL CHECK (factor_gastos_margen >= 1)
);

INSERT INTO public.producto_seguro (
  codigo,
  nombre,
  moneda,
  anios_proteccion,
  cobertura_minima,
  factor_gastos_margen
)
VALUES (
  'VIDA_EXPERIMENTO',
  'Seguro de vida experimental',
  'COP',
  10,
  50000000,
  1.3000
);

INSERT INTO public.mortalidad (
  edad,
  probabilidad_mortalidad_anual
)
SELECT
  edad::smallint,
  CASE
    WHEN edad BETWEEN 18 AND 29 THEN 0.0004000000
    WHEN edad BETWEEN 30 AND 34 THEN 0.0005000000
    WHEN edad BETWEEN 35 AND 39 THEN 0.0007000000
    WHEN edad BETWEEN 40 AND 44 THEN 0.0010000000
    WHEN edad BETWEEN 45 AND 49 THEN 0.0015000000
    WHEN edad BETWEEN 50 AND 54 THEN 0.0025000000
    WHEN edad BETWEEN 55 AND 59 THEN 0.0040000000
    WHEN edad BETWEEN 60 AND 64 THEN 0.0065000000
    WHEN edad BETWEEN 65 AND 69 THEN 0.0105000000
    WHEN edad BETWEEN 70 AND 74 THEN 0.0170000000
    WHEN edad BETWEEN 75 AND 79 THEN 0.0270000000
    ELSE 0.0430000000
  END::numeric(12,10)
FROM generate_series(18, 80) AS edades(edad);

INSERT INTO public.personas_finanzas (
  identificacion,
  fecha_nacimiento,
  gastos_mensuales,
  deuda_total,
  activos_liquidos
)
SELECT
  '99' || lpad(numero::text, 10, '0') AS identificacion,
  (
    CURRENT_DATE
    - make_interval(years => 18 + ((numero - 1) % 63))
  )::date AS fecha_nacimiento,
  (
    1000000 + ((numero - 1) % 20) * 250000
  )::numeric(18,2) AS gastos_mensuales,
  (
    ((numero - 1) % 31) * 10000000
  )::numeric(18,2) AS deuda_total,
  (
    ((numero - 1) % 41) * 8000000
  )::numeric(18,2) AS activos_liquidos
FROM generate_series(1, 1000) AS personas(numero);

COMMIT;

-- Comprobación esperada:
-- personas = 1000, edades_mortalidad = 63, productos = 1
SELECT
  (SELECT count(*) FROM public.personas_finanzas) AS personas,
  (SELECT count(*) FROM public.mortalidad) AS edades_mortalidad,
  (SELECT count(*) FROM public.producto_seguro) AS productos;
