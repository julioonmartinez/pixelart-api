import os
import base64
from PIL import Image
from typing import Tuple, Optional
import io
import logging

logger = logging.getLogger(__name__)

def convert_image_to_base64(image_path: str) -> Optional[str]:
    """
    Convierte una imagen a cadena base64.
    
    Args:
        image_path: Ruta al archivo de imagen
        
    Returns:
        Cadena base64 o None si hay error
    """
    try:
        if not os.path.exists(image_path):
            logger.error(f"Image file not found at {image_path}")
            return None
            
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    except Exception as e:
        logger.error(f"Error converting image to base64: {str(e)}")
        return None

def get_image_dimensions(image_path: str) -> Optional[Tuple[int, int]]:
    """
    Obtiene las dimensiones de una imagen.
    
    Args:
        image_path: Ruta al archivo de imagen
        
    Returns:
        Tupla (ancho, alto) o None si hay error
    """
    try:
        with Image.open(image_path) as img:
            return img.size
    except Exception as e:
        logger.error(f"Error getting image dimensions: {str(e)}")
        return None

def create_thumbnail(image_path: str, max_size: Tuple[int, int] = (150, 150)) -> Optional[str]:
    """
    Crea una miniatura de una imagen.
    
    Args:
        image_path: Ruta al archivo de imagen original
        max_size: Tamaño máximo de la miniatura (ancho, alto)
        
    Returns:
        Ruta a la miniatura creada o None si hay error
    """
    try:
        if not os.path.exists(image_path):
            logger.error(f"Image file not found at {image_path}")
            return None
            
        # Generar nombre para el thumbnail
        filename, ext = os.path.splitext(image_path)
        thumb_path = f"{filename}_thumb{ext}"
        
        # Crear thumbnail
        with Image.open(image_path) as img:
            img.thumbnail(max_size)
            img.save(thumb_path)
            
        return thumb_path
    except Exception as e:
        logger.error(f"Error creating thumbnail: {str(e)}")
        return None

def convert_base64_to_image(base64_string: str, output_path: str) -> bool:
    """
    Convierte una cadena base64 a imagen y la guarda.
    
    Args:
        base64_string: Cadena base64 que representa la imagen
        output_path: Ruta donde guardar la imagen
        
    Returns:
        True si se guardó correctamente, False en caso contrario
    """
    try:
        # Eliminar prefijo de data URL si existe
        if "base64," in base64_string:
            base64_string = base64_string.split("base64,")[1]
            
        # Decodificar y guardar
        image_data = base64.b64decode(base64_string)
        with open(output_path, "wb") as f:
            f.write(image_data)
            
        return True
    except Exception as e:
        logger.error(f"Error converting base64 to image: {str(e)}")
        return False