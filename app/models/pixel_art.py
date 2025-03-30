#app/models/pixel_art.py
from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class PixelArtStyle(str, Enum):
    RETRO_8BIT = "retro"
    MODERN_16BIT = "modern"
    MINIMALIST = "minimalist"
    DITHERED = "dithered"
    ISOMETRIC = "isometric"


class BackgroundType(str, Enum):
    TRANSPARENT = "transparent"
    SOLID = "solid"
    GRADIENT = "gradient"
    PATTERN = "pattern"


class AnimationType(str, Enum):
    NONE = "none"
    BREATHING = "breathing"
    FLICKERING = "flickering"
    FLOATING = "floating"


class ColorPalette(BaseModel):
    id: str
    name: str
    colors: List[str]


class PixelArtBase(BaseModel):
    name: str
    pixelSize: int = 8
    style: PixelArtStyle = PixelArtStyle.RETRO_8BIT
    backgroundType: BackgroundType = BackgroundType.TRANSPARENT
    paletteId: str
    animationType: AnimationType = AnimationType.NONE
    tags: List[str] = []


class PixelArtCreate(PixelArtBase):
    pass


class PixelArtProcessSettings(BaseModel):
    pixelSize: int = 8
    style: PixelArtStyle = PixelArtStyle.RETRO_8BIT
    paletteId: str
    contrast: int = 50
    sharpness: int = 70
    backgroundType: BackgroundType = BackgroundType.TRANSPARENT
    animationType: AnimationType = AnimationType.NONE


class PixelArt(PixelArtBase):
    id: str
    imageUrl: str
    thumbnailUrl: str
    createdAt: datetime
    width: int
    height: int
    isAnimated: bool
    palette: ColorPalette
    
    class Config:
        from_attributes = True


class PixelArtPromptRequest(BaseModel):
    prompt: str
    settings: PixelArtProcessSettings


class PixelArtImageRequest(BaseModel):
    settings: PixelArtProcessSettings
    # La imagen se enviará como un archivo, no como JSON


class PaletteList(BaseModel):
    palettes: List[ColorPalette]


class PixelArtList(BaseModel):
    items: List[PixelArt]
    total: int

class PixelArtVersion(BaseModel):
    timestamp: str
    imageUrl: str
    thumbnailUrl: str
    prompt: Optional[str] = None
    changes: dict

class PixelArt(PixelArtBase):
    id: str
    imageUrl: str
    thumbnailUrl: str
    createdAt: datetime
    updatedAt: Optional[datetime] = None
    width: int
    height: int
    isAnimated: bool
    palette: ColorPalette
    prompt: Optional[str] = None
    versionHistory: Optional[List[PixelArtVersion]] = None
    
    class Config:
        from_attributes = True