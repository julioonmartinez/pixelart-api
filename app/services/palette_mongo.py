import logging
from datetime import datetime
from typing import List, Optional, Dict
from app.database.mongodb import sync_palettes_collection, sync_pixel_arts_collection

logger = logging.getLogger(__name__)

class PaletteMongoService:
    """Servicio para gestionar paletas de colores en MongoDB"""
    
    @staticmethod
    def get_palettes() -> List[Dict]:
        """
        Obtiene todas las paletas de colores desde MongoDB.
        """
        return list(sync_palettes_collection.find())
    
    @staticmethod
    def get_palette_by_id(palette_id: str) -> Optional[Dict]:
        """
        Obtiene una paleta específica por su ID desde MongoDB.
        """
        return sync_palettes_collection.find_one({"id": palette_id})
    
    @staticmethod
    def create_palette(palette_id: str, name: str, colors: List[str], description: str = None) -> Dict:
        """
        Crea una nueva paleta de colores en MongoDB.
        
        Args:
            palette_id: ID único para la paleta
            name: Nombre descriptivo de la paleta
            colors: Lista de colores en formato hexadecimal
            description: Descripción opcional de la paleta
            
        Returns:
            La paleta creada como diccionario
        """
        # Verificar si ya existe una paleta con ese ID
        existing = PaletteMongoService.get_palette_by_id(palette_id)
        if existing:
            raise ValueError(f"Palette with ID {palette_id} already exists")
        
        # Crear la nueva paleta
        now = datetime.now()
        palette_doc = {
            "id": palette_id,
            "name": name,
            "colors": colors,
            "description": description,
            "createdAt": now,
            "updatedAt": now
        }
        
        # Insertar en MongoDB
        sync_palettes_collection.insert_one(palette_doc)
        
        return palette_doc
    
    @staticmethod
    def update_palette(palette_id: str, updates: Dict) -> Optional[Dict]:
        """
        Actualiza una paleta existente en MongoDB.
        
        Args:
            palette_id: ID de la paleta a actualizar
            updates: Diccionario con los campos a actualizar
            
        Returns:
            La paleta actualizada o None si no se encontró
        """
        # Verificar si existe
        existing = PaletteMongoService.get_palette_by_id(palette_id)
        if not existing:
            return None
        
        # Preparar las actualizaciones
        updates["updatedAt"] = datetime.now()
        
        # Actualizar en MongoDB
        sync_palettes_collection.update_one(
            {"id": palette_id},
            {"$set": updates}
        )
        
        # Obtener el documento actualizado
        return PaletteMongoService.get_palette_by_id(palette_id)
    
    @staticmethod
    def delete_palette(palette_id: str) -> bool:
        """
        Elimina una paleta de MongoDB.
        
        Args:
            palette_id: ID de la paleta a eliminar
            
        Returns:
            True si se eliminó correctamente, False si no se encontró
        """
        # Verificar si existe
        existing = PaletteMongoService.get_palette_by_id(palette_id)
        if not existing:
            return False
        
        # Verificar si hay pixel arts que usan esta paleta
        pixel_arts_count = sync_pixel_arts_collection.count_documents({"paletteId": palette_id})
        if pixel_arts_count > 0:
            raise ValueError(f"Cannot delete palette {palette_id} because it is used by {pixel_arts_count} existing pixel arts")
        
        # Eliminar de MongoDB
        result = sync_palettes_collection.delete_one({"id": palette_id})
        return result.deleted_count > 0
    
    @staticmethod
    def initialize_default_palettes():
        """
        Inicializa las paletas predeterminadas en MongoDB.
        """
        default_palettes = [
            {
                "id": "gameboy",
                "name": "GameBoy",
                "colors": ["#0f380f", "#306230", "#8bac0f", "#9bbc0f"],
                "description": "Paleta clásica de Game Boy"
            },
            {
                "id": "nes",
                "name": "NES",
                "colors": ["#000000", "#fcfcfc", "#f8f8f8", "#bcbcbc"],
                "description": "Paleta de Nintendo Entertainment System"
            },
            {
                "id": "cga",
                "name": "CGA",
                "colors": ["#000000", "#555555", "#aaaaaa", "#ffffff"],
                "description": "Paleta CGA de PC antigua"
            },
            {
                "id": "pico8",
                "name": "PICO-8",
                "colors": ["#000000", "#1D2B53", "#7E2553", "#008751"],
                "description": "Paleta de la consola fantástica PICO-8"
            },
            {
                "id": "moody",
                "name": "Moody Purple",
                "colors": ["#5e315b", "#8c3f5d", "#ba6156", "#f2a65a"],
                "description": "Paleta de tonos púrpuras y morados"
            }
        ]
        
        count = 0
        for palette_data in default_palettes:
            try:
                # Verificar si ya existe
                existing = PaletteMongoService.get_palette_by_id(palette_data["id"])
                if not existing:
                    # Crear la paleta
                    PaletteMongoService.create_palette(
                        palette_data["id"],
                        palette_data["name"],
                        palette_data["colors"],
                        palette_data.get("description")
                    )
                    count += 1
            except Exception as e:
                logger.error(f"Error initializing palette {palette_data['id']}: {str(e)}")
        
        logger.info(f"Initialized {count} default palettes in MongoDB")
        return count