# verify_db.py
import sys
import os
from dotenv import load_dotenv

# Cargar variables de entorno explícitamente para este script
load_dotenv()

# Asegurar que el directorio actual está en el path para importar modules
sys.path.append(os.getcwd())

try:
    from modules.database import init_db, get_db_connection
    print("Intentando conectar a la base de datos...")
    
    # Intentar inicializar (crea tablas si no existen)
    init_db()
    
    # Verificar conexión simple
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1")
    result = cur.fetchone()
    print(f"Conexión exitosa. SELECT 1 result: {result}")
    
    # Verificar tablas
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    tables = [row['table_name'] for row in cur.fetchall()]
    print(f"Tablas encontradas: {tables}")
    
    expected_tables = {'usuarios', 'pacientes', 'evaluaciones'}
    if expected_tables.issubset(set(tables)):
        print("✅ Todas las tablas esperadas existen.")
    else:
        print(f"❌ Faltan tablas. Esperadas: {expected_tables}, Encontradas: {set(tables)}")

    conn.close()

except Exception as e:
    print(f"\n❌ Error conectando a PostgreSQL: {e}")
    print("\nVerifique sus variables de entorno:")
    print(f"DB_HOST: {os.environ.get('DB_HOST', 'localhost')}")
    print(f"DB_NAME: {os.environ.get('DB_NAME', 'neumonia_db')}")
    print(f"DB_USER: {os.environ.get('DB_USER', 'postgres')}")
    print(f"DB_PORT: {os.environ.get('DB_PORT', '5432')}")
    sys.exit(1)
