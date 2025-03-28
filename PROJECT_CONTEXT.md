# Contexto del Proyecto PixelArt Generator API

Este documento proporciona un contexto detallado sobre la arquitectura, decisiones de diseño, y patrones de implementación del proyecto PixelArt Generator API. Está diseñado para que tanto desarrolladores humanos como asistentes de IA puedan comprender en profundidad cómo funciona el sistema.

## Visión General Arquitectónica

### Arquitectura de Capas

El proyecto sigue una arquitectura de capas bien definida:

1. **Capa de API (Controllers)**: Implementada en `app/api/routes/`.
   - Maneja las solicitudes HTTP.
   - Realiza validación básica de datos de entrada.
   - Delega el procesamiento a los servicios.

2. **Capa de Servicios**: Implementada en `app/services/`.
   - Contiene la lógica de negocio principal.
   - Coordina las operaciones entre repositorios y servicios externos.
   - Aísla la lógica de negocio de los detalles de la API y la persistencia.

3. **Capa de Modelos**: Implementada en `app/models/` y `app/database/models.py`.
   - Define entidades de dominio (modelos Pydantic para la API).
   - Define esquemas de bases de datos (modelos SQLAlchemy para SQLite).

4. **Capa de Persistencia**: Implementada en `app/database/`.
   - Gestiona la interacción con las bases de datos (SQLite y MongoDB).
   - Proporciona abstracciones para las operaciones CRUD.

5. **Capa de Servicios Externos**: Servicios como OpenAI y Cloudinary.
   - Encapsula la comunicación con APIs externas.

## Flujo de Datos Principal

![Diagrama de Flujo de Datos]

1. **Generación de Pixel Art desde Prompt**:
   - Cliente envía prompt a `/api/pixel-arts/generate-from-prompt` (SQLite) o `/api/mongo/pixel-arts/generate-from-prompt` (MongoDB).
   - Controller valida la solicitud y la pasa al servicio correspondiente.
   - `OpenAIService` genera una imagen base usando DALL-E.
   - La imagen se procesa para aplicar estilo pixel art y la paleta seleccionada.
   - La imagen se guarda localmente o en Cloudinary.
   - Los metadatos se guardan en la base de datos (SQLite o MongoDB).
   - Se devuelve la información completa al cliente.

2. **Procesamiento de Imagen Existente**:
   - Cliente sube imagen a `/api/pixel-arts/process-image` (SQLite) o `/api/mongo/pixel-arts/process-image` (MongoDB).
   - La imagen se procesa con `ImageProcessingService` para aplicar pixelación y paleta.
   - Opcionalmente se mejora con OpenAI.
   - La imagen resultante se guarda y se registra en la base de datos.
   - Se devuelve la información al cliente.

## Decisiones de Diseño Clave

### 1. Migración de SQLite a MongoDB

**Motivación**:
- **Persistencia en entornos cloud**: SQLite no es ideal para plataformas como Render debido a su naturaleza basada en archivos.
- **Escalabilidad**: MongoDB escala mejor para aplicaciones con crecimiento.
- **Esquema flexible**: Mejor para datos semiestructurados como metadatos y configuraciones.
- **Consultas avanzadas**: Capacidades de filtrado y búsqueda más potentes.

**Enfoque de implementación**:
- **Implementación paralela**: Se mantuvieron ambas implementaciones simultáneamente.
- **Rutas paralelas**: Nuevas rutas con prefijo `/api/mongo/` para facilitar pruebas.
- **Servicios espejo**: Para cada servicio de SQLite, se creó un equivalente para MongoDB.
- **Migración gradual**: Herramientas para transferir datos de SQLite a MongoDB.

### 2. Uso de Cloudinary para Almacenamiento de Imágenes

**Motivación**:
- **Persistencia de archivos**: Evitar pérdida de imágenes en reinicios de servidor.
- **CDN incorporado**: Mejor rendimiento en la entrega de imágenes.
- **Transformaciones de imágenes**: Generación automática de miniaturas.

**Implementación**:
- **Servicio dedicado**: `CloudinaryService` encapsula toda la interacción.
- **Configuración condicional**: Se puede habilitar/deshabilitar con la variable `USE_CLOUDINARY`.
- **Fallback local**: Si Cloudinary falla, se usa almacenamiento local.

### 3. Containerización con Docker

**Motivación**:
- **Consistencia de entorno**: Eliminar "funciona en mi máquina".
- **Despliegue simplificado**: Fácil de implementar en diferentes plataformas.
- **Aislamiento**: Cada componente corre en su propio contenedor.

**Implementación**:
- **Multi-container**: Separación de API, MongoDB y mongo-express.
- **Volúmenes persistentes**: Para datos de MongoDB e imágenes.
- **Healthchecks**: Para asegurar el correcto arranque de servicios dependientes.

## Patrones de Código y Convenciones

### Inyección de Dependencias

El proyecto usa FastAPI para inyección de dependencias:

```python
@router.get("/", response_model=PixelArtList)
def get_pixel_arts(
    skip: int = 0, 
    limit: int = 100,
    pixel_art_service: PixelArtMongoService = Depends(get_pixel_art_mongo_service)
):
    ...
```

Las dependencias están definidas en `app/api/deps.py`.

### Patrones de Servicio

Los servicios siguen un patrón común:
- Métodos estáticos para operaciones CRUD.
- Separación clara entre lógica de negocio y acceso a datos.
- Manejo de errores con excepciones específicas.

Por ejemplo:
```python
@staticmethod
def get_pixel_art_by_id(pixel_art_id: str) -> Optional[Dict]:
    """
    Obtiene un pixel art específico por su ID.
    """
    return sync_pixel_arts_collection.find_one({"id": pixel_art_id})
```

### Modelos Pydantic vs. Modelos de Base de Datos

Se mantiene una clara separación:
- **Modelos Pydantic** (`app/models/`): Para validación y serialización de API.
- **Modelos SQLAlchemy** (`app/database/models.py`): Para interacción con SQLite.
- **Diccionarios** (en servicios MongoDB): Para representar documentos.

### Manejo de Configuración

La configuración se centraliza en `app/config.py` usando Pydantic Settings:
- Variables de entorno gestionadas consistentemente.
- Valores por defecto sensatos.
- Validación de configuración al inicio.

## Casos de Uso Principales con Ejemplos

### 1. Generar Pixel Art desde un Prompt

**Solicitud API**:
```http
POST /api/mongo/pixel-arts/generate-from-prompt
Content-Type: application/json

{
  "prompt": "un gato ninja con sombrero",
  "settings": {
    "pixelSize": 8,
    "style": "retro",
    "paletteId": "gameboy",
    "backgroundType": "transparent",
    "animationType": "none"
  }
}
```

**Flujo interno**:
1. `pixel_art_mongo.py:generate_from_prompt` recibe la solicitud.
2. Valida la existencia de la paleta.
3. Llama a `openai_service.py:generate_from_prompt` para crear la imagen.
4. Llama a `pixel_art_mongo.py:create_pixel_art` para guardar los datos.
5. Si `USE_CLOUDINARY=True`, sube la imagen a Cloudinary con `cloudinary_service.py`.

**Respuesta**:
```json
{
  "id": "abcd1234-5678-...",
  "name": "Generated from: un gato ninja con sombrero...",
  "imageUrl": "/images/results/pixelart_1234567890.png",
  "thumbnailUrl": "/images/results/thumb_1234567890.png",
  "width": 128,
  "height": 128,
  "pixelSize": 8,
  "style": "retro",
  "backgroundType": "transparent",
  "animationType": "none",
  "isAnimated": false,
  "palette": {
    "id": "gameboy",
    "name": "GameBoy",
    "colors": ["#0f380f", "#306230", "#8bac0f", "#9bbc0f"]
  }
}
```

### 2. Procesar una Imagen Existente

**Solicitud API**:
```http
POST /api/mongo/pixel-arts/process-image
Content-Type: multipart/form-data

file: [archivo_imagen.jpg]
name: Mi imagen pixelada
pixelSize: 8
style: retro
paletteId: gameboy
contrast: 50
sharpness: 70
backgroundType: transparent
animationType: none
tags: gato, ninja, divertido
```

**Flujo interno**:
1. La imagen se guarda temporalmente.
2. Se aplica pixelación y procesamiento con `image_processing_service.py`.
3. Opcionalmente, se mejora con IA usando `openai_service.py:process_image`.
4. La imagen resultante se guarda y registra en MongoDB.

## Desafíos y Consideraciones Técnicas

### 1. Gestión de Archivos en Entornos Cloud

**Desafío**: Plataformas como Render pueden reiniciar los contenedores, perdiendo archivos locales.

**Soluciones implementadas**:
- Opción de Cloudinary para almacenamiento persistente.
- MongoDB para metadatos persistentes.
- Volúmenes de Docker para desarrollo local.

### 2. Rendimiento del Procesamiento de Imágenes

**Desafío**: El procesamiento de imágenes puede ser intensivo en CPU.

**Enfoque**:
- Procesamiento en segundo plano para tareas intensivas (futuro).
- Optimización del algoritmo de pixelación.
- Uso de miniaturas para previsualizaciones.

### 3. Migración de Datos

**Desafío**: Transición suave de SQLite a MongoDB sin pérdida de datos.

**Solución**:
- Endpoint de migración para transferir datos existentes.
- Validaciones para verificar integridad de datos migrados.
- Capacidad de ejecutar ambos sistemas en paralelo.

## Extensibilidad y Puntos de Expansión

### Nuevas Características Planificadas

1. **Animaciones**: Expandir los tipos de animación para pixel art animado.
   - Implementar en `image_processing_service.py` con nuevos algoritmos.
   - Actualizar modelos para soportar frames múltiples.

2. **Galería comunitaria**: Compartir creaciones entre usuarios.
   - Añadir conceptos de usuarios y autenticación.
   - Implementar privacidad y permisos.

3. **Estilos adicionales**: Más opciones de estilización de pixel art.
   - Expandir enumeración `PixelArtStyle`.
   - Implementar nuevos algoritmos en `image_processing_service.py`.

### Puntos de Integración

1. **Autenticación**: Preparado para integrar con:
   - OAuth (Auth0, Firebase)
   - Sistema de usuarios propio

2. **Sistemas de Almacenamiento**: Adicionales a Cloudinary:
   - Amazon S3
   - Google Cloud Storage

## Ejemplos de Código Clave

### Generación con OpenAI

```python
def generate_from_prompt(self, prompt: str, settings: PixelArtProcessSettings) -> Optional[Dict]:
    try:
        # Build a comprehensive prompt that incorporates all settings
        complete_prompt = self._build_comprehensive_prompt(prompt, settings)
        
        # Call OpenAI DALL-E 3 API
        response = self.client.images.generate(
            model="dall-e-3",
            prompt=complete_prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        
        # Get the generated image URL
        image_url = response.data[0].url
        
        # Download the image and save locally
        # ...código de procesamiento...
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating image from prompt: {str(e)}")
        return None
```

### Procesamiento de Imagen

```python
def _apply_color_palette(self, image: Image.Image, palette_colors: List[str]) -> Image.Image:
    """
    Aplica una paleta de colores específica a la imagen.
    """
    try:
        # Convertir colores hex a RGB
        rgb_palette = [self._hex_to_rgb(color) for color in palette_colors]
        
        # Convertir la imagen a numpy array
        img_array = np.array(image)
        
        # Para cada píxel, encontrar el color más cercano en la paleta
        for y in range(height):
            for x in range(width):
                if a is not None and a[y, x] < 128:
                    # Si es transparente, mantener la transparencia
                    new_img[y, x] = [0, 0, 0, 0]
                    continue
                
                pixel = [int(r[y, x]), int(g[y, x]), int(b[y, x])]
                closest_color = self._find_closest_color(pixel, rgb_palette)
                
                if a is not None:
                    new_img[y, x] = [closest_color[0], closest_color[1], closest_color[2], a[y, x]]
                else:
                    new_img[y, x] = closest_color
        
        # Convertir de vuelta a imagen PIL
        return Image.fromarray(new_img)
    except Exception as e:
        logger.error(f"Error applying color palette: {str(e)}")
        return image
```

## Conclusión

Este proyecto combina múltiples tecnologías (FastAPI, OpenAI, MongoDB, Cloudinary) para crear una solución completa de generación y procesamiento de pixel art. La arquitectura está diseñada para ser modular, extensible y robusta, con consideraciones específicas para entornos cloud y escalabilidad.

Las decisiones de diseño, como la migración a MongoDB y la opción de Cloudinary, están orientadas a resolver desafíos específicos de persistencia y escalabilidad, mientras que la implementación paralela facilita una transición gradual y segura.