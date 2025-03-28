import logging
from sqlalchemy.orm import Session
from app.database.mongodb import sync_pixel_arts_collection, sync_palettes_collection, sync_user_settings_collection
from app.database.models import DBPixelArt, DBColorPalette, DBUserSettings

logger = logging.getLogger(__name__)

class MigrationService:
    """Servicio para migrar datos desde SQLite a MongoDB"""
    
    @staticmethod
    def migrate_palettes(db: Session):
        """
        Migra todas las paletas de colores desde SQLite a MongoDB
        """
        try:
            # Obtener todas las paletas de SQLite
            sqlite_palettes = db.query(DBColorPalette).all()
            
            # Contar paletas migradas
            count = 0
            
            for palette in sqlite_palettes:
                # Convertir a diccionario para MongoDB
                palette_dict = {
                    "id": palette.id,
                    "name": palette.name,
                    "colors": palette.colors,
                    "description": palette.description,
                    "createdAt": palette.createdAt,
                    "updatedAt": palette.updatedAt
                }
                
                # Insertar en MongoDB (update_one con upsert=True para evitar duplicados)
                result = sync_palettes_collection.update_one(
                    {"id": palette.id},
                    {"$set": palette_dict},
                    upsert=True
                )
                
                if result.upserted_id or result.modified_count > 0:
                    count += 1
            
            logger.info(f"Migración completada: {count}/{len(sqlite_palettes)} paletas migradas a MongoDB")
            return count
        
        except Exception as e:
            logger.error(f"Error durante la migración de paletas: {str(e)}")
            return 0
    
    @staticmethod
    def migrate_pixel_arts(db: Session):
        """
        Migra todas las imágenes de pixel art desde SQLite a MongoDB
        """
        try:
            # Obtener todos los pixel arts de SQLite
            sqlite_pixel_arts = db.query(DBPixelArt).all()
            
            # Contar pixel arts migrados
            count = 0
            
            for pixel_art in sqlite_pixel_arts:
                # Convertir a diccionario para MongoDB
                pixel_art_dict = {
                    "id": pixel_art.id,
                    "name": pixel_art.name,
                    "imageUrl": pixel_art.imageUrl,
                    "thumbnailUrl": pixel_art.thumbnailUrl,
                    "width": pixel_art.width,
                    "height": pixel_art.height,
                    "pixelSize": pixel_art.pixelSize,
                    "style": pixel_art.style,
                    "backgroundType": pixel_art.backgroundType,
                    "animationType": pixel_art.animationType,
                    "isAnimated": pixel_art.isAnimated,
                    "paletteId": pixel_art.paletteId,
                    "tags": pixel_art.tags or [],
                    "description": pixel_art.description,
                    "createdAt": pixel_art.createdAt,
                    "updatedAt": pixel_art.updatedAt,
                    "cloudinaryPublicId": getattr(pixel_art, "cloudinaryPublicId", None)
                }
                
                # Insertar en MongoDB (update_one con upsert=True para evitar duplicados)
                result = sync_pixel_arts_collection.update_one(
                    {"id": pixel_art.id},
                    {"$set": pixel_art_dict},
                    upsert=True
                )
                
                if result.upserted_id or result.modified_count > 0:
                    count += 1
            
            logger.info(f"Migración completada: {count}/{len(sqlite_pixel_arts)} pixel arts migrados a MongoDB")
            return count
        
        except Exception as e:
            logger.error(f"Error durante la migración de pixel arts: {str(e)}")
            return 0
    
    @staticmethod
    def migrate_user_settings(db: Session):
        """
        Migra todas las configuraciones de usuario desde SQLite a MongoDB
        """
        try:
            # Obtener todas las configuraciones de usuario de SQLite
            sqlite_settings = db.query(DBUserSettings).all()
            
            # Contar configuraciones migradas
            count = 0
            
            for settings in sqlite_settings:
                # Convertir a diccionario para MongoDB
                settings_dict = {
                    "userId": settings.userId,
                    "pixelSize": settings.pixelSize,
                    "defaultStyle": settings.defaultStyle,
                    "defaultPalette": settings.defaultPalette,
                    "contrast": settings.contrast,
                    "sharpness": settings.sharpness,
                    "defaultBackground": settings.defaultBackground,
                    "defaultAnimationType": settings.defaultAnimationType,
                    "theme": settings.theme,
                    "createdAt": settings.createdAt,
                    "updatedAt": settings.updatedAt
                }
                
                # Insertar en MongoDB (update_one con upsert=True para evitar duplicados)
                result = sync_user_settings_collection.update_one(
                    {"userId": settings.userId},
                    {"$set": settings_dict},
                    upsert=True
                )
                
                if result.upserted_id or result.modified_count > 0:
                    count += 1
            
            logger.info(f"Migración completada: {count}/{len(sqlite_settings)} configuraciones de usuario migradas a MongoDB")
            return count
        
        except Exception as e:
            logger.error(f"Error durante la migración de configuraciones de usuario: {str(e)}")
            return 0
    
    @staticmethod
    def migrate_all_data(db: Session):
        """
        Migra todos los datos desde SQLite a MongoDB
        """
        palette_count = MigrationService.migrate_palettes(db)
        pixel_art_count = MigrationService.migrate_pixel_arts(db)
        settings_count = MigrationService.migrate_user_settings(db)
        
        return {
            "palettes": palette_count,
            "pixel_arts": pixel_art_count,
            "user_settings": settings_count
        }