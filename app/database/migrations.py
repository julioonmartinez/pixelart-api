# app/database/migrations.py
import logging
from sqlalchemy import create_engine, text
from app.config import settings

logger = logging.getLogger(__name__)

def run_migrations():
    """
    Ejecuta las migraciones necesarias para actualizar el esquema de la base de datos.
    """
    try:
        # Conectar a la base de datos
        engine = create_engine(settings.DATABASE_URL)
        
        # Definir las columnas que debemos verificar y añadir si no existen
        # La tupla contiene (nombre_columna, tipo_sql)
        pixel_arts_columns = [
            ("description", "TEXT"),
            ("updatedAt", "DATETIME"),
            ("createdAt", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
            ("cloudinaryPublicId", "TEXT")
        ]
        
        # Añadir las columnas faltantes a la tabla pixel_arts
        with engine.connect() as conn:
            # Verificar las columnas existentes
            result = conn.execute(text("PRAGMA table_info(pixel_arts)"))
            existing_columns = [row[1] for row in result]
            
            # Añadir las columnas que faltan
            for column_name, column_type in pixel_arts_columns:
                if column_name not in existing_columns:
                    logger.info(f"Añadiendo columna '{column_name}' a la tabla pixel_arts")
                    conn.execute(text(f"ALTER TABLE pixel_arts ADD COLUMN {column_name} {column_type}"))
            
            # Verificar la existencia de la tabla user_settings
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='user_settings'"))
            if not result.fetchone():
                logger.info("Creando tabla user_settings")
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS user_settings (
                        userId TEXT PRIMARY KEY,
                        pixelSize INTEGER DEFAULT 8,
                        defaultStyle TEXT DEFAULT 'retro',
                        defaultPalette TEXT DEFAULT 'gameboy',
                        contrast INTEGER DEFAULT 50,
                        sharpness INTEGER DEFAULT 70,
                        defaultBackground TEXT DEFAULT 'transparent',
                        defaultAnimationType TEXT DEFAULT 'none',
                        theme TEXT DEFAULT 'dark',
                        createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updatedAt DATETIME
                    )
                """))
            else:
                # Verificar columnas en user_settings
                result = conn.execute(text("PRAGMA table_info(user_settings)"))
                existing_columns = [row[1] for row in result]
                
                user_settings_columns = [
                    ("createdAt", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
                    ("updatedAt", "DATETIME")
                ]
                
                for column_name, column_type in user_settings_columns:
                    if column_name not in existing_columns:
                        logger.info(f"Añadiendo columna '{column_name}' a la tabla user_settings")
                        conn.execute(text(f"ALTER TABLE user_settings ADD COLUMN {column_name} {column_type}"))
            
            conn.commit()
            
        logger.info("Migración completada con éxito")
        return True
    except Exception as e:
        logger.error(f"Error durante la migración: {str(e)}")
        return False