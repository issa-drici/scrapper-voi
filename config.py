"""
Configuration centralisée du collecteur Voi.
Constantes, chemins et configuration du logging — sans dépendances tierces lourdes.
"""

import logging
from pathlib import Path

# API Voi - Le Havre (GBFS)
TARGET_URL = (
    "https://api.voiapp.io/gbfs/fr/6bb6b5dc-1cda-4da7-9216-d3023a0bc54a/v2/336/free_bike_status.json"
)
REQUEST_TIMEOUT = 30

# Polling
POLLING_INTERVAL_SECONDS = 600  # 10 minutes

# Stockage
DATA_DIR_DOCKER = Path("/app/data")
DATA_DIR_LOCAL = Path("./data")


def get_data_directory() -> Path:
    """Retourne le répertoire de données (Docker si /app/data existe, sinon local)."""
    if DATA_DIR_DOCKER.exists():
        return DATA_DIR_DOCKER
    path = DATA_DIR_LOCAL
    path.mkdir(exist_ok=True)
    return path


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure le logging et retourne le logger du module principal."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger(__name__)
