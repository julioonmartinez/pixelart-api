import os
import time
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
from typing import Tuple, List, Optional, Dict, Any
from app.config import settings  # This is your application settings
from app.models.pixel_art import PixelArtProcessSettings, BackgroundType, AnimationType
import logging

logger = logging.getLogger(__name__)

class ImageProcessingService:
    def __init__(self):
        # This ensures we have access to the application settings
        self.results_folder = settings.RESULTS_FOLDER
        
    def process_image(self, image_path: str, process_settings: PixelArtProcessSettings, palette_colors: List[str]) -> Optional[Dict[str, Any]]:
        """
        Procesa una imagen para convertirla en pixel art según las configuraciones.
        
        Args:
            image_path: Ruta a la imagen a procesar
            process_settings: Configuraciones de procesamiento
            palette_colors: Lista de colores hexadecimales para la paleta
            
        Returns:
            Diccionario con información de la imagen procesada o None si ocurre un error
        """
        try:
            logger.info(f"Processing image: {image_path}")
            logger.info(f"Using pixel size: {process_settings.pixelSize}")
            logger.info(f"Using palette with {len(palette_colors)} colors")
            
            # Abrir la imagen
            image = Image.open(image_path).convert("RGBA")
            
            # Ajustar contraste
            contrast_factor = process_settings.contrast / 50  # Normalizar a un factor (0.5-1.5)
            image = ImageEnhance.Contrast(image).enhance(contrast_factor)
            
            # Ajustar nitidez
            sharpness_factor = process_settings.sharpness / 50  # Normalizar a un factor (0.5-1.5)
            image = ImageEnhance.Sharpness(image).enhance(sharpness_factor)
            
            # Reducir a la resolución de pixel art
            w, h = image.size
            pixel_size = process_settings.pixelSize
            
            # Calcular nuevas dimensiones manteniendo la relación de aspecto
            new_w = max(1, w // pixel_size)
            new_h = max(1, h // pixel_size)
            
            # Redimensionar para "pixelar"
            pixelated = image.resize((new_w, new_h), Image.NEAREST)
            
            # Redimensionar de vuelta al tamaño original
            pixelated = pixelated.resize((w, h), Image.NEAREST)
            
            # Aplicar paleta de colores
            if palette_colors:
                pixelated = self._apply_color_palette(pixelated, palette_colors)
            
            # Manejar fondo
            if process_settings.backgroundType == BackgroundType.TRANSPARENT:
                # Asegurar que hay un canal alfa (transparencia)
                if pixelated.mode != 'RGBA':
                    pixelated = pixelated.convert('RGBA')
            
            # Generar nombre para la imagen de salida
            timestamp = int(time.time())
            output_filename = f"pixelart_{timestamp}.png"
            
            # Make sure the settings.RESULTS_FOLDER path exists
            os.makedirs(settings.RESULTS_FOLDER, exist_ok=True)
            
            output_path = os.path.join(settings.RESULTS_FOLDER, output_filename)
            logger.info(f"Saving pixelated image to: {output_path}")
            
            # Guardar imagen
            pixelated.save(output_path, "PNG")
            
            # Si es animada, crear la animación
            if process_settings.animationType != AnimationType.NONE:
                # Implementar la lógica de animación según el tipo
                # (Este sería un paso adicional para versiones futuras)
                pass
            
            # Crear thumbnail
            thumb_size = (150, 150)
            thumbnail = pixelated.copy()
            thumbnail.thumbnail(thumb_size)
            thumb_filename = f"thumb_{timestamp}.png"
            thumb_path = os.path.join(settings.RESULTS_FOLDER, thumb_filename)
            thumbnail.save(thumb_path, "PNG")
            
            # Return the relative URL paths for the frontend
            return {
                "image_url": f"/images/results/{output_filename}",
                "thumbnail_url": f"/images/results/{thumb_filename}",
                "width": new_w,
                "height": new_h
            }
            
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _apply_color_palette(self, image: Image.Image, palette_colors: List[str]) -> Image.Image:
        """
        Aplica una paleta de colores específica a la imagen.
        
        Args:
            image: Imagen PIL a procesar
            palette_colors: Lista de colores hex para usar como paleta
            
        Returns:
            Imagen con la paleta aplicada
        """
        try:
            # Convertir colores hex a RGB
            rgb_palette = [self._hex_to_rgb(color) for color in palette_colors]
            
            # Convertir la imagen a numpy array
            img_array = np.array(image)
            
            # Extraer los canales
            if img_array.shape[2] == 4:  # RGBA
                r, g, b, a = img_array[:, :, 0], img_array[:, :, 1], img_array[:, :, 2], img_array[:, :, 3]
            else:  # RGB
                r, g, b = img_array[:, :, 0], img_array[:, :, 1], img_array[:, :, 2]
                a = None
            
            # Crear una nueva imagen con los colores más cercanos de la paleta
            height, width = img_array.shape[:2]
            new_img = np.zeros((height, width, 4 if a is not None else 3), dtype=np.uint8)
            
            # Para cada píxel, encontrar el color más cercano en la paleta
            for y in range(height):
                for x in range(width):
                    if a is not None and a[y, x] < 128:
                        # Si es transparente, mantener la transparencia
                        new_img[y, x] = [0, 0, 0, 0]
                        continue
                    
                    # Convert to int to avoid overflow issues
                    pixel = [int(r[y, x]), int(g[y, x]), int(b[y, x])]
                    closest_color = self._find_closest_color(pixel, rgb_palette)
                    
                    if a is not None:
                        new_img[y, x] = [closest_color[0], closest_color[1], closest_color[2], a[y, x]]
                    else:
                        new_img[y, x] = closest_color
            
            # Convertir de vuelta a imagen PIL
            return Image.fromarray(new_img)
        except Exception as e:
            logger.error(f"Error applying color palette: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            # Return the original image if there was an error
            return image
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convierte un color hexadecimal a RGB."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _find_closest_color(self, pixel: List[int], palette: List[Tuple[int, int, int]]) -> Tuple[int, int, int]:
        """Encuentra el color más cercano en la paleta."""
        min_distance = float('inf')
        closest = palette[0]  # Default to first color
        
        for color in palette:
            # Calculate Euclidean distance, safely
            try:
                # Use a safer way to calculate distance
                distance = sum(((p - c) ** 2) for p, c in zip(pixel, color))
                
                if distance < min_distance:
                    min_distance = distance
                    closest = color
            except Exception as e:
                logger.error(f"Error calculating color distance: {str(e)}")
                # If there's an error, just continue with the next color
                continue
                
        return closest