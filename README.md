# Framework d'Expérimentation sur le Référencement des Sources

Ce projet fournit un framework complet pour mener des expérimentations à grande échelle sur la manière dont les modèles de langage (LLMs) et les moteurs de recherche citent leurs sources. Il est conçu pour être modulaire, extensible et automatisé.

## Nouveautés 🎉

### ✅ Support des fichiers de requêtes externes
Les requêtes peuvent maintenant être chargées depuis un fichier Excel ou CSV externe, évitant de modifier le fichier de configuration YAML.

### ✅ Réponses complètes sauvegardées
Les réponses complètes sont désormais sauvegardées dans le champ `response_raw` de la base de données.

### ✅ Nouveaux modèles et moteurs ajoutés
- **Bing Search API** - Moteur de recherche Microsoft
- **Google Gemini** - LLM de Google
- **Perplexity AI** - LLM avec recherche web intégrée
- **Claude** (déjà implémenté)

### 📖 Guide d'obtention des clés API
Consultez [API_SETUP_GUIDE.md](API_SETUP_GUIDE.md) pour des instructions détaillées sur l'obtention des clés API.

## Structure du Projet

```
.
├── 📂 experiment_results/
├── 📂 src/
│   ├── clients/
│   │   ├── __init__.py
│   │   ├── base_client.py
│   │   ├── claude_client.py
│   │   ├── openai_client.py
│   │   ├── gemini_client.py
│   │   ├── perplexity_client.py
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
├── CLAUDE.md
├── queries_pool_v1.xlsx           # Pool de requêtes Excel existant
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
python -m src.main run
```

### Avec configuration personnalisée
```bash
python -m src.main run --config mon_config.yaml
```

### Avec fichier de requêtes externe
Le système supporte maintenant le chargement des requêtes depuis un fichier externe (Excel ou CSV) :

```bash
# Avec un fichier Excel
python -m src.main run --queries queries_pool_v1.xlsx

# Avec un fichier CSV
python -m src.main run --queries queries_pool_example.csv

# Avec une configuration personnalisée ET un fichier de requêtes externe
python -m src.main run --config src/config_without_queries.yaml --queries queries_pool_v1.xlsx
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

## Prochaines étapes

- Bien regarder et travailler sur la doc 
- Vérifier les datas que l'on obtient en sortie 
- Il manque toujours la clé de Bing 
- Faire attention aux crédits sur les différentes clés API
- Commencer à faire une première analyse sur un test

Ensuite on verra pour :

- [ ] Système d'automatisation temporelle (planification des exécutions)
- [ ] Intégration Microsoft Copilot
- [ ] Amélioration du pool de requêtes
- [ ] Dashboard de visualisation en temps réel
