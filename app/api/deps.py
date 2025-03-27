#app/api/deps.py
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.services.openai_service import OpenAIService
from app.services.image_processing import ImageProcessingService
from app.services.pixel_art import PixelArtService
from app.services.palette import PaletteService
from app.services.user_settings import UserSettingsService
from app.services.cloudinary_service import CloudinaryService

def get_openai_service():
    return OpenAIService()

def get_image_processing_service():
    return ImageProcessingService()

def get_pixel_art_service():
    return PixelArtService()

def get_palette_service():
    return PaletteService()

def get_user_settings_service():
    return UserSettingsService()

def get_cloudinary_service():
    return CloudinaryService()