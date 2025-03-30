# PixelArt Generator API

API backend para la generación y procesamiento de arte en píxeles utilizando inteligencia artificial. Este proyecto complementa una aplicación Angular para la creación de imágenes tipo pixel art a partir de prompts o imágenes existentes.

## Características

- Generación de pixel art a partir de prompts de texto usando OpenAI DALL-E
- Procesamiento de imágenes para convertirlas en pixel art
- **¡NUEVO!** Modificación inteligente de imágenes existentes con prompts específicos
- **¡NUEVO!** Historial de versiones para seguir la evolución de tus creaciones
- Gestión de paletas de colores
- Configuración personalizada para el tamaño de píxel, estilo, fondo y más
- API RESTful construida con FastAPI
- Soporte para MongoDB para una mejor persistencia de datos
- Despliegue con Docker para facilitar la instalación y ejecución

## Requisitos previos

- Python 3.9+
- Una clave API de OpenAI con acceso a:
  - DALL-E 3 para generación de imágenes
  - GPT-4o para análisis de imágenes
- Docker y Docker Compose (para instalación con Docker)
- MongoDB (opcional, se puede usar con Docker)

## Instalación

### Usando Docker (Recomendado)

1. Clona el repositorio:

```bash
git clone https://github.com/julioonmartinez/pixelart-api.git
cd pixelart-api
```

2. Crea un archivo `.env` basado en `.env.example`:

```bash
cp .env.example .env
```

3. Edita el archivo `.env` y agrega tus credenciales:

```
OPENAI_API_KEY=tu_clave_api_aqui
MONGODB_URL=mongodb://mongodb:27017
MONGODB_DB_NAME=pixelart_db
USE_CLOUDINARY=False
# Si usas Cloudinary, añade estas variables
# CLOUDINARY_CLOUD_NAME=
# CLOUDINARY_API_KEY=
# CLOUDINARY_API_SECRET=
```

4. Inicia los servicios con Docker Compose:

```bash
docker-compose up -d
```

Este comando iniciará:
- La API de PixelArt en el puerto 8000
- MongoDB en el puerto 27017
- Mongo Express (interfaz web para MongoDB) en el puerto 8081

### Instalación Manual

1. Clona el repositorio:

```bash
git clone https://github.com/tuusuario/pixelart-api.git
cd pixelart-api
```

2. Crea un entorno virtual e instala las dependencias:

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Crea un archivo `.env` basado en `.env.example`:

```bash
cp .env.example .env
```

4. Edita el archivo `.env` y agrega tus credenciales.

5. Inicia el servidor:

```bash
python -m app.main
```

## Documentación de la API

Una vez que el servidor esté en funcionamiento, puedes acceder a la documentación interactiva de la API:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Base de Datos

### Opción 1: SQLite (Predeterminado)
El proyecto utiliza SQLite por defecto, lo que facilita la instalación y configuración inicial.

### Opción 2: MongoDB (Recomendado para producción)
Para una mayor persistencia y escalabilidad, se ha añadido soporte para MongoDB:

- Usar las rutas con prefijo `/api/mongo/` para acceder a los endpoints que utilizan MongoDB
- Para migrar datos existentes de SQLite a MongoDB:
  ```bash
  curl -X POST http://localhost:8000/api/migration/migrate-to-mongodb
  ```
- Para administrar MongoDB, accede a Mongo Express en `http://localhost:8081` 
  (Usuario predeterminado: admin, contraseña: pass)

## Estructura del proyecto

```
pixelart-api/
├── app/
│   ├── main.py                  # Punto de entrada de la aplicación
│   ├── config.py                # Configuraciones globales
│   ├── models/                  # Modelos de Pydantic
│   ├── database/                # Configuración de bases de datos
│   │   ├── database.py          # Conexión SQLite
│   │   ├── mongodb.py           # Conexión MongoDB
│   │   └── models.py            # Modelos SQLAlchemy
│   ├── services/                # Lógica de negocio
│   │   ├── pixel_art.py         # Servicio SQLite
│   │   ├── pixel_art_mongo.py   # Servicio MongoDB
│   │   ├── openai_service.py    # Interacción con OpenAI
│   │   └── ...
│   ├── api/                     # Rutas de la API
│   │   ├── routes/              # Controladores de rutas
│   │   │   ├── pixel_art.py     # Rutas SQLite
│   │   │   ├── pixel_art_mongo.py # Rutas MongoDB
│   │   │   └── ...
│   └── utils/                   # Utilidades
├── docker-compose.yml           # Configuración de Docker Compose
├── Dockerfile                   # Configuración de Docker
├── requirements.txt             # Dependencias del proyecto
└── .env                         # Variables de entorno
```

## Endpoints principales

### SQLite (Original)
- **GET /api/pixel-arts/**: Lista todos los pixel arts
- **POST /api/pixel-arts/generate-from-prompt**: Genera pixel art desde un prompt
- **POST /api/pixel-arts/process-image**: Procesa una imagen para convertirla en pixel art
- **GET /api/palettes/**: Lista todas las paletas disponibles

### MongoDB (Recomendado)
- **GET /api/mongo/pixel-arts/**: Lista todos los pixel arts (MongoDB)
- **POST /api/mongo/pixel-arts/generate-from-prompt**: Genera pixel art usando MongoDB
- **POST /api/mongo/pixel-arts/process-image**: Procesa una imagen usando MongoDB (ahora soporta prompt opcional)
- **PUT /api/mongo/pixel-arts/{id}**: Actualiza un pixel art existente, con opción para modificar la imagen con IA
- **GET /api/mongo/pixel-arts/search/**: Búsqueda avanzada (solo MongoDB)

### Migración
- **POST /api/migration/migrate-to-mongodb**: Migra todos los datos de SQLite a MongoDB
- **POST /api/migration/migrate-palettes**: Migra solo las paletas
- **POST /api/migration/migrate-pixel-arts**: Migra solo los pixel arts

## Nuevas Funcionalidades

### Modificación de imágenes con prompts

Ahora puedes modificar imágenes existentes enviando un prompt que describa los cambios deseados:

```http
PUT /api/mongo/pixel-arts/{id}
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

El sistema:
1. Analiza la imagen original con GPT-4o
2. Detecta el tipo de modificación solicitada
3. Aplica los cambios específicos manteniendo el resto de la imagen intacta
4. Guarda la versión anterior en el historial

### Historial de versiones

Cada pixel art ahora mantiene un historial de sus versiones anteriores (hasta 5 versiones):

```json
{
  "id": "abcd1234",
  "name": "Mi playa pixel art",
  "imageUrl": "...",
  "versionHistory": [
    {
      "timestamp": "2025-03-29T22:06:54.799",
      "imageUrl": "...",
      "thumbnailUrl": "...",
      "prompt": "Playa tropical",
      "changes": { ... }
    }
  ]
}
```

Esto permite a los usuarios:
- Ver cómo ha evolucionado su creación
- Restaurar versiones anteriores si lo desean
- Comparar los cambios entre versiones

### Procesamiento de imagen guiado por prompt

Al subir una imagen para ser procesada como pixel art, ahora puedes incluir un prompt opcional:

```
POST /api/mongo/pixel-arts/process-image
Content-Type: multipart/form-data

file: [archivo_imagen.jpg]
name: Playa tropical
pixelSize: 8
style: retro
paletteId: pico8
prompt: Una playa tropical con palmeras y agua cristalina
```

El prompt ayuda a guiar el proceso de conversión a pixel art, produciendo resultados más alineados con la visión del usuario.

## Despliegue en Producción

Para el despliegue en producción:

1. Configura MongoDB:
   - Usa MongoDB Atlas o un servidor MongoDB administrado
   - Actualiza `MONGODB_URL` en tu archivo `.env` con la URL de conexión completa

2. Configura las variables de entorno necesarias:
   - `OPENAI_API_KEY`: Tu clave API de OpenAI
   - `MONGODB_URL`: URL de conexión a MongoDB
   - `MONGODB_DB_NAME`: Nombre de la base de datos

3. Despliega con Docker:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

## Solución de problemas

### Logs
Para ver los logs de los contenedores:
```bash
docker logs pixelart-api
docker logs pixelart-mongodb
docker logs pixelart-mongo-express
```

### Problemas comunes
- **MongoDB no inicia**: Verifica que el puerto 27017 no esté siendo usado por otra aplicación
- **API no se conecta a MongoDB**: Revisa la URL de conexión y asegúrate que MongoDB esté ejecutándose
- **Error en la migración**: Verifica los logs para detalles específicos del error
- **Error 500 al actualizar imágenes**: Asegúrate de que tu cuenta de OpenAI tenga acceso a GPT-4o y DALL-E 3
- **Modificaciones imprecisas**: Intenta ser más específico en el prompt, describiendo exactamente qué cambios quieres realizar

## Licencia

Este proyecto está licenciado bajo la licencia MIT.