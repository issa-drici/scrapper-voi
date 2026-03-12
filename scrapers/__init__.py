"""
Registre des scrapers. Chaque sous-module (voi_havre, …) expose :
  SCRAPER_ID, NAME, get_data_dir(), run()
Optionnel pour le dashboard : map_center, file_label_prefix.
"""

from pathlib import Path
from typing import Any

# Import des scrapers pour les enregistrer
from scrapers import voi_havre

_REGISTRY: dict[str, Any] = {
    voi_havre.SCRAPER_ID: voi_havre,
}


def list_scrapers() -> list[tuple[str, str]]:
    """Liste (id, nom affiché) de tous les scrapers."""
    return [(sid, getattr(m, "NAME", sid)) for sid, m in _REGISTRY.items()]


def get_scraper(scraper_id: str):
    """Retourne le module scraper pour cet id."""
    if scraper_id not in _REGISTRY:
        raise ValueError(f"Scraper inconnu: {scraper_id}. Disponibles: {list(_REGISTRY.keys())}")
    return _REGISTRY[scraper_id]


def get_data_dir_for(scraper_id: str) -> Path:
    """Répertoire des données pour un scraper."""
    return get_scraper(scraper_id).get_data_dir()
