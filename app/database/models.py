from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base

class DBColorPalette(Base):
    __tablename__ = "color_palettes"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    colors = Column(JSON, nullable=False, default=list)
    description = Column(String, nullable=True)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relación con pixel arts
    pixel_arts = relationship("DBPixelArt", back_populates="palette")

class DBPixelArt(Base):
    __tablename__ = "pixel_arts"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    imageUrl = Column(String, nullable=False)
    thumbnailUrl = Column(String, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    pixelSize = Column(Integer, nullable=False, default=8)
    style = Column(String, nullable=False)
    backgroundType = Column(String, nullable=False)
    animationType = Column(String, nullable=False, default="none")
    isAnimated = Column(Boolean, default=False)
    paletteId = Column(String, ForeignKey("color_palettes.id"))
    tags = Column(JSON, nullable=True, default=list)
    description = Column(Text, nullable=True)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Nuevo campo para el ID público de Cloudinary
    cloudinaryPublicId = Column(String, nullable=True)
    
    # Relación con la paleta
    palette = relationship("DBColorPalette", back_populates="pixel_arts")

class DBUserSettings(Base):
    __tablename__ = "user_settings"
    
    userId = Column(String, primary_key=True, index=True)
    pixelSize = Column(Integer, default=8)
    defaultStyle = Column(String, default="retro")
    defaultPalette = Column(String, default="gameboy")
    contrast = Column(Integer, default=50)
    sharpness = Column(Integer, default=70)
    defaultBackground = Column(String, default="transparent")
    defaultAnimationType = Column(String, default="none")
    theme = Column(String, default="dark")
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), onupdate=func.now())