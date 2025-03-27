#!/usr/bin/env python3
"""
Script para probar la integración con Cloudinary.
Sube una imagen de prueba y verifica que se puede acceder a ella.
"""

import os
import sys
import logging
import argparse
import requests
import tempfile
from pathlib import Path

# Añadir el directorio raíz al path para importar desde app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.cloudinary_service import CloudinaryService
from app.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def download_test_image(url="https://placekitten.com/200/300"):
    """Descarga una imagen de prueba desde placekitten.com."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        fd, path = tempfile.mkstemp(suffix=".jpg")
        with os.fdopen(fd, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        
        return path
    except Exception as e:
        logger.error(f"Error downloading test image: {str(e)}")
        return None

def create_test_image(size=(200, 300), color=(255, 0, 0)):
    """Crea una imagen de prueba utilizando PIL."""
    try:
        from PIL import Image
        
        fd, path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        
        img = Image.new('RGB', size, color=color)
        img.save(path)
        
        return path
    except ImportError:
        logger.warning("PIL not installed, skipping image creation")
        return None
    except Exception as e:
        logger.error(f"Error creating test image: {str(e)}")
        return None

def test_cloudinary_upload():
    """Prueba la carga de imágenes a Cloudinary."""
    # Verificar configuración
    if not all([
        settings.CLOUDINARY_CLOUD_NAME,
        settings.CLOUDINARY_API_KEY,
        settings.CLOUDINARY_API_SECRET
    ]):
        logger.error("Cloudinary configuration is incomplete. Check your .env file.")
        return False
    
    # Crear servicio de Cloudinary
    cloudinary_service = CloudinaryService()
    
    if not cloudinary_service.is_configured:
        logger.error("Cloudinary service initialization failed.")
        return False
    
    # Intentar obtener una imagen de prueba
    test_image_path = download_test_image()
    
    if not test_image_path:
        # Intentar crear una imagen si no se pudo descargar
        test_image_path = create_test_image()
    
    if not test_image_path:
        logger.error("Could not obtain a test image.")
        return False
    
    logger.info(f"Using test image: {test_image_path}")
    
    try:
        # Subir imagen a Cloudinary
        logger.info("Uploading image to Cloudinary...")
        image_url, thumbnail_url, width, height = cloudinary_service.process_image_upload(
            test_image_path, is_result=True
        )
        
        logger.info(f"Image uploaded successfully!")
        logger.info(f"Image URL: {image_url}")
        logger.info(f"Thumbnail URL: {thumbnail_url}")
        logger.info(f"Dimensions: {width}x{height}")
        
        # Verificar que se pueda acceder a la imagen
        logger.info("Testing image access...")
        
        image_response = requests.head(image_url)
        if image_response.status_code == 200:
            logger.info("✅ Image is accessible")
        else:
            logger.warning(f"⚠️ Image access test failed: {image_response.status_code}")
        
        thumbnail_response = requests.head(thumbnail_url)
        if thumbnail_response.status_code == 200:
            logger.info("✅ Thumbnail is accessible")
        else:
            logger.warning(f"⚠️ Thumbnail access test failed: {thumbnail_response.status_code}")
        
        return True
    except Exception as e:
        logger.error(f"Error during Cloudinary test: {str(e)}")
        return False
    finally:
        # Limpiar archivo temporal si aún existe
        if test_image_path and os.path.exists(test_image_path):
            os.remove(test_image_path)
            logger.info(f"Temporary file removed: {test_image_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Cloudinary integration")
    args = parser.parse_args()
    
    logger.info("Starting Cloudinary integration test...")
    
    if test_cloudinary_upload():
        logger.info("✅ Cloudinary integration test passed!")
        sys.exit(0)
    else:
        logger.error("❌ Cloudinary integration test failed!")
        sys.exit(1)