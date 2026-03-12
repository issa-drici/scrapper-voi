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
