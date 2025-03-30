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

3. **Actualización de Imagen con Prompt**:
   - Cliente envía prompt de modificación a `/api/mongo/pixel-arts/{id}` con `apply_changes_to_image=true`.
   - Controller valida la solicitud y obtiene la imagen existente.
   - `OpenAIService.update_image` analiza la imagen actual con GPT-4o y aplica los cambios solicitados.
   - La función categoriza el tipo de modificación (añadir texto, cambiar colores, añadir elementos, etc.).
   - Genera un prompt especializado según el tipo de modificación.
   - La nueva versión se guarda conservando la versión anterior en el historial.
   - Se devuelve la información actualizada al cliente.

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

### 4. Sistema de Historial de Versiones

**Motivación**:
- **Seguimiento de cambios**: Permitir a los usuarios ver la evolución de sus creaciones.
- **Recuperación de versiones**: Posibilidad de revertir a estados anteriores.
- **Comparación visual**: Facilitar la comparación entre diferentes iteraciones.

**Implementación**:
- **Estructura de datos anidada**: Cada documento de pixel art tiene un array `versionHistory`.
- **Metadatos completos**: Cada versión almacena URLs de imagen, timestamp, prompt utilizado y cambios aplicados.
- **Preservación de recursos**: Las imágenes de versiones anteriores no se eliminan automáticamente.
- **Límite de versiones**: Se mantiene un máximo de 5 versiones por imagen para optimizar espacio.

### 5. Procesamiento Inteligente de Prompts

**Motivación**:
- **Precisión en las modificaciones**: Lograr que los cambios solicitados se apliquen exactamente como se solicitan.
- **Preservación de elementos**: Mantener intactos los elementos que no deben modificarse.
- **Experiencia de usuario mejorada**: Resultados predecibles que corresponden con las expectativas del usuario.

**Implementación**:
- **Categorización de prompts**: Detección automática del tipo de modificación solicitada.
- **Prompts especializados**: Construcción de prompts optimizados según el tipo de cambio.
- **Análisis avanzado de imágenes**: Uso de GPT-4o para describir detalladamente la imagen existente.
- **Instrucciones enfáticas**: Prompts que claramente especifican qué debe cambiarse y qué debe mantenerse.

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
prompt: Una playa tropical con palmeras
tags: playa, tropical, pixelart
```

**Flujo interno**:
1. La imagen se guarda temporalmente.
2. Se aplica pixelación y procesamiento con `image_processing_service.py`.
3. Opcionalmente, se mejora con IA usando `openai_service.py:process_image`.
4. Si se proporciona un prompt, se utiliza para guiar el procesamiento.
5. La imagen resultante se guarda y registra en MongoDB.

### 3. Actualizar un Pixel Art con Prompt

**Solicitud API**:
```http
PUT /api/mongo/pixel-arts/abcd1234-5678
Content-Type: application/json

{
  "pixel_art_update": {
    "pixelSize": 8,
    "style": "retro",
    "backgroundType": "transparent",
    "paletteId": "gameboy"
  },
  "prompt": "Añadir un título que diga 'Los Cabos'",
  "apply_changes_to_image": true
}
```

**Flujo interno**:
1. La solicitud es validada y se obtiene la imagen existente.
2. La imagen se descarga si está en Cloudinary.
3. GPT-4o analiza y describe detalladamente la imagen actual.
4. Se categoriza el tipo de modificación (en este caso, "add_text").
5. Se crea un prompt especializado que enfatiza mantener los elementos originales.
6. DALL-E 3 genera una nueva versión con la modificación solicitada.
7. La versión anterior se guarda en el historial de versiones.
8. La nueva imagen se guarda y se actualiza el documento en MongoDB.

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

### 4. Precisión en Modificaciones de Imágenes

**Desafío**: Lograr que DALL-E aplique solo los cambios solicitados sin alterar el resto de la imagen.

**Solución**:
- Categorización inteligente de los tipos de prompts.
- Prompts altamente especializados según el tipo de modificación.
- Análisis detallado de la imagen original con GPT-4o.
- Instrucciones explícitas sobre qué preservar y qué modificar.

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

4. **Categorización avanzada de prompts**:
   - Expandir los tipos de modificaciones detectables.
   - Implementar nuevos generadores de prompts especializados.
   - Mejorar la detección de intención del usuario.

### Puntos de Integración

1. **Autenticación**: Preparado para integrar con:
   - OAuth (Auth0, Firebase)
   - Sistema de usuarios propio

2. **Sistemas de Almacenamiento**: Adicionales a Cloudinary:
   - Amazon S3
   - Google Cloud Storage

## Ejemplos de Código Clave

### Sistema de Modificación Inteligente de Imágenes

```python
def _categorize_prompt_type(self, prompt: str) -> str:
    """
    Categoriza el tipo de prompt para optimizar la construcción del prompt.
    """
    prompt_lower = prompt.lower()
    
    # Detectar si se trata de agregar texto
    if any(keyword in prompt_lower for keyword in ["añadir texto", "agregar título"]):
        return "add_text"
    
    # Detectar si se trata de cambiar colores
    if any(keyword in prompt_lower for keyword in ["cambiar color", "modificar color"]):
        return "color_change"
    
    # Más categorías...
    
    # Por defecto
    return "general_modification"

def _create_add_text_prompt(self, image_description, prompt, style_info, pixel_scale, color_codes):
    """
    Crea un prompt optimizado para añadir texto a una imagen.
    """
    return (
        f"Reproduce exactamente esta imagen de pixel art: {image_description}. "
        f"Agrega el siguiente texto en un estilo de fuente pixel art que combine con la imagen: {prompt}. "
        f"El texto debe ser claramente legible e integrado armoniosamente en la composición. "
        f"IMPORTANTE: Todos los elementos originales de la imagen deben permanecer exactamente iguales y en las mismas posiciones. "
        # Más instrucciones...
    )
```

### Gestión del Historial de Versiones

```python
# Guardar la versión anterior en el historial
version_history = existing_pixel_art.get("versionHistory", [])
version_entry = {
    "timestamp": datetime.now().isoformat(),
    "imageUrl": existing_pixel_art["imageUrl"],
    "thumbnailUrl": existing_pixel_art["thumbnailUrl"],
    "prompt": existing_pixel_art.get("prompt", ""),
    "changes": pixel_art_update
}

# Limitar historial a 5 versiones como máximo
if len(version_history) >= 5:
    version_history = version_history[-4:] # Mantener solo las 4 más recientes

version_history.append(version_entry)

# Actualizar el pixel art con la nueva imagen y metadatos
update_data = pixel_art_update.copy()
update_data.update({
    "imageUrl": processed_image_data["image_url"],
    "thumbnailUrl": processed_image_data["thumbnail_url"],
    "prompt": prompt,
    "versionHistory": version_history,
    "updatedAt": datetime.now()
})
```

## Conclusión

Este proyecto combina múltiples tecnologías (FastAPI, OpenAI, MongoDB, Cloudinary) para crear una solución completa de generación y procesamiento de pixel art. La arquitectura está diseñada para ser modular, extensible y robusta, con consideraciones específicas para entornos cloud y escalabilidad.

Las mejoras recientes en el sistema de modificación de imágenes y el historial de versiones proporcionan una experiencia más rica y precisa para los usuarios, permitiéndoles iterar sobre sus creaciones con mayor control y visibilidad de los cambios realizados.

Las decisiones de diseño, como la migración a MongoDB, el uso de Cloudinary, y la implementación de prompts especializados, están orientadas a resolver desafíos específicos de persistencia, escalabilidad y precisión en las modificaciones, mientras que la implementación paralela facilita una transición gradual y segura.