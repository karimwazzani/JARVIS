# Usa una imagen oficial y confiable de Python
FROM python:3.12-slim

# Evita que Python escriba archivos .pyc en disco y asegura que los logs salgan rápido
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH="/app/src"

# Directorio de trabajo
WORKDIR /app

# Copia los archivos de requerimientos
COPY requirements.txt .

# Instala todas las librerías necesarias
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código fuente
COPY src/ /app/src/

# Comando principal para mantener a JARVIS corriendo en segundo plano
CMD ["python", "src/main.py"]
