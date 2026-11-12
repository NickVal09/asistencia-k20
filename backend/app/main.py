import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import engine, Base
from app.models import Dispositivo, Trabajador, Marcacion, EjecucionSincronizacion  # Asegura registro de modelos
from app.api.v1.api import api_router

# Carpeta con la aplicación web compilada (npm run build).
# Por defecto: <raíz del proyecto>/frontend/dist
FRONTEND_DIST = Path(
    os.getenv("FRONTEND_DIST", Path(__file__).resolve().parents[2] / "frontend" / "dist")
).resolve()
FRONTEND_INDEX = FRONTEND_DIST / "index.html"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Verificación de conexión y creación de tablas si no existen.
    # Si MySQL aún no está listo (por ejemplo al iniciar Windows), se reintenta
    # sin impedir que el servidor web arranque: la interfaz mostrará el error
    # con su botón "Reintentar" en lugar de quedarse cargando.
    for intento in range(1, 6):
        try:
            Base.metadata.create_all(bind=engine)
            break
        except Exception as exc:  # noqa: BLE001
            print(f"[startup] MySQL no disponible (intento {intento}/5): {exc}")
            time.sleep(2)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API REST para consulta rápida, exportación y control de marcaciones históricas del biométrico ZKTeco K20.",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

# Enrutador principal
app.include_router(api_router, prefix=settings.API_V1_STR)


# Archivos estáticos compilados de Vue (JS, CSS, imágenes).
# Se registran antes de la ruta comodín para que el navegador los reciba directo.
if (FRONTEND_DIST / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")


@app.get("/", include_in_schema=False)
def root():
    """Si existe la web compilada se sirve la aplicación; si no, información de la API."""
    if FRONTEND_INDEX.is_file():
        return FileResponse(FRONTEND_INDEX, headers={"Cache-Control": "no-cache"})
    return {
        "sistema": settings.PROJECT_NAME,
        "version": "1.0.0",
        "estado": "operativo",
        "documentacion": f"{settings.API_V1_STR}/docs",
        "dispositivo_configurado": {
            "nombre": settings.ZK_DEVICE_NAME,
            "ip": settings.ZK_DEVICE_IP,
            "puerto": settings.ZK_DEVICE_PORT,
            "plataforma": settings.ZK_DEVICE_PLATFORM,
        }
    }


@app.get("/health", tags=["General"])
def health_check():
    return {"status": "ok", "environment": settings.ENVIRONMENT}


# Rutas internas de la API que nunca deben devolver la web (SPA).
_RUTAS_RESERVADAS = ("api", "health")


@app.get("/{full_path:path}", include_in_schema=False)
def frontend_spa(full_path: str):
    """Devuelve archivos de la web compilada o index.html para las rutas de Vue Router."""
    if full_path.startswith(_RUTAS_RESERVADAS):
        raise HTTPException(status_code=404, detail="Not Found")

    # Archivos reales (favicon, manifest, etc.) sin permitir salir de frontend/dist
    if full_path:
        objetivo = (FRONTEND_DIST / full_path).resolve()
        if objetivo.is_file() and FRONTEND_DIST in objetivo.parents:
            cache = "public, max-age=31536000, immutable" if full_path.startswith("assets/") else "no-cache"
            return FileResponse(objetivo, headers={"Cache-Control": cache})

    if FRONTEND_INDEX.is_file():
        return FileResponse(FRONTEND_INDEX, headers={"Cache-Control": "no-cache"})

    raise HTTPException(status_code=404, detail="Not Found")
