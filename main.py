#!/usr/bin/env python3
"""
Voi Battery Tracker - Le Havre (V1)
Point d'entrée : boucle de collecte des données (orchestration).
"""

import time

from config import (
    POLLING_INTERVAL_SECONDS,
    REQUEST_TIMEOUT,
    TARGET_URL,
    get_data_directory,
    setup_logging,
)
from api import fetch_voi_data
from storage import process_and_save


def main() -> None:
    """Boucle principale de collecte des données."""
    logger = setup_logging()
    logger.info("Démarrage du collecteur Voi Battery Tracker - Le Havre")
    logger.info("URL cible: %s", TARGET_URL)
    logger.info(
        "Intervalle de polling: %d secondes (%d minutes)",
        POLLING_INTERVAL_SECONDS,
        POLLING_INTERVAL_SECONDS // 60,
    )

    data_dir = get_data_directory()
    logger.info("Répertoire de données: %s", data_dir)

    while True:
        try:
            logger.info("Récupération des données...")
            data = fetch_voi_data(TARGET_URL, timeout=REQUEST_TIMEOUT)
            process_and_save(data, data_dir)
            logger.info(
                "Prochaine collecte dans %d minutes...",
                POLLING_INTERVAL_SECONDS // 60,
            )
        except KeyboardInterrupt:
            logger.info("Arrêt demandé par l'utilisateur")
            break
        except Exception as e:
            logger.exception("Erreur dans la boucle principale: %s", e)
            logger.info(
                "Nouvelle tentative dans %d minutes...",
                POLLING_INTERVAL_SECONDS // 60,
            )

        time.sleep(POLLING_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
