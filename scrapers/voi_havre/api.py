"""Client API Voi GBFS. Dépendance : requests."""

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)


def fetch(url: str, timeout: int = 30) -> dict[str, Any]:
    """Récupère le JSON depuis l'API free_bike_status."""
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error("Erreur récupération données: %s", e)
        raise
