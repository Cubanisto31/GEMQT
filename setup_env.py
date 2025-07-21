#!/usr/bin/env python3
"""
Script utilitaire pour configurer les variables d'environnement nécessaires à l'expérimentation.
Usage: python setup_env.py
"""
import os
import sys
from pathlib import Path


def load_api_keys():
    """Charge les clés API depuis le fichier API KEY v1.txt."""
    api_file = Path("API KEY v1.txt")
    if not api_file.exists():
        print(f"❌ Fichier {api_file} non trouvé.")
        return None
    
    keys = {}
    with open(api_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Extraction des clés API
    import re
    openai_match = re.search(r'OPENAI_API_KEY="([^"]+)"', content)
    google_api_match = re.search(r'GOOGLE_API_KEY="([^"]+)"', content)
    google_cx_match = re.search(r'GOOGLE_CX="([^"]+)"', content)
    
    if openai_match:
        keys['OPENAI_API_KEY'] = openai_match.group(1)
    if google_api_match:
        keys['GOOGLE_API_KEY'] = google_api_match.group(1)
    if google_cx_match:
        keys['GOOGLE_CX'] = google_cx_match.group(1)
    
    return keys


def set_environment_variables(keys):
    """Configure les variables d'environnement."""
    for key, value in keys.items():
        os.environ[key] = value
        print(f"✅ {key} configuré")


def create_dotenv_file(keys):
    """Crée un fichier .env pour la persistance."""
    env_content = []
    for key, value in keys.items():
        env_content.append(f'{key}="{value}"')
    
    with open('.env', 'w') as f:
        f.write('\n'.join(env_content))
    print("✅ Fichier .env créé")


def verify_configuration():
    """Vérifie que toutes les clés nécessaires sont présentes."""
    required_keys = ['OPENAI_API_KEY', 'GOOGLE_API_KEY', 'GOOGLE_CX']
    missing_keys = []
    
    for key in required_keys:
        if not os.environ.get(key):
            missing_keys.append(key)
    
    if missing_keys:
        print(f"⚠️  Clés manquantes: {', '.join(missing_keys)}")
        return False
    
    print("✅ Toutes les clés API sont configurées")
    return True


def test_api_connectivity():
    """Teste la connectivité avec les APIs (optionnel)."""
    print("\n🔄 Test de connectivité des APIs...")
    
    # Test OpenAI (simple validation de la clé)
    openai_key = os.environ.get('OPENAI_API_KEY')
    if openai_key and openai_key.startswith('sk-'):
        print("✅ Format de clé OpenAI valide")
    else:
        print("❌ Format de clé OpenAI invalide")
    
    # Test Google API
    google_key = os.environ.get('GOOGLE_API_KEY')
    google_cx = os.environ.get('GOOGLE_CX')
    if google_key and google_cx:
        print("✅ Clés Google Search configurées")
    else:
        print("❌ Clés Google Search manquantes")


def main():
    print("🚀 Configuration de l'environnement pour l'expérimentation GEO")
    print("=" * 60)
    
    # Chargement des clés
    keys = load_api_keys()
    if not keys:
        print("❌ Impossible de charger les clés API")
        sys.exit(1)
    
    print(f"📝 {len(keys)} clés trouvées dans le fichier")
    
    # Configuration des variables d'environnement
    set_environment_variables(keys)
    
    # Création du fichier .env
    create_dotenv_file(keys)
    
    # Vérification
    if verify_configuration():
        print("\n🎉 Configuration terminée avec succès !")
        test_api_connectivity()
        
        print("\n📋 Prochaines étapes:")
        print("1. Vérifiez votre fichier src/config.yaml")
        print("2. Lancez l'expérience: python -m src.main")
        print("3. Consultez les logs dans experiment.log")
    else:
        print("❌ Configuration échouée")
        sys.exit(1)


if __name__ == "__main__":
    main()