#!/bin/sh
set -e
# Worker en arrière-plan (scraper par défaut : voi_havre)
python main.py voi_havre &
# Streamlit au premier plan (port 8501)
exec streamlit run dashboard.py --server.port=8501 --server.address=0.0.0.0
