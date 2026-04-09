# modules/ai_model.py
import numpy as np
from tensorflow import keras 
from PIL import Image, ImageOps
import io
import os
import cv2  #  manipulación de imágenes
import tensorflow as tf 
import matplotlib.cm as cm 
import base64 

# --- Constantes ---
MODEL_DIR = os.path.join("data", "outputs")
MODEL_FILENAME = "models-weights-01-val_accuracy-1.00-val_loss-0.07.keras" 
MODEL_PATH = os.path.join(MODEL_DIR, MODEL_FILENAME)
IMG_SIZE = (224, 224) # Tamaño esperado por InceptionV3
CLASS_NAMES = ["NORMAL", "PNEUMONIA"] 
LAST_CONV_LAYER_NAME = "mixed10"

# --- Variable Global para el Modelo ---
pneumonia_model = None

def load_pneumonia_model():
    """Carga el modelo Keras en memoria. Se llama una vez al inicio."""
    global pneumonia_model
    if not os.path.exists(MODEL_PATH):
        print(f"ERROR CRÍTICO: Archivo del modelo no encontrado en {MODEL_PATH}")
        pneumonia_model = None
        return

    try:
        pneumonia_model = keras.models.load_model(MODEL_PATH)
        print(f"Modelo de IA cargado exitosamente desde {MODEL_PATH}")
    except Exception as e:
        print(f"ERROR: No se pudo cargar el modelo de IA. {e}")
        pneumonia_model = None

def preprocess_xray_image(image_bytes: bytes) -> np.ndarray:
    """Pre-procesa los bytes de una imagen para el modelo."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img = ImageOps.exif_transpose(img) # Corregir rotación EXIF

        # Convertir a RGB si no lo es
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Redimensionar
        img = img.resize(IMG_SIZE)

        # Convertir a array y normalizar (0-1)
        img_array = np.array(img) / 255.0

        # Añadir dimensión de batch (1, height, width, channels)
        img_array = np.expand_dims(img_array, axis=0)

        return img_array
    except Exception as e:
        print(f"Error preprocesando imagen: {e}")
        raise ValueError(f"No se pudo procesar la imagen: {e}") # R para fastapi
    
    

def predict_pneumonia(image_bytes: bytes) -> dict:
    """Realiza la predicción y genera heatmap si es neumonía."""
    global pneumonia_model
    if pneumonia_model is None:
        raise RuntimeError("El modelo de IA no está cargado o falló al cargar.")

    # 1. Preprocesar
    processed_image = preprocess_xray_image(image_bytes)

    # 2. Predecir
    prediction = pneumonia_model.predict(processed_image)
    score = prediction[0]
    predicted_class_index = np.argmax(score)
    predicted_class_name = CLASS_NAMES[predicted_class_index]
    confidence = float(score[predicted_class_index])

    # 3. Generar Heatmap (SIEMPRE, para ver zonas sospechosas incluso en NORMAL)
    heatmap_base64 = None
    if True: # Generar siempre
        try:
            print("DEBUG: Generando heatmap...")
            # Forzamos a ver la clase "PNEUMONIA" (índice 1) para ver riesgos
            target_index = CLASS_NAMES.index("PNEUMONIA") 
            heatmap_base64 = generate_and_overlay_heatmap(
                image_bytes, processed_image, pneumonia_model, target_index
            )
            print("DEBUG: Heatmap generado.")
        except Exception as e:
            print(f"ERROR: Falló la generación del heatmap: {e}")
            # No detenemos la predicción, solo no habrá heatmap

    # 4. Preparar resultado
    result = {
        "resultado": predicted_class_name,
        "confianza": confidence,
        "detalle_prob": {name: float(prob) for name, prob in zip(CLASS_NAMES, score)},
        "heatmap_base64": heatmap_base64 # Añadimos el heatmap (puede ser None)
    }
    return result

# ... (load_pneumonia_model() al final) ...


def make_gradcam_heatmap(img_array, model, last_conv_layer_name, pred_index=None):
    """Genera el heatmap de Grad-CAM para una imagen."""
    # Crear un submodelo desde la entrada hasta la última capa conv
    grad_model = tf.keras.models.Model(
        [model.inputs], [model.get_layer(last_conv_layer_name).output, model.output]
    )

    # Calcular gradientes de la clase predicha con respecto a la salida de la capa conv
    with tf.GradientTape() as tape:
        last_conv_layer_output, preds = grad_model(img_array)
        if pred_index is None:
            pred_index = tf.argmax(preds[0])
        class_channel = preds[:, pred_index]

    grads = tape.gradient(class_channel, last_conv_layer_output)

    # Pooling de gradientes y ponderación de canales
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
    last_conv_layer_output = last_conv_layer_output[0]
    heatmap = last_conv_layer_output @ pooled_grads[..., tf.newaxis]
    heatmap = tf.squeeze(heatmap)

    # Normalizar y aplicar ReLU
    heatmap = tf.maximum(heatmap, 0) / tf.math.reduce_max(heatmap)
    return heatmap.numpy()


def generate_and_overlay_heatmap(original_image_bytes, processed_img_array, model, pred_index):
    """Genera heatmap, lo superpone y lo codifica en Base64."""
    # 1. Generar el heatmap (escala de grises 0-1)
    heatmap = make_gradcam_heatmap(processed_img_array, model, LAST_CONV_LAYER_NAME, pred_index)

    # 2. Cargar imagen original (para superposición)
    try:
        img = Image.open(io.BytesIO(original_image_bytes))
        img = ImageOps.exif_transpose(img) # Corregir rotación EXIF para alineación perfecta
        if img.mode != "RGB":

            img = img.convert("RGB")
        # NO redimensionamos la imagen original aquí. Mantenemos su tamaño real.
        original_size = img.size # (width, height)
        img = keras.utils.img_to_array(img)
    except Exception as e:
        print(f"Error al recargar imagen original para heatmap: {e}")
        return None 

    # 3. Colorear el heatmap y REDIMENSIONARLO al tamaño original
    # Usamos un colormap (ej. 'jet') y lo convertimos a RGB
    heatmap_colored = cm.jet(heatmap)[..., :3] # Tomamos solo RGB, descartamos Alpha
    heatmap_jet = keras.utils.array_to_img(heatmap_colored)
    
    
    # AQUÍ es el cambio clave: redimensionamos el heatmap al tamaño de la imagen original
    # Usamos LANCZOS para mejor calidad de interpolación
    heatmap_jet = heatmap_jet.resize(original_size, resample=Image.LANCZOS) 
    heatmap_jet = keras.utils.img_to_array(heatmap_jet)

    # 4. Superponer heatmap sobre imagen original
    superimposed_img = heatmap_jet * 0.4 + img * 0.6 # 0.4 es la intensidad del heatmap
    superimposed_img = keras.utils.array_to_img(superimposed_img)

    # 5. Codificar la imagen superpuesta a Base64
    buffered = io.BytesIO()
    superimposed_img.save(buffered, format="PNG") # Guardar como PNG en memoria
    
    # Guardar localmente en la raíz del proyecto
    try:
        output_filename = "heatmap_result.png"
        superimposed_img.save(output_filename)
        print(f"DEBUG: Imagen con heatmap guardada en: {os.path.abspath(output_filename)}")
    except Exception as e:
        print(f"ERROR: No se pudo guardar la imagen localmente: {e}")

    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

    return img_str # Retornamos el string Base64

load_pneumonia_model()