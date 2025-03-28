# app/config.py
from pydantic_settings import BaseSettings
import os
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "PixelArt Generator API"
    DESCRIPTION: str = "API para generar y gestionar pixel art"
    VERSION: str = "0.2.0"
    API_PREFIX: str = "/api"
    
    # Base de datos SQLite (para compatibilidad con código existente)
    DATABASE_URL: str = "sqlite:///./pixelart.db"
    
    # Configuración MongoDB
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "pixelart_db")
    
    # Directorio para subidas y resultados
    UPLOAD_FOLDER: str = "./images/uploads"
    RESULTS_FOLDER: str = "./images/results"
    
    # Configuración OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Cloudinary
    USE_CLOUDINARY: bool = os.getenv("USE_CLOUDINARY", "False").lower() == "true"
    CLOUDINARY_CLOUD_NAME: str = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY: str = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET: str = os.getenv("CLOUDINARY_API_SECRET", "")
    DELETE_LOCAL_FILES_AFTER_UPLOAD: bool = True
    model_config = {
        "env_file": ".env",
        "extra": "ignore"  # Ignora campos extra que no estén definidos
    }

    # class Config:
    #     env_file = ".env"


settings = Settings()