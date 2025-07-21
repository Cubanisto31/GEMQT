#!/usr/bin/env python3
"""
Test rapide pour vérifier que les corrections de regex fonctionnent
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.config import ExperimentConfig
from src import get_client


async def test_single_query():
    """Test avec une seule requête pour vérifier les corrections."""
    
    # Configuration des variables d'environnement
    os.environ['OPENAI_API_KEY'] = "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"
    os.environ['GOOGLE_API_KEY'] = "AIzaSyClqDB-4HfA7rNPdwQ_7_koklAWpsbBPUw"
    os.environ['GOOGLE_CX'] = "00d958f7659854ec3"
    
    print("🧪 TEST DES CORRECTIONS DE REGEX")
    print("=" * 50)
    
    # Chargement config
    config = ExperimentConfig.from_yaml("src/config.yaml")
    
    # Test requête simple
    test_query = "Quels sont les symptômes de la grippe ?"
    
    for model_config in config.models:
        if not model_config.enabled:
            continue
            
        print(f"\n🔄 Test {model_config.name}...")
        
        try:
            client = get_client(model_config)
            response = await client.query(test_query, "test_session")
            
            if response.get("response_raw", "").startswith("ERROR"):
                print(f"❌ Erreur: {response['response_raw']}")
            else:
                response_text = response.get("response_raw", "")
                sources = response.get("sources_extracted", [])
                
                print(f"✅ Réponse OK ({len(response_text)} chars)")
                print(f"📚 Sources détectées: {len(sources)}")
                
                if sources:
                    print("   Types:", [s.get('type', 'unknown') for s in sources[:3]])
                
                # Aperçu de la réponse
                if len(response_text) > 0:
                    preview = response_text[:150] + "..." if len(response_text) > 150 else response_text
                    print(f"   Aperçu: {preview}")
        
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
    
    print(f"\n✅ Test terminé!")


if __name__ == "__main__":
    asyncio.run(test_single_query())