# Framework d'Expérimentation sur le Référencement des Sources

Ce projet fournit un framework complet pour mener des expérimentations à grande échelle sur la manière dont les modèles de langage (LLMs) et les moteurs de recherche citent leurs sources. Il est conçu pour être modulaire, extensible et automatisé.

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
│   │   └── search_clients.py
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── runner.py
│   └── main.py
├── config.yaml
├── requirements.txt
└── README.md
```

*Note*
On a réussi grâce à claude code, à faire tourner le code et l'on est en mesure d'analyser les résultats. Toutefois il va falloir maintenant demandé à Claude code d'ajouter les réponses complètes aux requêtes (que je n'arrive pas encore à trouver).

Il va falloir également que l'on ajoute les autres modèles (il va falloir doucement se poser sur la question du prix de l'exp)

Il faudra aussi refaire une passe sur les requêtes testées

Il faut vérifier si le code tourne tous les jours comme prévu dans le Yaml ou pas (mais ça m'étonnerait)
