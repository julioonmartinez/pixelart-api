import os
import logging
import cloudinary
import cloudinary.uploader
import cloudinary.api
from typing import Optional, Dict, Any, Tuple
from app.config import settings

logger = logging.getLogger(__name__)

class CloudinaryService:
    """Servicio para gestionar la carga y recuperación de imágenes en Cloudinary."""
    
    def __init__(self):
        """Inicializa la configuración de Cloudinary con las credenciales de las variables de entorno."""
        self.is_configured = False
        try:
            cloudinary.config(
                cloud_name=settings.CLOUDINARY_CLOUD_NAME,
                api_key=settings.CLOUDINARY_API_KEY,
                api_secret=settings.CLOUDINARY_API_SECRET,
                secure=True
            )
            self.is_configured = True
            logger.info("Cloudinary service initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Cloudinary service: {str(e)}")
    
    def upload_image(self, file_path: str, folder: str = "pixel_arts", public_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Sube una imagen a Cloudinary.
        
        Args:
            file_path: Ruta local de la imagen a subir
            folder: Carpeta en Cloudinary donde se almacenará la imagen
            public_id: ID público personalizado para la imagen (opcional)
            
        Returns:
            Diccionario con los datos de la imagen subida, incluyendo URLs
            
        Raises:
            Exception: Si hay un error al subir la imagen
        """
        if not self.is_configured:
            raise ValueError("Cloudinary service is not properly configured")
            
        try:
            upload_options = {
                "folder": folder,
                "overwrite": True,
                "resource_type": "image",
                "use_filename": True,
                "unique_filename": True
            }
            
            # Si se proporciona un public_id, usarlo
            if public_id:
                upload_options["public_id"] = public_id
                
            # Subir la imagen a Cloudinary
            result = cloudinary.uploader.upload(file_path, **upload_options)
            
            logger.info(f"Image successfully uploaded to Cloudinary: {result.get('public_id')}")
            
            return {
                "public_id": result.get("public_id"),
                "url": result.get("secure_url"),
                "resource_type": result.get("resource_type"),
                "width": result.get("width"),
                "height": result.get("height"),
                "format": result.get("format"),
                "created_at": result.get("created_at")
            }
            
        except Exception as e:
            logger.error(f"Error uploading image to Cloudinary: {str(e)}")
            raise
    
    def create_thumbnail(self, public_id: str, width: int = 200, height: int = 200) -> str:
        """
        Genera una URL para una versión en miniatura de la imagen.
        
        Args:
            public_id: ID público de la imagen en Cloudinary
            width: Ancho deseado para la miniatura
            height: Alto deseado para la miniatura
            
        Returns:
            URL de la miniatura generada
        """
        try:
            # Determinar la extensión original, si es posible
            formato = "png"  # Por defecto
            if "." in public_id:
                formato = public_id.split(".")[-1]
            
            # Generar URL de thumbnail usando transformaciones de Cloudinary
            thumbnail_url = cloudinary.CloudinaryImage(public_id).build_url(
                width=width,
                height=height,
                crop="fill",
                quality="auto",
                format=formato  # Especificar formato para asegurar que tenga extensión
            )
            
            return thumbnail_url
            
        except Exception as e:
            logger.error(f"Error creating thumbnail for image {public_id}: {str(e)}")
            # Retornar None o una URL por defecto
            return ""
    
    def delete_image(self, public_id: str) -> bool:
        """
        Elimina una imagen de Cloudinary.
        
        Args:
            public_id: ID público de la imagen en Cloudinary
            
        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        if not self.is_configured:
            raise ValueError("Cloudinary service is not properly configured")
            
        try:
            result = cloudinary.uploader.destroy(public_id)
            
            if result.get("result") == "ok":
                logger.info(f"Image {public_id} successfully deleted from Cloudinary")
                return True
            else:
                logger.warning(f"Failed to delete image {public_id} from Cloudinary: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting image {public_id} from Cloudinary: {str(e)}")
            return False
    
    def process_image_upload(self, local_file_path: str, is_result: bool = True) -> Tuple[str, str, int, int]:
        """
        Procesa la carga de una imagen y devuelve los datos necesarios para guardar en la base de datos.
        
        Args:
            local_file_path: Ruta local de la imagen
            is_result: Indica si es una imagen resultado (True) o una subida por el usuario (False)
            
        Returns:
            Tupla (image_url, thumbnail_url, width, height)
        """
        try:
            # Determinar la carpeta en Cloudinary según el tipo de imagen
            folder = "results" if is_result else "uploads"
            
            # Extraer nombre de archivo para el public_id
            filename = os.path.basename(local_file_path)
            name_without_ext = os.path.splitext(filename)[0]
            
            # Subir la imagen a Cloudinary con timestamp para evitar duplicados
            import time
            timestamp = int(time.time())
            custom_public_id = f"{name_without_ext}_{timestamp}"
            
            # Subir la imagen a Cloudinary
            upload_result = self.upload_image(
                local_file_path, 
                folder=folder,
                public_id=custom_public_id
            )
            
            # Obtener la URL de la imagen
            image_url = upload_result.get("url")
            
            # Obtener datos de dimensiones
            width = upload_result.get("width", 0)
            height = upload_result.get("height", 0)
            
            # Crear thumbnail
            public_id = upload_result.get("public_id")
            thumbnail_size = min(width, height, 300)  # Limitar tamaño máximo de thumbnail
            thumbnail_url = self.create_thumbnail(public_id, width=thumbnail_size, height=thumbnail_size)
            
            # Limpiar el archivo local si es una imagen resultado (opcional)
            if is_result and os.path.exists(local_file_path) and settings.DELETE_LOCAL_FILES_AFTER_UPLOAD:
                try:
                    os.remove(local_file_path)
                    logger.info(f"Local file {local_file_path} removed after Cloudinary upload")
                except Exception as e:
                    logger.warning(f"Failed to remove local file {local_file_path}: {str(e)}")
            
            return image_url, thumbnail_url, width, height
            
        except Exception as e:
            logger.error(f"Error processing image upload: {str(e)}")
            # En caso de error, retornar la ruta local como fallback
            filename = os.path.basename(local_file_path)
            base_url = "/images/results" if is_result else "/images/uploads"
            fallback_url = f"{base_url}/{filename}"
            
            return fallback_url, fallback_url, 0, 0
    
    def get_cloudinary_data(self, public_id: str) -> Dict[str, Any]:
        """
        Obtiene información detallada sobre una imagen de Cloudinary.
        
        Args:
            public_id: ID público de la imagen en Cloudinary
            
        Returns:
            Diccionario con los detalles de la imagen o un diccionario vacío si hay un error
        """
        if not self.is_configured:
            raise ValueError("Cloudinary service is not properly configured")
            
        try:
            # Consultar detalles de la imagen
            result = cloudinary.api.resource(public_id)
            
            return {
                "public_id": result.get("public_id"),
                "url": result.get("secure_url"),
                "resource_type": result.get("resource_type"),
                "format": result.get("format"),
                "width": result.get("width"),
                "height": result.get("height"),
                "bytes": result.get("bytes"),
                "created_at": result.get("created_at"),
                "tags": result.get("tags", [])
            }
            
        except Exception as e:
            logger.error(f"Error retrieving image data from Cloudinary for {public_id}: {str(e)}")
            return {}
    
    def add_tag(self, public_id: str, tag: str) -> bool:
        """
        Añade una etiqueta a una imagen en Cloudinary.
        
        Args:
            public_id: ID público de la imagen en Cloudinary
            tag: Etiqueta a añadir
            
        Returns:
            True si se añadió correctamente, False en caso contrario
        """
        if not self.is_configured:
            raise ValueError("Cloudinary service is not properly configured")
            
        try:
            result = cloudinary.uploader.add_tag(tag, [public_id])
            
            if result.get("public_ids"):
                logger.info(f"Tag '{tag}' added to image {public_id}")
                return True
            else:
                logger.warning(f"Failed to add tag '{tag}' to image {public_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error adding tag to image: {str(e)}")
            return False
    
    def generate_gallery_urls(self, public_ids: list, width: int = 300, height: int = 300) -> list:
        """
        Genera URLs de miniaturas para una galería de imágenes.
        
        Args:
            public_ids: Lista de IDs públicos de imágenes en Cloudinary
            width: Ancho deseado para las miniaturas
            height: Alto deseado para las miniaturas
            
        Returns:
            Lista de URLs de miniaturas
        """
        if not self.is_configured:
            raise ValueError("Cloudinary service is not properly configured")
            
        thumbnail_urls = []
        
        for public_id in public_ids:
            try:
                thumbnail_url = self.create_thumbnail(public_id, width, height)
                thumbnail_urls.append({
                    "public_id": public_id,
                    "thumbnail_url": thumbnail_url
                })
            except Exception as e:
                logger.error(f"Error generating thumbnail for {public_id}: {str(e)}")
                
        return thumbnail_urls
    
    def search_images(self, tags: list = None, folder: str = None, limit: int = 100) -> list:
        """
        Busca imágenes en Cloudinary por etiquetas y/o carpeta.
        
        Args:
            tags: Lista de etiquetas para filtrar (opcional)
            folder: Carpeta donde buscar (opcional)
            limit: Número máximo de resultados
            
        Returns:
            Lista de imágenes encontradas
        """
        if not self.is_configured:
            raise ValueError("Cloudinary service is not properly configured")
            
        try:
            # Construir expresión de búsqueda
            expression = ""
            
            if folder:
                expression += f"folder={folder}"
                
            if tags:
                for tag in tags:
                    if expression:
                        expression += " AND "
                    expression += f"tags={tag}"
            
            # Si no hay expresión, buscar todas las imágenes
            if not expression:
                expression = "resource_type:image"
                
            # Realizar búsqueda
            result = cloudinary.Search().expression(expression).max_results(limit).execute()
            
            return result.get("resources", [])
            
        except Exception as e:
            logger.error(f"Error searching images in Cloudinary: {str(e)}")
            return []