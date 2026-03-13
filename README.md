# Scrapers — collecteurs de données

Repo multi-scrapers : chaque scraper enregistre des données en Parquet ; un dashboard Streamlit (port 8501) permet de les visualiser.

**Scraper inclus :** Voi Le Havre (flotte Voi, API GBFS).

---

**Pour ajouter un nouveau scraper et pour le déploiement (Docker, Coolify, lancement comme Voi), tout est décrit dans [GUIDE.md](GUIDE.md).** Ce guide définit le format à respecter pour qu’un nouveau scraper soit reconnu et lancé correctement au déploiement.

- **Local :** `pip install -r requirements.txt` puis `python main.py [scraper_id]` et/ou `streamlit run dashboard.py`
- **Docker :** volume sur `/app/data`, port 8501 pour Streamlit. Détails dans GUIDE.md.
