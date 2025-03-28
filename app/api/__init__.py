# app/api/__init__.py
from fastapi import APIRouter

# Crear el router principal y exportarlo
api_router = APIRouter()

# Importar y añadir las rutas
from app.api.routes import register_routes

# Registrar todas las rutas
register_routes(api_router)