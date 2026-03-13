#!/bin/sh
set -e
# Tous les scrapers en arrière-plan
for id in $(python -c "from scrapers import list_scrapers; print(' '.join(s[0] for s in list_scrapers()))"); do
  python main.py "$id" &
done
# Streamlit au premier plan (port 8501)
exec streamlit run dashboard.py --server.port=8501 --server.address=0.0.0.0
