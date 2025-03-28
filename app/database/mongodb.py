import motor.motor_asyncio
import logging
from pymongo import MongoClient
from pymongo.collection import Collection
from app.config import settings

# Configuración de logging
logger = logging.getLogger(__name__)

# Cliente de MongoDB para operaciones asíncronas
async_client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL)
async_db = async_client[settings.MONGODB_DB_NAME]

# Cliente de MongoDB para operaciones síncronas
sync_client = MongoClient(settings.MONGODB_URL)
sync_db = sync_client[settings.MONGODB_DB_NAME]

# Colecciones
pixel_arts_collection = async_db.pixel_arts
palettes_collection = async_db.palettes
user_settings_collection = async_db.user_settings

# Colecciones síncronas (para compatibilidad con código existente)
sync_pixel_arts_collection = sync_db.pixel_arts
sync_palettes_collection = sync_db.palettes
sync_user_settings_collection = sync_db.user_settings

# Función para obtener una colección de MongoDB de manera síncrona
def get_collection(collection_name: str) -> Collection:
    return sync_db[collection_name]

# Inicializar índices en MongoDB
async def init_mongodb():
    try:
        # Crear índices para búsquedas rápidas
        await pixel_arts_collection.create_index("id", unique=True)
        await palettes_collection.create_index("id", unique=True)
        await user_settings_collection.create_index("userId", unique=True)
        
        # Índices adicionales para búsquedas comunes
        await pixel_arts_collection.create_index("tags")
        await pixel_arts_collection.create_index("paletteId")
        await pixel_arts_collection.create_index("style")
        
        logger.info("MongoDB: Índices inicializados correctamente")
    except Exception as e:
        logger.error(f"Error inicializando índices de MongoDB: {e}")