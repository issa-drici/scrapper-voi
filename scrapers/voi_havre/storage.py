"""Persistance Parquet pour Voi. Dépendances : pandas, pyarrow."""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from scrapers.voi_havre import config as scraper_config

logger = logging.getLogger(__name__)


def process_and_save(data: dict[str, Any], data_dir: Path) -> None:
    """Extrait data.bikes, ajoute captured_at, sauvegarde en Parquet."""
    bikes = data.get("data", {}).get("bikes", [])
    if not bikes:
        logger.warning("Aucun véhicule dans la réponse API")
        return
    df = pd.DataFrame(bikes)
    ts = datetime.now(timezone.utc)
    df["captured_at"] = ts
    prefix = scraper_config.FILENAME_PREFIX
    filename = f"{prefix}_{ts.strftime('%Y%m%d_%H%M')}.parquet"
    filepath = data_dir / filename
    df.to_parquet(filepath, engine="pyarrow", compression="snappy", index=False)
    logger.info("Sauvegardé: %s (%d véhicules)", filename, len(df))
