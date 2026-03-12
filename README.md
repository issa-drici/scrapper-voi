# 🛴 Scrapers — Collecteurs de données

Repo multi-scrapers : chaque scraper collecte des données (API, etc.) et les enregistre en Parquet. Un **dashboard Streamlit** unique permet de choisir un scraper et de visualiser ses données (tableaux, graphiques, carte).

**Scrapers inclus :**
- **Voi Le Havre** — flotte trottinettes Voi au Havre (API GBFS, batteries / autonomie).

## 🔗 Configuration des API

Pour le Havre, l'architecture GBFS de Voi se décompose ainsi :

- **L'Index (Discovery URL)** : C'est le point d'entrée qui liste tous les flux disponibles.
  ```
  https://api.voiapp.io/gbfs/fr/6bb6b5dc-1cda-4da7-9216-d3023a0bc54a/v2/336/gbfs.json
  ```

- **Le Flux de Données (Target URL)** : C'est ce lien que le scraper doit interroger. Il contient la liste des véhicules, leurs positions et leurs batteries.
  ```
  https://api.voiapp.io/gbfs/fr/6bb6b5dc-1cda-4da7-9216-d3023a0bc54a/v2/336/free_bike_status.json
  ```

## 🛠 Stack Technique

- **Langage** : Python 3.11+
- **Format de stockage** : Apache Parquet (optimisé pour le stockage colonnaire et la compression).
- **Déploiement** : Docker / VPS (via Coolify).

### Structure du repo

- **scrapers/** : un dossier par scraper (ex. `voi_havre/` : config, api, storage, run). Registre dans `scrapers/__init__.py`.
- **config.py** : chemins globaux, logging. **main.py** : `python main.py [scraper_id]`. **dashboard.py** : Streamlit, choix du scraper dans la sidebar.

- **Installation** : `pip install -r requirements.txt` (voir aussi `requirements/core.txt`, `data.txt`, `dashboard.txt`).
- Chaque scraper a son dossier sous `scrapers/` et ses données sous `data/<scraper_id>/`.

### Dashboard Streamlit (même conteneur en prod)

En Docker/Coolify, le conteneur lance un **worker** (par défaut `voi_havre`) et le **dashboard** sur le port **8501**. Depuis le dashboard tu peux changer de scraper dans la sidebar pour voir les données de chaque source (tant que les Parquet sont dans `data/<scraper_id>/`).

**Migrer les données existantes** : si tu avais des fichiers dans `/app/data/*.parquet`, déplace-les dans `/app/data/voi_havre/` pour qu'ils apparaissent sous « Voi Le Havre ».

## 🏗 Logique du Collecteur (The Pipeline)

Le script fonctionne en boucle (polling) :

- **Fréquence** : Toutes les 10 minutes.
- **Traitement** :
  1. Récupération du JSON depuis la Target URL.
  2. Injection d'une colonne `captured_at` (Timestamp UTC).
  3. Conversion en DataFrame et sauvegarde en .parquet.
- **Stockage** : Les fichiers sont nommés selon le format `voi_havre_YYYYMMDD_HHMM.parquet`.

## 📂 Schéma des données capturées

| Champ | Type | Description |
|-------|------|-------------|
| `bike_id` | String | Identifiant unique du véhicule |
| `lat` / `lon` | Float | Coordonnées GPS précises |
| `current_range_meters` | Integer | Autonomie restante estimée (en mètres) |
| `vehicle_type_id` | String | Type de véhicule (voi_scooter, voi_bike) |
| `is_reserved` | Boolean | Véhicule réservé ou non |
| `is_disabled` | Boolean | Véhicule désactivé ou non |
| `last_reported` | Integer | Timestamp Unix de la dernière mise à jour |
| `pricing_plan_id` | String | Identifiant du plan tarifaire |
| `rental_uris` | Object | Liens de location (android, ios) |
| `captured_at` | DateTime | Horodatage de la capture (ajouté par le script) |

**Note importante** : L'API Voi ne fournit **pas** directement le niveau de batterie en pourcentage (`battery_level`). Seule l'autonomie restante (`current_range_meters`) est disponible, ce qui est suffisant pour l'analyse.

## 🚀 Déploiement

**⚠️ Important** : Ce n'est **pas** une application Django ou web. C'est un simple script Python qui tourne en boucle dans un conteneur Docker.

### Déploiement avec Coolify (Recommandé)

Coolify peut déployer directement ce conteneur Docker. Voir le guide complet dans **[DEPLOY.md](DEPLOY.md)**.

**Résumé rapide** :
1. Crée une nouvelle application Docker dans Coolify
2. Connecte ton repository Git
3. Crée un volume persistant `voi_data` et monte-le sur `/app/data`
4. Déploie !

### Déploiement Docker manuel

Voir **[DEPLOY.md](DEPLOY.md)** pour les instructions complètes.

**Résumé rapide** :
```bash
docker build -t voi-tracker .
docker run -d --name voi-tracker --restart unless-stopped -v voi_data:/app/data voi-tracker
```

### Analyse des données

Une fois les données accumulées, tu pourras utiliser DuckDB pour requêter directement tes milliers de fichiers Parquet comme s'ils étaient une seule table SQL :
   ```sql
   -- Exemple avec l'autonomie moyenne
   SELECT avg(current_range_meters) FROM 'data/*.parquet' WHERE lat > 49.5;
   
   -- Exemple par type de véhicule
   SELECT vehicle_type_id, avg(current_range_meters) FROM 'data/*.parquet' GROUP BY vehicle_type_id;
   ```

## 📦 Installation et Utilisation

### Développement local

```bash
# Création de l'environnement virtuel
python3 -m venv venv

# Activation de l'environnement virtuel
source venv/bin/activate

# Installation des dépendances
pip install -r requirements.txt

# Création du répertoire de données
mkdir -p data

# Lancement du collecteur (polling toutes les 10 minutes)
python main.py
```

### Déploiement Docker

```bash
# Construction de l'image
docker build -t voi-tracker .

# Lancement du conteneur avec volume persistant
docker run -d \
  --name voi-tracker \
  -v voi_data:/app/data \
  voi-tracker
```

## 📊 Exemple de requête avec DuckDB

Une fois les données collectées, tu peux utiliser DuckDB pour analyser les fichiers Parquet :

```python
import duckdb

conn = duckdb.connect()
result = conn.execute("""
    SELECT 
        DATE(captured_at) as date,
        AVG(current_range_meters) as avg_range,
        COUNT(*) as bike_count
    FROM 'data/*.parquet'
    GROUP BY DATE(captured_at)
    ORDER BY date DESC
""").fetchdf()

print(result)
```
