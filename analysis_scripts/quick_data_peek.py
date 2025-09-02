#!/usr/bin/env python3
"""
Script rapide pour examiner le contenu des réponses et comprendre pourquoi GPT-4o n'a pas de sources.
"""

import sqlite3
import json
from pathlib import Path

def peek_responses():
    """Examine quelques réponses pour comprendre les patterns de référencement."""
    
    db_path = "experiment_results/experiment_data.db"
    if not Path(db_path).exists():
        print(f"❌ Base de données {db_path} introuvable")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Récupère quelques réponses de chaque modèle
    query = """
    SELECT model_name, query_text, response_raw, sources_extracted
    FROM results 
    WHERE model_name IN ('GPT-4o', 'Google-Search')
    LIMIT 4
    """
    
    results = cursor.fetchall()
    
    print("🔍 ÉCHANTILLON DE RÉPONSES")
    print("=" * 80)
    
    for model, query, response, sources in cursor.execute(query):
        print(f"\n📋 MODÈLE: {model}")
        print(f"❓ REQUÊTE: {query[:60]}...")
        
        if response:
            print(f"💬 RÉPONSE ({len(response)} chars): {response[:200]}...")
            
            # Cherche manuellement des patterns de sources dans la réponse
            if model == 'GPT-4o':
                # Patterns de sources potentielles
                patterns_found = []
                if 'selon' in response.lower():
                    patterns_found.append('selon')
                if 'source' in response.lower():
                    patterns_found.append('source')  
                if 'https://' in response:
                    patterns_found.append('URL')
                if '[' in response and ']' in response:
                    patterns_found.append('citations')
                
                if patterns_found:
                    print(f"🔍 Patterns trouvés dans la réponse: {', '.join(patterns_found)}")
                else:
                    print("🔍 Aucun pattern de source détecté dans la réponse")
        
        # Sources extraites
        if sources and sources != '[]':
            try:
                sources_list = json.loads(sources) if isinstance(sources, str) else sources
                print(f"📚 SOURCES ({len(sources_list)}): {sources_list[:2] if len(sources_list) > 2 else sources_list}")
            except:
                print(f"📚 SOURCES (erreur parsing): {str(sources)[:100]}")
        else:
            print("📚 SOURCES: Aucune")
        
        print("-" * 60)
    
    conn.close()
    
    # Statistiques rapides
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"\n📊 STATISTIQUES RAPIDES")
    stats_query = """
    SELECT 
        model_name,
        COUNT(*) as total_responses,
        AVG(length(response_raw)) as avg_response_length,
        SUM(CASE WHEN sources_extracted != '[]' AND sources_extracted IS NOT NULL THEN 1 ELSE 0 END) as responses_with_sources
    FROM results
    GROUP BY model_name
    """
    
    print(f"{'Modèle':<15} {'Réponses':<10} {'Long.Moy':<10} {'Avec Sources':<12}")
    print("-" * 50)
    
    for row in cursor.execute(stats_query):
        model, total, avg_len, with_sources = row
        print(f"{model:<15} {total:<10} {avg_len:<10.0f} {with_sources:<12}")
    
    conn.close()

if __name__ == "__main__":
    peek_responses()