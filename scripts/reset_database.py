import os
import sys
import logging

# Añadir el directorio raíz al path para importar desde app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config import settings
from app.database.database import engine, Base
from app.database.models import DBColorPalette, DBPixelArt, DBUserSettings
from app.services.palette import PaletteService
from sqlalchemy.orm import Session

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def reset_database():
    """
    Elimina y recrea la base de datos desde cero.
    """
    # Determinar la ruta del archivo SQLite
    if settings.DATABASE_URL.startswith('sqlite:///'):
        db_path = settings.DATABASE_URL.replace('sqlite:///', '')
        
        # Si la ruta es relativa, convertirla a absoluta
        if not os.path.isabs(db_path):
            db_path = os.path.abspath(db_path)
            
        logger.info(f"Base de datos SQLite detectada en: {db_path}")
        
        # Verificar si el archivo existe
        if os.path.exists(db_path):
            try:
                logger.info("Eliminando archivo de base de datos existente...")
                os.remove(db_path)
                logger.info("Archivo de base de datos eliminado correctamente")
            except Exception as e:
                logger.error(f"Error al eliminar archivo de base de datos: {str(e)}")
                return False
    else:
        logger.warning("No se detectó una base de datos SQLite. Este script solo funciona con SQLite.")
        return False
    
    try:
        # Crear nuevas tablas
        logger.info("Creando nuevas tablas en la base de datos...")
        Base.metadata.create_all(bind=engine)
        
        # Inicializar paletas predeterminadas
        from sqlalchemy.orm import sessionmaker
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            logger.info("Inicializando paletas predeterminadas...")
            PaletteService.initialize_default_palettes(db)
            logger.info("Paletas predeterminadas inicializadas correctamente")
        except Exception as e:
            logger.error(f"Error al inicializar paletas predeterminadas: {str(e)}")
        finally:
            db.close()
        
        logger.info("¡Base de datos reiniciada correctamente!")
        return True
    except Exception as e:
        logger.error(f"Error al reiniciar la base de datos: {str(e)}")
        return False

if __name__ == "__main__":
    print("¡ATENCIÓN! Este script eliminará todos los datos de la base de datos.")
    confirmation = input("¿Estás seguro de que deseas continuar? (escribe 'SI' para confirmar): ")
    
    if confirmation.strip().upper() == "SI":
        if reset_database():
            print("Base de datos reiniciada correctamente.")
        else:
            print("Error al reiniciar la base de datos.")
    else:
        print("Operación cancelada.")