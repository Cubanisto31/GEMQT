# Instructions pour l'expérimentation sur le référencement par les agents conversationnels

## Contexte du projet

Tu travailles sur une expérimentation explorant comment les agents conversationnels (comme ChatGPT, Claude, etc.) référencent et citent leurs sources, comparativement aux moteurs de recherche traditionnels. Cette recherche s'inscrit dans le cadre de l'émergence des moteurs génératifs et de l'Optimisation pour Moteurs Génératifs (GEO).

## Objectifs de l'expérimentation

### Hypothèses à tester
1. **Hypothèse 1** : Le référencement repose principalement sur l'entraînement du modèle (sources intégrées lors du pré-entraînement)
2. **Hypothèse 2a** : Le référencement est largement influencé par les moteurs de recherche classiques à l'instant de la requête
3. **Hypothèse 2b** : Le référencement dépend des caractéristiques intrinsèques des sources (mots-clés, structure, lisibilité)

### Design expérimental
L'expérience suit cette structure :
1. Création de pools de requêtes (navigation, information, transactionnelles)
2. Soumission des requêtes aux agents conversationnels ET aux moteurs de recherche
3. Répétition `r` fois pour la robustesse
4. Répétition dans le temps pour observer l'évolution
5. Réplication avec différents agents et moteurs

## Tâches prioritaires à accomplir

### 1. Amélioration de la collecte de données
- [ ] **Ajouter les réponses complètes** aux requêtes dans le fichier de sortie (pas seulement les sources citées)
- [ ] Stocker la réponse textuelle intégrale de chaque agent conversationnel
- [ ] Conserver les métadonnées : timestamp, modèle utilisé, paramètres, etc.
- [ ] Implémenter un système de sauvegarde robuste avec gestion d'erreurs

### 2. Extension des modèles et moteurs
- [ ] **Ajouter d'autres modèles** :
  - OpenAI GPT-4 (déjà implémenté ?)
  - Claude (Anthropic)
  - Gemini (Google)
  - Perplexity AI
  - Microsoft Copilot
- [ ] **Ajouter d'autres moteurs de recherche** :
  - Bing Search API (priorité)
  - DuckDuckGo
  - Yahoo Search
- [ ] **Aide pour les clés API** : Guider l'utilisateur dans l'obtention des clés nécessaires

### 3. Automatisation temporelle
- [ ] **Système de planification** pour exécuter les requêtes sur plusieurs jours
- [ ] Configuration des intervalles de temps (quotidien, hebdomadaire, etc.)
- [ ] Gestion de la persistance des données entre les sessions
- [ ] Monitoring et logging des exécutions programmées

## Spécifications techniques importantes

### Structure des données
```
Pour chaque requête qi, instant tj, réplication ro :
- Requête originale
- Requête reformulée (si applicable)
- Réponse complète de l'agent
- Sources citées avec leur visibilité/poids
- Métadonnées (modèle, timestamp, paramètres)
```

### Pools de requêtes
Utilise la taxonomie de Broder (2002) :
- **Navigation** : requêtes visant un site particulier
- **Information** : requêtes cherchant des informations
- **Transactionnelles** : requêtes pour effectuer une action

### Contrôles expérimentaux
- **Invariance du modèle** : S'assurer qu'aucun réentraînement n'a lieu
- **Indépendance des requêtes** : Vérifier que P(f(qi+1)|f(qi)) = P(f(qi+1))

## Métriques à calculer

### Visibilité des sources
```
V(sh,qi,tj) = (1/R) × Σ(w_{i,j,o,m})
```

### Stabilité temporelle
```
σ(sh,qi) = √[(1/k) × Σ(V(sh,qi,tj) - V̄(sh,qi))²]
```

### Degré de superposition (coefficient de Jaccard)
```
k(qi) = |Sf(qi) ∩ Sg(qi)| / |Sf(qi) ∪ Sg(qi)|
```

## Instructions spéciales

### Gestion des APIs
- Implémenter un système de rate limiting robuste
- Gérer les erreurs et les timeouts gracieusement
- Permettre la pause/reprise des expérimentations longues
- Sauvegarder les résultats partiels régulièrement

### Analyse des réponses
- Extraire les citations et références dans les réponses
- Mesurer la longueur des extraits cités
- Identifier la position des sources dans la réponse
- Analyser le style et la présentation du contenu cité

### Configuration modulaire
- Permettre l'activation/désactivation de différents modèles
- Configuration flexible des paramètres (température, top-p, etc.)
- Options pour Chain of Thought activé/désactivé
- Options pour recherche web activée/désactivée

## Priorités immédiates

1. **URGENT** : Sauvegarder les réponses complètes (pas seulement les sources)
2. **IMPORTANT** : Ajouter Bing Search API avec guide d'obtention de clé
3. **IMPORTANT** : Ajouter Claude et autres modèles avec leurs APIs
4. **PLANIFICATION** : Système d'automatisation temporelle

## Notes techniques

- Utilise des formats de données structurés (JSON, CSV) pour faciliter l'analyse
- Implémenter des checksums pour vérifier l'intégrité des données
- Prévoir un système de backup automatique
- Logger toutes les opérations pour le debugging

## Ressources
- Fichier des requêtes : `queries pool v1`

Tu as déjà bien avancé sur ce projet. Continue sur cette lancée en te concentrant sur les tâches prioritaires listées ci-dessus. N'hésite pas à demander des clarifications si nécessaire.