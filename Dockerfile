FROM python:3.9

# Establecer directorio de trabajo
WORKDIR /app

# Instalar netcat para verificación de disponibilidad
RUN apt-get update && apt-get install -y netcat-openbsd

# Copiar archivos de dependencias
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY . .

# Crear estructura de directorios para imágenes
RUN mkdir -p /app/images/results
RUN mkdir -p /app/images/uploads
RUN chmod -R 755 /app/images

# Establecer PYTHONPATH para que incluya el directorio raíz
ENV PYTHONPATH="${PYTHONPATH}:/"

# Variables de entorno para MongoDB
ENV MONGODB_URL="mongodb://mongodb:27017"
ENV MONGODB_DB_NAME="pixelart_db"

# Exponer el puerto
EXPOSE 8000

# Script de inicio para esperar a que MongoDB esté disponible
COPY ./scripts/start.sh /start.sh
RUN chmod +x /start.sh

# Ejecutar script de inicio que incluye la espera a MongoDB
CMD ["/start.sh"]