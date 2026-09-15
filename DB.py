#Imports 
import os 
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DB_PASSWORD = os.getenv("DB_PASSWORD")

#Function to establish a connection
def connect_to_db():
    try:
        connection = psycopg2.connect(
            host = "localhost",
            database="coldcalls",
            user="postgres",
            password = DB_PASSWORD,
            port = "5432"
        )
    except Exception as e:
        print(f"[ERROR]:{e}")
