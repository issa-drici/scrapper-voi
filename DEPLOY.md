# 🚀 Guide de Déploiement

## Option 1 : Déploiement avec Coolify (Recommandé)

Coolify peut déployer directement un conteneur Docker. Voici comment faire :

### Étapes

1. **Préparer le projet**
   - Assure-toi que tous les fichiers sont commités dans Git
   - Le Dockerfile est déjà prêt

2. **Dans Coolify**
   - Crée une nouvelle application
   - Choisis "Docker" comme type
   - Connecte ton repository Git
   - Coolify détectera automatiquement le Dockerfile

3. **Configuration du volume persistant**
   - Dans les paramètres de l'application Coolify
   - Va dans "Volumes" ou "Storage"
   - Crée un volume nommé `voi_data` (ou autre nom)
   - Monte-le sur `/app/data` dans le conteneur
   - C'est ici que tes fichiers Parquet seront stockés

4. **Variables d'environnement (optionnel)**
   - Tu peux ajouter des variables si besoin, mais pour l'instant tout est dans le code

5. **Port du dashboard**
   - Le conteneur expose le **port 8501** (Streamlit)
   - Dans Coolify, configure l’application pour utiliser ce port (ex. « Port » ou « Application port » = 8501)
   - Associe ton nom de domaine à cette application : tu pourras ouvrir le dashboard à `https://ton-domaine.com`

6. **Déploiement**
   - Lance le déploiement
   - Le conteneur démarre : le **worker** collecte les données en arrière-plan, le **dashboard** Streamlit est accessible sur le port 8501

### Vérification

- **Logs** : tu devrais voir le démarrage du collecteur et, toutes les 10 minutes, la sauvegarde des Parquet.
- **Dashboard** : ouvre l’URL de ton application (nom de domaine) pour visualiser les données (tableaux, graphiques par autonomie, type de véhicule, etc.).

## Option 2 : Déploiement Docker manuel (VPS)

Si tu veux déployer manuellement sur un VPS :

```bash
# 1. Cloner ou copier le projet sur le serveur
git clone <ton-repo> /opt/voi-tracker
cd /opt/voi-tracker

# 2. Construire l'image Docker
docker build -t voi-tracker .

# 3. Créer un volume pour les données
docker volume create voi_data

# 4. Lancer le conteneur (port 8501 = dashboard Streamlit)
docker run -d \
  --name voi-tracker \
  --restart unless-stopped \
  -p 8501:8501 \
  -v voi_data:/app/data \
  voi-tracker

# 5. Vérifier les logs
docker logs -f voi-tracker
```

### Gestion du conteneur

```bash
# Voir les logs
docker logs voi-tracker

# Arrêter
docker stop voi-tracker

# Redémarrer
docker start voi-tracker

# Supprimer (si besoin)
docker stop voi-tracker
docker rm voi-tracker
```

## Option 3 : Test local avec Docker

Pour tester avant de déployer :

```bash
# Construire l'image
docker build -t voi-tracker .

# Lancer (les données seront dans ./data localement)
docker run -d \
  --name voi-tracker-test \
  -v $(pwd)/data:/app/data \
  voi-tracker

# Voir les logs
docker logs -f voi-tracker-test

# Arrêter le test
docker stop voi-tracker-test
docker rm voi-tracker-test
```

## 📊 Accéder aux données

Une fois déployé, les fichiers Parquet sont dans `/app/data` dans le conteneur.

### Avec Coolify
- Les données sont dans le volume persistant que tu as créé
- Tu peux y accéder via les outils de Coolify ou en montant le volume sur un autre conteneur

### Avec Docker manuel
```bash
# Accéder aux données
docker exec -it voi-tracker ls -lh /app/data

# Copier un fichier localement
docker cp voi-tracker:/app/data/voi_havre_20260312_1200.parquet ./
```

## 🔧 Maintenance

### Mettre à jour le code

1. Faire tes modifications
2. Commit et push sur Git
3. Dans Coolify : relancer le déploiement
4. Ou manuellement : reconstruire l'image et redémarrer le conteneur

### Vérifier que ça fonctionne

Les logs doivent montrer :
- Démarrage réussi
- Collecte toutes les 10 minutes
- Fichiers Parquet créés régulièrement

Si ça ne fonctionne pas :
- Vérifier les logs : `docker logs voi-tracker`
- Vérifier que le volume est bien monté
- Vérifier les permissions du volume
