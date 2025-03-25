import os
import uuid
import shutil
from typing import List
from venv import logger
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, Query, Request
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.pixel_art import (
    PixelArt, PixelArtCreate, PixelArtList, 
    PixelArtPromptRequest, PixelArtProcessSettings
)
from app.services.pixel_art import PixelArtService
from app.services.openai_service import OpenAIService
from app.services.image_processing import ImageProcessingService
from app.services.palette import PaletteService
from app.api.deps import (
    get_pixel_art_service, 
    get_openai_service, 
    get_image_processing_service,
    get_palette_service
)
from app.config import settings

router = APIRouter()

# Obtener todos los pixel arts
@router.get("/", response_model=PixelArtList)
def get_pixel_arts(
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db),
    pixel_art_service: PixelArtService = Depends(get_pixel_art_service)
):
    """
    Obtiene una lista de todos los pixel arts.
    """
    pixel_arts = pixel_art_service.get_pixel_arts(db, skip=skip, limit=limit)
    return {"items": pixel_arts, "total": len(pixel_arts)}

# Obtener un pixel art específico
@router.get("/{pixel_art_id}", response_model=PixelArt)
def get_pixel_art(
    pixel_art_id: str,
    db: Session = Depends(get_db),
    pixel_art_service: PixelArtService = Depends(get_pixel_art_service)
):
    """
    Obtiene un pixel art específico por su ID.
    """
    pixel_art = pixel_art_service.get_pixel_art_by_id(db, pixel_art_id)
    if not pixel_art:
        raise HTTPException(status_code=404, detail="Pixel art not found")
    return pixel_art

# Crear un nuevo pixel art desde un prompt
@router.post("/generate-from-prompt", response_model=PixelArt)
async def generate_from_prompt(
    request: PixelArtPromptRequest,
    db: Session = Depends(get_db),
    openai_service: OpenAIService = Depends(get_openai_service),
    pixel_art_service: PixelArtService = Depends(get_pixel_art_service),
    palette_service: PaletteService = Depends(get_palette_service)
):
    """
    Genera un nuevo pixel art a partir de un prompt utilizando IA.
    """
    # Obtener la paleta
    palette = palette_service.get_palette_by_id(db, request.settings.paletteId)
    print(palette)
    print(request.settings)
    if not palette:
        raise HTTPException(status_code=404, detail=f"Palette with id {request.settings.paletteId} not found")
    
    # Generar la imagen con OpenAI
    image_url = openai_service.generate_from_prompt(request.prompt, request.settings)
    
    if not image_url:
        raise HTTPException(status_code=500, detail="Failed to generate image from prompt")
    
    # Preparar datos para crear el pixel art
    pixel_art_data = PixelArtCreate(
        name=f"Generated from: {request.prompt[:30]}...",
        pixelSize=request.settings.pixelSize,
        style=request.settings.style,
        backgroundType=request.settings.backgroundType,
        paletteId=request.settings.paletteId,
        animationType=request.settings.animationType,
        tags=["ai-generated", "prompt"]
    )
    
    # Obtener dimensiones (para una implementación real, esto vendría del procesamiento de la imagen)
    img_width = 64  # Valores de ejemplo
    img_height = 64
    
    # Crear el registro en la base de datos
    image_data = {
        "image_url": image_url,
        "thumbnail_url": image_url,  # En un entorno real, se generaría un thumbnail específico
        "width": img_width,
        "height": img_height
    }
    
    pixel_art = pixel_art_service.create_pixel_art(db, pixel_art_data, image_data)
    return pixel_art

# Procesar una imagen subida
# In your pixel_art_router.py file, update the process_image endpoint

@router.post("/process-image", response_model=PixelArt)
async def process_image(
    file: UploadFile = File(...),
    name: str = Form(...),
    pixelSize: int = Form(8),
    style: str = Form("retro"),
    paletteId: str = Form("gameboy"),
    contrast: int = Form(50),
    sharpness: int = Form(70),
    backgroundType: str = Form("transparent"),
    animationType: str = Form("none"),
    tags: str = Form(""),
    db: Session = Depends(get_db),
    image_processing_service: ImageProcessingService = Depends(get_image_processing_service),
    pixel_art_service: PixelArtService = Depends(get_pixel_art_service),
    palette_service: PaletteService = Depends(get_palette_service)
):
    """
    Procesa una imagen subida para convertirla en pixel art.
    """
    # Validar el formato de la imagen
    valid_formats = [".jpg", ".jpeg", ".png", ".webp"]
    file_ext = os.path.splitext(file.filename or "unknown.png")[1].lower()
    
    if file_ext not in valid_formats:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file format. Supported formats: {', '.join(valid_formats)}"
        )
    
    # Ensure upload folder exists
    os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
    
    # Guardar la imagen subida temporalmente
    temp_filename = f"{uuid.uuid4()}{file_ext}"
    temp_file_path = os.path.join(settings.UPLOAD_FOLDER, temp_filename)
    
    try:
        # Log what we're doing
        logger.info(f"Saving uploaded file to: {temp_file_path}")
        
        # Guardar el archivo
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Obtener la paleta
        palette = palette_service.get_palette_by_id(db, paletteId)
        if not palette:
            raise HTTPException(status_code=404, detail=f"Palette with id {paletteId} not found")
        
        # Crear settings para el procesamiento
        process_settings = PixelArtProcessSettings(
            pixelSize=pixelSize,
            style=style,
            paletteId=paletteId,
            contrast=contrast,
            sharpness=sharpness,
            backgroundType=backgroundType,
            animationType=animationType
        )
        
        logger.info(f"Created process settings: {process_settings}")
        
        # Procesar la imagen
        processed_image_data = image_processing_service.process_image(
            temp_file_path, 
            process_settings,
            palette.colors
        )
        
        if not processed_image_data:
            logger.error("Failed to process image: No data returned from image processing service")
            raise HTTPException(status_code=500, detail="Failed to process image")
        
        # Preparar datos para crear el pixel art
        tag_list = [tag.strip() for tag in tags.split(",")] if tags else []
        pixel_art_data = PixelArtCreate(
            name=name,
            pixelSize=pixelSize,
            style=style,
            backgroundType=backgroundType,
            paletteId=paletteId,
            animationType=animationType,
            tags=tag_list
        )
        
        # Crear el registro en la base de datos
        pixel_art = pixel_art_service.create_pixel_art(db, pixel_art_data, processed_image_data)
        return pixel_art
        
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Asegurar que limpiamos el archivo temporal en caso de error
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")
    
    finally:
        # Limpiar el archivo temporal
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as e:
                logger.error(f"Error removing temporary file: {str(e)}")

# Actualizar un pixel art
@router.put("/{pixel_art_id}", response_model=PixelArt)
def update_pixel_art(
    pixel_art_id: str,
    pixel_art_update: dict,
    db: Session = Depends(get_db),
    pixel_art_service: PixelArtService = Depends(get_pixel_art_service)
):
    """
    Actualiza un pixel art existente.
    """
    updated_pixel_art = pixel_art_service.update_pixel_art(db, pixel_art_id, pixel_art_update)
    if not updated_pixel_art:
        raise HTTPException(status_code=404, detail="Pixel art not found")
    return updated_pixel_art

# Eliminar un pixel art
@router.delete("/{pixel_art_id}")
def delete_pixel_art(
    pixel_art_id: str,
    db: Session = Depends(get_db),
    pixel_art_service: PixelArtService = Depends(get_pixel_art_service)
):
    """
    Elimina un pixel art existente.
    """
    success = pixel_art_service.delete_pixel_art(db, pixel_art_id)
    if not success:
        raise HTTPException(status_code=404, detail="Pixel art not found")
    return {"message": "Pixel art deleted successfully"}

@router.post("/test-prompt", status_code=200)
async def test_prompt(request: dict):
    """
    Endpoint de prueba para verificar que los prompts llegan correctamente.
    """
    print("Solicitud de prueba recibida:", request)
    return {
        "status": "success", 
        "message": "Test exitoso", 
        "received_data": request
    }