import logging
from typing import Dict, Optional
from datetime import datetime
from app.database.mongodb import sync_user_settings_collection

logger = logging.getLogger(__name__)

class UserSettingsMongoService:
    """Servicio para gestionar las configuraciones de usuario en MongoDB"""
    
    @staticmethod
    def get_user_settings(user_id: str = "default") -> Dict:
        """
        Obtiene las configuraciones de un usuario específico.
        Si no existen, crea unas configuraciones por defecto.
        
        Args:
            user_id: ID del usuario (default para el usuario anónimo)
            
        Returns:
            Configuraciones del usuario como diccionario
        """
        # Buscar configuraciones existentes
        settings = sync_user_settings_collection.find_one({"userId": user_id})
        
        # Si no existen, crear configuraciones por defecto
        if not settings:
            now = datetime.now()
            default_settings = {
                "userId": user_id,
                "pixelSize": 8,
                "defaultStyle": "retro",
                "defaultPalette": "gameboy",
                "contrast": 50,
                "sharpness": 70,
                "defaultBackground": "transparent",
                "defaultAnimationType": "none",
                "theme": "dark",
                "createdAt": now,
                "updatedAt": now
            }
            
            # Insertar en MongoDB
            sync_user_settings_collection.insert_one(default_settings)
            
            # Devolver las configuraciones creadas
            return default_settings
        
        return settings
    
    @staticmethod
    def update_user_settings(user_id: str, updates: Dict) -> Dict:
        """
        Actualiza las configuraciones de un usuario.
        
        Args:
            user_id: ID del usuario
            updates: Diccionario con los campos a actualizar
            
        Returns:
            Configuraciones actualizadas
        """
        # Asegurar que existen las configuraciones
        existing = UserSettingsMongoService.get_user_settings(user_id)
        
        # Preparar actualizaciones
        updates["updatedAt"] = datetime.now()
        
        # Actualizar en MongoDB
        sync_user_settings_collection.update_one(
            {"userId": user_id},
            {"$set": updates}
        )
        
        # Obtener el documento actualizado
        return sync_user_settings_collection.find_one({"userId": user_id})