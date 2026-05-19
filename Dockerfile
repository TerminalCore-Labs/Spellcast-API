FROM python:3.12.3-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Instalar dependencias

RUN apt-get update && apt-get install -y \
    build-essential \
    libasound2 \
    libssl-dev \
    ca-certificates \
    wget \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Copiar el resto de tu código
COPY . .

# Exponer el puerto que Fly.io usará
EXPOSE 8000

# Ejecutar la app con Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]