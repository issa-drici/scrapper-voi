# Ajouter un nouveau scraper

1. **Créer un dossier** `scrapers/<id>/` (ex. `scrapers/autre_ville/`).

2. **Fichiers requis dans ce dossier :**
   - **`__init__.py`** — expose au minimum :
     - `SCRAPER_ID` (str)
     - `NAME` (str, nom affiché dans le dashboard)
     - `get_data_dir()` → `Path` (sous-dossier des Parquet, ex. `get_base_data_dir() / SCRAPER_ID`)
     - `run()` — lance la boucle de collecte
   - **`config.py`** — URL, intervalle, préfixe des fichiers, etc.
   - **`api.py`** — fonction de récupération (ex. `fetch(url, timeout=...)`)
   - **`storage.py`** — fonction qui écrit en Parquet (ex. `process_and_save(data, data_dir)`)
   - **`run.py`** — boucle `while True`: fetch → process_and_save → sleep(intervalle)

3. **Enregistrer le scraper** dans `scrapers/__init__.py` :
   - `from scrapers import mon_nouveau`
   - ajouter `mon_nouveau.SCRAPER_ID: mon_nouveau` dans `_REGISTRY`.

4. **Optionnel (dashboard)** : dans `__init__.py` du scraper, tu peux ajouter :
   - `map_center` (dict avec latitude, longitude, zoom) pour la carte heatmap
   - `file_label_prefix` (str) pour afficher les noms de fichiers sans le préfixe

5. **Lancer** : `python main.py <id>` ou laisser l’entrypoint Docker lancer le scraper par défaut.
