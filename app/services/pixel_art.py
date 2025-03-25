import os
import uuid
import logging
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from app.database.models import DBPixelArt, DBColorPalette
from app.models.pixel_art import PixelArt, PixelArtCreate, ColorPalette
from app.config import settings

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
    def create_pixel_art(db: Session, pixel_art: PixelArtCreate, image_data: Dict) -> DBPixelArt:
        """
        Crea un nuevo pixel art en la base de datos.
        
        Args:
            db: Sesión de base de datos
            pixel_art: Datos del pixel art a crear
            image_data: Información de la imagen procesada (URLs, dimensiones)
            
        Returns:
            El nuevo objeto DBPixelArt creado
        """
        # Verificar si la paleta existe
        db_palette = db.query(DBColorPalette).filter(DBColorPalette.id == pixel_art.paletteId).first()
        if not db_palette:
            raise ValueError(f"Palette with ID {pixel_art.paletteId} not found")
        
        # Crear el nuevo pixel art
        db_pixel_art = DBPixelArt(
            id=str(uuid.uuid4()),
            name=pixel_art.name,
            imageUrl=image_data["image_url"],
            thumbnailUrl=image_data["thumbnail_url"],
            width=image_data["width"],
            height=image_data["height"],
            pixelSize=pixel_art.pixelSize,
            style=pixel_art.style.value,
            backgroundType=pixel_art.backgroundType.value,
            animationType=pixel_art.animationType.value,
            isAnimated=pixel_art.animationType != "none",
            paletteId=pixel_art.paletteId,
            tags=pixel_art.tags
        )
        
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
    def delete_pixel_art(db: Session, pixel_art_id: str) -> bool:
        """
        Elimina un pixel art de la base de datos.
        
        Args:
            db: Sesión de base de datos
            pixel_art_id: ID del pixel art a eliminar
            
        Returns:
            True si se eliminó correctamente, False si no se encontró
        """
        db_pixel_art = PixelArtService.get_pixel_art_by_id(db, pixel_art_id)
        if not db_pixel_art:
            return False
            
        # Intentar eliminar los archivos físicos
        try:
            # Extraer nombre del archivo de las URLs
            image_file = os.path.basename(db_pixel_art.imageUrl)
            thumb_file = os.path.basename(db_pixel_art.thumbnailUrl)
            
            # Construir rutas completas
            image_path = os.path.join(settings.RESULTS_FOLDER, image_file)
            thumb_path = os.path.join(settings.RESULTS_FOLDER, thumb_file)
            
            # Eliminar archivos si existen
            if os.path.exists(image_path):
                os.remove(image_path)
            
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
                
        except Exception as e:
            logger.warning(f"Error removing image files for pixel art {pixel_art_id}: {str(e)}")
        
        # Eliminar de la base de datos
        db.delete(db_pixel_art)
        db.commit()
        return True