#app/services/pixel_art.py
import os
import uuid
import logging
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from app.database.models import DBPixelArt, DBColorPalette
from app.models.pixel_art import PixelArt, PixelArtCreate, ColorPalette
from app.config import settings
from app.services.cloudinary_service import CloudinaryService

logger = logging.getLogger(__name__)

class PixelArtService:
    @staticmethod
    def get_pixel_arts(db: Session, skip: int = 0, limit: int = 100) -> List[DBPixelArt]:
        """
        Obtiene una lista de pixel arts desde la base de datos.
        """
        db_pixel_arts = db.query(DBPixelArt).offset(skip).limit(limit).all()
        return db_pixel_arts
    
    @staticmethod
    def get_pixel_art_by_id(db: Session, pixel_art_id: str) -> Optional[DBPixelArt]:
        """
        Obtiene un pixel art específico por su ID.
        """
        return db.query(DBPixelArt).filter(DBPixelArt.id == pixel_art_id).first()
    
    @staticmethod
    def create_pixel_art(
        db: Session, 
        pixel_art: PixelArtCreate, 
        image_data: Dict, 
        cloudinary_service: Optional[CloudinaryService] = None
    ) -> DBPixelArt:
        """
        Crea un nuevo pixel art en la base de datos.
        
        Args:
            db: Sesión de base de datos
            pixel_art: Datos del pixel art a crear
            image_data: Información de la imagen procesada (URLs, dimensiones)
            cloudinary_service: Servicio opcional de Cloudinary
            
        Returns:
            El nuevo objeto DBPixelArt creado
        """
        # Verificar si la paleta existe
        db_palette = db.query(DBColorPalette).filter(DBColorPalette.id == pixel_art.paletteId).first()
        if not db_palette:
            raise ValueError(f"Palette with ID {pixel_art.paletteId} not found")
        
        # Determinar los valores de imagen y miniatura
        image_url = image_data.get("image_url", "")
        thumbnail_url = image_data.get("thumbnail_url", image_url)
        width = image_data.get("width", 0)
        height = image_data.get("height", 0)
        
        # Si hay una ruta de archivo local y Cloudinary está disponible, subir a Cloudinary
        local_image_path = image_data.get("local_path", "")
        cloudinary_public_id = ""
        
        if local_image_path and os.path.exists(local_image_path) and settings.USE_CLOUDINARY and cloudinary_service:
            try:
                # Subir la imagen a Cloudinary
                is_result = True  # Asumimos que es una imagen resultado
                cloudinary_image_url, cloudinary_thumbnail_url, cloud_width, cloud_height = cloudinary_service.process_image_upload(
                    local_image_path, is_result
                )
                
                # Actualizar los valores
                image_url = cloudinary_image_url
                thumbnail_url = cloudinary_thumbnail_url
                
                # Extraer el ID público de la URL de Cloudinary
                if "cloudinary.com" in image_url:
                    parts = image_url.split("/")
                    if "upload" in parts:
                        idx = parts.index("upload")
                        if idx + 2 < len(parts):
                            cloudinary_public_id = parts[idx + 2].split(".")[0]
                
                # Usar las dimensiones de Cloudinary si están disponibles
                if cloud_width > 0 and cloud_height > 0:
                    width = cloud_width
                    height = cloud_height
                    
                logger.info(f"Image uploaded to Cloudinary: {image_url}")
                
            except Exception as e:
                logger.error(f"Error uploading to Cloudinary: {str(e)}. Using local path as fallback.")
                # Si hay un error, usamos la URL original como respaldo
        
        # Crear un diccionario con los valores básicos
        pixel_art_dict = {
            "id": str(uuid.uuid4()),
            "name": pixel_art.name,
            "imageUrl": image_url,
            "thumbnailUrl": thumbnail_url,
            "width": width,
            "height": height,
            "pixelSize": pixel_art.pixelSize,
            "style": pixel_art.style.value,
            "backgroundType": pixel_art.backgroundType.value,
            "animationType": pixel_art.animationType.value,
            "isAnimated": pixel_art.animationType != "none",
            "paletteId": pixel_art.paletteId,
            "tags": pixel_art.tags
        }
        
        # Añadir el ID de Cloudinary si está disponible
        if cloudinary_public_id:
            pixel_art_dict["cloudinaryPublicId"] = cloudinary_public_id
        
        # Crear el objeto de forma segura (sin hacer referencia a columnas que pueden no existir)
        db_pixel_art = DBPixelArt(**pixel_art_dict)
        
        # Añadir a la base de datos y guardar
        db.add(db_pixel_art)
        db.commit()
        db.refresh(db_pixel_art)
        
        return db_pixel_art
    
    @staticmethod
    def update_pixel_art(db: Session, pixel_art_id: str, updates: Dict) -> Optional[DBPixelArt]:
        """
        Actualiza un pixel art existente.
        
        Args:
            db: Sesión de base de datos
            pixel_art_id: ID del pixel art a actualizar
            updates: Diccionario con los campos a actualizar
            
        Returns:
            El objeto DBPixelArt actualizado o None si no se encuentra
        """
        db_pixel_art = PixelArtService.get_pixel_art_by_id(db, pixel_art_id)
        if not db_pixel_art:
            return None
            
        # Actualizar campos
        for key, value in updates.items():
            if hasattr(db_pixel_art, key):
                setattr(db_pixel_art, key, value)
        
        db.commit()
        db.refresh(db_pixel_art)
        return db_pixel_art
    
    @staticmethod
    def delete_pixel_art(
        db: Session, 
        pixel_art_id: str, 
        cloudinary_service: Optional[CloudinaryService] = None
    ) -> bool:
        """
        Elimina un pixel art de la base de datos.
        
        Args:
            db: Sesión de base de datos
            pixel_art_id: ID del pixel art a eliminar
            cloudinary_service: Servicio opcional de Cloudinary
            
        Returns:
            True si se eliminó correctamente, False si no se encontró
        """
        db_pixel_art = PixelArtService.get_pixel_art_by_id(db, pixel_art_id)
        if not db_pixel_art:
            return False
        
        # Si hay un ID de Cloudinary y el servicio está disponible, eliminar de Cloudinary
        if hasattr(db_pixel_art, 'cloudinaryPublicId') and db_pixel_art.cloudinaryPublicId and settings.USE_CLOUDINARY and cloudinary_service:
            try:
                cloudinary_service.delete_image(db_pixel_art.cloudinaryPublicId)
                logger.info(f"Deleted image from Cloudinary: {db_pixel_art.cloudinaryPublicId}")
            except Exception as e:
                logger.error(f"Error deleting image from Cloudinary: {str(e)}")
            
        # Intentar eliminar los archivos físicos locales (si existen)
        try:
            # Extraer nombre del archivo de las URLs
            image_file = os.path.basename(db_pixel_art.imageUrl)
            thumb_file = os.path.basename(db_pixel_art.thumbnailUrl)
            
            # Verificar si son rutas locales
            if not db_pixel_art.imageUrl.startswith('http'):
                # Construir rutas completas
                image_path = os.path.join(settings.RESULTS_FOLDER, image_file)
                
                # Eliminar archivos si existen
                if os.path.exists(image_path):
                    os.remove(image_path)
                    logger.info(f"Deleted local file: {image_path}")
            
            if not db_pixel_art.thumbnailUrl.startswith('http') and thumb_file != image_file:
                thumb_path = os.path.join(settings.RESULTS_FOLDER, thumb_file)
                if os.path.exists(thumb_path):
                    os.remove(thumb_path)
                    logger.info(f"Deleted local file: {thumb_path}")
                
        except Exception as e:
            logger.warning(f"Error removing image files for pixel art {pixel_art_id}: {str(e)}")
        
        # Eliminar de la base de datos
        db.delete(db_pixel_art)
        db.commit()
        return True