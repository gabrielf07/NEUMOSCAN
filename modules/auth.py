# modules/auth.py
import hashlib
import re
from fastapi import HTTPException
import psycopg2
from modules.database import get_db_connection

# --- Funciones de Validación ---
def validar_email(email: str) -> bool:
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(patron, email) is not None

def validar_telefono(telefono: str) -> bool:
    return telefono.isdigit() and len(telefono) == 11 and telefono.startswith('04')

def validar_cedula(cedula: str) -> bool:
    return cedula.isdigit() and 8 <= len(cedula) <= 10

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# --- Funciones de Autenticación ---
def register_user(user_data: dict):
    # ... (Validaciones de contraseña, etc. como las tenías) ...
    if not all([user_data['primer_nombre'], user_data['primer_apellido'], user_data['cedula'],
                user_data['email'], user_data['password'], user_data['confirm_password'],
                user_data['telefono'], user_data['especialidad']]):
        raise HTTPException(status_code=400, detail="Faltan campos obligatorios")
    if user_data['password'] != user_data['confirm_password']:
         raise HTTPException(status_code=400, detail="Las contraseñas no coinciden")
    # ... (Añade el resto de tus validaciones aquí) ...

    hashed_pass = hash_password(user_data['password'])
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # En Postgres usamos RETURNING id para obtener el ID generado
        cursor.execute('''
            INSERT INTO usuarios (primer_nombre, segundo_nombre, primer_apellido, segundo_apellido, cedula, email, password, telefono, especialidad)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (user_data['primer_nombre'], user_data['segundo_nombre'], user_data['primer_apellido'],
              user_data['segundo_apellido'], user_data['cedula'], user_data['email'], hashed_pass,
              user_data['telefono'], user_data['especialidad']))
        
        user_id = cursor.fetchone()['id'] # RealDictCursor permite acceso por clave
        conn.commit()

        # Obtenemos el usuario recién creado
        cursor.execute('SELECT id, primer_nombre, primer_apellido, email, especialidad, cedula FROM usuarios WHERE id = %s', (user_id,))
        new_user = cursor.fetchone()
        return dict(new_user)
        
    except psycopg2.IntegrityError as e:
        conn.rollback() # Importante hacer rollback en Postgres si hay error
        error_msg = "Error desconocido de integridad"
        e_str = str(e)
        if "usuarios_email_key" in e_str or "email" in e_str: # Nombres de constraints por defecto en Postgres suelen incluir la columna
             error_msg = "El correo electrónico ya está registrado."
        elif "usuarios_cedula_key" in e_str or "cedula" in e_str:
             error_msg = "La cédula ya está registrada."
        elif "usuarios_telefono_key" in e_str or "telefono" in e_str:
             error_msg = "El teléfono ya está registrado."
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error en registro: {str(e)}")
    finally:
        conn.close()


def login_user(identificacion: str, password: str):
    hashed_pass = hash_password(password)
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, primer_nombre, primer_apellido, email, especialidad, cedula
            FROM usuarios
            WHERE (email = %s OR cedula = %s) AND password = %s AND activo = TRUE
        ''', (identificacion, identificacion, hashed_pass))
        user = cursor.fetchone()
        
        if user:
            return dict(user)
        else:
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
    finally:
        conn.close()
