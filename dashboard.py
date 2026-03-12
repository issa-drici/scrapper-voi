"""
Dashboard Streamlit — visualisation multi-scrapers.
Choisis un scraper dans la sidebar, puis explore ses fichiers Parquet.
"""

import streamlit as st
import pandas as pd
import pydeck as pdk
from pathlib import Path

from scrapers import list_scrapers, get_scraper

st.set_page_config(page_title="Scrapers — Données", layout="wide")

scrapers_list = list_scrapers()
if not scrapers_list:
    st.error("Aucun scraper enregistré.")
    st.stop()

# Sidebar : choix du scraper
scraper_options = {name: sid for sid, name in scrapers_list}
selected_name = st.sidebar.selectbox(
    "Scraper / source",
    options=list(scraper_options.keys()),
    index=0,
)
scraper_id = scraper_options[selected_name]
scraper = get_scraper(scraper_id)
data_dir = scraper.get_data_dir()
map_center = getattr(scraper, "map_center", None)
file_label_prefix = getattr(scraper, "file_label_prefix", "")

files = sorted(data_dir.glob("*.parquet"), key=lambda p: p.stat().st_mtime, reverse=True)

st.title(selected_name)
st.caption(f"Répertoire : `{data_dir}` • {len(files)} fichier(s) Parquet")

if not files:
    st.warning("Aucun fichier Parquet pour ce scraper. Le collecteur enregistre des captures périodiquement.")
    st.stop()

# ---------- Vue agrégée : secteur le plus chargé en batteries faibles (par jour + heure) ----------
# Affichée uniquement si les données ont lat, lon, current_range_meters, captured_at
required_for_aggregate = ["lat", "lon", "current_range_meters", "captured_at"]
sample_df = pd.read_parquet(files[0])
if all(c in sample_df.columns for c in required_for_aggregate):
    st.subheader("Secteur avec le plus de trottinettes à faible autonomie (tous les fichiers)")
    threshold_km = st.sidebar.slider(
        "Seuil « faible autonomie » (km)",
        min_value=1,
        max_value=20,
        value=5,
        help="Une trottinette est comptée à faible autonomie si elle a moins que ce nombre de km restants.",
    )
    threshold_m = threshold_km * 1000

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
        out = pd.DataFrame(rows)
        return out.sort_values(["Date", "Heure"], ascending=[False, False])

    agg_df = _compute_top_sector_per_capture(files, threshold_m)
    if agg_df is not None and not agg_df.empty:
        st.caption(f"Pour chaque capture, le secteur (grille lat/lon) où il y a le plus de véhicules avec moins de {threshold_km} km d'autonomie. Données agrégées sur {len(files)} fichier(s).")
        st.dataframe(agg_df, use_container_width=True, hide_index=True)

    # ---------- Optimisation pour rechargeurs : meilleur créneau + meilleur secteur ----------
    @st.cache_data(ttl=300)
    def _compute_recharger_optimization(_files, _threshold_m):
        """Retourne (by_hour, by_sector, by_sector_hour) pour optimiser créneau et secteur."""
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
        by_combo = by_combo[["Heure", "Secteur", "count"]].rename(columns={"count": "Moy. à recharger"})
        return by_hour, by_sector, by_combo

    opt_hour, opt_sector, opt_combo = _compute_recharger_optimization(files, threshold_m)
    if opt_hour is not None:
        st.subheader("Optimisation pour rechargeurs : où et quand intervenir ?")
        st.caption("Objectif : choisir le **créneau horaire** et le **secteur** où il y a en moyenne le plus de trottinettes à recharger (sous le seuil défini ci-dessus), pour maximiser ton travail.")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Meilleurs créneaux horaires** (moyenne de trottinettes à recharger par capture)")
            if not opt_hour.empty:
                st.bar_chart(opt_hour.set_index("Heure"))
            else:
                st.info("Pas de données.")
        with c2:
            st.markdown("**Meilleurs secteurs** (top 20, moyenne par capture)")
            if opt_sector is not None and not opt_sector.empty:
                st.dataframe(opt_sector, use_container_width=True, hide_index=True)
            else:
                st.info("Pas de données.")
        st.markdown("**Meilleures combinaisons secteur + heure** (top 25 — où et quand tu as le plus de véhicules à recharger)")
        if opt_combo is not None and not opt_combo.empty:
            st.dataframe(opt_combo, use_container_width=True, hide_index=True)
        else:
            st.info("Pas de données.")
    else:
        st.info("Pas assez de données pour l’optimisation créneau/secteur.")

# Fichier à afficher
options = [f.name for f in files]
selected_file = st.sidebar.selectbox("Fichier à afficher", options, index=0)
filepath = data_dir / selected_file
df = pd.read_parquet(filepath)

# Métriques
col1, col2, col3, col4 = st.columns(4)
col1.metric("Véhicules", len(df))
if "current_range_meters" in df.columns:
    col2.metric("Autonomie moyenne (km)", f"{(df['current_range_meters'].mean() / 1000):.1f}")
if "vehicle_type_id" in df.columns:
    col3.metric("Types", df["vehicle_type_id"].nunique())
label = filepath.stem.replace(file_label_prefix, "").replace("_", " ") if file_label_prefix else filepath.stem
col4.metric("Capture", label)

# Carte (si le scraper fournit un centre et que les données ont lat/lon)
if map_center and "lat" in df.columns and "lon" in df.columns:
    st.subheader("Heatmap — batteries déchargées")
    st.caption("Plus la zone est rouge, plus les véhicules ont une autonomie faible.")
    map_df = df[["lat", "lon"]].copy().dropna(subset=["lat", "lon"])
    if "current_range_meters" in df.columns:
        map_df = df[["lat", "lon", "current_range_meters"]].dropna(
            subset=["lat", "lon", "current_range_meters"]
        )
        map_df = map_df.assign(
            weight=(100 - (map_df["current_range_meters"] / 100).clip(0, 100)).astype(float)
        )
    else:
        map_df["weight"] = 1.0
    if not map_df.empty:
        layer = pdk.Layer(
            "HeatmapLayer",
            data=map_df,
            get_position=["lon", "lat"],
            get_weight="weight",
            radius_pixels=60,
            intensity=1.2,
            threshold=0.3,
        )
        st.pydeck_chart(
            pdk.Deck(
                layers=[layer],
                initial_view_state=pdk.ViewState(**map_center),
                map_style="carto-positron",
                tooltip={"text": "Concentration véhicules à faible autonomie"},
            )
        )
    else:
        st.info("Aucune position valide dans ce fichier.")
elif "lat" in df.columns and "lon" in df.columns:
    st.info("Carte disponible uniquement pour les scrapers avec vue définie (ex. Voi Le Havre).")

# Aperçu
st.subheader("Aperçu des données")
st.dataframe(df.head(200), use_container_width=True)

# Graphiques
st.subheader("Répartition")
tab1, tab2, tab3 = st.tabs(["Autonomie (km)", "Type de véhicule", "Évolution des captures"])

with tab1:
    if "current_range_meters" in df.columns:
        km = (df["current_range_meters"] / 1000).clip(0, 50)
        st.bar_chart(km.value_counts().sort_index())

with tab2:
    if "vehicle_type_id" in df.columns:
        st.bar_chart(df["vehicle_type_id"].value_counts())

with tab3:
    if len(files) > 1:
        counts, labels = [], []
        for f in files[:24]:
            try:
                d = pd.read_parquet(f)
                counts.append(len(d))
                labels.append(f.stem.replace(file_label_prefix, "") if file_label_prefix else f.stem)
            except Exception:
                counts.append(0)
                labels.append(f.stem)
        st.line_chart(pd.DataFrame({"véhicules": counts}, index=labels))
