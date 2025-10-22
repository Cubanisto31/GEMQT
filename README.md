# Framework d'Expérimentation sur le Référencement des Sources

Ce projet fournit un framework complet pour mener des expérimentations à grande échelle sur la manière dont les modèles de langage (LLMs) et les moteurs de recherche citent leurs sources. Il est conçu pour être modulaire, extensible et automatisé.

## Nouveautés 

### Clients de recherche web avancés
- **Perplexity Sonar Pro** : Extraction optimisée avec plus de citations
- **Claude Web Search** : API officielle de recherche web Anthropic ($10/1000 requêtes)
- **Gemini Grounding** : Recherche Google intégrée ($35/1000 requêtes)

### Support des fichiers de requêtes externes
Les requêtes peuvent maintenant être chargées depuis un fichier Excel ou CSV externe, évitant de modifier le fichier de configuration YAML.

### Réponses complètes sauvegardées
Les réponses complètes sont désormais sauvegardées dans le champ `response_raw` de la base de données.

### Guide d'obtention des clés API
Consultez [API_SETUP_GUIDE.md](API_SETUP_GUIDE.md) pour des instructions détaillées sur l'obtention des clés API.

## Structure du Projet

```
.
├── experiment_results/
├── src/
│   ├── clients/
│   │   ├── __init__.py
│   │   ├── base_client.py
│   │   ├── claude_client.py
│   │   ├── claude_search_client.py
│   │   ├── openai_client.py
│   │   ├── openai_search_client.py
│   │   ├── gemini_client.py
│   │   ├── gemini_search_client.py
│   │   ├── perplexity_client.py
│   │   ├── perplexity_search_client.py
│   │   └── search_clients.py
│   ├── __init__.py
│   ├── config.py
│   ├── config.yaml
│   ├── config_without_queries.yaml  # Config sans requêtes intégrées
│   ├── query_loader.py             # Chargement des requêtes externes
│   ├── database.py
│   ├── runner.py
│   └── main.py
├── API_SETUP_GUIDE.md
├── test_queries_bis.xlsx           # Pool de requêtes Excel de test
├── queries_pool_example.csv       # Exemple de fichier CSV
├── requirements.txt
└── README.md
```

## Configuration

### 1. Installation des dépendances
```bash
pip install -r requirements.txt
```

### 2. Configuration des clés API
Créez un fichier `.env` à la racine du projet :
```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
BING_API_KEY=...
GEMINI_API_KEY=...
PERPLEXITY_API_KEY=...
GOOGLE_API_KEY=...
GOOGLE_CX=...
```

### 3. Activation des modèles
Dans `src/config.yaml`, changez `enabled: false` en `enabled: true` pour les modèles que vous souhaitez utiliser.

## Utilisation

### Exécution simple
```bash
python -m src.main
```

### Avec configuration personnalisée
```bash
python -m src.main --config mon_config.yaml
```

### Avec fichier de requêtes externe
Le système supporte maintenant le chargement des requêtes depuis un fichier externe (Excel ou CSV) :

```bash
# Avec un fichier Excel
python -m src.main --queries test_queries_bis.xlsx

# Avec un fichier CSV
python -m src.main --queries queries_pool_example.csv

# Avec une configuration personnalisée ET un fichier de requêtes externe
python -m src.main --config src/config_without_queries.yaml --queries test_queries_bis.xlsx
```

#### Format du fichier de requêtes

Le fichier Excel ou CSV doit contenir au minimum les colonnes suivantes :
- **id** : Identifiant unique de la requête
- **text** : Texte de la requête
- **category** : Catégorie de la requête (ex: "Informationnelle - Santé", "Transactionnelle - Voyage", etc.)

Les colonnes supplémentaires seront automatiquement ajoutées comme métadonnées. Exemple de fichier CSV :

```csv
id,text,category,complexité,domaine,intention
info_sante_001,"Quels sont les symptômes de la grippe ?","Informationnelle - Santé",faible,santé,
info_tech_001,"Explique le fonctionnement des transformeurs dans GPT.","Informationnelle - Technique",élevée,technologie,
transac_voyage_001,"Trouver les meilleurs hôtels à Rome.","Transactionnelle - Voyage",,tourisme,réservation
```

## Base de données et stockage des résultats

### Configuration du fichier de sortie

Le fichier de base de données est configuré dans le fichier `config.yaml` via le paramètre `database_url` :

```yaml
database_url: "sqlite:///experiment_results/experiment_data.db"
```

Vous pouvez modifier ce chemin pour :
- Changer l'emplacement de la base de données
- Utiliser une base de données différente pour chaque expérimentation
- Utiliser d'autres systèmes de base de données supportés par SQLAlchemy (PostgreSQL, MySQL, etc.)

Exemple avec PostgreSQL :
```yaml
database_url: "postgresql://user:password@localhost/experiment_db"
```
### Nouvelle expérimentation

Si je n'ai pas retiré le fichier de base de données du dossier experiment_results

  # Sauvegarder la base actuelle avec un timestamp
  mv experiment_results/experiment_data.db experiment_results/experiment_data_backup_$(date +%Y%m%d_%H%M%S).db

  # L'expérimentation créera automatiquement une nouvelle base vide
  python -m src.main --queries test_queries.csv


### Structure de la base de données

La base de données SQLite contient une table `results` avec la structure suivante :

| Champ | Type | Description |
|-------|------|-------------|
| **id** | String (PK) | Identifiant unique de chaque résultat |
| **experiment_id** | String | Nom de l'expérimentation (depuis config.yaml) |
| **session_id** | String | UUID unique de la session d'exécution |
| **query_id** | String | Identifiant de la requête |
| **query_text** | Text | Texte complet de la requête |
| **query_category** | String | Catégorie de la requête |
| **iteration** | Integer | Numéro de l'itération (pour les répétitions) |
| **model_name** | String | Nom du modèle/moteur utilisé |
| **model_type** | String | Type (llm ou search_engine) |
| **response_raw** | Text | **Réponse complète** du modèle/moteur |
| **sources_extracted** | JSON | Sources citées extraites de la réponse |
| **chain_of_thought** | Text | Raisonnement extrait (si applicable) |
| **response_time_ms** | Integer | Temps de réponse en millisecondes |
| **timestamp** | DateTime | Date et heure de l'exécution |
| **extra_metadata** | JSON | Métadonnées supplémentaires |

### Manipulation des données

#### Accès direct avec SQLite

```bash
# Ouvrir la base de données
sqlite3 experiment_results/experiment_data.db

# Commandes SQL utiles
.tables                          # Lister les tables
.schema results                  # Voir la structure de la table
SELECT COUNT(*) FROM results;   # Compter les résultats
.mode column                     # Affichage en colonnes
.headers on                      # Afficher les en-têtes
```

#### Requêtes SQL exemples

```sql
-- Voir les derniers résultats
SELECT model_name, query_id, response_time_ms, timestamp 
FROM results 
ORDER BY timestamp DESC 
LIMIT 10;

-- Statistiques par modèle
SELECT model_name, 
       COUNT(*) as nb_requetes,
       AVG(response_time_ms) as temps_moyen_ms,
       COUNT(DISTINCT query_id) as nb_requetes_uniques
FROM results 
GROUP BY model_name;

-- Exporter les réponses complètes pour une requête
SELECT model_name, response_raw 
FROM results 
WHERE query_id = 'info_sante_001';

-- Compter les sources par modèle
SELECT model_name, 
       AVG(json_array_length(sources_extracted)) as nb_moyen_sources
FROM results 
GROUP BY model_name;
```

#### Accès avec Python

```python
import sqlite3
import pandas as pd
import json

# Connexion à la base
conn = sqlite3.connect('experiment_results/experiment_data.db')

# Charger les données dans un DataFrame
df = pd.read_sql_query("SELECT * FROM results", conn)

# Analyser les réponses
for index, row in df.iterrows():
    print(f"Modèle: {row['model_name']}")
    print(f"Requête: {row['query_text'][:50]}...")
    print(f"Longueur réponse: {len(row['response_raw'])} caractères")
    
    # Analyser les sources
    sources = json.loads(row['sources_extracted']) if row['sources_extracted'] else []
    print(f"Nombre de sources: {len(sources)}")
    print("-" * 50)

# Exporter vers CSV
df.to_csv('resultats_experimentation.csv', index=False)

conn.close()
```

#### Scripts d'analyse fournis

Le projet inclut plusieurs scripts pour analyser les données :

- **`export_to_csv.py`** : Exporte les données vers CSV avec agrégations
- **`analyze_experiment.py`** : Génère des statistiques et graphiques
- **`quick_data_peek.py`** : Aperçu rapide des derniers résultats

Utilisation :
```bash
# Exporter vers CSV
python export_to_csv.py

# Analyser et créer des graphiques
python analyze_experiment.py

# Aperçu rapide
python quick_data_peek.py
```

### Sauvegarde et archivage

Il est recommandé de :
1. **Sauvegarder régulièrement** la base de données (le fichier `.db`)
2. **Créer des copies** avant chaque nouvelle expérimentation majeure
3. **Exporter vers CSV** pour l'archivage long terme et le partage

```bash
# Créer une sauvegarde
cp experiment_results/experiment_data.db experiment_results/backup_$(date +%Y%m%d_%H%M%S).db

# Exporter tout vers CSV
sqlite3 experiment_results/experiment_data.db ".mode csv" ".headers on" \
        ".output all_results.csv" "SELECT * FROM results;" ".quit"
```

## Modèles et Clients Disponibles

### Agents Conversationnels Classiques
- **GPT-4o** (`openai`) : Modèle OpenAI sans recherche web
- **Claude-3-Sonnet** (`claude`) : Modèle Anthropic sans recherche web
- **Gemini-Pro** (`gemini`) : Modèle Google sans recherche web
- **Perplexity-Online** (`perplexity`) : Modèle Perplexity avec recherche web native

### Agents avec Recherche Web Avancée
- **Claude-3-Sonnet-Search** (`claude_search`) : Claude + Web Search API
- **Gemini-Flash-Grounding** (`gemini_search`) : Gemini + Google Search Grounding
- **Perplexity-Sonar-Pro** (`perplexity_search`) : Version Pro avec extraction optimisée

### Moteur de Recherche
- **Google-Search** (`google_search`) : API Google Custom Search

Note : GPT-4-Search est désactivé car OpenAI ne propose pas de recherche web native dans son API.

## Prochaines étapes

- Faire attention aux crédits sur les différentes clés API
- Commencer à faire une première analyse sur un test
- Système d'automatisation temporelle (planification des exécutions)
- Amélioration du pool de requêtes
