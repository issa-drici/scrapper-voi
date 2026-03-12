"""Boucle de collecte pour Voi Le Havre."""

import time

from config import setup_logging
from scrapers.voi_havre import config as scraper_config
from scrapers.voi_havre import get_data_dir
from scrapers.voi_havre.api import fetch
from scrapers.voi_havre.storage import process_and_save


def run() -> None:
    """Boucle principale : fetch toutes les POLLING_INTERVAL_SECONDS."""
    logger = setup_logging()
    data_dir = get_data_dir()
    logger.info("Démarrage collecteur Voi Le Havre — données: %s", data_dir)
    logger.info("URL: %s — intervalle: %d s", scraper_config.TARGET_URL, scraper_config.POLLING_INTERVAL_SECONDS)

    while True:
        try:
            logger.info("Récupération...")
            data = fetch(scraper_config.TARGET_URL, timeout=scraper_config.REQUEST_TIMEOUT)
            process_and_save(data, data_dir)
            logger.info("Prochaine collecte dans %d min", scraper_config.POLLING_INTERVAL_SECONDS // 60)
        except KeyboardInterrupt:
            logger.info("Arrêt demandé")
            break
        except Exception as e:
            logger.exception("Erreur: %s", e)
            logger.info("Nouvelle tentative dans %d min", scraper_config.POLLING_INTERVAL_SECONDS // 60)
        time.sleep(scraper_config.POLLING_INTERVAL_SECONDS)
