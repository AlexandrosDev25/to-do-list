from database import get_connection
from todo_cli import main

if __name__ == "__main__":
    print("🔌 Probando conexión a PostgreSQL...")
    conn = get_connection()

    if conn:
        print("✅ ¡Conexión exitosa!")
        conn.close()
        main()  # Ejecuta la interfaz CLI
    else:
        print("❌ Falló la conexión")
