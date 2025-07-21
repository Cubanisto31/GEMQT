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

*Tips perso*
Pour run le programme :
- assure toi de bien exporté les API keys avec les commandes indiqués dans le fichier API KEY v1

- utilise la commande python -m src.main (dans une invite powershell) dans le dossier testACv1


Reprendre en regardant les nouveaux resultats et en fonction demander pourquoi les llm ne montrent pas les résultats

