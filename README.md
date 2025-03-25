# PixelArt Generator API

API backend para la generación y procesamiento de arte en píxeles utilizando inteligencia artificial. Este proyecto complementa una aplicación Angular 19 para la creación de imágenes tipo pixel art a partir de prompts o imágenes existentes.

## Características

- Generación de pixel art a partir de prompts de texto usando OpenAI DALL-E
- Procesamiento de imágenes para convertirlas en pixel art
- Gestión de paletas de colores
- Configuración personalizada para el tamaño de píxel, estilo, fondo y más
- API RESTful construida con FastAPI

## Requisitos previos

- Python 3.9+
- Una clave API de OpenAI

## Instalación

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

4. Edita el archivo `.env` y agrega tu clave API de OpenAI:

```
OPENAI_API_KEY=tu_clave_api_aqui
```

## Ejecución

Inicia el servidor de desarrollo:

```bash
python -m app.main
```

O usando uvicorn directamente:

```bash
uvicorn app.main:app --reload
```

El servidor se iniciará en `http://localhost:8000`.

## Documentación de la API

Una vez que el servidor esté en funcionamiento, puedes acceder a la documentación interactiva de la API:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Estructura del proyecto

```
pixelart-api/
├── app/
│   ├── main.py              # Punto de entrada de la aplicación
│   ├── config.py            # Configuraciones globales
│   ├── models/              # Modelos de Pydantic
│   ├── database/            # Configuración de la base de datos
│   ├── services/            # Lógica de negocio
│   ├── api/                 # Rutas de la API
│   └── utils/               # Utilidades
├── requirements.txt         # Dependencias del proyecto
└── .env                     # Variables de entorno
```

## Endpoints principales

- **GET /api/v1/pixel-arts/**: Lista todos los pixel arts
- **POST /api/v1/pixel-arts/generate-from-prompt**: Genera pixel art desde un prompt
- **POST /api/v1/pixel-arts/process-image**: Procesa una imagen para convertirla en pixel art
- **GET /api/v1/palettes/**: Lista todas las paletas disponibles
- **GET /api/v1/settings/**: Obtiene la configuración del usuario

## Integración con Angular

Esta API está diseñada para integrarse con una aplicación Angular 19 que proporciona la interfaz de usuario. La aplicación Angular debe configurarse para hacer solicitudes a esta API en `http://localhost:8000/api/v1/`.

## Licencia

Este proyecto está licenciado bajo la licencia MIT.