# app/api/routes/__init__.py
from fastapi import APIRouter
from .pixel_art import router as pixel_art_router
from .palettes import router as palettes_router
from .settings import router as settings_router

api_router = APIRouter()

api_router.include_router(pixel_art_router, prefix="/pixel-arts", tags=["pixel-arts"])
api_router.include_router(palettes_router, prefix="/palettes", tags=["palettes"])
api_router.include_router(settings_router, prefix="/settings", tags=["settings"])