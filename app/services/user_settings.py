from typing import Optional, Dict
from sqlalchemy.orm import Session
from app.database.models import DBUserSettings
import logging

logger = logging.getLogger(__name__)

class UserSettingsService:
    @staticmethod
    def get_user_settings(db: Session, user_id: str = "default") -> DBUserSettings:
        """
        Obtiene las configuraciones de usuario.
        Si no existen, las crea con valores predeterminados.
        
        Args:
            db: Sesión de base de datos
            user_id: ID del usuario (por defecto "default" para un solo usuario)
            
        Returns:
            Las configuraciones del usuario
        """
        db_settings = db.query(DBUserSettings).filter(DBUserSettings.id == user_id).first()
        
        if not db_settings:
            # Crear configuraciones por defecto
            db_settings = DBUserSettings(
                id=user_id,
                pixelSize=8,
                defaultStyle="retro",
                defaultPalette="gameboy",
                contrast=50,
                sharpness=70,
                defaultBackground="transparent",
                defaultAnimationType="none",
                theme="dark"
            )
            db.add(db_settings)
            db.commit()
            db.refresh(db_settings)
        
        return db_settings
    
    @staticmethod
    def update_user_settings(db: Session, user_id: str, updates: Dict) -> DBUserSettings:
        """
        Actualiza las configuraciones de usuario.
        
        Args:
            db: Sesión de base de datos
            user_id: ID del usuario
            updates: Diccionario con los campos a actualizar
            
        Returns:
            Las configuraciones actualizadas
        """
        # Obtener o crear las configuraciones
        db_settings = UserSettingsService.get_user_settings(db, user_id)
        
        # Actualizar campos
        for key, value in updates.items():
            if hasattr(db_settings, key) and value is not None:
                setattr(db_settings, key, value)
        
        db.commit()
        db.refresh(db_settings)
        return db_settings