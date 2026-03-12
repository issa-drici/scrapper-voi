"""
Configuration globale du repo (chemins de données, logging).
Chaque scraper a sa propre config dans scrapers/<id>/config.py.
"""

import logging
from pathlib import Path

# Répertoire racine des données (chaque scraper a un sous-dossier)
DATA_DIR_DOCKER = Path("/app/data")
DATA_DIR_LOCAL = Path("./data")


def get_base_data_dir() -> Path:
    """Répertoire racine des données (Docker si /app/data existe, sinon local)."""
    if DATA_DIR_DOCKER.exists():
        return DATA_DIR_DOCKER
    path = DATA_DIR_LOCAL
    path.mkdir(exist_ok=True)
    return path


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure le logging et retourne un logger."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger(__name__)
