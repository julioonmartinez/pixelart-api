#!/bin/bash

# Función para esperar hasta que MongoDB esté disponible
wait_for_mongodb() {
    echo "Waiting for MongoDB to be ready..."
    
    # Si estamos en Render, omitir la verificación de conexión
    if [ -n "$RENDER" ]; then
        echo "Running on Render, skipping MongoDB connection check..."
        return 0
    fi
    
    # Verificar si es una URL SRV (mongodb+srv://)
    if [[ "$MONGODB_URL" == mongodb+srv://* ]]; then
        echo "Detected MongoDB Atlas SRV URL. Skipping connection check..."
        return 0
    fi
    
    # Para URLs normales de MongoDB, extraer host y puerto
    MONGODB_HOST=$(echo $MONGODB_URL | sed -e 's/^mongodb:\/\///' | cut -d':' -f1 | cut -d'/' -f1)
    MONGODB_PORT=$(echo $MONGODB_URL | sed -e 's/^mongodb:\/\///' | cut -d':' -f2 | cut -d'/' -f1)
    
    # Si el puerto no se ha extraído, usar el puerto predeterminado 27017
    if [ -z "$MONGODB_PORT" ]; then
        MONGODB_PORT=27017
    fi
    
    echo "Checking MongoDB connection at $MONGODB_HOST:$MONGODB_PORT..."
    
    # Esperar hasta que MongoDB esté disponible, con un límite de intentos
    MAX_RETRIES=30
    COUNT=0
    until nc -z $MONGODB_HOST $MONGODB_PORT || [ $COUNT -eq $MAX_RETRIES ]; do
        echo "MongoDB is unavailable - sleeping (attempt $COUNT/$MAX_RETRIES)"
        sleep 1
        COUNT=$((COUNT+1))
    done
    
    if [ $COUNT -eq $MAX_RETRIES ]; then
        echo "WARNING: Could not connect to MongoDB after $MAX_RETRIES attempts. Continuing anyway..."
        return 0
    fi
    
    echo "MongoDB is up and running!"
}

# Establecer valores por defecto si no están definidos
if [ -z "$MONGODB_URL" ]; then
  echo "No MONGODB_URL specified, using default"
  export MONGODB_URL="mongodb://localhost:27017"
fi

if [ -z "$MONGODB_DB_NAME" ]; then
  echo "No MONGODB_DB_NAME specified, using default"
  export MONGODB_DB_NAME="pixelart_db"
fi

echo "MONGODB_URL: $MONGODB_URL (host: $(echo $MONGODB_URL | sed -e 's/^mongodb:\/\///' | cut -d':' -f1))"
echo "MONGODB_DB_NAME: $MONGODB_DB_NAME"

# Esperar a que MongoDB esté disponible (si es local)
wait_for_mongodb

# Obtener el puerto de la variable de entorno o usar 8000 como predeterminado
PORT=${PORT:-8000}

# Iniciar la aplicación FastAPI
echo "Starting FastAPI application on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT