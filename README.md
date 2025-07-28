# Framework d'Expérimentation sur le Référencement des Sources

Ce projet fournit un framework complet pour mener des expérimentations à grande échelle sur la manière dont les modèles de langage (LLMs) et les moteurs de recherche citent leurs sources. Il est conçu pour être modulaire, extensible et automatisé.

## Nouveautés 🎉

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
│   ├── database.py
│   ├── runner.py
│   └── main.py
├── API_SETUP_GUIDE.md
├── CLAUDE.md
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
