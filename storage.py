"""
Persistance des données Voi en Parquet.
Dépendances : pandas, pyarrow.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def process_and_save(data: dict[str, Any], data_dir: Path) -> None:
    """
    Extrait les véhicules du JSON GBFS, ajoute captured_at et sauvegarde en Parquet.

    Args:
        data: Réponse JSON de l'API (data.bikes)
        data_dir: Répertoire de sauvegarde
    """
    bikes = data.get("data", {}).get("bikes", [])

    if not bikes:
        logger.warning("Aucun véhicule trouvé dans la réponse API")
        return

    df = pd.DataFrame(bikes)
    ts = datetime.now(timezone.utc)
    df["captured_at"] = ts

    filename = f"voi_havre_{ts.strftime('%Y%m%d_%H%M')}.parquet"
    filepath = data_dir / filename

    df.to_parquet(filepath, engine="pyarrow", compression="snappy", index=False)
    logger.info("Données sauvegardées: %s (%d véhicules)", filename, len(df))
