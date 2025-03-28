#!/bin/bash

# Función para esperar hasta que MongoDB esté disponible
wait_for_mongodb() {
    echo "Waiting for MongoDB to be ready..."
    
    # Verificar si es una URL SRV (mongodb+srv://)
    if [[ "$MONGODB_URL" == mongodb+srv://* ]]; then
        echo "Detectada URL SRV de MongoDB Atlas. No se puede verificar con nc, continuando..."
        # Para MongoDB Atlas, simplemente esperamos un poco
        sleep 5
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
    
    # Esperar hasta que MongoDB esté disponible
    until nc -z $MONGODB_HOST $MONGODB_PORT; do
        echo "MongoDB is unavailable - sleeping"
        sleep 1
    done
    
    echo "MongoDB is up and running!"
}

# Establecer valores por defecto si no están definidos
if [ -z "$MONGODB_URL" ]; then
  export MONGODB_URL="mongodb://mongodb:27017"
fi

if [ -z "$MONGODB_DB_NAME" ]; then
  export MONGODB_DB_NAME="pixelart_db"
fi

echo "MONGODB_URL: $MONGODB_URL"
echo "MONGODB_DB_NAME: $MONGODB_DB_NAME"

# Esperar a que MongoDB esté disponible (si es local)
wait_for_mongodb

# Iniciar la aplicación FastAPI
echo "Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000