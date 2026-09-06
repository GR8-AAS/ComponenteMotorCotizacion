import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL").split("?")[0]

with open("semilla-motor-calculo.sql", "r", encoding="utf-8") as f:
    sql = f.read()

conn = psycopg2.connect(DATABASE_URL)
try:
    with conn.cursor() as cur:
        cur.execute(sql)
        rows = cur.fetchall()
        colnames = [desc[0] for desc in cur.description]
        print(colnames)
        for row in rows:
            print(row)
    conn.commit()
finally:
    conn.close()
