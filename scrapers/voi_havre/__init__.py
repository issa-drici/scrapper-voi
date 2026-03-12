"""Scraper Voi — Le Havre (GBFS free_bike_status)."""

from pathlib import Path

from config import get_base_data_dir

SCRAPER_ID = "voi_havre"
NAME = "Voi Le Havre"

# Optionnel : vue carte pour le dashboard (heatmap)
map_center = {"latitude": 49.4944, "longitude": 0.1079, "zoom": 12, "pitch": 0, "bearing": 0}
file_label_prefix = "voi_havre_"


def get_data_dir() -> Path:
    """Répertoire des Parquet pour ce scraper."""
    path = get_base_data_dir() / SCRAPER_ID
    path.mkdir(parents=True, exist_ok=True)
    return path


def run() -> None:
    """Lance la boucle de collecte."""
    from scrapers.voi_havre.run import run as _run
    _run()
