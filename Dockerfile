FROM python:3.11-slim

WORKDIR /app

# Copie des dépendances et installation
COPY requirements.txt .
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY config.py api.py storage.py main.py .

# Création du répertoire de données (sera monté comme volume)
RUN mkdir -p /app/data && chmod 755 /app/data

# Commande par défaut
CMD ["python", "main.py"]
