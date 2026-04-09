
# mainTEST.py
from fastapi import FastAPI, HTTPException, Path, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pymongo import MongoClient
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import random
import string
import os

# Importar funciones de nuestros módulos existentes
from modules.database import get_db_connection
from modules.auth import register_user as register_user_sql, login_user
from modules.patients import add_new_patient, get_patients_by_doctor
from modules.ai_model import predict_pneumonia, pneumonia_model

# from routes import RutaPrueba # Comentado porque no existe en el sistema actual

# Crea una instancia de la aplicación FastAPI.
app = FastAPI(title="NeumoAPI", description="API para sistema de detección de neumonía")

# --- Configuración de CORS ---
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# -------------------------

# --- Configuración de FastAPI-Mail (NUEVO) ---
# !! REEMPLAZA ESTOS VALORES CON TUS CREDENCIALES !!
conf = ConnectionConfig(
    MAIL_USERNAME = "projectneumonia@gmail.com",
    MAIL_PASSWORD = "aa11..**", # IMPORTANTE: Usa una contraseña de aplicación
    MAIL_FROM = "projectneumonia@gmail.com",
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)
# ----------------------------------

# --- Configuración de MongoDB (NUEVO) ---
Mongo_Uri = "mongodb://localhost:27017/"
DB_Name = "Pruebas"
Tabla_DB = "registro_Especialista"

client = MongoClient(Mongo_Uri)
db = client[DB_Name]
Coleccion = db[Tabla_DB]
# ----------------------------------

# Servir archivos estáticos (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")
# Configurar Jinja2 para servir HTML desde la carpeta 'templates'
templates = Jinja2Templates(directory="templates")


# --- Modelos de Pydantic (NUEVOS - MongoDB) ---
class User(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    usuario: str
    email: EmailStr # Pydantic validará que sea un email
    clave: str
    verified: bool = False
    verification_code: Optional[str] = None

    class Config:
        populate_by_name = True

class Especialista(BaseModel):
      id: Optional[str] = Field(alias="_id", default=None)
      PNombre : str
      SNombre : str
      PApellido : str
      SApellido : str
      Cedula : str
      Correo : EmailStr
      Tlf : str
      Contraseña : str
      Cargo: int
      Verificado: bool = False
      verification_code: Optional[str] = None
      
      class Config:
        populate_by_name = True


class VerificationData(BaseModel):
    Correo: EmailStr
    code: str

# --- Modelos Pydantic (EXISTENTES - SQL) ---
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

# ---------------------------------------

# --- Rutas HTML ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("registro.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    return templates.TemplateResponse("dashboards.html", {"request": request})


# --- Rutas API (Autenticación Principal - MongoDB & Email) ---

@app.post("/register", response_model=dict)
async def register_user_mongo(user: Especialista):
    # Verifica si el usuario o el email ya existen
    if Coleccion.find_one({"Correo": user.Correo}):
        raise HTTPException(status_code=400, detail="Email already registered")
    """if Coleccion.find_one({"usuario": user.usuario}):
        raise HTTPException(status_code=400, detail="Username already taken")"""

    code = ''.join(random.choices(string.digits, k=6))
    user.verification_code = code

    # Prepara el mensaje de correo
    message = MessageSchema(
        subject="Tu código de verificación",
        recipients=[user.Correo],
        body=f"Gracias por registrarte. Tu código de verificación es: {code}",
        subtype="html"
    )

    try:
        # Envía el correo
        fm = FastMail(conf)
        await fm.send_message(message)
    except Exception as e:
        # Si el correo falla, no se crea el usuario y se devuelve un error
        raise HTTPException(status_code=500, detail=f"Failed to send email: {e}")

    # Guarda el usuario no verificado en la base de datos
    Coleccion.insert_one(user.model_dump(by_alias=True, exclude=["id"]))

    return {"message": "Registration successful. Please check your email for the verification code."}

@app.post("/verify", response_model=dict)
async def verify_user(data: VerificationData):
    user = Coleccion.find_one({"Correo": data.Correo, "verification_code": data.code})

    if not user:
        raise HTTPException(status_code=400, detail="Invalid verification code or email.")

    Coleccion.update_one(
        {"_id": user["_id"]},
        {"$set": {"Verificado": True}, "$unset": {"verification_code": ""}}
    )

    return {"message": "Account verified successfully!"}


# --- Rutas API (Autenticación Legada - SQL) ---
# Renombrada a /register-sql para evitar conflicto con la nueva ruta /register
@app.post("/register-sql")
async def register_sql(user: UserRegister):
    try:
        # Pasamos los datos validados como diccionario a la función del módulo
        new_user = register_user_sql(user.dict())
        return JSONResponse({
            "message": "Médico registrado correctamente",
            "user": new_user,
            "redirect_url": "/dashboard"
        })
    except HTTPException as e:
        raise e 
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno en registro: {str(e)}")

@app.post("/login")
async def login(user: UserLogin):
    try:
        logged_user = login_user(user.identificacion, user.password) # Usamos la función del módulo
        user_response = {
             "id": logged_user['id'],
             "primer_nombre": logged_user['primer_nombre'],
             "primer_apellido": logged_user['primer_apellido'],
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
@app.post("/add-patient")
async def add_patient(patient: PatientRegister):
    try:
        result = add_new_patient(patient.dict())
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno añadiendo paciente: {str(e)}")

@app.get("/patients/{doctor_id}")
async def get_patients(doctor_id: int = Path(..., ge=1)):
    try:
        patient_list = get_patients_by_doctor(doctor_id)
        return patient_list
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno obteniendo pacientes: {str(e)}")


# --- RUTA DE PREDICCIÓN IA ---
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

        # Devolver el resultado formateado
        return {
            "resultado": prediction_result["resultado"],
            "confianza": f"{prediction_result['confianza'] * 100:.2f}%",
            "detalle": {
                name: f"{prob * 100:.2f}%" for name, prob in prediction_result["detalle_prob"].items()
            },
            "heatmap_base64": prediction_result.get("heatmap_base64")
        }

    except ValueError as e: 
        raise HTTPException(status_code=400, detail=f"Error procesando imagen: {str(e)}")
    except RuntimeError as e: 
         raise HTTPException(status_code=500, detail=str(e))
    except Exception as e: 
        print(f"Error inesperado en predicción: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno durante la predicción.")


# --- Ruta de Salud ---
@app.get("/health")
async def health_check():
    return {"message": "API funcionando correctamente"}

# --- Evento Startup ---
@app.on_event("startup")
async def startup_event():
    print("Servidor iniciado con mainTEST. Modelo de IA debería estar cargado si existe.")
    pass

# app.include_router(RutaPrueba.router, prefix="/testt") # Comentado

if __name__ == "__main__":
    import uvicorn
    print("Iniciando servidor de PRUEBA (mainTEST) en http://127.0.0.1:8000")
    uvicorn.run("mainTEST:app", host="127.0.0.1", port=8000, reload=True)
