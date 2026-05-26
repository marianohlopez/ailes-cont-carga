from pymongo import MongoClient
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

# --- CARGAR VARIABLES DE ENTORNO ---
load_dotenv()

MONGO_URL = os.getenv('MONGO_URL')
MONGO_DB = os.getenv('MONGO_DB')
COLLECTION = os.getenv('COLLECTION')

client = MongoClient(MONGO_URL)
db = client[MONGO_DB]
collection = db[COLLECTION]

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