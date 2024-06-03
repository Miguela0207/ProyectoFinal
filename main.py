import cv2
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

# Configurar la carpeta de plantillas y archivos estáticos
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="templates"), name="static")

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



