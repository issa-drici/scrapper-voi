"""
Dashboard Streamlit — optimisation pour rechargeurs.
Uniquement : secteurs les plus chargés (par capture) + meilleurs créneaux et secteurs.
"""

import streamlit as st
import pandas as pd

from scrapers import list_scrapers, get_scraper

st.set_page_config(page_title="Optimisation rechargeurs", layout="wide")

scrapers_list = list_scrapers()
if not scrapers_list:
    st.error("Aucun scraper enregistré.")
    st.stop()

# Sidebar : scraper
scraper_options = {name: sid for sid, name in scrapers_list}
selected_name = st.sidebar.selectbox(
    "Scraper / source",
    options=list(scraper_options.keys()),
    index=0,
)
scraper_id = scraper_options[selected_name]
scraper = get_scraper(scraper_id)
data_dir = scraper.get_data_dir()

# Voi : ~15 km = batterie faible à recharger, ~40 km = bonne batterie
THRESHOLD_KM = 15
threshold_m = THRESHOLD_KM * 1000

files = sorted(data_dir.glob("*.parquet"), key=lambda p: p.stat().st_mtime, reverse=True)

st.title(selected_name)
st.caption(f"{len(files)} fichier(s) Parquet analysés")

if not files:
    st.warning("Aucun fichier Parquet. Le collecteur enregistre des captures périodiquement.")
    st.stop()

required_for_aggregate = ["lat", "lon", "current_range_meters", "captured_at"]
sample_df = pd.read_parquet(files[0])
if not all(c in sample_df.columns for c in required_for_aggregate):
    st.error("Les données de ce scraper n’ont pas les colonnes nécessaires (lat, lon, current_range_meters, captured_at).")
    st.stop()

# ---------- Tableau : secteur le plus chargé par capture ----------
@st.cache_data(ttl=300)
def _compute_top_sector_per_capture(_files, _threshold_m):
    rows = []
    for path in _files:
        try:
            d = pd.read_parquet(path)
            if d.empty or not all(c in d.columns for c in required_for_aggregate):
                continue
            d = d.dropna(subset=["lat", "lon", "current_range_meters", "captured_at"])
            low = d[d["current_range_meters"] < _threshold_m].copy()
            if low.empty:
                continue
            low["sector_lat"] = low["lat"].round(2)
            low["sector_lon"] = low["lon"].round(2)
            by_sector = low.groupby(["sector_lat", "sector_lon"], as_index=False).size()
            by_sector.columns = ["sector_lat", "sector_lon", "count"]
            top = by_sector.loc[by_sector["count"].idxmax()]
            ts = pd.to_datetime(low["captured_at"].iloc[0])
            rows.append({
                "Date": ts.date(),
                "Heure": ts.hour,
                "Secteur": f"({top['sector_lat']:.2f}, {top['sector_lon']:.2f})",
                "Nb trottinettes (faible autonomie)": int(top["count"]),
            })
        except Exception:
            continue
    if not rows:
        return None
    return pd.DataFrame(rows).sort_values(["Date", "Heure"], ascending=[False, False])

st.subheader("Secteur le plus chargé par capture (tous les fichiers)")
agg_df = _compute_top_sector_per_capture(files, threshold_m)
if agg_df is not None and not agg_df.empty:
    st.caption(f"Secteur (grille lat/lon) avec le plus de véhicules à recharger (< {THRESHOLD_KM} km d'autonomie, batterie faible Voi) pour chaque capture.")
    st.dataframe(agg_df, use_container_width=True, hide_index=True)
else:
    st.info("Pas assez de données.")

# ---------- Optimisation : créneau + secteur ----------
@st.cache_data(ttl=300)
def _compute_recharger_optimization(_files, _threshold_m):
    hour_rows = []
    sector_rows = []
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
            hour = ts.hour
            low["sector_lat"] = low["lat"].round(2)
            low["sector_lon"] = low["lon"].round(2)
            hour_rows.append({"hour": hour, "count": len(low)})
            for (slat, slon), cnt in low.groupby(["sector_lat", "sector_lon"]).size().items():
                sector_rows.append({"sector_lat": slat, "sector_lon": slon, "count": cnt})
                combo_rows.append({"hour": hour, "sector_lat": slat, "sector_lon": slon, "count": cnt})
        except Exception:
            continue
    if not hour_rows:
        return None, None, None
    by_hour = pd.DataFrame(hour_rows).groupby("hour", as_index=False)["count"].mean().round(1)
    by_hour.columns = ["Heure", "Moy. trottinettes à recharger"]
    by_sector = pd.DataFrame(sector_rows).groupby(["sector_lat", "sector_lon"], as_index=False)["count"].mean().round(1)
    by_sector = by_sector.sort_values("count", ascending=False).head(20)
    by_sector["Secteur"] = by_sector.apply(lambda r: f"({r['sector_lat']:.2f}, {r['sector_lon']:.2f})", axis=1)
    by_sector = by_sector[["Secteur", "count"]].rename(columns={"count": "Moy. trottinettes à recharger"})
    by_combo = pd.DataFrame(combo_rows).groupby(["hour", "sector_lat", "sector_lon"], as_index=False)["count"].mean().round(1)
    by_combo = by_combo.sort_values("count", ascending=False).head(25)
    by_combo["Secteur"] = by_combo.apply(lambda r: f"({r['sector_lat']:.2f}, {r['sector_lon']:.2f})", axis=1)
    by_combo = by_combo[["hour", "Secteur", "count"]].rename(columns={"hour": "Heure", "count": "Moy. à recharger"})
    return by_hour, by_sector, by_combo

opt_hour, opt_sector, opt_combo = _compute_recharger_optimization(files, threshold_m)
if opt_hour is not None:
    st.subheader("Où et quand intervenir ?")
    st.caption("Meilleurs **créneaux** et **secteurs** pour maximiser le nombre de trottinettes à recharger.")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Meilleurs créneaux horaires**")
        if not opt_hour.empty:
            st.bar_chart(opt_hour.set_index("Heure"))
        else:
            st.info("Pas de données.")
    with c2:
        st.markdown("**Meilleurs secteurs** (top 20)")
        if opt_sector is not None and not opt_sector.empty:
            st.dataframe(opt_sector, use_container_width=True, hide_index=True)
        else:
            st.info("Pas de données.")
    st.markdown("**Meilleures combinaisons secteur + heure** (top 25)")
    if opt_combo is not None and not opt_combo.empty:
        st.dataframe(opt_combo, use_container_width=True, hide_index=True)
    else:
        st.info("Pas de données.")
else:
    st.info("Pas assez de données pour l’optimisation.")
