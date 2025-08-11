"""Database connection module for PostgreSQL using environment variables."""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()  # Carga variables desde .env


def get_connection():
    """Conecta a PostgreSQL usando variables de entorno."""
    try:
        return psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT", "5432")
        )
    except psycopg2.Error as e:
        print(f"Error de conexión: {e}")
        return None
