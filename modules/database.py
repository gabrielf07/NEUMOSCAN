# modules/database.py
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

# Cargar variables desde .env si existe
load_dotenv()

# Configuración de base de datos desde variables de entorno
# Se usan valores por defecto para desarrollo local si no están definidos
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "neumonia_db")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")
DB_PORT = os.environ.get("DB_PORT", "5432") # Puerto por defecto de Postgres

def get_db_connection():
    """Crea y retorna una conexión a la base de datos PostgreSQL."""
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
        cursor_factory=RealDictCursor # Para acceder a columnas por nombre
    )
    return conn

def init_db():
    """Inicializa las tablas de la base de datos si no existen."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Tabla de usuarios (médicos)
        c.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                primer_nombre TEXT NOT NULL,
                segundo_nombre TEXT,
                primer_apellido TEXT NOT NULL,
                segundo_apellido TEXT,
                cedula TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                telefono TEXT UNIQUE NOT NULL,
                especialidad TEXT NOT NULL,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                activo BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # Tabla para pacientes
        c.execute('''
            CREATE TABLE IF NOT EXISTS pacientes (
                id SERIAL PRIMARY KEY,
                doctor_id INTEGER NOT NULL,
                primer_nombre TEXT NOT NULL,
                segundo_nombre TEXT,
                primer_apellido TEXT NOT NULL,
                segundo_apellido TEXT,
                cedula TEXT UNIQUE NOT NULL,
                telefono TEXT NOT NULL,
                email TEXT,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (doctor_id) REFERENCES usuarios (id)
            )
        ''')
        
        # Tabla de Evaluaciones
        c.execute('''
            CREATE TABLE IF NOT EXISTS evaluaciones (
                id SERIAL PRIMARY KEY,
                paciente_id INTEGER NOT NULL,
                doctor_id INTEGER NOT NULL,
                fecha_evaluacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resultado_predicho TEXT NOT NULL,
                confianza REAL NOT NULL,
                FOREIGN KEY (paciente_id) REFERENCES pacientes (id),
                FOREIGN KEY (doctor_id) REFERENCES usuarios (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"Base de datos PostgreSQL '{DB_NAME}' inicializada/verificada en {DB_HOST}.")
        
    except Exception as e:
        print(f"Error inicializando la base de datos: {e}")
        print("Asegúrate de que PostgreSQL esté corriendo y las credenciales sean correctas.")

# Llama a init_db() una vez al inicio
if __name__ == "__main__":
    init_db()
else:
    # Intenta inicializar al importar
    pass