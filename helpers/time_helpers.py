"""
Dates et heures du projet.

- **Stockage** : toujours en UTC (captures, noms de fichiers cohérents serveur).
- **Affichage / stats** : Europe/Paris (heure locale française).

Utiliser ce module partout qu’on manipule `captured_at` ou des créneaux horaires.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd

TZ_STORED = "UTC"
TZ_PARIS = "Europe/Paris"
_ZONE_PARIS = ZoneInfo(TZ_PARIS)


def now_utc() -> datetime:
    """Horodatage « maintenant » pour enregistrement (timezone-aware UTC)."""
    return datetime.now(timezone.utc)


def to_paris(dt: datetime) -> datetime:
    """Un instant UTC (ou naïf interprété comme UTC) → même instant en Europe/Paris."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.astimezone(_ZONE_PARIS)


def series_captured_at_to_paris(s: pd.Series) -> pd.Series:
    """
    Colonne `captured_at` (série) → datetimes timezone-aware Europe/Paris.
    Naïf = UTC.
    """
    ts = pd.to_datetime(s)
    if ts.dt.tz is None:
        ts = ts.dt.tz_localize(TZ_STORED)
    else:
        ts = ts.dt.tz_convert(TZ_STORED)
    return ts.dt.tz_convert(TZ_PARIS)


def paris_hour(captured_at: Any) -> int:
    """Heure 0–23 à Paris pour un instant de capture (UTC ou naïf UTC)."""
    ts = pd.Timestamp(captured_at)
    if ts.tzinfo is None:
        ts = ts.tz_localize(TZ_STORED)
    else:
        ts = ts.tz_convert(TZ_STORED)
    return int(ts.tz_convert(TZ_PARIS).hour)


def paris_date_and_slot_30(captured_at: Any) -> tuple:
    """
    Instant de capture → (date calendaire Paris, créneau 30 min 'HHhMM').
    """
    ts = pd.Timestamp(captured_at)
    if ts.tzinfo is None:
        ts = ts.tz_localize(TZ_STORED)
    else:
        ts = ts.tz_convert(TZ_STORED)
    paris = ts.tz_convert(TZ_PARIS)
    minute_bin = (paris.minute // 30) * 30
    slot = f"{paris.hour:02d}h{minute_bin:02d}"
    return paris.date(), slot
