# Importa el módulo 'os', que permite interactuar con el sistema operativo.
# Por ejemplo, puedes acceder a variables de entorno, manipular archivos, etc.
import os

# Importa el módulo 'psycopg2', que es una librería externa para conectarse y trabajar con bases de datos PostgreSQL desde Python.
import psycopg2

# Importa la función 'load_dotenv' del paquete 'dotenv'.
# Esta función sirve para cargar variables de entorno desde un archivo llamado '.env'.
# Las variables de entorno son valores que se pueden usar para configurar el comportamiento de tu aplicación (por ejemplo, contraseñas, nombres de usuario, etc.).
from dotenv import load_dotenv

# Importa la función 'sleep' del módulo 'time'.
# 'sleep' permite pausar la ejecución del programa durante una cantidad de segundos que tú determines.
from time import sleep

# Llama a la función 'load_dotenv()' para cargar las variables de entorno desde el archivo '.env'.
# Así, puedes acceder a ellas usando 'os.getenv' más adelante en el código.
load_dotenv()


def get_connection():
    """
    Esta función intenta conectarse a una base de datos PostgreSQL usando los datos de las variables de entorno.
    Si la conexión es exitosa, devuelve el objeto de conexión.
    Si ocurre un error (por ejemplo, datos incorrectos o la base de datos no está disponible), devuelve None.
    """
    try:
        # 'try' es una estructura de control que permite intentar ejecutar un bloque de código.
        # Si ocurre un error dentro del bloque, el flujo pasa al bloque 'except'.
        # Aquí, se intenta crear una conexión a la base de datos usando los datos de las variables de entorno
        return psycopg2.connect(
            # Obtiene el valor de la variable de entorno 'DB_HOST'.
            host=os.getenv("DB_HOST"),
            # Obtiene el nombre de la base de datos.
            database=os.getenv("DB_NAME"),
            # Obtiene el usuario de la base de datos.
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),  # Obtiene la contraseña.
            # Obtiene el puerto, o usa '5432' si no está definido.
            port=os.getenv("DB_PORT", "5432")
        )
    except psycopg2.Error as e:
        # 'except' captura errores específicos del tipo 'psycopg2.Error'.
        # Si ocurre un error, imprime un mensaje y devuelve None.
        print(f"❌ Error de conexión: {e}")
        return None


def create_table():
    """
    Esta función crea la tabla 'todos' en la base de datos si no existe.
    Devuelve True si la tabla se creó o ya existía, y False si hubo un error.
    """
    conn = get_connection()  # Llama a la función anterior para obtener una conexión.
    if not conn:
        # Si la conexión no fue exitosa (es None), retorna False.
        return False

    try:
        # Usa un 'cursor', que es un objeto que permite ejecutar comandos SQL en la base de datos.
        with conn.cursor() as cursor:
            # Ejecuta una consulta SQL para crear la tabla solo si no existe.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS todos (
                    id SERIAL PRIMARY KEY,           # 'id' es un número que se incrementa solo y es la clave primaria.
                    task TEXT NOT NULL,              # 'task' es el texto de la tarea, no puede ser nulo.
                    completed BOOLEAN DEFAULT FALSE, # 'completed' indica si la tarea está completada, por defecto es False.
                    created_at TIMESTAMP DEFAULT NOW() # 'created_at' guarda la fecha y hora de creación, por defecto es el momento actual.
                )
            """)
            conn.commit()  # 'commit' guarda los cambios realizados en la base de datos.
            return True
    except psycopg2.Error as e:
        # Si ocurre un error al ejecutar la consulta, imprime el error y retorna False.
        print(f"❌ Error al crear tabla: {e}")
        return False
    finally:
        # 'finally' se ejecuta siempre, ocurra o no un error.
        # Aquí, se cierra la conexión a la base de datos para liberar recursos.
        conn.close()


def add_task(task):
    """
    Esta función añade una nueva tarea a la tabla 'todos'.
    Recibe como parámetro el texto de la tarea.
    Devuelve True si la tarea se añadió correctamente, o False si hubo un error.
    """
    conn = get_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cursor:
            # Inserta la nueva tarea en la tabla y pide que devuelva el id generado automáticamente.
            cursor.execute(
                "INSERT INTO todos (task) VALUES (%s) RETURNING id",
                (task,)  # El parámetro se pasa como una tupla.
            )
            # Obtiene el id de la nueva tarea insertada.
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
    """
    Esta función lista todas las tareas almacenadas en la tabla 'todos'.
    Imprime cada tarea con su id, estado (completada o no), descripción y fecha de creación.
    Devuelve True si la operación fue exitosa, o False si hubo un error.
    """
    conn = get_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cursor:
            # Selecciona todas las tareas, ordenadas por fecha de creación descendente.
            cursor.execute("""
                SELECT id, task, completed, 
                       TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI') 
                FROM todos 
                ORDER BY created_at DESC
            """)
            tasks = cursor.fetchall()  # Obtiene todas las filas resultantes de la consulta.

            if not tasks:
                # Si no hay tareas, informa al usuario.
                print("📭 No hay tareas en la lista")
                return True

            print("\n📋 Lista de Tareas:")
            print("-" * 50)
            for task in tasks:
                # task[2] es el campo 'completed'. Si es True, muestra ✓, si es False, muestra ✗.
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
    """
    Esta función actualiza una tarea existente.
    Puede cambiar la descripción ('new_task'), el estado de completada ('completed'), o ambos.
    'task_id' es el identificador de la tarea a modificar.
    """
    conn = get_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cursor:
            # Dependiendo de los argumentos recibidos, actualiza la descripción, el estado, o ambos.
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
                # Si no se actualizó ninguna fila, es porque no existe una tarea con ese id.
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
    """
    Esta función elimina una tarea de la tabla 'todos' usando su id.
    Devuelve True si la tarea fue eliminada, o False si hubo un error o no se encontró la tarea.
    """
    conn = get_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM todos WHERE id = %s", (task_id,))

            if cursor.rowcount == 0:
                # Si no se eliminó ninguna fila, es porque no existe una tarea con ese id.
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
    """
    Esta función limpia la pantalla de la terminal.
    Usa el comando 'cls' si el sistema operativo es Windows ('nt'), o 'clear' en otros sistemas (Linux, Mac).
    """
    os.system('cls' if os.name == 'nt' else 'clear')


def show_menu():
    """
    Esta función imprime el menú principal de la aplicación.
    Muestra las opciones disponibles para el usuario.
    """
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
    """
    Esta es la función principal del programa.
    Controla el ciclo principal, mostrando el menú y ejecutando la opción seleccionada por el usuario.
    """
    # Primero, verifica si se puede conectar a la base de datos.
    if not get_connection():
        return

    # Luego, intenta crear la tabla si no existe.
    if not create_table():
        print("No se pudo crear la tabla. Saliendo...")
        return

    while True:
        # Limpia la pantalla y muestra el menú.
        clear_screen()
        show_menu()

        try:
            # Solicita al usuario que elija una opción.
            option = input("\nSeleccione una opción (1-6): ")

            if option == "1":  # Listar tareas
                clear_screen()
                list_tasks()
                input("\nPresione Enter para continuar...")

            elif option == "2":  # Añadir tarea
                clear_screen()
                print("➕ Añadir Nueva Tarea")
                task = input("\nDescripción de la tarea: ").strip()
                if task:
                    add_task(task)
                else:
                    print("⚠️ La descripción no puede estar vacía")
                input("\nPresione Enter para continuar...")

            elif option == "3":  # Editar tarea
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
                    # 'ValueError' ocurre si el usuario ingresa algo que no es un número.
                    print("⚠️ Debe ingresar un número válido")
                input("\nPresione Enter para continuar...")

            elif option == "4":  # Marcar como completada
                clear_screen()
                list_tasks()
                try:
                    task_id = int(
                        input("\nID de la tarea a marcar como completada: "))
                    update_task(task_id, completed=True)
                except ValueError:
                    print("⚠️ Debe ingresar un número válido")
                input("\nPresione Enter para continuar...")

            elif option == "5":  # Eliminar tarea
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
                # Si el usuario ingresa una opción no válida, muestra un mensaje y espera un segundo.
                print("⚠️ Opción no válida. Intente nuevamente.")
                sleep(1)

        except KeyboardInterrupt:
            # 'KeyboardInterrupt' ocurre cuando el usuario presiona Ctrl+C.
            # Permite salir del programa de forma amigable.
            print("\n👋 ¡Hasta luego!")
            break


# Este bloque verifica si el archivo se está ejecutando directamente (no importado como módulo).
# Si es así, llama a la función principal 'main()'.
if __name__ == "__main__":
    main()
