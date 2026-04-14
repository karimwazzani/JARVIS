# Usa una imagen oficial y confiable de Python
FROM python:3.12-slim

# Evita que Python escriba archivos .pyc en disco y asegura que los logs salgan rápido
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Directorio de trabajo
WORKDIR /app

# Instala dependencias del sistema necesarias (ej: compiladores)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copia los archivos de requerimientos
COPY requirements.txt .

# Instala todas las librerías necesarias
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código fuente
COPY src/ /app/src/

# Comando principal para mantener a JARVIS corriendo 24/7
CMD ["python", "src/main.py"]
