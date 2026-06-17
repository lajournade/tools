# tools

Collection de scripts utilitaires.

---

## Scripts GitLab

Deux scripts complémentaires pour analyser les pipelines GitLab CI sur une période donnée.
Ils partagent le même module interne `_gitlab_common.py` (client API, pagination, arguments CLI).

| Script | Basé sur | Cas d'usage |
|---|---|---|
| `gitlab_test_report.py` | Rapports JUnit | Statistiques par cas de test unitaire |
| `gitlab_job_stats.py` | Nom des jobs | Statistiques par job, y compris les jobs sans rapport |

---

## scripts/gitlab_test_report.py

Récupère les résultats de tests de tous les pipelines GitLab sur une période donnée et génère un fichier CSV indiquant combien de fois chaque test a réussi ou échoué.

> **Limitation :** ne couvre que les jobs qui publient un rapport JUnit. Les jobs qui échouent avant de générer ce rapport sont ignorés. Utiliser `gitlab_job_stats.py` pour couvrir tous les jobs.

### Prérequis

- Python 3.8+
- Bibliothèque `requests` :

```bash
pip install requests
```

- Un token d'accès GitLab (Personal Access Token ou Project Access Token) avec le scope **read_api**.
- Les jobs GitLab CI doivent publier des rapports JUnit dans leur configuration :

```yaml
# Exemple .gitlab-ci.yml
test:
  script: pytest --junitxml=report.xml
  artifacts:
    reports:
      junit: report.xml
```

### Utilisation

```bash
python scripts/gitlab_test_report.py \
    --url https://gitlab.com \
    --token glpat-xxxxxxxxxxxxxxxxxxxx \
    --project mygroup/myproject \
    --days 30
```

Le fichier `test_report.csv` est généré dans le répertoire courant.

### Arguments

| Argument | Obligatoire | Défaut | Description |
|---|---|---|---|
| `--url` | Non | `https://gitlab.com` | URL de l'instance GitLab |
| `--token` | Oui* | `$GITLAB_TOKEN` | Token d'accès GitLab |
| `--project` | Oui | — | ID numérique ou chemin du projet (ex. `mygroup/myproject`) |
| `--days` | Non | `30` | Nombre de jours à analyser |
| `--ref` | Non | toutes | Filtrer par branche ou tag |
| `--status` | Non | tous | Filtrer par statut de pipeline (`success`, `failed`, …) |
| `--output` | Non | `test_report.csv` | Chemin du fichier CSV de sortie |

*Le token peut aussi être fourni via la variable d'environnement `GITLAB_URL` / `GITLAB_TOKEN`.

### Format du CSV généré

| Colonne | Description |
|---|---|
| `suite` | Nom de la suite de tests |
| `test_name` | Nom du cas de test |
| `success` | Nombre d'exécutions réussies |
| `failed` | Nombre d'exécutions en échec |
| `error` | Nombre d'exécutions en erreur |
| `skipped` | Nombre d'exécutions ignorées |
| `total_runs` | Total d'exécutions sur la période |
| `success_rate_%` | Taux de succès en pourcentage |

### Exemples

```bash
# 30 derniers jours sur gitlab.com
python scripts/gitlab_test_report.py \
    --url https://gitlab.com \
    --token glpat-xxxxxxxxxxxxxxxxxxxx \
    --project mygroup/myproject \
    --days 30

# 7 derniers jours, branche main uniquement, pipelines réussis seulement
python scripts/gitlab_test_report.py \
    --url https://gitlab.example.com \
    --token glpat-xxxxxxxxxxxxxxxxxxxx \
    --project 42 \
    --days 7 \
    --ref main \
    --status success \
    --output rapport_semaine.csv
```

Via variables d'environnement :

```bash
export GITLAB_URL=https://gitlab.com
export GITLAB_TOKEN=glpat-xxxxxxxxxxxxxxxxxxxx

python scripts/gitlab_test_report.py --project mygroup/myproject --days 14
```

---

## scripts/gitlab_job_stats.py

Récupère le statut de **tous les jobs** de chaque pipeline sur une période donnée et génère un fichier CSV avec les compteurs de succès/échec par nom de job.

Contrairement à `gitlab_test_report.py`, ce script ne dépend pas des rapports JUnit : un job qui échoue sans produire de rapport est quand même comptabilisé.

### Prérequis

- Python 3.8+
- Bibliothèque `requests` :

```bash
pip install requests
```

- Un token d'accès GitLab avec le scope **read_api**.

### Utilisation

```bash
python scripts/gitlab_job_stats.py \
    --url https://gitlab.com \
    --token glpat-xxxxxxxxxxxxxxxxxxxx \
    --project mygroup/myproject \
    --days 30
```

Le fichier `job_stats.csv` est généré dans le répertoire courant.

### Arguments

| Argument | Obligatoire | Défaut | Description |
|---|---|---|---|
| `--url` | Non | `https://gitlab.com` | URL de l'instance GitLab |
| `--token` | Oui* | `$GITLAB_TOKEN` | Token d'accès GitLab |
| `--project` | Oui | — | ID numérique ou chemin du projet (ex. `mygroup/myproject`) |
| `--days` | Non | `30` | Nombre de jours à analyser |
| `--ref` | Non | toutes | Filtrer par branche ou tag |
| `--status` | Non | tous | Filtrer par statut de pipeline (`success`, `failed`, …) |
| `--job-name` | Non | tous | Filtre (sous-chaîne) sur le nom du job |
| `--output` | Non | `job_stats.csv` | Chemin du fichier CSV de sortie |

*Le token peut aussi être fourni via la variable d'environnement `GITLAB_URL` / `GITLAB_TOKEN`.

### Format du CSV généré

| Colonne | Description |
|---|---|
| `job_name` | Nom du job GitLab CI |
| `success` | Nombre d'exécutions réussies |
| `failed` | Nombre d'exécutions en échec |
| `canceled` | Nombre d'exécutions annulées |
| `skipped` | Nombre d'exécutions ignorées ou manuelles |
| `other` | Autres statuts (pending, running, …) |
| `total_runs` | Total d'exécutions sur la période |
| `success_rate_%` | Taux de succès en pourcentage |

### Exemples

```bash
# 30 derniers jours, tous les jobs
python scripts/gitlab_job_stats.py \
    --url https://gitlab.com \
    --token glpat-xxxxxxxxxxxxxxxxxxxx \
    --project mygroup/myproject \
    --days 30

# 7 derniers jours, uniquement les jobs dont le nom contient "test", branche main
python scripts/gitlab_job_stats.py \
    --url https://gitlab.com \
    --token glpat-xxxxxxxxxxxxxxxxxxxx \
    --project mygroup/myproject \
    --days 7 \
    --ref main \
    --job-name test \
    --output job_stats_semaine.csv
```

Via variables d'environnement :

```bash
export GITLAB_URL=https://gitlab.com
export GITLAB_TOKEN=glpat-xxxxxxxxxxxxxxxxxxxx

python scripts/gitlab_job_stats.py --project mygroup/myproject --days 14
```