# 🐍 Imagen base optimizada
FROM python:3.13-slim

# Configuración del entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=America/Argentina/Buenos_Aires

WORKDIR /app

# Dependencias del sistema necesarias (PostgreSQL, compiladores)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt gunicorn

# Copiar el resto del código
COPY . .

# Exponer el puerto de FastAPI
EXPOSE 8000

# 🧠 Comando de inicio (modo producción con Gunicorn)
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "60"]
