from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.services.migration_service import MigrationService

router = APIRouter()

@router.post("/migrate-to-mongodb")
def migrate_to_mongodb(db: Session = Depends(get_db)):
    """
    Migra todos los datos desde SQLite a MongoDB.
    Este endpoint es administrativo y debería estar protegido en producción.
    """
    try:
        result = MigrationService.migrate_all_data(db)
        return {
            "success": True,
            "message": "Migración completada con éxito",
            "details": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error durante la migración: {str(e)}"
        )

@router.post("/migrate-palettes")
def migrate_palettes(db: Session = Depends(get_db)):
    """
    Migra solo las paletas de colores desde SQLite a MongoDB.
    """
    try:
        count = MigrationService.migrate_palettes(db)
        return {
            "success": True,
            "message": f"Migración de paletas completada: {count} paletas migradas"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error durante la migración de paletas: {str(e)}"
        )

@router.post("/migrate-pixel-arts")
def migrate_pixel_arts(db: Session = Depends(get_db)):
    """
    Migra solo los pixel arts desde SQLite a MongoDB.
    """
    try:
        count = MigrationService.migrate_pixel_arts(db)
        return {
            "success": True,
            "message": f"Migración de pixel arts completada: {count} pixel arts migrados"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error durante la migración de pixel arts: {str(e)}"
        )

@router.post("/migrate-user-settings")
def migrate_user_settings(db: Session = Depends(get_db)):
    """
    Migra solo las configuraciones de usuario desde SQLite a MongoDB.
    """
    try:
        count = MigrationService.migrate_user_settings(db)
        return {
            "success": True,
            "message": f"Migración de configuraciones de usuario completada: {count} configuraciones migradas"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error durante la migración de configuraciones de usuario: {str(e)}"
        )