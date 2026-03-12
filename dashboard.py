"""
Dashboard Streamlit — visualisation des données Voi collectées.
Lit les fichiers Parquet depuis le même répertoire que le worker.
"""

import streamlit as st
import pandas as pd
from pathlib import Path

from config import get_data_directory

st.set_page_config(page_title="Voi Le Havre — Données", layout="wide")

data_dir = get_data_directory()
files = sorted(data_dir.glob("*.parquet"), key=lambda p: p.stat().st_mtime, reverse=True)

st.title("Voi Battery Tracker — Le Havre")
st.caption(f"Répertoire : `{data_dir}` • {len(files)} fichier(s) Parquet")

if not files:
    st.warning("Aucun fichier Parquet pour l’instant. Le collecteur enregistre une capture toutes les 10 minutes.")
    st.stop()

# Sélection du fichier (dernier par défaut)
options = [f.name for f in files]
selected = st.sidebar.selectbox("Fichier à afficher", options, index=0)
filepath = data_dir / selected
df = pd.read_parquet(filepath)

# Métriques
col1, col2, col3, col4 = st.columns(4)
col1.metric("Véhicules", len(df))
if "current_range_meters" in df.columns:
    col2.metric("Autonomie moyenne (km)", f"{(df['current_range_meters'].mean() / 1000):.1f}")
if "vehicle_type_id" in df.columns:
    col3.metric("Types", df["vehicle_type_id"].nunique())
col4.metric("Dernière capture", filepath.stem.replace("voi_havre_", "").replace("_", " "))

# Aperçu des données
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
        # Nombre de véhicules par fichier (derniers fichiers)
        counts = []
        labels = []
        for f in files[:24]:  # dernières 24 captures
            try:
                d = pd.read_parquet(f)
                counts.append(len(d))
                labels.append(f.stem.replace("voi_havre_", ""))
            except Exception:
                counts.append(0)
                labels.append(f.stem)
        st.line_chart(pd.DataFrame({"véhicules": counts}, index=labels))
