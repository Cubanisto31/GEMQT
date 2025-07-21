#!/usr/bin/env python3
"""
Script de test rapide pour vérifier que l'installation fonctionne correctement.
Usage: python test_setup.py
"""
import asyncio
import os
import sys
from pathlib import Path

# Ajouter le répertoire racine au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

from src.config import ExperimentConfig
from src import get_client


async def test_clients():
    """Teste l'initialisation et le fonctionnement basique des clients."""
    print("🧪 Test des clients API...")
    
    # Chargement de la configuration
    try:
        config = ExperimentConfig.from_yaml("src/config.yaml")
        print("✅ Configuration chargée")
    except Exception as e:
        print(f"❌ Erreur lors du chargement de la configuration: {e}")
        return False
    
    success_count = 0
    total_clients = len([m for m in config.models if m.enabled])
    
    for model_config in config.models:
        if not model_config.enabled:
            continue
            
        print(f"\n🔄 Test du client {model_config.name}...")
        
        try:
            # Initialisation du client
            client = get_client(model_config)
            print(f"✅ Client {model_config.name} initialisé")
            
            # Test d'une requête simple
            if model_config.type == "llm":
                test_query = "Bonjour, pouvez-vous me dire quelle est la capitale de la France ?"
                print(f"🔍 Test de requête: {test_query[:30]}...")
                
                response = await client.query(test_query, "test_session")
                
                if response and response.get("response_raw"):
                    sources_count = len(response.get("sources_extracted", []))
                    print(f"✅ Réponse reçue ({len(response['response_raw'])} chars, {sources_count} sources)")
                    success_count += 1
                else:
                    print("❌ Réponse vide ou invalide")
                    
            elif model_config.type == "search_engine":
                test_query = "python programming language"
                print(f"🔍 Test de recherche: {test_query}")
                
                response = await client.query(test_query, "test_session")
                
                if response and response.get("sources_extracted"):
                    results_count = len(response["sources_extracted"])
                    print(f"✅ Recherche réussie ({results_count} résultats)")
                    success_count += 1
                else:
                    print("❌ Recherche échouée")
        
        except Exception as e:
            print(f"❌ Erreur avec {model_config.name}: {str(e)[:100]}...")
    
    print(f"\n📊 Résultats: {success_count}/{total_clients} clients fonctionnels")
    return success_count == total_clients


def test_database():
    """Teste la connexion à la base de données."""
    print("\n🗄️  Test de la base de données...")
    
    try:
        from src.database import initialize_database, get_db_session
        
        # Initialisation
        db_url = "sqlite:///test_experiment.db"
        initialize_database(db_url)
        print("✅ Base de données initialisée")
        
        # Test de session
        with get_db_session() as session:
            print("✅ Session de base de données fonctionnelle")
        
        # Nettoyage
        Path("test_experiment.db").unlink(missing_ok=True)
        return True
        
    except Exception as e:
        print(f"❌ Erreur de base de données: {e}")
        return False


def check_environment():
    """Vérifie les variables d'environnement."""
    print("\n🔧 Vérification de l'environnement...")
    
    required_vars = ['OPENAI_API_KEY', 'GOOGLE_API_KEY', 'GOOGLE_CX']
    missing_vars = []
    
    for var in required_vars:
        if os.environ.get(var):
            print(f"✅ {var} configuré")
        else:
            print(f"❌ {var} manquant")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️  Variables manquantes: {', '.join(missing_vars)}")
        print("💡 Lancez: python setup_env.py")
        return False
    
    return True


async def main():
    print("🧪 Test de l'installation de l'expérimentation GEO")
    print("=" * 60)
    
    # Vérifications préliminaires
    env_ok = check_environment()
    db_ok = test_database()
    
    if not env_ok:
        print("\n❌ Configuration d'environnement incomplète")
        return
    
    if not db_ok:
        print("\n❌ Problème avec la base de données")
        return
    
    # Test des clients API
    clients_ok = await test_clients()
    
    print("\n" + "=" * 60)
    if clients_ok:
        print("🎉 Tous les tests sont passés ! Votre installation est prête.")
        print("\n📋 Pour lancer l'expérience:")
        print("   python -m src.main --config src/config.yaml")
    else:
        print("❌ Certains tests ont échoué. Vérifiez votre configuration.")


if __name__ == "__main__":
    asyncio.run(main())