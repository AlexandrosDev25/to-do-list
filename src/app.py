from database import get_connection

if __name__ == "__main__":
    print("🔌 Probando conexión a PostgreSQL...")
    conn = get_connection()
    print("✅ ¡Conexión exitosa!" if conn else "❌ Falló la conexión")
