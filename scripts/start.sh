#!/bin/bash

# Función para esperar hasta que MongoDB esté disponible
wait_for_mongodb() {
    echo "Waiting for MongoDB to be ready..."
    
    # Extraer host y puerto de la URL de MongoDB
    MONGODB_HOST=$(echo $MONGODB_URL | sed -e 's/^mongodb:\/\///' | cut -d':' -f1)
    MONGODB_PORT=$(echo $MONGODB_URL | sed -e 's/^mongodb:\/\///' | cut -d':' -f2 | cut -d'/' -f1)
    
    # Si el puerto no se ha extraído, usar el puerto predeterminado 27017
    if [ -z "$MONGODB_PORT" ]; then
        MONGODB_PORT=27017
    fi
    
    echo "Checking MongoDB connection at $MONGODB_HOST:$MONGODB_PORT..."
    
    # Esperar hasta que MongoDB esté disponible
    until nc -z $MONGODB_HOST $MONGODB_PORT; do
        echo "MongoDB is unavailable - sleeping"
        sleep 1
    done
    
    echo "MongoDB is up and running!"
}

# Comprobar si estamos usando MongoDB
if [ -n "$MONGODB_URL" ]; then
    # Instalar netcat para la comprobación de disponibilidad
    apt-get update && apt-get install -y netcat
    
    # Esperar a que MongoDB esté disponible
    wait_for_mongodb
fi

# Iniciar la aplicación FastAPI
echo "Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000