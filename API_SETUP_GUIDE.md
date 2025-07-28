# Guide d'obtention des clés API

Ce guide vous aide à obtenir les clés API nécessaires pour l'expérimentation sur le référencement par les agents conversationnels.

## 1. Bing Web Search API

### ⚠️ Notice de fin de vie de Bing Search v7
**IMPORTANT**: Bing Search v7 sera retiré le **11 août 2025**. Microsoft recommande de migrer vers la nouvelle **Bing Web Search API**.

### Option 1: Bing Web Search API (Recommandé)

#### Étapes pour obtenir une clé API Bing Web Search:

1. **Créer un compte Azure** (si vous n'en avez pas)
   - Visitez [portal.azure.com](https://portal.azure.com)
   - Créez un compte gratuit (200$ de crédit gratuit pendant 30 jours)

2. **Créer une ressource Bing Web Search API**
   - Dans le portail Azure, cliquez sur "Créer une ressource"
   - Recherchez "Bing Search APIs v7" puis sélectionnez "Bing Web Search"
   - Sélectionnez le plan tarifaire:
     - **F1** (gratuit): 1000 requêtes/mois, 3 requêtes/seconde
     - **S1** (payant): 1M requêtes/mois, 50 requêtes/seconde
   - Créez la ressource

3. **Récupérer la clé API**
   - Allez dans votre ressource Bing Web Search
   - Dans le menu de gauche, cliquez sur "Clés et point de terminaison"
   - Copiez la "Clé 1" ou la "Clé 2"

4. **Configurer la variable d'environnement**
   ```bash
   export BING_API_KEY="votre_clé_api_ici"
   ```

### Option 2: Alternatives à Bing Search

#### Google Custom Search API
1. **Créer un projet Google Cloud**
   - Visitez [console.cloud.google.com](https://console.cloud.google.com)
   - Créez un nouveau projet

2. **Activer l'API Custom Search**
   - Allez dans "APIs & Services" > "Library"
   - Recherchez "Custom Search API" et activez-la

3. **Créer des identifiants**
   - Allez dans "APIs & Services" > "Credentials"
   - Créez une clé API

4. **Configurer un moteur de recherche personnalisé**
   - Visitez [cse.google.com](https://cse.google.com)
   - Créez un nouveau moteur de recherche
   - Configurez-le pour rechercher sur tout le web
   - Récupérez l'ID du moteur (CX)

5. **Variables d'environnement**
   ```bash
   export GOOGLE_API_KEY="votre_clé_api_google"
   export GOOGLE_CX="votre_cx_id"
   ```

#### DuckDuckGo (Sans clé API)
DuckDuckGo peut être utilisé via web scraping, mais attention aux limitations et au respect des conditions d'utilisation.

### Limites des plans gratuits:
- **Bing Web Search F1**: 1000 requêtes/mois, 3 requêtes/seconde
- **Google Custom Search**: 100 requêtes/jour gratuitement

## 2. Claude API (Anthropic)

### Étapes pour obtenir une clé API Claude:

1. **Créer un compte Anthropic**
   - Visitez [console.anthropic.com](https://console.anthropic.com)
   - Inscrivez-vous avec votre email

2. **Obtenir l'accès à l'API**
   - Complétez votre profil
   - Demandez l'accès à l'API (peut nécessiter une approbation)
   - Une fois approuvé, vous recevrez un email de confirmation

3. **Générer une clé API**
   - Connectez-vous à la console Anthropic
   - Allez dans "API Keys"
   - Cliquez sur "Create Key"
   - Donnez un nom à votre clé et copiez-la

4. **Configurer la variable d'environnement**
   ```bash
   export ANTHROPIC_API_KEY="votre_clé_api_ici"
   ```

### Tarification:
- Claude 3 Sonnet: ~3$ pour 1M tokens d'entrée, ~15$ pour 1M tokens de sortie
- Claude 3 Opus: ~15$ pour 1M tokens d'entrée, ~75$ pour 1M tokens de sortie

## 3. Google Gemini API

### Étapes pour obtenir une clé API Gemini:

1. **Accéder à Google AI Studio**
   - Visitez [aistudio.google.com](https://aistudio.google.com)
   - Connectez-vous avec votre compte Google

2. **Obtenir une clé API**
   - Cliquez sur "Get API key"
   - Créez un nouveau projet ou sélectionnez un projet existant
   - Générez une nouvelle clé API

3. **Configurer la variable d'environnement**
   ```bash
   export GEMINI_API_KEY="votre_clé_api_ici"
   ```

### Limites gratuites:
- 60 requêtes par minute
- Quotas quotidiens généreux

## 4. Perplexity API

### Étapes pour obtenir une clé API Perplexity:

1. **Créer un compte Perplexity**
   - Visitez [perplexity.ai](https://www.perplexity.ai)
   - Inscrivez-vous et connectez-vous

2. **Accéder aux paramètres API**
   - Allez dans les paramètres de votre compte
   - Cherchez la section "API Access"
   - Générez une nouvelle clé API

3. **Configurer la variable d'environnement**
   ```bash
   export PERPLEXITY_API_KEY="votre_clé_api_ici"
   ```

## 5. Microsoft Copilot (via Azure OpenAI)

### Étapes pour accéder à Azure OpenAI:

1. **Demander l'accès à Azure OpenAI**
   - Remplissez le formulaire sur [aka.ms/oai/access](https://aka.ms/oai/access)
   - L'approbation peut prendre quelques jours

2. **Créer une ressource Azure OpenAI**
   - Une fois approuvé, créez une ressource dans le portail Azure
   - Déployez un modèle (GPT-4, etc.)

3. **Récupérer les informations de connexion**
   - Endpoint URL
   - Clé API
   - Nom du déploiement

4. **Configurer les variables d'environnement**
   ```bash
   export AZURE_OPENAI_KEY="votre_clé_api"
   export AZURE_OPENAI_ENDPOINT="https://votre-ressource.openai.azure.com/"
   export AZURE_OPENAI_DEPLOYMENT="nom-de-votre-deploiement"
   ```

## Configuration dans le projet

Une fois les clés obtenues:

1. Créez un fichier `.env` à la racine du projet (s'il n'existe pas)
2. Ajoutez vos clés API:
   ```
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-ant-...
   BING_API_KEY=...
   GEMINI_API_KEY=...
   PERPLEXITY_API_KEY=...
   GOOGLE_API_KEY=...
   GOOGLE_CX=...
   ```

3. Activez les modèles souhaités dans `src/config.yaml` en changeant `enabled: false` en `enabled: true`

## Sécurité

- **Ne partagez jamais vos clés API**
- Ajoutez `.env` à votre `.gitignore`
- Utilisez des variables d'environnement plutôt que de coder en dur les clés
- Surveillez régulièrement votre utilisation pour éviter les frais inattendus

## Support

Si vous rencontrez des problèmes pour obtenir une clé API, consultez:
- La documentation officielle de chaque service
- Les forums de support respectifs
- Les guides de démarrage rapide fournis par chaque plateforme