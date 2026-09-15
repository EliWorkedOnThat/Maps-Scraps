import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")


# Function to establish a connection
def connect_to_db():
    try:
        connection = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )

        return connection

    except Exception as e:
        print(f"[ERROR]: {e}")


# Function to create the table if it doesn't exist
def setup_table(connection):
    try:
        cur = connection.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS coldcalls (
                id SERIAL PRIMARY KEY,
                business_name TEXT,
                phone TEXT,
                address TEXT
            );
        """)

        connection.commit()
        cur.close()

    except Exception as e:
        print(f"[ERROR]: {e}")