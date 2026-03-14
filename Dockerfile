FROM python:3.11-slim

WORKDIR /app

# Copie des dépendances et installation
COPY requirements.txt .
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source (scrapers + dashboard)
COPY config.py main.py dashboard.py entrypoint.sh .
COPY helpers/ helpers/
COPY scrapers/ scrapers/
RUN chmod +x entrypoint.sh

# Création du répertoire de données (sera monté comme volume)
RUN mkdir -p /app/data && chmod 755 /app/data

# Streamlit écoute sur 8501
EXPOSE 8501

# Worker en arrière-plan + Streamlit au premier plan
CMD ["./entrypoint.sh"]
