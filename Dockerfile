FROM python:3.9

WORKDIR /app

# Copiar archivos de dependencias
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY . .

# Crear estructura de directorios para imágenes
RUN mkdir -p /app/images/results
RUN mkdir -p /app/images/uploads

# Establecer permisos adecuados
RUN chmod -R 755 /app/images

# Exponer el puerto
EXPOSE 8000

# Ejecutar la aplicación
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]