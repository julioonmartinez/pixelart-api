# PixelArt Generator API

API backend para la generación y procesamiento de arte en píxeles utilizando inteligencia artificial. Este proyecto complementa una aplicación Angular para la creación de imágenes tipo pixel art a partir de prompts o imágenes existentes.

## Características

- Generación de pixel art a partir de prompts de texto usando OpenAI DALL-E
- Procesamiento de imágenes para convertirlas en pixel art
- Gestión de paletas de colores
- Configuración personalizada para el tamaño de píxel, estilo, fondo y más
- API RESTful construida con FastAPI
- **¡NUEVO!** Soporte para MongoDB para una mejor persistencia de datos
- **¡NUEVO!** Despliegue con Docker para facilitar la instalación y ejecución

## Requisitos previos

- Python 3.9+
- Una clave API de OpenAI
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

### MongoDB (Nuevo)
- **GET /api/mongo/pixel-arts/**: Lista todos los pixel arts (MongoDB)
- **POST /api/mongo/pixel-arts/generate-from-prompt**: Genera pixel art usando MongoDB
- **POST /api/mongo/pixel-arts/process-image**: Procesa una imagen usando MongoDB
- **GET /api/mongo/pixel-arts/search/**: Búsqueda avanzada (solo MongoDB)

### Migración
- **POST /api/migration/migrate-to-mongodb**: Migra todos los datos de SQLite a MongoDB
- **POST /api/migration/migrate-palettes**: Migra solo las paletas
- **POST /api/migration/migrate-pixel-arts**: Migra solo los pixel arts

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

## Licencia

Este proyecto está licenciado bajo la licencia MIT.