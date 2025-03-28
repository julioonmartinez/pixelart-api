# app/api/routes/setting
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.user import UserSettings, UserSettingsUpdate
from app.services.user_settings import UserSettingsService
from app.api.deps import get_user_settings_service

router = APIRouter()

# Obtener configuraciones de usuario
@router.get("/", response_model=UserSettings)
def get_user_settings(
    user_id: str = "default",
    db: Session = Depends(get_db),
    settings_service: UserSettingsService = Depends(get_user_settings_service)
):
    """
    Obtiene las configuraciones del usuario.
    Si no existen, crea unas por defecto.
    """
    db_settings = settings_service.get_user_settings(db, user_id)
    return db_settings

# Actualizar configuraciones de usuario
@router.put("/", response_model=UserSettings)
def update_user_settings(
    settings_update: UserSettingsUpdate,
    user_id: str = "default",
    db: Session = Depends(get_db),
    settings_service: UserSettingsService = Depends(get_user_settings_service)
):
    """
    Actualiza las configuraciones del usuario.
    """
    # Convertir a diccionario y eliminar valores None
    update_data = settings_update.model_dump(exclude_unset=True)
    
    # Actualizar configuraciones
    updated_settings = settings_service.update_user_settings(db, user_id, update_data)
    return updated_settings

# Restablecer configuraciones predeterminadas
@router.post("/reset", response_model=UserSettings)
def reset_user_settings(
    user_id: str = "default",
    db: Session = Depends(get_db),
    settings_service: UserSettingsService = Depends(get_user_settings_service)
):
    """
    Restablece las configuraciones del usuario a los valores predeterminados.
    """
    # Valores predeterminados
    default_settings = {
        "pixelSize": 8,
        "defaultStyle": "retro",
        "defaultPalette": "gameboy",
        "contrast": 50,
        "sharpness": 70,
        "defaultBackground": "transparent",
        "defaultAnimationType": "none",
        "theme": "dark"
    }
    
    # Actualizar con los valores predeterminados
    updated_settings = settings_service.update_user_settings(db, user_id, default_settings)
    return updated_settings