from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .database import Base


class DBPixelArt(Base):
    __tablename__ = "pixel_arts"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, index=True)
    
    # Rutas de imágenes
    imageUrl = Column(String)
    thumbnailUrl = Column(String)
    
    # Metadatos
    createdAt = Column(DateTime, default=datetime.utcnow)
    width = Column(Integer)
    height = Column(Integer)
    pixelSize = Column(Integer)
    
    # Estilo y configuración
    style = Column(String)
    backgroundType = Column(String)
    animationType = Column(String, default="none")
    isAnimated = Column(Boolean, default=False)
    
    # Relación con la paleta
    paletteId = Column(String, ForeignKey("palettes.id"))
    palette = relationship("DBColorPalette", back_populates="pixel_arts")
    
    # Etiquetas como lista JSON
    tags = Column(JSON, default=list)


class DBColorPalette(Base):
    __tablename__ = "palettes"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    colors = Column(JSON)  # Lista de colores en formato hex
    
    # Relación con los pixel arts
    pixel_arts = relationship("DBPixelArt", back_populates="palette")


class DBUserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(String, primary_key=True, index=True)
    pixelSize = Column(Integer, default=8)
    defaultStyle = Column(String, default="retro")
    defaultPalette = Column(String, default="gameboy")
    contrast = Column(Integer, default=50)
    sharpness = Column(Integer, default=70)
    defaultBackground = Column(String, default="transparent")
    defaultAnimationType = Column(String, default="none")
    theme = Column(String, default="dark")