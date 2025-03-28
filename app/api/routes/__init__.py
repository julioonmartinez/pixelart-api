from fastapi import APIRouter
from app.api.routes import pixel_art, palettes, settings
from app.api.routes import pixel_art_mongo, migration

def register_routes(api_router: APIRouter):
    # Añadir rutas de la API anterior (SQLite)
    api_router.include_router(pixel_art.router, prefix="/pixel-arts", tags=["pixel-arts"])
    api_router.include_router(palettes.router, prefix="/palettes", tags=["palettes"])
    api_router.include_router(settings.router, prefix="/settings", tags=["settings"])

    # Añadir rutas de la nueva API (MongoDB)
    api_router.include_router(pixel_art_mongo.router, prefix="/mongo/pixel-arts", tags=["mongo-pixel-arts"])
    api_router.include_router(migration.router, prefix="/migration", tags=["migration"])