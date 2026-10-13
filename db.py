from pymongo import MongoClient
import mysql.connector
from datetime import datetime, timedelta
from dotenv import load_dotenv
import re
import os

# --- CARGAR VARIABLES DE ENTORNO ---
load_dotenv()

MONGO_URL = os.getenv('MONGO_URL')
MONGO_DB = os.getenv('MONGO_DB')
COLLECTION = os.getenv('COLLECTION')

DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_NAME = os.getenv('DB_NAME')

client = MongoClient(MONGO_URL)
db = client[MONGO_DB]
collection = db[COLLECTION]

DB_CONFIG = {
    "host": DB_HOST,
    "port": DB_PORT,
    "user": DB_USER,
    "password": DB_PASS,
    "database": DB_NAME,
}

QUERY = """
    SELECT c.NroComprobante, c.ImpTotal, c.cbteFch, c.fec_envio_os, c.factura_cobro_descrip, c.mes_anio,
           o.os_nombre, p.alumno_nombre, p.alumno_apellido, c.factura_obs, e.etiqueta
    FROM v_comprobantes c
    LEFT JOIN v_etiquetas_facturas e ON c.id = e.comprobante_id
    JOIN v_os o ON c.os_id = o.os_id
    JOIN v_prestaciones p ON c.prestacion_id = p.prestacion_id
    WHERE YEAR(cbteFch) IN (2025, 2026)
"""

def register_obs(cant_obs_a_ingresar, obs_ingresadas, obs_ing_anteriormente,
                    tiempo_total):
  try:

    fecha_arg = datetime.now() - timedelta(hours=3)

    if cant_obs_a_ingresar > 0 and obs_ingresadas == 0 and obs_ing_anteriormente == 0:
      error = True
    else:
      error = False

    doc = {
      "fecha_hora": fecha_arg,
      "cant_obs_a_ingresar": cant_obs_a_ingresar,
      "obs_ingresadas": obs_ingresadas,
      "obs_ing_anteriormente": obs_ing_anteriormente,
      "tiempo_total": tiempo_total,
      "error": error,
    }

    collection.insert_one(doc)

    print("✅ Informe registrado en Mongo")

  except Exception as e:
      print("Error registrando informe en Mongo:", e)

def normalizar_texto(txt):
    if not txt:
        return ''
    txt = txt.lower()
    txt = txt.replace('<br>', ' ')
    txt = re.sub(r'\s+', ' ', txt)  # espacios, tabs, saltos de línea
    return txt.strip()

def clave(fc_id, importe, fecha, periodo):
    return (fc_id, f"{float(str(importe).replace(',', '.')):.2f}", fecha, periodo)


def obtener_obs_db(db_config=DB_CONFIG):
    """Devuelve {clave_identificatoria: set de observaciones normalizadas en la base}."""
    conn = mysql.connector.connect(**db_config)
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(QUERY)
        filas = cur.fetchall()
        cur.close()
    finally:
        conn.close()

    obs_por_clave = {}
    for f in filas:
        k = clave(f["NroComprobante"], f["ImpTotal"],
                  f["cbteFch"].strftime("%d/%m/%Y"), f["mes_anio"])
        obs_por_clave.setdefault(k, set()).add(normalizar_texto(f["factura_obs"]))
    return obs_por_clave

def filtrar_no_cargadas(data, db_config=DB_CONFIG):
    obs_db = obtener_obs_db(db_config)

    pendientes, ya_en_db, sin_match = [], 0, []
    for data_row in data:
        k = clave(data_row[0], data_row[1], data_row[2].strftime("%d/%m/%Y"), data_row[6])

        if k not in obs_db:
            sin_match.append(data_row)
            print(f"⚠ Factura {data_row[0]}: no coincide factura/importe/fecha/periodo con la base, NO se carga")
        elif normalizar_texto(data_row[10]) in obs_db[k]:
            ya_en_db += 1
            print(f"⏭ Factura {data_row[0]} ya tiene esa observación en la base, se omite")
        else:
            pendientes.append(data_row)

    print(f"🔎 Validación previa: {len(data)} en excel, {ya_en_db} ya cargadas, "
          f"{len(sin_match)} sin coincidencia, {len(pendientes)} a cargar")
    return pendientes, ya_en_db, sin_match