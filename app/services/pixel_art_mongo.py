#app/services/pixel_art_mongo.py
import os
import uuid
import logging
from typing import List, Optional, Dict, Union
from datetime import datetime
from app.database.mongodb import sync_pixel_arts_collection, sync_palettes_collection
from app.models.pixel_art import PixelArt, PixelArtCreate, ColorPalette
from app.config import settings
from app.services.cloudinary_service import CloudinaryService

logger = logging.getLogger(__name__)

class PixelArtMongoService:
    """Servicio para gestionar pixel arts en MongoDB"""
    
    @staticmethod
    def get_pixel_arts(skip: int = 0, limit: int = 100) -> List[Dict]:
        """
        Obtiene una lista de pixel arts desde MongoDB, incluyendo la información de la paleta.
        """
        pixel_arts = list(sync_pixel_arts_collection.find().skip(skip).limit(limit))
        
        # Obtener todas las paletas disponibles para hacer una búsqueda eficiente
        all_palettes = {p["id"]: p for p in sync_palettes_collection.find()}
       
        
        # Agregar el campo palette a cada pixel art
        for art in pixel_arts:
            if "paletteId" in art and art["paletteId"] in all_palettes:
                # Si encontramos la paleta, la agregamos al objeto
                art["palette"] = all_palettes[art["paletteId"]]
            else:
                # Si no encontramos la paleta, creamos una por defecto
                default_palette = {
                    "id": art.get("paletteId", "default"),
                    "name": art.get("paletteId", "Default").capitalize(),
                    "colors": ["#0f380f", "#306230", "#8bac0f", "#9bbc0f"]  # Colores Gameboy por defecto
                }
                art["palette"] = default_palette
        print(pixel_arts)
        return pixel_arts
    
    @staticmethod
    def get_pixel_art_by_id(pixel_art_id: str) -> Optional[Dict]:
        """
        Obtiene un pixel art específico por su ID.
        """
        return sync_pixel_arts_collection.find_one({"id": pixel_art_id})
    
    @staticmethod
    def create_pixel_art(
        pixel_art: PixelArtCreate, 
        image_data: Dict, 
        cloudinary_service: Optional[CloudinaryService] = None
    ) -> Dict:
        """
        Crea un nuevo pixel art en MongoDB.
        
        Args:
            pixel_art: Datos del pixel art a crear
            image_data: Información de la imagen procesada (URLs, dimensiones)
            cloudinary_service: Servicio opcional de Cloudinary
            
        Returns:
            El nuevo objeto pixel art creado como diccionario
        """
        # Verificar si la paleta existe
        db_palette = sync_palettes_collection.find_one({"id": pixel_art.paletteId})
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
        
        # Preparar el documento para MongoDB
        now = datetime.now()
        pixel_art_id = str(uuid.uuid4())
        
        pixel_art_doc = {
            "id": pixel_art_id,
            "name": pixel_art.name,
            "imageUrl": image_url,
            "thumbnailUrl": thumbnail_url,
            "width": width,
            "height": height,
            "pixelSize": pixel_art.pixelSize,
            "style": pixel_art.style,
            "backgroundType": pixel_art.backgroundType,
            "animationType": pixel_art.animationType,
            "isAnimated": pixel_art.animationType != "none",
            "paletteId": pixel_art.paletteId,
            "tags": pixel_art.tags or [],
            "description": None,
            "createdAt": now,
            "updatedAt": now
        }
        
        # Añadir el ID de Cloudinary si está disponible
        if cloudinary_public_id:
            pixel_art_doc["cloudinaryPublicId"] = cloudinary_public_id
        
        # Insertar en MongoDB
        sync_pixel_arts_collection.insert_one(pixel_art_doc)
        
        # Añadir la información de la paleta al resultado (para mantener compatibilidad con el modelo Pydantic)
        palette = {
            "id": db_palette["id"],
            "name": db_palette["name"],
            "colors": db_palette["colors"]
        }
        
        pixel_art_doc["palette"] = palette
        
        return pixel_art_doc
    
    @staticmethod
    def update_pixel_art(pixel_art_id: str, updates: Dict) -> Optional[Dict]:
        """
        Actualiza un pixel art existente.
        
        Args:
            pixel_art_id: ID del pixel art a actualizar
            updates: Diccionario con los campos a actualizar
            
        Returns:
            El objeto pixel art actualizado o None si no se encuentra
        """
        # Verificar si existe
        existing = PixelArtMongoService.get_pixel_art_by_id(pixel_art_id)
        if not existing:
            return None
        
        # Preparar las actualizaciones
        updates["updatedAt"] = datetime.now()
        
        # Actualizar en MongoDB
        sync_pixel_arts_collection.update_one(
            {"id": pixel_art_id},
            {"$set": updates}
        )
        
        # Obtener el documento actualizado
        updated = PixelArtMongoService.get_pixel_art_by_id(pixel_art_id)
        
        # Añadir la información de la paleta
        if updated:
            palette = sync_palettes_collection.find_one({"id": updated["paletteId"]})
            if palette:
                updated["palette"] = {
                    "id": palette["id"],
                    "name": palette["name"],
                    "colors": palette["colors"]
                }
        
        return updated
    
    @staticmethod
    def delete_pixel_art(
        pixel_art_id: str, 
        cloudinary_service: Optional[CloudinaryService] = None
    ) -> bool:
        """
        Elimina un pixel art de MongoDB.
        
        Args:
            pixel_art_id: ID del pixel art a eliminar
            cloudinary_service: Servicio opcional de Cloudinary
            
        Returns:
            True si se eliminó correctamente, False si no se encontró
        """
        # Verificar si existe
        existing = PixelArtMongoService.get_pixel_art_by_id(pixel_art_id)
        if not existing:
            return False
        
        # Si hay un ID de Cloudinary y el servicio está disponible, eliminar de Cloudinary
        if "cloudinaryPublicId" in existing and existing["cloudinaryPublicId"] and settings.USE_CLOUDINARY and cloudinary_service:
            try:
                cloudinary_service.delete_image(existing["cloudinaryPublicId"])
                logger.info(f"Deleted image from Cloudinary: {existing['cloudinaryPublicId']}")
            except Exception as e:
                logger.error(f"Error deleting image from Cloudinary: {str(e)}")
        
        # Intentar eliminar los archivos físicos locales (si existen)
        try:
            # Extraer nombre del archivo de las URLs
            image_file = os.path.basename(existing["imageUrl"])
            thumb_file = os.path.basename(existing["thumbnailUrl"])
            
            # Verificar si son rutas locales
            if not existing["imageUrl"].startswith('http'):
                # Construir rutas completas
                image_path = os.path.join(settings.RESULTS_FOLDER, image_file)
                
                # Eliminar archivos si existen
                if os.path.exists(image_path):
                    os.remove(image_path)
                    logger.info(f"Deleted local file: {image_path}")
            
            if not existing["thumbnailUrl"].startswith('http') and thumb_file != image_file:
                thumb_path = os.path.join(settings.RESULTS_FOLDER, thumb_file)
                if os.path.exists(thumb_path):
                    os.remove(thumb_path)
                    logger.info(f"Deleted local file: {thumb_path}")
                
        except Exception as e:
            logger.warning(f"Error removing image files for pixel art {pixel_art_id}: {str(e)}")
        
        # Eliminar de MongoDB
        result = sync_pixel_arts_collection.delete_one({"id": pixel_art_id})
        return result.deleted_count > 0
    
    @staticmethod
    def search_pixel_arts(
        tags: Optional[List[str]] = None,
        style: Optional[str] = None,
        palette_id: Optional[str] = None,
        search_term: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Dict:
        """
        Busca pixel arts con filtros diversos.
        
        Args:
            tags: Lista de etiquetas para filtrar
            style: Estilo de pixel art
            palette_id: ID de la paleta
            search_term: Término de búsqueda para el nombre
            skip: Número de documentos a saltar
            limit: Límite de resultados
            
        Returns:
            Diccionario con items y total
        """
        # Construir el filtro
        filter_query = {}
        
        if tags:
            filter_query["tags"] = {"$in": tags}
        
        if style:
            filter_query["style"] = style
        
        if palette_id:
            filter_query["paletteId"] = palette_id
        
        if search_term:
            filter_query["name"] = {"$regex": search_term, "$options": "i"}
        
        # Ejecutar la consulta
        cursor = sync_pixel_arts_collection.find(filter_query).skip(skip).limit(limit)
        items = list(cursor)
        
        # Obtener el total
        total = sync_pixel_arts_collection.count_documents(filter_query)
        
        # Añadir información de paletas a los resultados
        for item in items:
            palette = sync_palettes_collection.find_one({"id": item["paletteId"]})
            if palette:
                item["palette"] = {
                    "id": palette["id"],
                    "name": palette["name"],
                    "colors": palette["colors"]
                }
        
        return {
            "items": items,
            "total": total
        }