import cv2
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from tf_keras.models import load_model
from tf_keras.preprocessing import image
from PIL import Image
import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
import shutil
from fastapi.middleware.cors import CORSMiddleware
import io

app = FastAPI()

# Configurar la carpeta de plantillas y archivos estáticos
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="templates"), name="static")

# Habilitar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Puedes ajustar esto a los orígenes que desees permitir
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Acceder a la cámara
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("La cámara no pudo ser activada.")
    raise ValueError("No se puede acceder a la cámara")
else:
    print("La cámara está activa.")

# Generador para transmitir el video
def generate():
    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

# Cargar el modelo una sola vez al inicio
with tf.keras.utils.custom_object_scope({'KerasLayer': hub.KerasLayer}):
    modelo_cargado = load_model('../IA-Medica-Remota--main/breast_canser.h5')

# Mapeo de etiquetas
label = {0: "benign", 1: "malignant"}

# Ruta para la transmisión de video
@app.get("/video")
async def video_feed():
    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace;boundary=frame"
    )

# Ruta para la página principal
@app.get("/")
async def get_html(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Ruta para la carga y predicción de imágenes
@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Leer la imagen desde los datos recibidos
        contents = await file.read()
        img = Image.open(io.BytesIO(contents)).resize((244, 244))

        # Convertir la imagen a un array numpy
        imag = np.array(img)
        imag = np.expand_dims(imag, axis=0)

        # Realizar la predicción
        pred = modelo_cargado.predict(imag)
        pred = np.argmax(pred, axis=1)
        result = label[pred[0]]

        # Devolver el resultado en formato JSON
        return JSONResponse(content={"result": result})
    except Exception as e:
        return JSONResponse(content={"error": str(e)})