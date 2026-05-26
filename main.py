from extract import extract_data
from load import load_data
from db import register_obs
from dotenv import load_dotenv
import time
from datetime import timedelta
import os

load_dotenv()

email = os.getenv("MAIL_USER")
password = os.getenv("PASSWORD")

def main():

  start = time.time()

  data = extract_data()

  result = load_data(email, password, data)

  end = time.time()

  full_time = int(end - start)

  register_obs(
    cant_obs_a_ingresar=len(data),
    obs_ingresadas=result["obs_ingresadas"],
    obs_ing_anteriormente=result["obs_ing_anteriormente"],
    tiempo_total=full_time
  )

if __name__ == "__main__":
  main()