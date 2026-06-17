# tools

Collection de scripts utilitaires.

---

## scripts/gitlab_test_report.py

Récupère les résultats de tests de tous les pipelines GitLab sur une période donnée et génère un fichier CSV indiquant combien de fois chaque test a réussi ou échoué.

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