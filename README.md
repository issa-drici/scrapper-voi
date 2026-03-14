# Scrapers — collecteurs de données

Repo multi-scrapers : chaque scraper enregistre des données en Parquet ; un dashboard Streamlit (port 8501) permet de les visualiser.

**Scraper inclus :** Voi Le Havre (flotte Voi, API GBFS).

---

**[GUIDE.md](GUIDE.md)** — ajouter un scraper, contract, démarrage. **`helpers/time_helpers.py`** — dates/heures : stockage UTC (`now_utc()`), affichage Paris.

- **Local :** `pip install -r requirements.txt` puis `python main.py [scraper_id]` et/ou `streamlit run dashboard.py`
- **Docker :** volume sur `/app/data`, port 8501 pour Streamlit. Détails dans GUIDE.md.
