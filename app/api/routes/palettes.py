from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.pixel_art import ColorPalette, PaletteList
from app.services.palette import PaletteService
from app.api.deps import get_palette_service

router = APIRouter()

# Obtener todas las paletas
@router.get("/", response_model=PaletteList)
def get_palettes(
    db: Session = Depends(get_db),
    palette_service: PaletteService = Depends(get_palette_service)
):
    """
    Obtiene todas las paletas de colores disponibles.
    """
    palettes = palette_service.get_palettes(db)
    return {"palettes": palettes}

# Obtener una paleta específica
@router.get("/{palette_id}", response_model=ColorPalette)
def get_palette(
    palette_id: str,
    db: Session = Depends(get_db),
    palette_service: PaletteService = Depends(get_palette_service)
):
    """
    Obtiene una paleta específica por su ID.
    """
    palette = palette_service.get_palette_by_id(db, palette_id)
    if not palette:
        raise HTTPException(status_code=404, detail="Palette not found")
    return palette

# Crear una nueva paleta
@router.post("/", response_model=ColorPalette)
def create_palette(
    palette: ColorPalette,
    db: Session = Depends(get_db),
    palette_service: PaletteService = Depends(get_palette_service)
):
    """
    Crea una nueva paleta de colores.
    """
    try:
        db_palette = palette_service.create_palette(db, palette.id, palette.name, palette.colors)
        return db_palette
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Actualizar una paleta existente
@router.put("/{palette_id}", response_model=ColorPalette)
def update_palette(
    palette_id: str,
    palette_update: dict,
    db: Session = Depends(get_db),
    palette_service: PaletteService = Depends(get_palette_service)
):
    """
    Actualiza una paleta existente.
    """
    updated_palette = palette_service.update_palette(db, palette_id, palette_update)
    if not updated_palette:
        raise HTTPException(status_code=404, detail="Palette not found")
    return updated_palette

# Eliminar una paleta
@router.delete("/{palette_id}")
def delete_palette(
    palette_id: str,
    db: Session = Depends(get_db),
    palette_service: PaletteService = Depends(get_palette_service)
):
    """
    Elimina una paleta existente.
    """
    try:
        success = palette_service.delete_palette(db, palette_id)
        if not success:
            raise HTTPException(status_code=404, detail="Palette not found")
        return {"message": "Palette deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))