#app/main.py
import os
import logging
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.api import api_router
from app.config import settings
from app.database.database import get_db, engine
from app.database.models import Base
from app.services.palette import PaletteService
from app.database.migrations import run_migrations  # Importar el script de migración

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

origins = [
    "http://localhost:4200",  # Tu frontend de Angular
    "http://localhost:8000",  # Tu backend
    "*"  # Para desarrollo (quitar en producción)
]

logger = logging.getLogger(__name__)

# Crear las tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Ejecutar migraciones adicionales para actualizar el esquema
run_migrations()

# Inicializar la aplicación
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todas las URLs temporalmente
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Montar las carpetas estáticas para servir imágenes
app.mount("/images/results", StaticFiles(directory=settings.RESULTS_FOLDER), name="results")
app.mount("/images/uploads", StaticFiles(directory=settings.UPLOAD_FOLDER), name="uploads")

# Incluir rutas de la API
app.include_router(api_router, prefix=settings.API_PREFIX)

# Evento de inicio
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up PixelArt Generator API...")
    
    # Crear las carpetas necesarias si no existen
    os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(settings.RESULTS_FOLDER, exist_ok=True)
    
    # Inicializar paletas predeterminadas
    db = next(get_db())
    try:
        PaletteService.initialize_default_palettes(db)
        logger.info("Default palettes initialized")
    except Exception as e:
        logger.error(f"Error initializing default palettes: {str(e)}")
    finally:
        db.close()

# Ruta raíz
@app.get("/")
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": settings.DESCRIPTION,
    }

# Ruta de estado (health check)
@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    
    # Ejecutar el servidor
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )