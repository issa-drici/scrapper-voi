"""
Dashboard Streamlit — uniquement : meilleures combinaisons secteur + jour + créneau 30 min.
"""

import streamlit as st
import pandas as pd

from scrapers import list_scrapers, get_scraper

st.set_page_config(page_title="Optimisation rechargeurs", layout="wide")

# Voi : ~15 km = batterie faible à recharger
THRESHOLD_KM = 15
threshold_m = THRESHOLD_KM * 1000

required_for_aggregate = ["lat", "lon", "current_range_meters", "captured_at"]

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
    st.warning("Aucun fichier Parquet. Le collecteur enregistre des captures périodiquement.")
    st.stop()

sample_df = pd.read_parquet(files[0])
if not all(c in sample_df.columns for c in required_for_aggregate):
    st.error("Les données de ce scraper n'ont pas les colonnes nécessaires (lat, lon, current_range_meters, captured_at).")
    st.stop()


@st.cache_data(ttl=300)
def _compute_combo_table(_files, _threshold_m):
    combo_rows = []
    for path in _files:
        try:
            d = pd.read_parquet(path)
            if d.empty or not all(c in d.columns for c in required_for_aggregate):
                continue
            d = d.dropna(subset=["lat", "lon", "current_range_meters", "captured_at"])
            low = d[d["current_range_meters"] < _threshold_m].copy()
            if low.empty:
                continue
            ts = pd.to_datetime(low["captured_at"].iloc[0])
            minute_bin = (ts.minute // 30) * 30
            slot_30 = f"{ts.hour:02d}h{minute_bin:02d}"
            day = ts.date()
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
    st.caption(f"Secteur, jour et créneau où il y a en moyenne le plus de trottinettes à recharger (< {THRESHOLD_KM} km).")
    st.dataframe(combo_df, width="stretch", hide_index=True)
else:
    st.info("Pas assez de données.")
