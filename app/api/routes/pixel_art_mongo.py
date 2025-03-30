#app/api/routes/pixel_art_mongo.py
import os
import uuid
import httpx
import shutil
from datetime import datetime
from typing import List, Optional, Dict
from venv import logger
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, Query, Request, Body
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
    prompt: Optional[str] = Form(None),  # Prompt opcional
    tags: str = Form(""),
    image_processing_service: ImageProcessingService = Depends(get_image_processing_service),
    pixel_art_service: PixelArtMongoService = Depends(get_pixel_art_mongo_service),
    palette_service: PaletteMongoService = Depends(get_palette_mongo_service),
    openai_service: OpenAIService = Depends(get_openai_service),
    cloudinary_service: CloudinaryService = Depends(get_cloudinary_service)
):
    """
    Procesa una imagen subida para convertirla en pixel art.
    Si se proporciona un prompt, se utilizará para mejorar o modificar la imagen con IA.
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
        
        # Determinar flujo de procesamiento basado en la presencia del prompt
        final_image_data = None
        
        if prompt:
            # Si hay un prompt, procesamos directamente con OpenAI usando la función mejorada
            logger.info(f"Processing image with prompt: {prompt}")
            final_image_data = await openai_service.process_image(
                temp_file_path,  # Ruta de la imagen original
                process_settings,
                palette["colors"],
                prompt  # Pasamos el prompt a la función mejorada
            )
            
            if not final_image_data:
                logger.warning("OpenAI processing failed, falling back to basic processing")
                # Si falla OpenAI, usamos el procesamiento básico
                final_image_data = image_processing_service.process_image(
                    temp_file_path, 
                    process_settings,
                    palette["colors"]
                )
        else:
            # Sin prompt, usamos el procesamiento básico
            logger.info("Processing image without prompt")
            final_image_data = image_processing_service.process_image(
                temp_file_path, 
                process_settings,
                palette["colors"]
            )
        
        if not final_image_data:
            logger.error("Failed to process image: No data returned from processing")
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
        
        # Crear el registro en la base de datos con soporte para Cloudinary
        pixel_art = pixel_art_service.create_pixel_art(
            pixel_art_data, 
            final_image_data, 
            cloudinary_service if settings.USE_CLOUDINARY else None
        )
        
        # Añadir el prompt al registro si existe
        if prompt:
            # Guardar el prompt directamente en el pixel art en lugar de hacerlo en dos pasos
            update_data = {
                "prompt": prompt
            }
            
            # Inicializar el historial de versiones vacío si no existe
            if "versionHistory" not in pixel_art or not pixel_art["versionHistory"]:
                update_data["versionHistory"] = []
            
            # Actualizar el pixel art con el prompt
            updated_pixel_art = pixel_art_service.update_pixel_art(pixel_art["id"], update_data)
            if updated_pixel_art:
                pixel_art = updated_pixel_art
                logger.info(f"Added prompt and initialized version history for pixel art {pixel_art['id']}")

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
async def update_pixel_art(
    pixel_art_id: str,
    pixel_art_update: Dict = Body(...),
    prompt: Optional[str] = Body(None),
    apply_changes_to_image: bool = Body(False),
    openai_service: OpenAIService = Depends(get_openai_service),
    pixel_art_service: PixelArtMongoService = Depends(get_pixel_art_mongo_service),
    palette_service: PaletteMongoService = Depends(get_palette_mongo_service),
    image_processing_service: ImageProcessingService = Depends(get_image_processing_service),
    cloudinary_service: CloudinaryService = Depends(get_cloudinary_service)
):
    """
    Actualiza un pixel art existente.
    
    Si apply_changes_to_image es True, generará una nueva versión de la imagen
    aplicando las modificaciones solicitadas usando OpenAI.
    """
    # Verificar que el pixel art existe
    existing_pixel_art = pixel_art_service.get_pixel_art_by_id(pixel_art_id)
    if not existing_pixel_art:
        raise HTTPException(status_code=404, detail="Pixel art not found")
    
    # Si no se solicita aplicar cambios a la imagen, simplemente actualizar los metadatos
    if not apply_changes_to_image:
        updated_pixel_art = pixel_art_service.update_pixel_art(pixel_art_id, pixel_art_update)
        return updated_pixel_art
    
    # Si se solicita aplicar cambios a la imagen, procesar con OpenAI
    if not prompt:
        raise HTTPException(
            status_code=400, 
            detail="Se requiere un prompt para aplicar cambios a la imagen"
        )
    
    # Obtener la paleta
    palette_id = pixel_art_update.get("paletteId", existing_pixel_art.get("paletteId"))
    palette = palette_service.get_palette_by_id(palette_id)
    if not palette:
        raise HTTPException(status_code=404, detail=f"Palette with id {palette_id} not found")
    
    # Crear configuración de procesamiento
    process_settings = PixelArtProcessSettings(
        pixelSize=pixel_art_update.get("pixelSize", existing_pixel_art.get("pixelSize", 8)),
        style=pixel_art_update.get("style", existing_pixel_art.get("style", "retro")),
        paletteId=palette_id,
        contrast=pixel_art_update.get("contrast", 50),
        sharpness=pixel_art_update.get("sharpness", 70),
        backgroundType=pixel_art_update.get("backgroundType", existing_pixel_art.get("backgroundType", "transparent")),
        animationType=pixel_art_update.get("animationType", existing_pixel_art.get("animationType", "none"))
    )
    
    # Construir la ruta de la imagen actual
    image_url = existing_pixel_art.get("imageUrl", "")
    local_image_path = None
    
    # Si la imagen está en Cloudinary o es una URL externa, descargarla primero
    if image_url.startswith(("http://", "https://")):
        try:
            # Descargar la imagen de Cloudinary
            local_image_path = os.path.join(
                settings.UPLOAD_FOLDER, 
                f"temp_{uuid.uuid4()}.png"
            )
            response = httpx.get(image_url)
            with open(local_image_path, "wb") as f:
                f.write(response.content)
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Error descargando la imagen de Cloudinary: {str(e)}"
            )
    else:
        # Convertir la URL relativa a una ruta local absoluta
        filename = os.path.basename(image_url)
        local_image_path = os.path.join(settings.RESULTS_FOLDER, filename)
        
        if not os.path.exists(local_image_path):
            raise HTTPException(
                status_code=404, 
                detail="No se encontró la imagen local para aplicar cambios"
            )
    
    try:
        # Procesar la imagen con OpenAI
        processed_image_data = await openai_service.update_image(
            local_image_path,
            prompt,
            process_settings,
            palette["colors"]
        )
        
        if not processed_image_data:
            raise HTTPException(
                status_code=500, 
                detail="Error al procesar la imagen con OpenAI"
            )
        
        # Guardar la versión anterior en el historial
        version_history = existing_pixel_art.get("versionHistory", [])
        # Si no existe el historial, inicializarlo
        if version_history is None:
            version_history = []
            logger.info(f"Initializing version history for pixel art {pixel_art_id}")
        
        # Crear entrada para la versión actual (que pasará a ser una versión anterior)
        version_entry = {
            "timestamp": datetime.now().isoformat(),
            "imageUrl": existing_pixel_art["imageUrl"],
            "thumbnailUrl": existing_pixel_art["thumbnailUrl"],
            "prompt": existing_pixel_art.get("prompt", ""),
            "changes": pixel_art_update
        }
        
        # Limitar historial a 5 versiones como máximo
        if len(version_history) >= 5:
            version_history = version_history[-4:] # Mantener solo las 4 más recientes
        
        version_history.append(version_entry)
        logger.info(f"Added version to history, now has {len(version_history)} versions")
        # Actualizar el pixel art con la nueva imagen y metadatos
        update_data = pixel_art_update.copy()
        update_data.update({
            "imageUrl": processed_image_data["image_url"],
            "thumbnailUrl": processed_image_data["thumbnail_url"],
            "width": processed_image_data["width"],
            "height": processed_image_data["height"],
            "prompt": prompt,
            "versionHistory": version_history,
            "updatedAt": datetime.now()
        })
        logger.info(f"Updating pixel art with new data including version history")
        
        # Crear el registro actualizado en la base de datos con soporte para Cloudinary
        updated_pixel_art = pixel_art_service.update_pixel_art_with_image(
            pixel_art_id, 
            update_data, 
            processed_image_data,
            cloudinary_service if settings.USE_CLOUDINARY else None
        )
        
        return updated_pixel_art
    
    except Exception as e:
        logger.error(f"Error updating pixel art image: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Limpiar archivos temporales
        if local_image_path and "temp_" in local_image_path and os.path.exists(local_image_path):
            try:
                os.remove(local_image_path)
            except:
                pass
        
        raise HTTPException(status_code=500, detail=f"Error updating pixel art: {str(e)}")