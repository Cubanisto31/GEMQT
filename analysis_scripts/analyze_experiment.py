#!/usr/bin/env python3
"""
Script d'analyse des résultats d'expérience
"""

import sqlite3
import pandas as pd
import json
from datetime import datetime

def load_experiment_data():
    """Charge les données de l'expérience depuis la base SQLite"""
    db_path = "experiment_results/experiment_data.db"
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Récupérer toutes les données
        query = """
        SELECT 
            query_id,
            query_text,
            model_name,
            response_raw as response_text,
            sources_extracted as sources_json,
            response_time_ms,
            timestamp,
            session_id,
            iteration,
            query_category
        FROM results 
        ORDER BY timestamp DESC
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        print(f"📊 {len(df)} enregistrements chargés depuis la base de données")
        return df
        
    except Exception as e:
        print(f"❌ Erreur lors du chargement: {e}")
        return None

def analyze_sources(df):
    """Analyse les sources citées par chaque modèle"""
    print("\n🔍 ANALYSE DES SOURCES PAR MODÈLE")
    print("=" * 60)
    
    source_stats = {}
    
    for _, row in df.iterrows():
        model = row['model_name']
        if model not in source_stats:
            source_stats[model] = {'with_sources': 0, 'total': 0, 'total_sources': 0}
        
        source_stats[model]['total'] += 1
        
        # Parser les sources JSON
        try:
            sources = json.loads(row['sources_json']) if row['sources_json'] else []
            if sources:
                source_stats[model]['with_sources'] += 1
                source_stats[model]['total_sources'] += len(sources)
        except:
            pass
    
    # Afficher les statistiques
    for model, stats in source_stats.items():
        pct_with_sources = (stats['with_sources'] / stats['total']) * 100 if stats['total'] > 0 else 0
        avg_sources = stats['total_sources'] / stats['with_sources'] if stats['with_sources'] > 0 else 0
        
        print(f"\n📋 {model}:")
        print(f"  • Réponses avec sources: {stats['with_sources']}/{stats['total']} ({pct_with_sources:.1f}%)")
        print(f"  • Sources moyennes par réponse: {avg_sources:.1f}")
        print(f"  • Total sources uniques: {stats['total_sources']}")

def analyze_response_quality(df):
    """Analyse la qualité et longueur des réponses"""
    print("\n📝 ANALYSE DE LA QUALITÉ DES RÉPONSES")
    print("=" * 60)
    
    response_stats = df.groupby('model_name').agg({
        'response_text': ['count', lambda x: x.str.len().mean(), lambda x: x.str.len().std()],
        'response_time_ms': ['mean', 'std']
    }).round(2)
    
    response_stats.columns = ['Nb_Réponses', 'Long_Moyenne', 'Écart_Type_Long', 'Temps_Moyen_ms', 'Écart_Type_Temps']
    
    print(response_stats)

def analyze_by_query_type(df):
    """Analyse les résultats par type de requête"""
    print("\n🎯 ANALYSE PAR TYPE DE REQUÊTE")
    print("=" * 60)
    
    # Mapper les query_id aux catégories
    query_categories = {
        'info_sante_001': 'Informationnelle - Santé',
        'info_tech_001': 'Informationnelle - Technique', 
        'transac_voyage_001': 'Transactionnelle - Voyage'
    }
    
    for query_id, category in query_categories.items():
        query_data = df[df['query_id'] == query_id]
        if len(query_data) > 0:
            print(f"\n🔍 {category} ({query_id}):")
            print(f"  • Total réponses: {len(query_data)}")
            
            # Analyser par modèle
            for model in query_data['model_name'].unique():
                model_data = query_data[query_data['model_name'] == model]
                avg_length = model_data['response_text'].str.len().mean()
                
                # Compter les sources
                sources_count = 0
                for _, row in model_data.iterrows():
                    try:
                        sources = json.loads(row['sources_json']) if row['sources_json'] else []
                        sources_count += len(sources)
                    except:
                        pass
                
                print(f"    - {model}: {len(model_data)} réponses, {avg_length:.0f} chars moy., {sources_count} sources")

def show_sample_responses(df):
    """Affiche des échantillons de réponses"""
    print("\n📄 ÉCHANTILLONS DE RÉPONSES DÉTAILLÉES")
    print("=" * 80)
    
    # Prendre un échantillon de chaque modèle
    for model in df['model_name'].unique():
        model_data = df[df['model_name'] == model].head(1)
        
        for _, row in model_data.iterrows():
            print(f"\n🤖 MODÈLE: {row['model_name']}")
            print(f"❓ REQUÊTE: {row['query_text'][:60]}...")
            print(f"⏱️  TEMPS: {row['response_time_ms']}ms")
            print(f"💬 RÉPONSE ({len(row['response_text'])} chars):")
            print(f"   {row['response_text'][:200]}...")
            
            try:
                sources = json.loads(row['sources_json']) if row['sources_json'] else []
                if sources:
                    print(f"📚 SOURCES ({len(sources)}):")
                    for i, source in enumerate(sources[:3], 1):
                        title = source.get('title', 'Sans titre')[:50]
                        url = source.get('url', 'Sans URL')[:50]
                        print(f"   {i}. {title} - {url}")
                else:
                    print("📚 SOURCES: Aucune")
            except:
                print("📚 SOURCES: Erreur de parsing")
            
            print("-" * 80)

def main():
    """Fonction principale d'analyse"""
    print("🔬 ANALYSE DES RÉSULTATS D'EXPÉRIENCE")
    print("=" * 80)
    
    df = load_experiment_data()
    if df is None:
        return
    
    print(f"📅 Période analysée: {df['timestamp'].min()} à {df['timestamp'].max()}")
    print(f"🔄 Sessions: {df['session_id'].nunique()}")
    print(f"❓ Requêtes uniques: {df['query_id'].nunique()}")
    print(f"🤖 Modèles testés: {', '.join(df['model_name'].unique())}")
    
    analyze_sources(df)
    analyze_response_quality(df)
    analyze_by_query_type(df)
    show_sample_responses(df)

if __name__ == "__main__":
    main()