FROM python:3.9

# Establecer directorio de trabajo
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
RUN chmod -R 755 /app/images

# Establecer PYTHONPATH para que incluya el directorio raíz
# Esto permite que Python encuentre los módulos correctamente
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Mostrar la estructura del proyecto para depuración
RUN find /app -type f -name "*.py" | sort

# Exponer el puerto
EXPOSE 8000

# Ejecutar la aplicación
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]