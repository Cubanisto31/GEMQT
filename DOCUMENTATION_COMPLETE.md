# Documentation complète - Système d'analyse du référencement par les agents conversationnels

## Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture du système](#architecture-du-système)
3. [Structure des fichiers](#structure-des-fichiers)
4. [Configuration](#configuration)
5. [Modules principaux](#modules-principaux)
6. [Clients API](#clients-api)
7. [Base de données](#base-de-données)
8. [Processus d'expérimentation](#processus-dexpérimentation)
9. [Analyse des données](#analyse-des-données)
10. [Guide d'utilisation](#guide-dutilisation)
11. [Troubleshooting](#troubleshooting)

---

## 1. Vue d'ensemble

### Objectif du projet
Ce système a été conçu pour analyser comment différents agents conversationnels (ChatGPT, Claude, Gemini, Perplexity) et moteurs de recherche référencent et citent leurs sources, dans le contexte de l'émergence de l'Optimisation pour Moteurs Génératifs (GEO).

### Hypothèses testées
1. **H1** : Le référencement repose sur l'entraînement du modèle
2. **H2a** : Le référencement est influencé par les moteurs de recherche classiques
3. **H2b** : Le référencement dépend des caractéristiques intrinsèques des sources

### Fonctionnalités principales
- Interrogation automatisée de multiples APIs (LLMs et moteurs de recherche)
- Extraction et analyse des sources citées
- Stockage des résultats dans une base SQLite
- Export vers CSV pour analyse dans R
- Support de multiples itérations et sessions

---

## 2. Architecture du système

```
┌─────────────────────────────────────────────────────────────────┐
│                         Interface CLI                           │
│                        (src/main.py)                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    ExperimentRunner                             │
│                   (src/runner.py)                               │
│  • Orchestration des requêtes                                   │
│  • Gestion des sessions et itérations                           │
│  • Coordination des clients                                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
         ┌───────────────────┴───────────────────┐
         │                                       │
┌────────▼──────────┐                 ┌─────────▼──────────┐
│   Clients API     │                 │   Base de données  │
│  (src/clients/)   │                 │  (src/database.py) │
│                   │                 │                    │
│ • OpenAI          │                 │ • SQLite           │
│ • Claude          │                 │ • ORM SQLAlchemy   │
│ • Gemini          │                 │ • Modèle Result    │
│ • Perplexity      │                 │                    │
│ • Google Search   │                 └────────────────────┘
│ • Bing Search     │
└───────────────────┘
```

---

## 3. Structure des fichiers

```
testACv1/
├── src/                          # Code source principal
│   ├── __init__.py
│   ├── main.py                   # Point d'entrée CLI
│   ├── config.py                 # Classes de configuration Pydantic
│   ├── config.yaml               # Configuration de l'expérience
│   ├── runner.py                 # Orchestrateur principal
│   ├── database.py               # Modèles et gestion BDD
│   ├── utils.py                  # Fonctions utilitaires
│   └── clients/                  # Implémentations des clients API
│       ├── base_client.py        # Classe abstraite de base
│       ├── openai_client.py      # Client OpenAI (GPT-4)
│       ├── claude_client.py      # Client Anthropic (Claude)
│       ├── gemini_client.py      # Client Google Gemini
│       ├── perplexity_client.py  # Client Perplexity
│       └── search_clients.py     # Clients moteurs de recherche
├── experiment_results/           # Données d'expérience
│   └── experiment_data.db        # Base de données SQLite
├── analysis_exports/             # Exports CSV et analyses
│   ├── experiment_data_*.csv    # Données complètes
│   ├── sources_detail_*.csv     # Détail des sources
│   ├── aggregated_data_*.csv    # Données agrégées
│   ├── temporal_analysis_*.csv  # Analyse temporelle
│   └── analysis_script.R        # Script R généré
├── .env                          # Variables d'environnement (clés API)
├── API_SETUP_GUIDE.md           # Guide d'obtention des clés API
├── README.md                     # Documentation générale
├── export_to_csv.py             # Script d'export vers CSV
└── test_queries_bis.xlsx         # Pool de requêtes d'expérience
```

---

## 4. Configuration

### 4.1 Configuration de l'expérience (config.yaml)

```yaml
experiment_name: "Analyse_Referencement_Sources_2024"
duration_days: 14                    # Durée de l'expérience
iterations_per_query: 30             # Répétitions par requête
delay_between_iterations_seconds: 5  # Délai entre requêtes
randomize_query_order: true          # Ordre aléatoire
use_different_sessions: true         # Sessions distinctes
database_url: "sqlite:///experiment_results/experiment_data.db"

models:
  - name: "GPT-4o"
    type: "llm"                      # llm ou search_engine
    client: "openai"                 # Identifiant du client
    enabled: true                    # Actif ou non
    api_key_env_var: "OPENAI_API_KEY"
    parameters:
      model_name: "gpt-4o"
      temperature: 0.7
      max_tokens: 4000

queries:
  - id: "info_sante_001"
    text: "Quels sont les symptômes..."
    category: "Informationnelle - Santé"
    metadata: { "complexité": "faible" }
```

### 4.2 Variables d'environnement (.env)

```bash
# APIs LLM
OPENAI_API_KEY="sk-..."
ANTHROPIC_API_KEY="sk-ant-..."
GEMINI_API_KEY="AIza..."
PERPLEXITY_API_KEY="pplx-..."

# APIs Moteurs de recherche
GOOGLE_API_KEY="AIza..."
GOOGLE_CX="00d958..."
BING_API_KEY="..."
```

---

## 5. Modules principaux

### 5.1 main.py - Point d'entrée

```python
# Fonctionnalités :
- Chargement des variables d'environnement
- Parsing de la configuration YAML
- Initialisation de la base de données
- Lancement de l'ExperimentRunner
- Gestion des erreurs globales
```

### 5.2 runner.py - Orchestrateur

**Classe ExperimentRunner**
- `__init__()`: Initialise les clients selon la configuration
- `run()`: Lance l'expérience complète
- `_run_query()`: Exécute une requête sur un modèle
- `_save_result()`: Sauvegarde en base de données

**Processus d'exécution :**
1. Initialisation des clients activés
2. Pour chaque itération :
   - Randomisation de l'ordre des requêtes
   - Pour chaque requête × modèle :
     - Appel API asynchrone
     - Extraction des sources
     - Sauvegarde des résultats
   - Délai entre requêtes

### 5.3 config.py - Modèles de configuration

**Classes Pydantic :**
- `QueryConfig`: Structure d'une requête
- `ModelParameters`: Paramètres d'un modèle
- `ModelConfig`: Configuration complète d'un modèle
- `ExperimentConfig`: Configuration globale

### 5.4 database.py - Gestion des données

**Modèle Result (SQLAlchemy) :**
```python
- id: UUID unique
- experiment_id: ID de l expérience
- session_id: ID de session
- query_id: ID de la requête
- query_text: Texte complet
- query_category: Catégorie
- iteration: Numéro d itération
- model_name: Nom du modèle
- model_type: llm ou search_engine
- response_raw: Réponse brute
- sources_extracted: JSON des sources
- response_time_ms: Temps de réponse
- timestamp: Horodatage
```

### 5.5 utils.py - Fonctions utilitaires

- `async_retry`: Décorateur pour retry automatique
- `is_retryable_error`: Détection des erreurs à réessayer
- Classes d'exception personnalisées

---

## 6. Clients API

### 6.1 Architecture des clients

**Classe abstraite BaseClient :**
```python
class BaseClient(ABC):
    @abstractmethod
    async def query(text: str, session_id: str) -> Dict
    
    @abstractmethod
    def _extract_sources(response_text: str) -> List[Dict]
    
    def _extract_chain_of_thought(response_text: str) -> str
```

### 6.2 Implémentations spécifiques

#### OpenAIClient
- Utilise l'API ChatCompletion d'OpenAI
- Modèles supportés : gpt-4o, gpt-4, gpt-3.5-turbo
- Extraction de sources par patterns regex

#### ClaudeClient
- API Messages d'Anthropic
- Modèles : claude-3-5-sonnet, claude-3-opus
- Gestion du header anthropic-version

#### GeminiClient
- API Google Generative AI
- Modèles : gemini-1.5-flash, gemini-pro
- Format de requête spécifique Google

#### PerplexityClient
- API avec recherche web intégrée
- Modèles : sonar, sonar-reasoning
- Extraction des citations natives + patterns

#### SearchClients (Google, Bing)
- API Custom Search de Google
- Bing Web Search API
- Retourne les résultats bruts JSON

### 6.3 Extraction des sources

**Patterns recherchés :**
1. Liens markdown : `[texte](url)`
2. URLs brutes : `https://...`
3. Citations numérotées : `[1], [2]`
4. Format "Source:" ou "Référence:"
5. Citations natives (Perplexity)

---

## 7. Base de données

### 7.1 Schema SQLite

```sql
CREATE TABLE results (
    id VARCHAR PRIMARY KEY,
    experiment_id VARCHAR NOT NULL,
    session_id VARCHAR NOT NULL,
    query_id VARCHAR NOT NULL,
    query_text TEXT NOT NULL,
    query_category VARCHAR NOT NULL,
    iteration INTEGER NOT NULL,
    model_name VARCHAR NOT NULL,
    model_type VARCHAR NOT NULL,
    response_raw TEXT,
    sources_extracted JSON,
    chain_of_thought TEXT,
    response_time_ms INTEGER,
    timestamp DATETIME,
    extra_metadata JSON
);

-- Indices pour optimisation
CREATE INDEX ix_results_experiment_id ON results (experiment_id);
CREATE INDEX ix_results_query_id ON results (query_id);
CREATE INDEX ix_results_model_name ON results (model_name);
CREATE INDEX ix_results_session_id ON results (session_id);
```

### 7.2 Format des sources extraites

```json
[
  {
    "type": "markdown_link",
    "text": "Article Wikipedia",
    "url": "https://wikipedia.org/...",
    "position": 0,
    "extraction_method": "markdown_pattern"
  },
  {
    "type": "perplexity_citation",
    "url": "https://example.com",
    "title": "Titre de la page",
    "snippet": "Extrait du contenu...",
    "position": 1,
    "extraction_method": "perplexity_api_citations"
  }
]
```

---

## 8. Processus d'expérimentation

### 8.1 Flux d'exécution complet

```
1. Démarrage (main.py)
   ├─ Chargement .env
   ├─ Lecture config.yaml
   └─ Initialisation BDD

2. Configuration (ExperimentRunner)
   ├─ Création clients API
   ├─ Validation des clés
   └─ Génération session_id

3. Boucle principale
   ├─ Pour chaque itération (1 → N)
   │   ├─ Randomisation requêtes
   │   └─ Pour chaque requête
   │       └─ Pour chaque modèle
   │           ├─ Appel API async
   │           ├─ Mesure temps
   │           ├─ Extraction sources
   │           └─ Sauvegarde BDD
   └─ Délai inter-itération

4. Finalisation
   ├─ Logs finaux
   └─ Fermeture connexions
```

### 8.2 Gestion des erreurs

**Retry automatique pour :**
- Rate limiting (429)
- Erreurs serveur (5xx)
- Timeouts réseau
- Erreurs de connexion

**Stratégie de retry :**
- Max 3 tentatives
- Délai exponentiel (1s, 2s, 4s)

### 8.3 Métriques collectées

Pour chaque requête :
- Temps de réponse (ms)
- Nombre de sources citées
- Longueur de la réponse
- Métadonnées (tokens, modèle, etc.)

---

## 9. Analyse des données

### 9.1 Export vers CSV (export_to_csv.py)

**Fichiers générés :**

1. **experiment_data_*.csv**
   - Toutes les données brutes
   - Colonnes calculées (longueur, has_sources)
   - Format optimal pour R

2. **sources_detail_*.csv**
   - Une ligne par source citée
   - URL, titre, snippet
   - Lien avec result_id

3. **aggregated_data_*.csv**
   - Moyennes par modèle/requête
   - Écarts-types
   - Pourcentages avec sources

4. **temporal_analysis_*.csv**
   - Évolution temporelle
   - Groupé par heure/jour
   - Métriques moyennes

### 9.2 Script R généré

**Analyses automatiques :**
- Distribution des longueurs (boxplot)
- Temps de réponse par modèle
- Pourcentage de citations
- Analyse par catégorie

### 9.3 Métriques calculées

**Visibilité des sources :**
```
V(s,q,t) = (1/R) × Σ(w_i,j,o,m)
```

**Stabilité temporelle :**
```
σ(s,q) = √[(1/k) × Σ(V(s,q,t) - V̄(s,q))²]
```

**Superposition (Jaccard) :**
```
k(q) = |S_f(q) ∩ S_g(q)| / |S_f(q) ∪ S_g(q)|
```

---

## 10. Guide d'utilisation

### 10.1 Installation

```bash
# 1. Cloner le projet
git clone [repository]
cd testACv1

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configurer les clés API
cp .env.example .env
# Éditer .env avec vos clés
```

### 10.2 Configuration

```bash
# 1. Éditer la configuration
nano src/config.yaml

# 2. Activer/désactiver les modèles
enabled: true/false

# 3. Ajuster les paramètres
iterations_per_query: 10
delay_between_iterations_seconds: 5
```

### 10.3 Lancement d'une expérience

```bash
# Expérience complète
python -m src.main

# Avec configuration custom
python -m src.main --config my_config.yaml
```

### 10.4 Analyse des résultats

```bash
# 1. Export vers CSV
python export_to_csv.py

# 2. Analyse dans R
cd analysis_exports
Rscript analysis_script.R

# 3. Ou dans RStudio
# Ouvrir analysis_script.R
```

### 10.5 Ajout de nouvelles requêtes

Éditer `config.yaml` :
```yaml
queries:
  - id: "nouveau_001"
    text: "Ma nouvelle requête..."
    category: "Nouvelle catégorie"
    metadata: { "tag": "valeur" }
```

### 10.6 Ajout d'un nouveau modèle

1. Créer `src/clients/nouveau_client.py`
2. Hériter de `BaseClient`
3. Implémenter `query()` et `_extract_sources()`
4. Ajouter dans `config.yaml`

---

## 11. Troubleshooting

### 11.1 Erreurs communes

**"No module named 'src'"**
```bash
# Lancer depuis la racine
cd /path/to/testACv1
python -m src.main
```

**"API key not found"**
```bash
# Vérifier .env
cat .env
# Vérifier le nom de la variable
grep "API_KEY" src/config.yaml
```

**"Rate limit exceeded"**
- Augmenter `delay_between_iterations_seconds`
- Réduire `iterations_per_query`
- Utiliser des clés API différentes

### 11.2 Problèmes de performance

**Expérience trop lente :**
- Réduire `max_tokens` dans les paramètres
- Paralléliser avec moins de modèles
- Utiliser des modèles plus rapides

**Base de données volumineuse :**
```bash
# Nettoyer anciennes données
sqlite3 experiment_results/experiment_data.db
DELETE FROM results WHERE timestamp < '2025-01-01';
VACUUM;
```

### 11.3 Debugging

**Activer les logs détaillés :**
```python
# Dans runner.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Tester un seul modèle :**
```yaml
# Désactiver tous sauf un
enabled: false  # Pour tous
enabled: true   # Sauf celui à tester
```

**Requête de test rapide :**
```yaml
iterations_per_query: 1
queries:
  - id: "test"
    text: "Test"
    category: "Test"
```

### 11.4 Sauvegarde et restauration

**Backup de la base :**
```bash
cp experiment_results/experiment_data.db \
   experiment_results/backup_$(date +%Y%m%d).db
```

**Export complet :**
```bash
python export_to_csv.py
tar -czf backup_$(date +%Y%m%d).tar.gz analysis_exports/
```

---

## Annexes

### A. Format des réponses API

**OpenAI :**
```json
{
  "choices": [{
    "message": {
      "content": "Réponse..."
    }
  }],
  "usage": {
    "total_tokens": 150
  }
}
```

**Claude :**
```json
{
  "content": [{
    "text": "Réponse..."
  }],
  "usage": {
    "input_tokens": 50,
    "output_tokens": 100
  }
}
```

**Perplexity (avec citations) :**
```json
{
  "choices": [{
    "message": {
      "content": "Réponse [1]...",
      "citations": [{
        "url": "https://...",
        "title": "..."
      }]
    }
  }]
}
```

### B. Méthodes d'extraction de sources

1. **Regex Patterns**
   - Markdown: `\[([^\]]+)\]\((https?://[^)]+)\)`
   - URL brute: `https?://[^\s]+`
   - Citations: `\[(\d+)\]`

2. **Parsing structuré**
   - JSON pour moteurs de recherche
   - Citations natives Perplexity

3. **Heuristiques**
   - Lignes commençant par "Source:"
   - Sections "Références"

### C. Optimisations possibles

1. **Performance**
   - Cache des réponses
   - Requêtes parallèles par batch
   - Connection pooling SQLite

2. **Qualité**
   - Validation des URLs extraites
   - Déduplication des sources
   - Scoring de pertinence

3. **Analyses avancées**
   - NLP sur les réponses
   - Clustering des sources
   - Analyse de sentiment

---

Cette documentation sera mise à jour au fur et à mesure de l'évolution du projet. Pour toute question ou contribution, référez-vous au README.md principal.