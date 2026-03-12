"""Configuration du scraper Voi Le Havre (GBFS)."""

# API
TARGET_URL = (
    "https://api.voiapp.io/gbfs/fr/6bb6b5dc-1cda-4da7-9216-d3023a0bc54a/v2/336/free_bike_status.json"
)
REQUEST_TIMEOUT = 30

# Polling
POLLING_INTERVAL_SECONDS = 600  # 10 minutes

# Fichiers Parquet
FILENAME_PREFIX = "voi_havre"
