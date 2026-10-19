#!/bin/bash

# Script de démarrage pour le projet MICI

echo "=== Démarrage du projet MICI ==="

# Activer l'environnement virtuel
source venv/bin/activate

# Créer les migrations si nécessaire
echo "Création des migrations..."
python manage.py makemigrations

# Appliquer les migrations
echo "Application des migrations..."
python manage.py migrate

# Collecter les fichiers statiques
echo "Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# Lancer le serveur
echo "Lancement du serveur de développement..."
python manage.py runserver

