"""
Dashboard Streamlit — autonomie moyenne par heure de la journée + combinaisons secteur (optionnel).
Heures / jours affichés via helpers.time_helpers (Europe/Paris).
"""

import streamlit as st
import pandas as pd

from scrapers import list_scrapers, get_scraper
from helpers.time_helpers import TZ_PARIS, TZ_STORED, paris_date_and_slot_30, series_captured_at_to_paris

st.set_page_config(page_title="Dashboard Voi", layout="wide")

THRESHOLD_KM = 15
threshold_m = THRESHOLD_KM * 1000
required_combo = ["lat", "lon", "current_range_meters", "captured_at"]
required_hourly = ["current_range_meters", "captured_at"]

scrapers_list = list_scrapers()
if not scrapers_list:
    st.error("Aucun scraper enregistré.")
    st.stop()

scraper_options = {name: sid for sid, name in scrapers_list}
selected_name = st.sidebar.selectbox(
    "Scraper / source",
    options=list(scraper_options.keys()),
    index=0,
)
scraper_id = scraper_options[selected_name]
scraper = get_scraper(scraper_id)
data_dir = scraper.get_data_dir()

files = sorted(data_dir.glob("*.parquet"), key=lambda p: p.stat().st_mtime, reverse=True)

st.title(selected_name)
st.caption(f"{len(files)} fichier(s) Parquet analysés")

if not files:
    st.warning("Aucun fichier Parquet.")
    st.stop()

sample_df = pd.read_parquet(files[0])
if not all(c in sample_df.columns for c in required_hourly):
    st.error("Colonnes requises : current_range_meters, captured_at.")
    st.stop()


@st.cache_data(ttl=300)
def _hourly_avg_autonomy_km(_files):
    """Heures 0–23 Paris ; moyenne autonomie (km)."""
    parts = []
    for path in _files:
        try:
            d = pd.read_parquet(path)
            if d.empty or not all(c in d.columns for c in required_hourly):
                continue
            d = d.dropna(subset=["current_range_meters", "captured_at"])
            if d.empty:
                continue
            d = d.assign(hour=series_captured_at_to_paris(d["captured_at"]).dt.hour)
            parts.append(d[["hour", "current_range_meters"]])
        except Exception:
            continue
    if not parts:
        return None
    big = pd.concat(parts, ignore_index=True)
    by_h = big.groupby("hour", as_index=True)["current_range_meters"].mean() / 1000
    full = pd.Series(index=range(24), dtype=float)
    for h in range(24):
        full[h] = by_h[h] if h in by_h.index else float("nan")
    return full


hourly_km = _hourly_avg_autonomy_km(files)
if hourly_km is not None and hourly_km.notna().any():
    st.subheader("Autonomie moyenne par heure de la journée")
    st.caption(
        f"Heures **{TZ_PARIS}** (captures en **{TZ_STORED}**, conversion via `helpers.time_helpers`). "
        "0h–23h Paris. Ordonnée : autonomie moyenne (km)."
    )
    table = pd.DataFrame({
        "Heure": [f"{h}h" for h in range(24)],
        "Autonomie moyenne (km)": hourly_km.round(2).values,
    })
    st.dataframe(table, width="stretch", hide_index=True)
    chart_df = pd.DataFrame({"Autonomie moyenne (km)": hourly_km.values}, index=[f"{h}h" for h in range(24)])
    st.bar_chart(chart_df)
else:
    st.info("Pas assez de données pour l’autonomie par heure.")


if all(c in sample_df.columns for c in required_combo):

    @st.cache_data(ttl=300)
    def _compute_combo_table(_files, _threshold_m):
        combo_rows = []
        for path in _files:
            try:
                d = pd.read_parquet(path)
                if d.empty or not all(c in d.columns for c in required_combo):
                    continue
                d = d.dropna(subset=["lat", "lon", "current_range_meters", "captured_at"])
                low = d[d["current_range_meters"] < _threshold_m].copy()
                if low.empty:
                    continue
                day, slot_30 = paris_date_and_slot_30(low["captured_at"].iloc[0])
                low["sector_lat"] = low["lat"].round(2)
                low["sector_lon"] = low["lon"].round(2)
                for (slat, slon), cnt in low.groupby(["sector_lat", "sector_lon"]).size().items():
                    combo_rows.append({"date": day, "slot_30": slot_30, "sector_lat": slat, "sector_lon": slon, "count": cnt})
            except Exception:
                continue
        if not combo_rows:
            return None
        by_combo = pd.DataFrame(combo_rows).groupby(["date", "slot_30", "sector_lat", "sector_lon"], as_index=False)["count"].mean().round(1)
        by_combo = by_combo.sort_values("count", ascending=False).head(25)
        by_combo["Secteur"] = by_combo.apply(lambda r: f"({r['sector_lat']:.2f}, {r['sector_lon']:.2f})", axis=1)
        return by_combo[["date", "slot_30", "Secteur", "count"]].rename(columns={"date": "Jour", "slot_30": "Créneau (30 min)", "count": "Moy. à recharger"})

    st.subheader("Meilleures combinaisons secteur + jour + créneau 30 min (top 25)")
    combo_df = _compute_combo_table(files, threshold_m)
    if combo_df is not None and not combo_df.empty:
        st.caption(f"Jour / créneaux en **{TZ_PARIS}** (`helpers.time_helpers`). Trottinettes < {THRESHOLD_KM} km.")
        st.dataframe(combo_df, width="stretch", hide_index=True)
    else:
        st.info("Pas assez de données pour les combinaisons secteur.")
