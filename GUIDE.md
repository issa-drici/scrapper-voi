# Guide unique : ajouter un scraper

Ce document est la référence pour créer un nouveau scraper au bon format. Au démarrage du conteneur, **tous** les scrapers enregistrés sont lancés en arrière-plan, puis le dashboard Streamlit au premier plan.

---

## 1. Structure du repo

```
scrapers/
  __init__.py          # Registre : importer chaque scraper, les ajouter à _REGISTRY
  voi_havre/           # Exemple de scraper
    __init__.py        # Contract (voir ci-dessous)
    config.py          # URL, intervalle, préfixe des fichiers
    api.py             # fetch(url, timeout=...) → dict
    storage.py         # process_and_save(data, data_dir) → écrit Parquet
    run.py             # Boucle : fetch → process_and_save → sleep(intervalle)
config.py              # Racine : get_base_data_dir(), setup_logging()
main.py                # CLI : python main.py [scraper_id]
dashboard.py           # Streamlit (port 8501), lit data/<scraper_id>/*.parquet
entrypoint.sh          # Lance tous les scrapers du registre en arrière-plan, puis streamlit
```

- Données : chaque scraper écrit dans `get_base_data_dir() / SCRAPER_ID` (ex. `./data/voi_havre/` en local, `/app/data/voi_havre/` en conteneur).
- Au démarrage du conteneur : `entrypoint.sh` lance **un processus** `python main.py <id> &` pour **chaque** scraper du registre, puis Streamlit. Aucune modification de l’entrypoint à faire quand tu ajoutes un scraper : il suffit de l’enregistrer dans `scrapers/__init__.py`.

---

## 2. Contract d’un scraper (obligatoire)

Pour qu’un nouveau scraper soit reconnu et lancé au démarrage du conteneur avec les autres, il **doit** respecter ce format.

### 2.1 Dossier `scrapers/<id>/`

Créer un dossier avec l’id du scraper (ex. `scrapers/mon_scraper/`).

### 2.2 Fichier `scrapers/<id>/__init__.py`

Doit exposer **exactement** :

| Symbole | Type | Description |
|--------|------|-------------|
| `SCRAPER_ID` | `str` | Id unique (ex. `"voi_havre"`). Utilisé comme sous-dossier des données et pour `python main.py <id>`. |
| `NAME` | `str` | Nom affiché dans le dashboard (ex. `"Voi Le Havre"`). |
| `get_data_dir()` | `() -> Path` | Retourne le répertoire des Parquet. Doit faire `get_base_data_dir() / SCRAPER_ID` et créer le dossier si besoin. |
| `run()` | `() -> None` | Lance la boucle de collecte (sans retour). En général : importer et appeler la fonction `run()` de `run.py`. |

Optionnel (pour le dashboard) :

- `map_center` : `dict` avec `latitude`, `longitude`, `zoom`, `pitch`, `bearing` (carte).
- `file_label_prefix` : `str` (ex. `"voi_havre_"`) pour l’affichage des noms de fichiers.

Exemple minimal (sans optionnel) :

```python
from pathlib import Path
from config import get_base_data_dir

SCRAPER_ID = "mon_scraper"
NAME = "Mon Scraper"

def get_data_dir() -> Path:
    path = get_base_data_dir() / SCRAPER_ID
    path.mkdir(parents=True, exist_ok=True)
    return path

def run() -> None:
    from scrapers.mon_scraper.run import run as _run
    _run()
```

### 2.3 Fichier `scrapers/<id>/config.py`

Variables utilisées par ce scraper uniquement, par exemple :

- URL(s) à scraper.
- Timeout des requêtes.
- Intervalle de polling en secondes.
- Préfixe des noms de fichiers Parquet (ex. `FILENAME_PREFIX = "voi_havre"`).

Pas de contract strict ; à adapter au besoin.

### 2.4 Fichier `scrapers/<id>/api.py`

Au moins une fonction qui récupère les données (ex. HTTP) et retourne un `dict` (ou structure utilisable par `storage`). Exemple :

```python
def fetch(url: str, timeout: int = 30) -> dict:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.json()
```

### 2.5 Fichier `scrapers/<id>/storage.py`

Une fonction qui prend les données (ex. `dict`) et le `Path` du répertoire de données, et écrit un ou plusieurs fichiers Parquet. Doit ajouter un horodatage de capture (ex. `captured_at` UTC) si pertinent.

Exemple de signature :

```python
def process_and_save(data: dict, data_dir: Path) -> None:
    ...
    df.to_parquet(filepath, engine="pyarrow", compression="snappy", index=False)
```

Nom des fichiers : recommandation `{FILENAME_PREFIX}_{YYYYMMDD}_{HHMM}.parquet` pour une seule capture par fichier.

### 2.6 Fichier `scrapers/<id>/run.py`

Boucle de collecte :

1. Utiliser `config` du scraper (URL, intervalle, timeout).
2. Appeler la fonction de fetch (ex. `api.fetch(...)`).
3. Appeler le storage (ex. `storage.process_and_save(data, get_data_dir())`).
4. `time.sleep(intervalle_secondes)`.
5. Gérer `KeyboardInterrupt` et les erreurs (log, puis continuer ou sortir selon le besoin).

`get_data_dir()` doit être importé depuis le package du scraper (ex. `from scrapers.mon_scraper import get_data_dir`), pas depuis la racine.

---

## 3. Enregistrement du scraper

Dans `scrapers/__init__.py` :

1. Importer le module du nouveau scraper : `from scrapers import mon_scraper`
2. L’ajouter au registre : `_REGISTRY[mon_scraper.SCRAPER_ID] = mon_scraper`

Exemple après ajout de `mon_scraper` :

```python
from scrapers import voi_havre
from scrapers import mon_scraper

_REGISTRY: dict[str, Any] = {
    voi_havre.SCRAPER_ID: voi_havre,
    mon_scraper.SCRAPER_ID: mon_scraper,
}
```

Sans cette étape, le scraper n’apparaît pas dans le dashboard et ne sera pas lancé au démarrage du conteneur.

---

## 4. Récapitulatif pour une IA

Pour ajouter un nouveau scraper (il sera lancé automatiquement au démarrage avec les autres) :

1. Créer `scrapers/<id>/` avec `__init__.py`, `config.py`, `api.py`, `storage.py`, `run.py`.
2. Respecter le **contract** dans `__init__.py` : `SCRAPER_ID`, `NAME`, `get_data_dir()`, `run()`.
3. Dans `run.py`, boucle fetch → process_and_save → sleep ; utiliser `get_data_dir()` du scraper et la config du scraper.
4. Enregistrer le module dans `scrapers/__init__.py` (`_REGISTRY[id] = module`).

Rien d’autre à faire : l’entrypoint lance déjà tous les scrapers du registre en arrière-plan, puis Streamlit. Les données sont dans `get_base_data_dir() / SCRAPER_ID`.
