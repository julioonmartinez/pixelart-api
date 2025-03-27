# app/config.py
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

class Settings(BaseSettings):
    API_PREFIX: str = os.getenv("API_PREFIX", "/api/v1")
    
    # Base de datos
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./pixelart.db")
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Carpetas para imágenes - MODIFICADO
    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", "./images/uploads")
    RESULTS_FOLDER: str = os.getenv("RESULTS_FOLDER", "./images/results")
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:4200", "https://localhost:4200"]
    
    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY: str = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET: str = os.getenv("CLOUDINARY_API_SECRET", "")
    USE_CLOUDINARY: bool = os.getenv("USE_CLOUDINARY", "True").lower() in ("true", "1", "t")
    DELETE_LOCAL_FILES_AFTER_UPLOAD: bool = os.getenv("DELETE_LOCAL_FILES_AFTER_UPLOAD", "True").lower() in ("true", "1", "t")
    
    # Configuración de la aplicación
    PROJECT_NAME: str = "PixelArt Generator API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "API para generar arte en píxeles a partir de imágenes o textos utilizando IA"


settings = Settings()

# Crear las carpetas necesarias si no existen
os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(settings.RESULTS_FOLDER, exist_ok=True)