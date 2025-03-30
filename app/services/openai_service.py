#app/services/openai_service.py
import os
import time
import httpx
import base64
from openai import OpenAI
from app.config import settings as app_settings
from app.models.pixel_art import PixelArtStyle, BackgroundType, AnimationType, PixelArtProcessSettings
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.client = OpenAI(api_key=app_settings.OPENAI_API_KEY)
        
    def generate_from_prompt(self, prompt: str, settings: PixelArtProcessSettings) -> Optional[Dict]:
        """
        Generates pixel art from a text prompt using OpenAI DALL-E.
        
        Args:
            prompt: The descriptive prompt to generate the image
            settings: Processing configuration for the pixel art
            
        Returns:
            Dictionary with image data or None if there was an error
        """
        try:
            # Debug logs
            logger.debug(f"Using OpenAI API Key: {bool(app_settings.OPENAI_API_KEY)}")
            logger.debug(f"Original prompt: {prompt}")
            
            # Build a comprehensive prompt that incorporates all settings
            complete_prompt = self._build_comprehensive_prompt(prompt, settings)
            
            logger.info(f"Sending prompt to OpenAI: {complete_prompt[:100]}...")
            print(f"Complete prompt for OpenAI: {complete_prompt}")
            
            # Call OpenAI DALL-E 3 API
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=complete_prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            
            # Get the generated image URL
            image_url = response.data[0].url
            
            # Download the image
            image_data = httpx.get(image_url).content
            
            # Save the image locally
            os.makedirs(app_settings.RESULTS_FOLDER, exist_ok=True)
            timestamp = int(time.time())
            image_filename = f"prompt_{timestamp}.png"
            image_path = os.path.join(app_settings.RESULTS_FOLDER, image_filename)
            
            with open(image_path, "wb") as f:
                f.write(image_data)
                
            # Prepare the result data with local path for potential Cloudinary upload
            result = {
                "image_url": f"/images/results/{image_filename}",  # Relative path for the frontend
                "thumbnail_url": f"/images/results/{image_filename}",  # Same for thumbnail initially
                "width": 1024,  # Default DALL-E size
                "height": 1024,
                "local_path": image_path  # Add local path for Cloudinary upload
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating image from prompt: {str(e)}")
            return None
    
    def _build_comprehensive_prompt(self, prompt: str, settings: PixelArtProcessSettings) -> str:
        """
        Builds a comprehensive prompt that incorporates all pixel art settings.
        
        Args:
            prompt: The user's original descriptive prompt
            settings: Processing configuration for the pixel art
            
        Returns:
            A detailed prompt for DALL-E that incorporates all settings
        """
        # Obtener detalles del estilo pixel art solicitado
        style_info = self._get_style_info(settings.style)
        pixel_scale = settings.pixelSize
        
        # Obtener colores de la paleta
        palette_colors = self._get_palette_colors(settings.paletteId)
        color_codes = " ".join(palette_colors)
        
        # Obtener información sobre el fondo
        background_info = self._get_background_info(settings.backgroundType)
        
        # Crear una descripción compacta y específica
        background_directive = "transparent background" if settings.backgroundType == BackgroundType.TRANSPARENT else background_info

        # Prompt principal - evitando mencionar "paletas" o cualquier cosa relacionada con swatches
        main_prompt = f"Create a {style_info} pixel art character of a {prompt}, with {pixel_scale}x{pixel_scale} pixel blocks, on a {background_directive}. Color scheme: {color_codes}. Character only, no text, no UI elements."
        
        # Verificación adicional para asegurarse de que el prompt no mencione paletas
        final_prompt = main_prompt.replace("palette", "colors").replace("swatch", "colors").replace("color scheme display", "")
        
        return final_prompt
    
    def _get_style_info(self, style: PixelArtStyle) -> str:
        """
        Returns a simple description of the pixel art style.
        """
        style_info = {
            PixelArtStyle.RETRO_8BIT: "retro 8-bit NES-style",
            PixelArtStyle.MODERN_16BIT: "16-bit SNES-style",
            PixelArtStyle.MINIMALIST: "minimalist",
            PixelArtStyle.DITHERED: "dithered",
            PixelArtStyle.ISOMETRIC: "isometric"
        }
        return style_info.get(style, "classic")
    
    def _get_palette_colors(self, palette_id: str) -> list:
        """
        Returns the color codes for the specified palette.
        """
        palette_colors = {
            'gameboy': ["#0f380f", "#306230", "#8bac0f", "#9bbc0f"],
            'nes': ["#000000", "#fcfcfc", "#f8f8f8", "#bcbcbc", "#7c7c7c", "#a4000c"],
            'cga': ["#000000", "#555555", "#aaaaaa", "#ffffff", "#0000aa", "#5555ff"],
            'pico8': ["#000000", "#1D2B53", "#7E2553", "#008751", "#AB5236", "#5F574F"],
            'moody': ["#5e315b", "#8c3f5d", "#ba6156", "#f2a65a"]
        }
        
        return palette_colors.get(palette_id, ["#000000", "#333333", "#777777", "#ffffff"])
    
    def _get_background_info(self, background_type: BackgroundType) -> str:
        """
        Returns a simple description of the background.
        """
        background_info = {
            BackgroundType.TRANSPARENT: "transparent",
            BackgroundType.SOLID: "simple solid color",
            BackgroundType.GRADIENT: "subtle gradient",
            BackgroundType.PATTERN: "simple pattern"
        }
        return background_info.get(background_type, "simple")
    
    async def process_image(self, image_path: str, settings: PixelArtProcessSettings, palette_colors: list = None) -> Optional[Dict]:
        """
        Procesa una imagen existente para convertirla en pixel art.
        
        Args:
            image_path: Ruta local de la imagen a procesar
            settings: Configuración de procesamiento para el pixel art
            palette_colors: Lista opcional de colores de la paleta a usar
            
        Returns:
            Diccionario con los datos de la imagen procesada o None si hubo un error
        """
        try:
            # Leer la imagen
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Obtener estilo y configuración
            style_info = self._get_style_info(settings.style)
            pixel_scale = settings.pixelSize
            
            # Obtener colores de la paleta
            if palette_colors and len(palette_colors) > 0:
                colors = palette_colors
            else:
                colors = self._get_palette_colors(settings.paletteId)
            
            color_codes = " ".join(colors)
            
            # Crear un prompt simplificado
            prompt = f"Transform this image into a {style_info} pixel art with {pixel_scale}x{pixel_scale} pixel blocks. Colors to use: {color_codes}. Faithfully preserve the original subject but in pixel art style. No text, no UI elements."
            
            # Procesamiento
            try:
                # Usar DALL-E 3
                response = self.client.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    size="1024x1024",
                    quality="standard",
                    n=1,
                )
                
                processed_url = response.data[0].url
                
            except Exception as inner_e:
                logger.warning(f"DALL-E 3 generation failed, trying image variation: {str(inner_e)}")
                
                # Alternativa: variación de imagen
                response = self.client.images.create_variation(
                    image=open(image_path, "rb"),
                    n=1,
                    size="1024x1024"
                )
                
                processed_url = response.data[0].url
            
            # Descargar imagen procesada
            image_data = httpx.get(processed_url).content
            
            # Guardar localmente
            timestamp = int(time.time())
            processed_filename = f"processed_{timestamp}.png"
            processed_path = os.path.join(app_settings.RESULTS_FOLDER, processed_filename)
            
            with open(processed_path, "wb") as f:
                f.write(image_data)
            
            # Preparar resultado
            result = {
                "image_url": f"/images/results/{processed_filename}",
                "thumbnail_url": f"/images/results/{processed_filename}",
                "width": 1024,
                "height": 1024,
                "local_path": processed_path
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            return None
    async def update_image(self, image_path: str, prompt: str, settings: PixelArtProcessSettings, palette_colors: list = None) -> Optional[Dict]:
        """
        Actualiza una imagen de pixel art existente aplicando modificaciones según el prompt.
        Utiliza GPT-4 con visión para analizar la imagen y DALL-E 3 para generar la versión actualizada.
        
        Args:
            image_path: Ruta local de la imagen existente
            prompt: Texto que describe las modificaciones a realizar
            settings: Configuración de procesamiento para el pixel art
            palette_colors: Lista opcional de colores de la paleta a usar
                
        Returns:
            Diccionario con los datos de la imagen procesada o None si hubo un error
        """
        try:
            # Leer la imagen para convertir a base64
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Obtener estilo y configuración
            style_info = self._get_style_info(settings.style)
            pixel_scale = settings.pixelSize
            
            # Obtener colores de la paleta
            if palette_colors and len(palette_colors) > 0:
                colors = palette_colors
            else:
                colors = self._get_palette_colors(settings.paletteId)
            
            color_codes = " ".join(colors)
            
            # Paso 1: Usar GPT-4 con visión para analizar la imagen actual
            try:
                logger.info(f"Analyzing image with GPT-4 Vision: {image_path}")
                
                # Usar la versión actual de GPT-4 con capacidades de visión
                response_vision = self.client.chat.completions.create(
                    model="gpt-4o", # La última versión con capacidades de visión
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text", 
                                    "text": "Describe esta imagen de pixel art en detalle. Menciona el tema principal, estilo, colores, elementos importantes y cualquier característica destacable. Sé muy específico."
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/png;base64,{base64_image}"}
                                }
                            ]
                        }
                    ],
                    max_tokens=500
                )
                
                # Obtener la descripción de la imagen actual
                image_description = response_vision.choices[0].message.content
                logger.info(f"Image analysis complete. Description length: {len(image_description)}")
                
            except Exception as vision_error:
                logger.warning(f"GPT-4 Vision analysis failed: {str(vision_error)}, using simplified approach")
                # Crear una descripción genérica si la visión falla
                image_description = f"a pixel art image in {style_info} style with {pixel_scale}x{pixel_scale} pixel blocks"
            
            # Paso 2: Crear un prompt combinado para DALL-E 3
            detailed_prompt = (
                f"Based on the following detailed analysis, recreate the original pixel art image exactly: {image_description}. "
                f"Then, apply this specific modification without altering any other elements: {prompt}. "
                f"Ensure that the final image is almost identical to the original in composition, style, and elements, "
                f"maintaining the exact {style_info} pixel art style with {pixel_scale}x{pixel_scale} pixel blocks. "
                f"Use exclusively these colors: {color_codes}. "
                f"The only change should be the one described (e.g., adding a title 'los cabos'). "
                f"Do not alter any details other than the requested modification."
            )
            
            logger.info(f"Generating modified image with DALL-E 3 using prompt: {detailed_prompt[:100]}...")
            
            # Paso 3: Generar la imagen actualizada con DALL-E 3
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=detailed_prompt,
                size="1024x1024",
                quality="hd",  # Usar calidad HD para más detalle
                n=1,
            )
            
            processed_url = response.data[0].url
            logger.info("Successfully generated updated image with DALL-E 3")
            
            # Descargar imagen procesada
            image_data = httpx.get(processed_url).content
            
            # Guardar localmente
            timestamp = int(time.time())
            processed_filename = f"updated_{timestamp}.png"
            processed_path = os.path.join(app_settings.RESULTS_FOLDER, processed_filename)
            
            with open(processed_path, "wb") as f:
                f.write(image_data)
            
            # Preparar resultado
            result = {
                "image_url": f"/images/results/{processed_filename}",
                "thumbnail_url": f"/images/results/{processed_filename}",
                "width": 1024,
                "height": 1024,
                "local_path": processed_path
            }
            
            return result
                
        except Exception as e:
            logger.error(f"Error updating image: {str(e)}")
            return None