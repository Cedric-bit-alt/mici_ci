# ------------------------------------------------------
# Dockerfile pour Ada Bank - Environnement de développement
# ------------------------------------------------------

# Image de base Python
FROM python:3.10-slim

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    GDAL_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgdal.so.32 \
    GEOS_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgeos_c.so.1

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    gcc g++ \
    libpq-dev \
    postgresql-client \
    gdal-bin \
    libgdal-dev \
    python3-gdal \
    libgeos-dev \
    libproj-dev \
    libgobject-2.0-0 \
    libglib2.0-0 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Création du répertoire de travail
WORKDIR /app

# Copie des fichiers de dépendances
COPY requirements.txt .

# Installation des dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source (inclut le fichier .env)
COPY . .

# Création des répertoires nécessaires
RUN mkdir -p logs media static

# Exposition du port Django
EXPOSE 8080

# Commande par défaut :
# 1. Appliquer les migrations
# 2. Collecter les fichiers statiques
# 3. Lancer le serveur Django sur 0.0.0.0:8080
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8080"]
# Note : Pour le développement, le serveur Django est utilisé.
# En production, il est recommandé d'utiliser un serveur WSGI comme Gunicorn ou uWSGI.