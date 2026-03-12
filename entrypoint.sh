#!/bin/sh
set -e
# Worker en arrière-plan (collecte toutes les 10 min)
python main.py &
# Streamlit au premier plan (port 8501, accessible depuis l'extérieur)
exec streamlit run dashboard.py --server.port=8501 --server.address=0.0.0.0
