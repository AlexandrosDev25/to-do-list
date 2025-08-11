import os
import psycopg2
from dotenv import load_dotenv
from time import sleep

load_dotenv()


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
        print(f"❌ Error de conexión: {e}")
        return None


def create_table():
    """Crea la tabla todos si no existe"""
    conn = get_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS todos (
                    id SERIAL PRIMARY KEY,
                    task TEXT NOT NULL,
                    completed BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            conn.commit()
            return True
    except psycopg2.Error as e:
        print(f"❌ Error al crear tabla: {e}")
        return False
    finally:
        conn.close()


def add_task(task):
    """Añade una nueva tarea"""
    conn = get_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO todos (task) VALUES (%s) RETURNING id",
                (task,)
            )
            task_id = cursor.fetchone()[0]
            conn.commit()
            print(f"✅ Tarea añadida con ID: {task_id}")
            return True
    except psycopg2.Error as e:
        print(f"❌ Error al añadir tarea: {e}")
        return False
    finally:
        conn.close()


def list_tasks():
    """Lista todas las tareas"""
    conn = get_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, task, completed, 
                       TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI') 
                FROM todos 
                ORDER BY created_at DESC
            """)
            tasks = cursor.fetchall()

            if not tasks:
                print("📭 No hay tareas en la lista")
                return True

            print("\n📋 Lista de Tareas:")
            print("-" * 50)
            for task in tasks:
                status = "✓" if task[2] else "✗"
                print(f"{task[0]}. [{status}] {task[1]} (Creada: {task[3]})")
            print("-" * 50)
            return True
    except psycopg2.Error as e:
        print(f"❌ Error al listar tareas: {e}")
        return False
    finally:
        conn.close()


def update_task(task_id, new_task=None, completed=None):
    """Actualiza una tarea"""
    conn = get_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cursor:
            if new_task and completed is not None:
                cursor.execute(
                    "UPDATE todos SET task = %s, completed = %s WHERE id = %s",
                    (new_task, completed, task_id)
                )
            elif new_task:
                cursor.execute(
                    "UPDATE todos SET task = %s WHERE id = %s",
                    (new_task, task_id)
                )
            elif completed is not None:
                cursor.execute(
                    "UPDATE todos SET completed = %s WHERE id = %s",
                    (completed, task_id)
                )

            if cursor.rowcount == 0:
                print("⚠️ No se encontró la tarea con ese ID")
                return False

            conn.commit()
            print("✅ Tarea actualizada")
            return True
    except psycopg2.Error as e:
        print(f"❌ Error al actualizar tarea: {e}")
        return False
    finally:
        conn.close()


def delete_task(task_id):
    """Elimina una tarea"""
    conn = get_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM todos WHERE id = %s", (task_id,))

            if cursor.rowcount == 0:
                print("⚠️ No se encontró la tarea con ese ID")
                return False

            conn.commit()
            print("✅ Tarea eliminada")
            return True
    except psycopg2.Error as e:
        print(f"❌ Error al eliminar tarea: {e}")
        return False
    finally:
        conn.close()


def clear_screen():
    """Limpia la pantalla de la terminal"""
    os.system('cls' if os.name == 'nt' else 'clear')


def show_menu():
    """Muestra el menú principal"""
    print("\n" + "=" * 50)
    print("📝 TO-DO LIST MANAGER".center(50))
    print("=" * 50)
    print("1. 📋 Listar tareas")
    print("2. ➕ Añadir tarea")
    print("3. ✏️ Editar tarea")
    print("4. ✓ Marcar como completada")
    print("5. ❌ Eliminar tarea")
    print("6. 🚪 Salir")
    print("=" * 50)


def main():
    # Verificar conexión y tabla
    if not get_connection():
        return

    if not create_table():
        print("No se pudo crear la tabla. Saliendo...")
        return

    while True:
        clear_screen()
        show_menu()

        try:
            option = input("\nSeleccione una opción (1-6): ")

            if option == "1":  # Listar
                clear_screen()
                list_tasks()
                input("\nPresione Enter para continuar...")

            elif option == "2":  # Añadir
                clear_screen()
                print("➕ Añadir Nueva Tarea")
                task = input("\nDescripción de la tarea: ").strip()
                if task:
                    add_task(task)
                else:
                    print("⚠️ La descripción no puede estar vacía")
                input("\nPresione Enter para continuar...")

            elif option == "3":  # Editar
                clear_screen()
                list_tasks()
                try:
                    task_id = int(input("\nID de la tarea a editar: "))
                    new_task = input("Nueva descripción: ").strip()
                    if new_task:
                        update_task(task_id, new_task=new_task)
                    else:
                        print("⚠️ La descripción no puede estar vacía")
                except ValueError:
                    print("⚠️ Debe ingresar un número válido")
                input("\nPresione Enter para continuar...")

            elif option == "4":  # Completar
                clear_screen()
                list_tasks()
                try:
                    task_id = int(
                        input("\nID de la tarea a marcar como completada: "))
                    update_task(task_id, completed=True)
                except ValueError:
                    print("⚠️ Debe ingresar un número válido")
                input("\nPresione Enter para continuar...")

            elif option == "5":  # Eliminar
                clear_screen()
                list_tasks()
                try:
                    task_id = int(input("\nID de la tarea a eliminar: "))
                    delete_task(task_id)
                except ValueError:
                    print("⚠️ Debe ingresar un número válido")
                input("\nPresione Enter para continuar...")

            elif option == "6":  # Salir
                print("\n👋 ¡Hasta luego!")
                break

            else:
                print("⚠️ Opción no válida. Intente nuevamente.")
                sleep(1)

        except KeyboardInterrupt:
            print("\n👋 ¡Hasta luego!")
            break


if __name__ == "__main__":
    main()
