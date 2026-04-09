# modules/patients.py
from fastapi import HTTPException
import psycopg2
from modules.database import get_db_connection
from modules.auth import validar_cedula, validar_telefono, validar_email # Reutilizamos validaciones

def add_new_patient(patient_data: dict):
    # Validaciones
    if not validar_cedula(patient_data['cedula']):
        raise HTTPException(status_code=400, detail="Cédula inválida")
    if not validar_telefono(patient_data['telefono']):
         raise HTTPException(status_code=400, detail="Teléfono inválido")
    if patient_data.get('email') and not validar_email(patient_data['email']):
         raise HTTPException(status_code=400, detail="Email inválido")

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM pacientes WHERE cedula = %s', (patient_data['cedula'],))
        if cursor.fetchone():
             raise HTTPException(status_code=400, detail="La cédula de este paciente ya está registrada.")

        cursor.execute('''
            INSERT INTO pacientes (doctor_id, primer_nombre, segundo_nombre, primer_apellido, segundo_apellido, cedula, telefono, email)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (patient_data['doctor_id'], patient_data['primer_nombre'], patient_data['segundo_nombre'],
              patient_data['primer_apellido'], patient_data['segundo_apellido'], patient_data['cedula'],
              patient_data['telefono'], patient_data.get('email')))
        conn.commit()
        return {"message": "Paciente registrado correctamente"}
    except psycopg2.IntegrityError:
         conn.rollback() # Siempre rollback en error con Postgres
         # Podríamos ser más específicos aquí si quisiéramos, pero por ahora mantenemos el mensaje genérico
         raise HTTPException(status_code=400, detail="Error: Cédula de paciente duplicada o error de integridad.")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno añadiendo paciente: {str(e)}")
    finally:
        conn.close()

def get_patients_by_doctor(doctor_id: int):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, primer_nombre, segundo_nombre, primer_apellido, segundo_apellido, cedula, telefono, email
            FROM pacientes
            WHERE doctor_id = %s
            ORDER BY primer_apellido, primer_nombre
        ''', (doctor_id,))
        patients = cursor.fetchall()
        # RealDictCursor devuelve objetos tipo diccionario, así que la conversión explícita
        # dict() en una comprensión de lista sigue siendo válida (aunque quizás redundante si ya son dicts)
        # pero asegura compatibilidad si retorna Rows. 
        return [dict(p) for p in patients]
    finally:
        conn.close()
