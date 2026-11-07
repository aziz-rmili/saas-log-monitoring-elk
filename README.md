# LogMonitor — Monitoring et analyse de logs (ELK, NoSQL, Web)

Scénario D (application SaaS). Plateforme où l'on dépose des logs, indexés par Logstash dans Elasticsearch,
consultables dans Kibana et dans l'application web Flask. Tout tourne avec Docker Compose.

| Service | Rôle | Port |
|---|---|---|
| Elasticsearch 8.15 | Stockage et recherche des logs | 9200 |
| Kibana 8.15 | Visualisation | 5601 |
| Logstash 8.15 | Lecture des fichiers de `uploads/` et envoi vers Elasticsearch | — |
| MongoDB 7 | Métadonnées des fichiers, historique des recherches | 27017 |
| Redis 7 | Cache | 6379 |
| Webapp (Flask) | Interface web et API | 8000 |

## Structure du projet

```
elk-saas-logs/
├── docker-compose.yml        # les 6 services
├── .env.example              # variables (copier en .env)
├── app/                      # application Flask (Dockerfile, routes, templates, static, models)
├── logstash/pipeline/        # pipeline Logstash (logs.conf)
├── elasticsearch/            # template d'index (mapping)
├── scripts/                  # génération de logs de test, initialisation du template
├── data/                     # logs de test générés (non versionnés)
├── uploads/                  # dossier surveillé par Logstash
└── docs/                     # documentation
```

## Installation sur Windows avec WSL 2

Tout se fait **dans Ubuntu (WSL)**, sauf mention contraire.

### 1. Installer WSL et Ubuntu (PowerShell en administrateur)

```powershell
wsl --install -d Ubuntu-24.04
```

Redémarrez Windows si demandé, puis ouvrez « Ubuntu » depuis le menu Démarrer et créez votre utilisateur.
Vérification : `wsl -l -v` doit afficher Ubuntu en **VERSION 2**.

### 2. Installer Docker

**Option A (recommandée) : Docker Desktop**
1. Installez Docker Desktop pour Windows.
2. Settings > General : cochez *Use the WSL 2 based engine*.
3. Settings > Resources > WSL integration : activez *Ubuntu-24.04*, puis *Apply & restart*.

**Option B : Docker Engine directement dans Ubuntu**
```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER      # puis fermez et rouvrez le terminal Ubuntu
```

Vérification (dans Ubuntu) :
```bash
docker --version && docker compose version
```

### 3. Donner assez de mémoire à WSL

La stack ELK demande environ 4 Go. Dans Windows, créez le fichier `C:\Users\<votre_nom>\.wslconfig` :

```ini
[wsl2]
memory=6GB
processors=4
```

Puis dans PowerShell : `wsl --shutdown`, et rouvrez Ubuntu.

### 4. Récupérer le projet (dans le disque Linux, pas dans /mnt/c)

```bash
cd ~
git clone <URL_DU_DEPOT> elk-saas-logs
cd elk-saas-logs
```

> Travaillez dans `~/` et non dans `/mnt/c/...` : c'est beaucoup plus rapide et évite les problèmes de droits.

### 5. Démarrer la stack

```bash
cp .env.example .env
docker compose up -d --build
docker compose ps          # attendre que les services soient « healthy » (1 à 2 minutes)
```

### 6. Vérifier que tout répond

```bash
curl http://localhost:9200                 # infos Elasticsearch
curl http://localhost:8000/health          # {"status":"healthy", ...}
```

Dans le navigateur Windows : http://localhost:5601 (Kibana) et http://localhost:8000 (application).

### 7. Créer le template, générer et injecter des logs de test

```bash
sudo apt update && sudo apt install -y python3-venv
python3 -m venv .venv && source .venv/bin/activate
pip install -r scripts/requirements.txt

bash scripts/init_elasticsearch.sh         # 1) template d'index logs-*
python scripts/generate_logs.py            # 2) crée data/logs_test.csv et data/logs_test.json
cp data/logs_test.json uploads/            # 3) Logstash détecte le fichier et l'indexe
```

Après environ 20 secondes :
```bash
curl "http://localhost:9200/logs-*/_count?pretty"     # doit afficher "count" : 10000
```

### 8. Voir les données dans Kibana

1. Ouvrir http://localhost:5601
2. Menu > Stack Management > Data Views > *Create data view*
3. Nom et motif : `logs-*`, champ de temps : `@timestamp` (période : 7 derniers jours)
4. Menu > Discover : les logs s'affichent

## Commandes utiles

| Action | Commande |
|---|---|
| Voir l'état | `docker compose ps` |
| Voir les logs d'un service | `docker compose logs -f logstash` |
| Arrêter | `docker compose down` |
| Tout supprimer, données comprises | `docker compose down -v` |
| Reconstruire l'application | `docker compose up -d --build webapp` |

## Dépannage

| Problème | Solution |
|---|---|
| Elasticsearch redémarre en boucle | Manque de mémoire : augmenter `memory` dans `.wslconfig`, puis `wsl --shutdown` |
| Erreur `max virtual memory areas vm.max_map_count` | `sudo sysctl -w vm.max_map_count=262144` (Docker Desktop : `wsl -d docker-desktop sysctl -w vm.max_map_count=262144`) |
| `permission denied` sur docker | Option B : `sudo usermod -aG docker $USER`, puis rouvrir le terminal |
| Port déjà utilisé | Changer le port à gauche dans `docker-compose.yml` (ex. `"8001:8000"`) |
| Kibana n'affiche aucune donnée | Élargir la période en haut à droite, vérifier le count avec curl |
| Logstash n'indexe pas | `docker compose logs logstash` ; vérifier que le fichier est bien dans `uploads/` |

## Travail avec Git et Jira

- Branche : `LOG-<numéro du ticket>-description-courte`
- Message de commit : `LOG-<numéro> : ce qui a été fait`
