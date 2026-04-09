# main.py
from fastapi import FastAPI, HTTPException, Path, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates # <-- Para servir HTML desde /templates
from pydantic import BaseModel
from typing import Optional
import os # <-- Importar OS para join

# Importar funciones de nuestros módulos
from modules.database import get_db_connection # init_db ya se llama en database.py
from modules.auth import register_user, login_user # Importamos SÓLO las funciones
# Eliminamos PatientRegister de aquí porque se definirá abajo
from modules.patients import add_new_patient, get_patients_by_doctor
from modules.ai_model import predict_pneumonia, pneumonia_model # Importamos el modelo y la función

app = FastAPI(title="NeumoAPI", description="API para sistema de detección de neumonía")

# --- Modelos Pydantic (DEFINIDOS AQUÍ) ---
# Estas clases le dicen a FastAPI cómo esperar los datos del frontend
class UserRegister(BaseModel):
    primer_nombre: str
    segundo_nombre: Optional[str] = ""
    primer_apellido: str
    segundo_apellido: Optional[str] = ""
    cedula: str
    email: str
    password: str
    confirm_password: str
    telefono: str
    especialidad: str

class UserLogin(BaseModel):
    identificacion: str
    password: str

class PatientRegister(BaseModel):
    doctor_id: int
    primer_nombre: str
    segundo_nombre: Optional[str] = ""
    primer_apellido: str
    segundo_apellido: Optional[str] = ""
    cedula: str
    telefono: str
    email: Optional[str] = ""

# --- Configuración (CORS, Estáticos, Templates) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)
# Servir archivos estáticos (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")
# Configurar Jinja2 para servir HTML desde la carpeta 'templates'
templates = Jinja2Templates(directory="templates")


# --- Rutas HTML ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("registro.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    # Aquí podrías pasar datos iniciales al dashboard si fuera necesario
    return templates.TemplateResponse("dashboards.html", {"request": request})


# --- Rutas API (Autenticación) ---
# FastAPI usa la clase UserRegister definida arriba para validar los datos que llegan
@app.post("/register")
async def register(user: UserRegister):
    try:
        # Pasamos los datos validados como diccionario a la función del módulo
        new_user = register_user(user.dict())
        return JSONResponse({
            "message": "Médico registrado correctamente",
            "user": new_user,
            "redirect_url": "/dashboard"
        })
    except HTTPException as e:
        raise e # Re-lanzar excepciones HTTP de validación
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno en registro: {str(e)}")

# FastAPI usa la clase UserLogin definida arriba
@app.post("/login")
async def login(user: UserLogin):
    try:
        logged_user = login_user(user.identificacion, user.password) # Usamos la función del módulo
        # Corregir nombres devueltos si es necesario para coincidir con JS
        user_response = {
             "id": logged_user['id'],
             "primer_nombre": logged_user['primer_nombre'], # Asegurar nombre correcto
             "primer_apellido": logged_user['primer_apellido'], # Asegurar nombre correcto
             "email": logged_user['email'],
             "especialidad": logged_user['especialidad'],
             "cedula": logged_user['cedula']
        }
        return JSONResponse({
            "message": "Inicio de sesión exitoso",
            "user": user_response,
            "redirect_url": "/dashboard"
        })
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno en login: {str(e)}")


# --- Rutas API (Pacientes) ---
# FastAPI usa la clase PatientRegister definida arriba
@app.post("/add-patient")
async def add_patient(patient: PatientRegister):
    try:
        result = add_new_patient(patient.dict()) # Usamos la función del módulo
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno añadiendo paciente: {str(e)}")


@app.get("/patients/{doctor_id}")
async def get_patients(doctor_id: int = Path(..., ge=1)):
    try:
        patient_list = get_patients_by_doctor(doctor_id) # Usamos la función del módulo
        return patient_list
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno obteniendo pacientes: {str(e)}")


# --- RUTA DE PREDICCIÓN IA --- 👈 ¡La Nueva Ruta!
@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    # Verificar si el modelo se cargó correctamente
    if pneumonia_model is None:
        raise HTTPException(status_code=503, detail="Modelo de IA no disponible. Contacta al administrador.")

    # Leer los bytes de la imagen
    image_bytes = await file.read()

    try:
        # Realizar la predicción usando la función del módulo ai_model
        prediction_result = predict_pneumonia(image_bytes)

        # Aquí podrías añadir lógica para guardar el resultado en la tabla 'evaluaciones'
        # conn = get_db_connection()
        # cursor = conn.cursor()
        # cursor.execute("INSERT INTO evaluaciones (paciente_id, doctor_id, resultado_predicho, confianza) VALUES (?, ?, ?, ?)",
        #                (id_del_paciente, id_del_doctor, prediction_result["resultado"], prediction_result["confianza"]))
        # conn.commit()
        # conn.close()

        # Devolver el resultado formateado
        return {
            "resultado": prediction_result["resultado"],
            "confianza": f"{prediction_result['confianza'] * 100:.2f}%",
            "detalle": {
                name: f"{prob * 100:.2f}%" for name, prob in prediction_result["detalle_prob"].items()
            },
            "heatmap_base64": prediction_result.get("heatmap_base64") # Usamos .get() por si es None
        }

    except ValueError as e: # Error de preprocesamiento
        raise HTTPException(status_code=400, detail=f"Error procesando imagen: {str(e)}")
    except RuntimeError as e: # Error si el modelo no está cargado
         raise HTTPException(status_code=500, detail=str(e))
    except Exception as e: # Otros errores durante la predicción
        print(f"Error inesperado en predicción: {e}") # Log para el servidor
        raise HTTPException(status_code=500, detail=f"Error interno durante la predicción.")


# --- Ruta de Salud ---
@app.get("/health")
async def health_check():
    return {"message": "API funcionando correctamente"}

# --- Evento Startup (No necesita init_db aquí) ---
@app.on_event("startup")
async def startup_event():
    # El modelo de IA ya se carga cuando se importa ai_model.py
    print("Servidor iniciado. Modelo de IA debería estar cargado si existe.")
    pass

# --- Ejecución (si corres este archivo directamente) ---
if __name__ == "__main__":
    import uvicorn
    print("Iniciando servidor en http://127.0.0.1:8000")
    # reload=True es útil para desarrollo, quítalo en producción
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)