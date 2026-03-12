"""
Client API Voi (GBFS).
Dépendance : requests uniquement.
"""

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)


def fetch_voi_data(url: str, timeout: int = 30) -> dict[str, Any]:
    """
    Récupère les données depuis l'API GBFS de Voi.

    Args:
        url: URL de l'API free_bike_status
        timeout: Délai maximal de la requête en secondes

    Returns:
        Données JSON de l'API (structure GBFS)

    Raises:
        requests.RequestException: En cas d'erreur HTTP ou réseau
    """
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error("Erreur lors de la récupération des données: %s", e)
        raise
