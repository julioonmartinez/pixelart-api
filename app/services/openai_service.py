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
        
    def generate_from_prompt(self, prompt: str, settings: PixelArtProcessSettings) -> Optional[str]:
        """
        Generates pixel art from a text prompt using OpenAI DALL-E.
        
        Args:
            prompt: The descriptive prompt to generate the image
            settings: Processing configuration for the pixel art
            
        Returns:
            Local URL of the generated image or None if there was an error
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
                
            # Return the relative path for the frontend
            return f"/images/results/{image_filename}"
            
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
        # Get style description
        style_description = self._get_style_description(settings.style)
        
        # Get pixel size description
        pixel_size_desc = f"{settings.pixelSize}x{settings.pixelSize} pixels per block"
        
        # Get background description
        background_desc = self._get_background_description(settings.backgroundType)
        
        # Get animation description (if applicable)
        animation_desc = self._get_animation_description(settings.animationType)
        
        # Get color palette guidance (if palette is defined)
        palette_guidance = ""
        if hasattr(settings, 'paletteId') and settings.paletteId:
            palette_guidance = self._get_palette_guidance(settings.paletteId)
        
        # Get contrast and sharpness adjustments
        quality_adjustments = self._get_quality_adjustments(
            getattr(settings, 'contrast', 50), 
            getattr(settings, 'sharpness', 70)
        )
        
        # Build the complete prompt
        components = [
            f"Create a {style_description} pixel art with {pixel_size_desc}.",
            f"The image should ONLY depict: {prompt}.",
            background_desc,
            animation_desc,
            palette_guidance,
            quality_adjustments,
            "Make sure the result looks like authentic pixel art with clear, defined pixels.",
            "Do not add text, color palettes, rulers, or color swatches to the image.",
            "The image should only show the requested pixel art subject with no additional elements."
        ]
        
        # Remove empty components and join
        complete_prompt = " ".join([c for c in components if c])
        
        return complete_prompt
            
    def _get_style_description(self, style: PixelArtStyle) -> str:
        """
        Converts the style enum to a textual description for the prompt.
        """
        style_descriptions = {
            PixelArtStyle.RETRO_8BIT: "retro 8-bit style reminiscent of NES games with limited color palette, bold outlines, and simplified shapes",
            PixelArtStyle.MODERN_16BIT: "detailed modern 16-bit style similar to SNES games with more colors, smoother gradients, and finer details",
            PixelArtStyle.MINIMALIST: "minimalist pixel art with very limited colors (4-8 total), high contrast, and essential shapes only",
            PixelArtStyle.DITHERED: "pixel art with dithering patterns to create textured gradients and the illusion of more colors",
            PixelArtStyle.ISOMETRIC: "isometric perspective pixel art with 2:1 diamond-shaped pixels creating a 3D-like appearance"
        }
        
        return style_descriptions.get(style, "retro 8-bit style")
    
    def _get_background_description(self, background_type: BackgroundType) -> str:
        """
        Provides a description for the background type.
        """
        background_descriptions = {
            BackgroundType.TRANSPARENT: "Create the main subject only, with no background (transparent background).",
            BackgroundType.SOLID: "Use a simple solid color background that complements the main subject.",
            BackgroundType.GRADIENT: "Use a subtle gradient background that enhances the mood of the image.",
            BackgroundType.PATTERN: "Include a simple repeating pattern as background that fits the theme."
        }
        
        return background_descriptions.get(background_type, "")
    
    def _get_animation_description(self, animation_type: AnimationType) -> str:
        """
        Provides a description for the animation type, if applicable.
        """
        # Note: DALL-E can't generate actual animations, but we can suggest a frame
        # that implies the type of animation intended
        animation_descriptions = {
            AnimationType.NONE: "",
            AnimationType.BREATHING: "Design the image to suggest a breathing/pulsating effect (as a single frame).",
            AnimationType.FLICKERING: "Create the image with elements that suggest a flickering effect (as a single frame).",
            AnimationType.FLOATING: "Design elements that suggest floating/hovering motion (as a single frame)."
        }
        
        return animation_descriptions.get(animation_type, "")
    
    def _get_palette_guidance(self, palette_id: str) -> str:
        """
        Provides color palette guidance based on palette ID.
        """
        # Define common pixel art palettes
        palette_descriptions = {
            'gameboy': "Use only 4 shades of greenish-gray colors, similar to the original Game Boy palette for the entire image. DO NOT include a color palette chart or color swatches in the image itself.",
            'nes': "Use the NES color palette with limited but vibrant colors for the entire image. DO NOT show any color swatches or palette references within the image.",
            'commodore64': "Use the Commodore 64's distinctive 16-color palette with blues and purples for the pixel art. DO NOT include a color palette chart in the image.",
            'cga': "Use the CGA palette with its characteristic cyan, magenta, and black colors. DO NOT draw or include the palette itself in the image.",
            'pico8': "Use the PICO-8 fantasy console's 16-color palette with its distinctive look for the entire illustration. DO NOT include a visual color reference in the image.",
            'monochrome': "Use only black and white or a single color with different shades. DO NOT include any color reference swatches in the image.",
            'pastel': "Use soft, light pastel colors with low saturation. DO NOT show a palette or color guide within the image.",
            'cyberpunk': "Use neon colors like pink, cyan, and purple on dark backgrounds for a cyberpunk feel. DO NOT include a color palette visualization in the image."
        }
        
        return palette_descriptions.get(palette_id, "Use a cohesive and limited color palette appropriate for pixel art. DO NOT include a color palette chart or color swatches in the actual image.")
    
    def _get_quality_adjustments(self, contrast: int, sharpness: int) -> str:
        """
        Generates guidance for contrast and sharpness based on settings.
        """
        contrast_desc = ""
        if contrast < 30:
            contrast_desc = "with low contrast for a softer look"
        elif contrast > 70:
            contrast_desc = "with high contrast for a bold look"
            
        sharpness_desc = ""
        if sharpness < 30:
            sharpness_desc = "keep edges slightly soft"
        elif sharpness > 70:
            sharpness_desc = "ensure pixel edges are very crisp and well-defined"
            
        if contrast_desc and sharpness_desc:
            return f"Create the image {contrast_desc} and {sharpness_desc}."
        elif contrast_desc:
            return f"Create the image {contrast_desc}."
        elif sharpness_desc:
            return f"Create the image with {sharpness_desc}."
        else:
            return ""
async def process_image(self, image_path: str, settings: PixelArtProcessSettings) -> Optional[str]:
    """
    Processes an existing image to convert it into pixel art.
    
    Args:
        image_path: Local path to the image to process
        settings: Processing configuration for the pixel art
        
    Returns:
        Local URL of the processed image or None if there was an error
    """
    try:
        # Read the image and convert to base64
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Extract the filename without extension for reference in the prompt
        image_filename = os.path.basename(image_path).split(".")[0]
        
        # Get detailed style descriptions from settings
        style_description = self._get_style_description(settings.style)
        pixel_size_desc = f"{settings.pixelSize}x{settings.pixelSize} pixels per block"
        background_desc = self._get_background_description(settings.backgroundType)
        
        # Get animation description (if applicable)
        animation_desc = self._get_animation_description(settings.animationType)
        
        # Get color palette guidance (if palette is defined)
        palette_guidance = ""
        if hasattr(settings, 'paletteId') and settings.paletteId:
            palette_guidance = self._get_palette_guidance(settings.paletteId)
        
        # Get contrast and sharpness adjustments
        quality_adjustments = self._get_quality_adjustments(
            getattr(settings, 'contrast', 50), 
            getattr(settings, 'sharpness', 70)
        )
        
        # Build a comprehensive prompt for the transformation
        components = [
            f"Transform this image into authentic {style_description} pixel art with {pixel_size_desc}.",
            f"Preserve the main subject and composition of the original image, but recreate it completely in pixel art style.",
            "Make sure each pixel is clearly defined and visible.",
            background_desc,
            animation_desc,
            palette_guidance,
            quality_adjustments,
            "The result should look like genuine pixel art made of individual square pixels.",
            "Focus on clear silhouettes and recognizable forms.",
            "Simplify complex details while maintaining the essence of the original image.",
            "Do not add text, color palettes, rulers, or color swatches to the image."
        ]
        
        # Remove empty components and join
        complete_prompt = " ".join([c for c in components if c])
        
        logger.info(f"Processing image with prompt: {complete_prompt[:100]}...")
        print(f"Complete image processing prompt: {complete_prompt}")
        
        # Option 1: Try using the variation API (might work better for pixel art transformation)
        try:
            # First, try using DALL-E 3 with the image as a reference
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=complete_prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            
            # Get processed image URL
            processed_url = response.data[0].url
            
        except Exception as inner_e:
            logger.warning(f"DALL-E 3 generation failed, trying images.create_variation: {str(inner_e)}")
            
            # Fallback to image variation if that fails
            response = self.client.images.create_variation(
                image=base64_image,
                n=1,
                size="1024x1024"
            )
            
            processed_url = response.data[0].url
        
        # Download processed image
        image_data = httpx.get(processed_url).content
        
        # Save locally
        timestamp = int(time.time())
        processed_filename = f"processed_{timestamp}.png"
        processed_path = os.path.join(app_settings.RESULTS_FOLDER, processed_filename)
        
        with open(processed_path, "wb") as f:
            f.write(image_data)
            
        # Return relative path for the frontend
        return f"/images/results/{processed_filename}"
        
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        return None