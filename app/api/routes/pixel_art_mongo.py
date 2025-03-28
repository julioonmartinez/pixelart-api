import os
import uuid
import shutil
from typing import List, Optional
from venv import logger
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, Query, Request
from app.models.pixel_art import (
    PixelArt, PixelArtCreate, PixelArtList, 
    PixelArtPromptRequest, PixelArtProcessSettings
)
from app.services.pixel_art_mongo import PixelArtMongoService
from app.services.openai_service import OpenAIService
from app.services.image_processing import ImageProcessingService
from app.services.palette_mongo import PaletteMongoService
from app.services.cloudinary_service import CloudinaryService
from app.api.deps import (
    get_openai_service, 
    get_image_processing_service,
    get_cloudinary_service,
    get_pixel_art_mongo_service,
    get_palette_mongo_service
)
from app.config import settings

router = APIRouter()

# Obtener todos los pixel arts
@router.get("/", response_model=PixelArtList)
def get_pixel_arts(
    skip: int = 0, 
    limit: int = 100,
    pixel_art_service: PixelArtMongoService = Depends(get_pixel_art_mongo_service)
):
    """
    Obtiene una lista de todos los pixel arts.
    """
    result = pixel_art_service.get_pixel_arts(skip=skip, limit=limit)
    return {"items": result, "total": len(result)}

# Obtener un pixel art específico
@router.get("/{pixel_art_id}", response_model=PixelArt)
def get_pixel_art(
    pixel_art_id: str,
    pixel_art_service: PixelArtMongoService = Depends(get_pixel_art_mongo_service)
):
    """
    Obtiene un pixel art específico por su ID.
    """
    pixel_art = pixel_art_service.get_pixel_art_by_id(pixel_art_id)
    if not pixel_art:
        raise HTTPException(status_code=404, detail="Pixel art not found")
    return pixel_art

# Crear un nuevo pixel art desde un prompt
@router.post("/generate-from-prompt", response_model=PixelArt)
async def generate_from_prompt(
    request: PixelArtPromptRequest,
    openai_service: OpenAIService = Depends(get_openai_service),
    pixel_art_service: PixelArtMongoService = Depends(get_pixel_art_mongo_service),
    palette_service: PaletteMongoService = Depends(get_palette_mongo_service),
    cloudinary_service: CloudinaryService = Depends(get_cloudinary_service)
):
    """
    Genera un nuevo pixel art a partir de un prompt utilizando IA.
    """
    # Obtener la paleta
    palette = palette_service.get_palette_by_id(request.settings.paletteId)
    if not palette:
        raise HTTPException(status_code=404, detail=f"Palette with id {request.settings.paletteId} not found")
    
    # Generar la imagen con OpenAI
    image_data = openai_service.generate_from_prompt(request.prompt, request.settings)
    
    if not image_data:
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
    
    # Crear el registro en la base de datos con soporte para Cloudinary
    pixel_art = pixel_art_service.create_pixel_art(
        pixel_art_data, 
        image_data, 
        cloudinary_service if settings.USE_CLOUDINARY else None
    )
    
    return pixel_art

# Procesar una imagen subida
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
    image_processing_service: ImageProcessingService = Depends(get_image_processing_service),
    pixel_art_service: PixelArtMongoService = Depends(get_pixel_art_mongo_service),
    palette_service: PaletteMongoService = Depends(get_palette_mongo_service),
    cloudinary_service: CloudinaryService = Depends(get_cloudinary_service)
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
        palette = palette_service.get_palette_by_id(paletteId)
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
            palette["colors"]
        )
        
        if not processed_image_data:
            logger.error("Failed to process image: No data returned from image processing service")
            raise HTTPException(status_code=500, detail="Failed to process image")
        
        # Si estamos usando OpenAI para procesamiento avanzado
        openai_service = OpenAIService()
        advanced_processed = await openai_service.process_image(
            temp_file_path,
            process_settings,
            palette["colors"]
        )
        
        # Usar el resultado de OpenAI si está disponible, sino usar el procesamiento local
        image_data = advanced_processed if advanced_processed else processed_image_data
        
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
        
        # Crear el registro en la base de datos con soporte para Cloudinary
        pixel_art = pixel_art_service.create_pixel_art(
            pixel_art_data, 
            image_data, 
            cloudinary_service if settings.USE_CLOUDINARY else None
        )
        
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
    pixel_art_service: PixelArtMongoService = Depends(get_pixel_art_mongo_service)
):
    """
    Actualiza un pixel art existente.
    """
    updated_pixel_art = pixel_art_service.update_pixel_art(pixel_art_id, pixel_art_update)
    if not updated_pixel_art:
        raise HTTPException(status_code=404, detail="Pixel art not found")
    return updated_pixel_art

# Eliminar un pixel art
@router.delete("/{pixel_art_id}")
def delete_pixel_art(
    pixel_art_id: str,
    pixel_art_service: PixelArtMongoService = Depends(get_pixel_art_mongo_service),
    cloudinary_service: CloudinaryService = Depends(get_cloudinary_service)
):
    """
    Elimina un pixel art existente.
    """
    success = pixel_art_service.delete_pixel_art(
        pixel_art_id, 
        cloudinary_service if settings.USE_CLOUDINARY else None
    )
    if not success:
        raise HTTPException(status_code=404, detail="Pixel art not found")
    return {"message": "Pixel art deleted successfully"}

# Búsqueda avanzada de pixel arts
@router.get("/search/", response_model=PixelArtList)
def search_pixel_arts(
    tags: Optional[List[str]] = Query(None),
    style: Optional[str] = Query(None),
    palette_id: Optional[str] = Query(None),
    search_term: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 100,
    pixel_art_service: PixelArtMongoService = Depends(get_pixel_art_mongo_service)
):
    """
    Busca pixel arts con diversos filtros.
    """
    result = pixel_art_service.search_pixel_arts(
        tags=tags,
        style=style,
        palette_id=palette_id,
        search_term=search_term,
        skip=skip,
        limit=limit
    )
    
    return result