from extract import extract_data
from load import load_data
from dotenv import load_dotenv
import os

load_dotenv()

email = os.getenv("MAIL_USER")
password = os.getenv("PASSWORD")

def main():
  data = extract_data()
  load_data(email, password, data)

if __name__ == "__main__":
  main()