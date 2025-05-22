# database.py

import sqlite3
import os

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

    db.commit()
    db.close()
    print("Base de datos inicializada correctamente con CI como clave primaria.")

if __name__ == '__main__':
    # Si ejecutas este archivo directamente, inicializará la base de datos
    init_db()