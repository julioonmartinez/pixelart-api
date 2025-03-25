from pydantic import BaseModel
from .pixel_art import PixelArtStyle, BackgroundType, AnimationType


class ThemeType(str):
    DARK = "dark"
    LIGHT = "light"


class UserSettings(BaseModel):
    id: str
    pixelSize: int = 8
    defaultStyle: PixelArtStyle = PixelArtStyle.RETRO_8BIT
    defaultPalette: str = "gameboy"
    contrast: int = 50
    sharpness: int = 70
    defaultBackground: BackgroundType = BackgroundType.TRANSPARENT
    defaultAnimationType: AnimationType = AnimationType.NONE
    theme: str = "dark"


class UserSettingsUpdate(BaseModel):
    pixelSize: int = None
    defaultStyle: PixelArtStyle = None
    defaultPalette: str = None
    contrast: int = None
    sharpness: int = None
    defaultBackground: BackgroundType = None
    defaultAnimationType: AnimationType = None
    theme: str = None