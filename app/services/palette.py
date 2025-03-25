from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from app.database.models import DBColorPalette
import logging

logger = logging.getLogger(__name__)

class PaletteService:
    @staticmethod
    def get_palettes(db: Session) -> List[DBColorPalette]:
        """
        Obtiene todas las paletas de colores.
        """
        return db.query(DBColorPalette).all()
    
    @staticmethod
    def get_palette_by_id(db: Session, palette_id: str) -> Optional[DBColorPalette]:
        """
        Obtiene una paleta específica por su ID.
        """
        return db.query(DBColorPalette).filter(DBColorPalette.id == palette_id).first()
    
    @staticmethod
    def create_palette(db: Session, palette_id: str, name: str, colors: List[str]) -> DBColorPalette:
        """
        Crea una nueva paleta de colores.
        
        Args:
            db: Sesión de base de datos
            palette_id: ID único para la paleta
            name: Nombre descriptivo de la paleta
            colors: Lista de colores en formato hexadecimal
            
        Returns:
            La paleta creada
        """
        # Verificar si ya existe una paleta con ese ID
        existing = PaletteService.get_palette_by_id(db, palette_id)
        if existing:
            raise ValueError(f"Palette with ID {palette_id} already exists")
        
        # Crear la nueva paleta
        db_palette = DBColorPalette(
            id=palette_id,
            name=name,
            colors=colors
        )
        
        db.add(db_palette)
        db.commit()
        db.refresh(db_palette)
        
        return db_palette
    
    @staticmethod
    def update_palette(db: Session, palette_id: str, updates: Dict) -> Optional[DBColorPalette]:
        """
        Actualiza una paleta existente.
        
        Args:
            db: Sesión de base de datos
            palette_id: ID de la paleta a actualizar
            updates: Diccionario con los campos a actualizar
            
        Returns:
            La paleta actualizada o None si no se encontró
        """
        db_palette = PaletteService.get_palette_by_id(db, palette_id)
        if not db_palette:
            return None
            
        # Actualizar campos
        for key, value in updates.items():
            if hasattr(db_palette, key):
                setattr(db_palette, key, value)
        
        db.commit()
        db.refresh(db_palette)
        return db_palette
    
    @staticmethod
    def delete_palette(db: Session, palette_id: str) -> bool:
        """
        Elimina una paleta de la base de datos.
        
        Args:
            db: Sesión de base de datos
            palette_id: ID de la paleta a eliminar
            
        Returns:
            True si se eliminó correctamente, False si no se encontró
        """
        db_palette = PaletteService.get_palette_by_id(db, palette_id)
        if not db_palette:
            return False
            
        # Verificar si hay pixel arts que usan esta paleta
        if db_palette.pixel_arts and len(db_palette.pixel_arts) > 0:
            raise ValueError(f"Cannot delete palette {palette_id} because it is used by existing pixel arts")
        
        db.delete(db_palette)
        db.commit()
        return True
    
    @staticmethod
    def initialize_default_palettes(db: Session):
        """
        Inicializa las paletas predeterminadas en la base de datos.
        """
        default_palettes = [
            {
                "id": "gameboy",
                "name": "GameBoy",
                "colors": ["#0f380f", "#306230", "#8bac0f", "#9bbc0f"]
            },
            {
                "id": "nes",
                "name": "NES",
                "colors": ["#000000", "#fcfcfc", "#f8f8f8", "#bcbcbc"]
            },
            {
                "id": "cga",
                "name": "CGA",
                "colors": ["#000000", "#555555", "#aaaaaa", "#ffffff"]
            },
            {
                "id": "pico8",
                "name": "PICO-8",
                "colors": ["#000000", "#1D2B53", "#7E2553", "#008751"]
            },
            {
                "id": "moody",
                "name": "Moody Purple",
                "colors": ["#5e315b", "#8c3f5d", "#ba6156", "#f2a65a"]
            }
        ]
        
        for palette_data in default_palettes:
            # Verificar si ya existe
            if not PaletteService.get_palette_by_id(db, palette_data["id"]):
                # Crear la paleta
                db_palette = DBColorPalette(
                    id=palette_data["id"],
                    name=palette_data["name"],
                    colors=palette_data["colors"]
                )
                db.add(db_palette)
        
        db.commit()