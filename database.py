import sqlite3
import os
from werkzeug.security import generate_password_hash # Importa para generar el hash de la contraseña

DATABASE = 'database.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    cursor = db.cursor()

    # Opcional: Elimina las tablas si ya existen (útil para desarrollo y para aplicar cambios de esquema)
    # cursor.execute("DROP TABLE IF EXISTS diagnosticos;")
    # cursor.execute("DROP TABLE IF EXISTS clientes;")
    # cursor.execute("DROP TABLE IF EXISTS users;") 

    # Crea la tabla de clientes con CI como PRIMARY KEY
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            ci TEXT PRIMARY KEY NOT NULL, -- CI como clave primaria y no nula
            nombre TEXT NOT NULL,
            telefono TEXT,
            email TEXT,
            direccion TEXT
        );
    """)

    # Crea la tabla de diagnosticos, referenciando cliente_ci
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS diagnosticos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_ci TEXT NOT NULL, -- Ahora referencia a la CI del cliente
            fecha_recepcion TEXT NOT NULL,
            tipo_equipo TEXT NOT NULL,
            marca TEXT,
            modelo TEXT,
            serial TEXT,
            componentes TEXT, -- Campo de componentes añadido
            accesorios_recibidos TEXT,
            problema_reportado TEXT NOT NULL,
            diagnostico_inicial TEXT,
            solucion_aplicada TEXT,
            piezas_reemplazadas TEXT,
            estado_final TEXT NOT NULL,
            fecha_entrega TEXT,
            costo_servicio REAL,
            observaciones_adicionales TEXT,
            FOREIGN KEY (cliente_ci) REFERENCES clientes(ci)
        );
    """)

    # Crea la tabla de usuarios para la autenticación
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user' -- 'admin' o 'user'
        );
    """)

    # --- Lógica para crear el usuario administrador por defecto ---
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]

    if user_count == 0:
        # Define las credenciales del admin por defecto
        # ¡ADVERTENCIA DE SEGURIDAD! Para producción, NO uses contraseñas hardcodeadas.
        # Usa variables de entorno o un sistema de configuración seguro.
        default_admin_username = "admin"
        default_admin_password = "adminpass" 
        
        # Genera el hash de la contraseña
        hashed_password = generate_password_hash(default_admin_password)
        
        # Inserta el usuario administrador por defecto
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (default_admin_username, hashed_password, 'admin')
        )
        print(f"Usuario administrador por defecto '{default_admin_username}' (contraseña: '{default_admin_password}') creado.")
    # --- Fin de la lógica del usuario admin por defecto ---

    db.commit()
    db.close()
    print("Base de datos inicializada correctamente con tablas clientes, diagnosticos y users.") # Mensaje de confirmación

if __name__ == '__main__':
    init_db()
