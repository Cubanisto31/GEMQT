#!/usr/bin/env python3
"""
Script d'analyse des données d'expérimentation GEO
Génère des exports CSV pour RStudio et des analyses préliminaires en Python

Usage: python analyze_data.py
"""

import pandas as pd
import sqlite3
import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
import sys


def load_data_from_db(db_path="experiment_results/experiment_data.db"):
    """Charge les données depuis la base SQLite."""
    if not Path(db_path).exists():
        print(f"❌ Base de données {db_path} introuvable")
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Requête principale avec toutes les colonnes
        query = """
        SELECT 
            id,
            experiment_id,
            session_id,
            query_id,
            query_text,
            query_category,
            iteration,
            model_name,
            model_type,
            response_raw,
            sources_extracted,
            chain_of_thought,
            response_time_ms,
            timestamp,
            extra_metadata
        FROM results
        ORDER BY timestamp, iteration, query_id, model_name
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        print(f"✅ {len(df)} enregistrements chargés depuis {db_path}")
        return df
        
    except Exception as e:
        print(f"❌ Erreur lors du chargement: {e}")
        return None


def process_sources_data(df):
    """Traite et expanse les données de sources."""
    processed_data = []
    
    for _, row in df.iterrows():
        base_data = {
            'id': row['id'],
            'experiment_id': row['experiment_id'],
            'session_id': row['session_id'],
            'query_id': row['query_id'],
            'query_text': row['query_text'],
            'query_category': row['query_category'],
            'iteration': row['iteration'],
            'model_name': row['model_name'],
            'model_type': row['model_type'],
            'response_time_ms': row['response_time_ms'],
            'timestamp': row['timestamp'],
            'response_length': len(str(row['response_raw'])) if row['response_raw'] else 0,
        }
        
        # Traitement des sources
        sources = row['sources_extracted']
        if sources and sources != '[]':
            try:
                if isinstance(sources, str):
                    sources_list = json.loads(sources)
                else:
                    sources_list = sources
                
                if sources_list and len(sources_list) > 0:
                    for i, source in enumerate(sources_list):
                        source_data = base_data.copy()
                        source_data.update({
                            'source_rank': i + 1,
                            'source_type': source.get('type', 'unknown'),
                            'source_url': source.get('url', source.get('link', '')),
                            'source_title': source.get('title', source.get('text', '')),
                            'source_snippet': source.get('snippet', '')[:200],  # Tronquer
                            'has_sources': True,
                            'total_sources': len(sources_list)
                        })
                        processed_data.append(source_data)
                else:
                    # Pas de sources
                    no_source_data = base_data.copy()
                    no_source_data.update({
                        'source_rank': 0,
                        'source_type': 'none',
                        'source_url': '',
                        'source_title': '',
                        'source_snippet': '',
                        'has_sources': False,
                        'total_sources': 0
                    })
                    processed_data.append(no_source_data)
            except (json.JSONDecodeError, TypeError) as e:
                print(f"⚠️  Erreur JSON pour {row['id']}: {e}")
                no_source_data = base_data.copy()
                no_source_data.update({
                    'source_rank': 0,
                    'source_type': 'error',
                    'source_url': '',
                    'source_title': '',
                    'source_snippet': '',
                    'has_sources': False,
                    'total_sources': 0
                })
                processed_data.append(no_source_data)
        else:
            # Aucune source
            no_source_data = base_data.copy()
            no_source_data.update({
                'source_rank': 0,
                'source_type': 'none',
                'source_url': '',
                'source_title': '',
                'source_snippet': '',
                'has_sources': False,
                'total_sources': 0
            })
            processed_data.append(no_source_data)
    
    return pd.DataFrame(processed_data)


def generate_summary_stats(df, df_sources):
    """Génère des statistiques descriptives."""
    print("\n" + "="*60)
    print("📊 STATISTIQUES DESCRIPTIVES")
    print("="*60)
    
    # Vue d'ensemble
    print(f"🔢 Total d'enregistrements: {len(df)}")
    print(f"🔢 Total de sources individuelles: {len(df_sources)}")
    print(f"📅 Période: {df['timestamp'].min()} → {df['timestamp'].max()}")
    
    # Par modèle
    print(f"\n📈 RÉPARTITION PAR MODÈLE:")
    model_stats = df.groupby('model_name').agg({
        'id': 'count',
        'response_time_ms': ['mean', 'median', 'std']
    }).round(2)
    print(model_stats)
    
    # Par catégorie de requête
    print(f"\n🎯 RÉPARTITION PAR CATÉGORIE:")
    category_stats = df.groupby('query_category').agg({
        'id': 'count',
        'response_time_ms': 'mean'
    }).round(2)
    print(category_stats)
    
    # Sources par modèle
    print(f"\n🔗 SOURCES PAR MODÈLE:")
    source_stats = df_sources.groupby('model_name').agg({
        'total_sources': 'mean',
        'has_sources': 'mean'
    }).round(3)
    print(source_stats)
    
    return {
        'total_records': len(df),
        'total_sources': len(df_sources),
        'date_range': (df['timestamp'].min(), df['timestamp'].max()),
        'model_stats': model_stats,
        'category_stats': category_stats,
        'source_stats': source_stats
    }


def export_to_csv(df, df_sources, output_dir="analysis_exports"):
    """Exporte les données vers des fichiers CSV pour RStudio."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Export principal
    main_file = output_path / f"experiment_data_{timestamp}.csv"
    df.to_csv(main_file, index=False, encoding='utf-8')
    print(f"✅ Export principal: {main_file}")
    
    # Export sources détaillé
    sources_file = output_path / f"sources_detail_{timestamp}.csv"
    df_sources.to_csv(sources_file, index=False, encoding='utf-8')
    print(f"✅ Export sources: {sources_file}")
    
    # Export agrégé par requête/modèle
    agg_data = df_sources.groupby(['query_id', 'query_category', 'model_name', 'iteration']).agg({
        'total_sources': 'first',
        'has_sources': 'first',
        'response_time_ms': 'first',
        'response_length': 'first'
    }).reset_index()
    
    agg_file = output_path / f"aggregated_data_{timestamp}.csv"
    agg_data.to_csv(agg_file, index=False, encoding='utf-8')
    print(f"✅ Export agrégé: {agg_file}")
    
    # Export pour analyse temporelle
    temporal_data = df.groupby(['timestamp', 'model_name', 'query_category']).agg({
        'response_time_ms': 'mean',
        'id': 'count'
    }).reset_index()
    temporal_data.columns = ['timestamp', 'model_name', 'query_category', 'avg_response_time', 'count']
    
    temporal_file = output_path / f"temporal_analysis_{timestamp}.csv"
    temporal_data.to_csv(temporal_file, index=False, encoding='utf-8')
    print(f"✅ Export temporel: {temporal_file}")
    
    return {
        'main': main_file,
        'sources': sources_file,
        'aggregated': agg_file,
        'temporal': temporal_file
    }


def create_visualizations(df_sources, output_dir="analysis_exports"):
    """Crée des visualisations préliminaires."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    plt.style.use('default')
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Analyse Préliminaire - Référencement par les Agents Conversationnels', fontsize=16)
    
    # 1. Sources par modèle
    ax1 = axes[0, 0]
    source_counts = df_sources.groupby('model_name')['total_sources'].mean()
    bars1 = ax1.bar(source_counts.index, source_counts.values)
    ax1.set_title('Nombre moyen de sources par modèle')
    ax1.set_ylabel('Nombre de sources')
    ax1.tick_params(axis='x', rotation=45)
    
    # Ajouter les valeurs sur les barres
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}', ha='center', va='bottom')
    
    # 2. Temps de réponse par modèle
    ax2 = axes[0, 1]
    df_sources.boxplot(column='response_time_ms', by='model_name', ax=ax2)
    ax2.set_title('Distribution des temps de réponse par modèle')
    ax2.set_xlabel('Modèle')
    ax2.set_ylabel('Temps de réponse (ms)')
    
    # 3. Sources par catégorie
    ax3 = axes[1, 0]
    category_sources = df_sources.groupby('query_category')['total_sources'].mean()
    bars3 = ax3.bar(category_sources.index, category_sources.values)
    ax3.set_title('Sources par catégorie de requête')
    ax3.set_ylabel('Nombre moyen de sources')
    ax3.tick_params(axis='x', rotation=45)
    
    for bar in bars3:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}', ha='center', va='bottom')
    
    # 4. Heatmap corrélation temps/sources
    ax4 = axes[1, 1]
    correlation_data = df_sources.pivot_table(
        values='response_time_ms', 
        index='query_category', 
        columns='model_name', 
        aggfunc='mean'
    )
    sns.heatmap(correlation_data, annot=True, fmt='.0f', ax=ax4, cmap='YlOrRd')
    ax4.set_title('Temps de réponse moyen (ms)')
    
    plt.tight_layout()
    
    # Sauvegarder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plot_file = output_path / f"analysis_plots_{timestamp}.png"
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    print(f"✅ Graphiques sauvegardés: {plot_file}")
    
    plt.show()
    return plot_file


def generate_r_analysis_script(csv_files, output_dir="analysis_exports"):
    """Génère un script R prêt à utiliser pour l'analyse."""
    output_path = Path(output_dir)
    
    r_script = f'''# Script R pour l'analyse des données GEO
# Généré automatiquement le {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

library(tidyverse)
library(readr)
library(ggplot2)
library(dplyr)
library(corrplot)

# Chargement des données
main_data <- read_csv("{csv_files['main'].name}")
sources_data <- read_csv("{csv_files['sources'].name}")
aggregated_data <- read_csv("{csv_files['aggregated'].name}")
temporal_data <- read_csv("{csv_files['temporal'].name}")

# Vérification des données
cat("=== RÉSUMÉ DES DONNÉES ===\\n")
cat("Enregistrements principaux:", nrow(main_data), "\\n")
cat("Sources détaillées:", nrow(sources_data), "\\n")
cat("Données agrégées:", nrow(aggregated_data), "\\n")

# Statistiques descriptives
summary(aggregated_data)

# Analyse par modèle
cat("\\n=== ANALYSE PAR MODÈLE ===\\n")
model_summary <- aggregated_data %>%
  group_by(model_name) %>%
  summarise(
    n_queries = n(),
    avg_sources = mean(total_sources, na.rm = TRUE),
    avg_response_time = mean(response_time_ms, na.rm = TRUE),
    pct_with_sources = mean(has_sources, na.rm = TRUE) * 100
  )
print(model_summary)

# Test de l'hypothèse 2a : Corrélation entre modèles
cat("\\n=== HYPOTHÈSE 2a : CORRÉLATION ENTRE MODÈLES ===\\n")
if(length(unique(aggregated_data$model_name)) >= 2) {{
  correlation_data <- aggregated_data %>%
    select(query_id, model_name, total_sources) %>%
    pivot_wider(names_from = model_name, values_from = total_sources)
  
  if(ncol(correlation_data) >= 3) {{
    cor_matrix <- cor(correlation_data[,-1], use = "complete.obs")
    print(cor_matrix)
    
    # Test de corrélation
    if(ncol(correlation_data) == 3) {{
      cor_test <- cor.test(correlation_data[[2]], correlation_data[[3]])
      cat("Corrélation p-value:", cor_test$p.value, "\\n")
    }}
  }}
}}

# Analyse temporelle (Hypothèse 1)
cat("\\n=== HYPOTHÈSE 1 : STABILITÉ TEMPORELLE ===\\n")
temporal_stability <- aggregated_data %>%
  group_by(query_id, model_name) %>%
  summarise(
    cv_sources = sd(total_sources, na.rm = TRUE) / mean(total_sources, na.rm = TRUE),
    .groups = "drop"
  ) %>%
  filter(!is.na(cv_sources) & is.finite(cv_sources))

print(summary(temporal_stability$cv_sources))

# Graphiques recommandés pour votre recherche
# 1. Distribution des sources par modèle
p1 <- ggplot(aggregated_data, aes(x = model_name, y = total_sources)) +
  geom_boxplot() +
  labs(title = "Distribution du nombre de sources par modèle",
       x = "Modèle", y = "Nombre de sources") +
  theme_minimal()

# 2. Evolution temporelle par itération
p2 <- ggplot(aggregated_data, aes(x = iteration, y = total_sources, color = model_name)) +
  geom_line(stat = "summary", fun = mean) +
  geom_point(stat = "summary", fun = mean) +
  labs(title = "Évolution du référencement par itération",
       x = "Itération", y = "Nombre moyen de sources") +
  theme_minimal()

# 3. Comparaison par catégorie de requête
p3 <- ggplot(aggregated_data, aes(x = query_category, y = total_sources, fill = model_name)) +
  geom_bar(stat = "summary", fun = mean, position = "dodge") +
  labs(title = "Sources par catégorie de requête",
       x = "Catégorie", y = "Nombre moyen de sources") +
  theme_minimal() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1))

# Sauvegarder les graphiques
ggsave("sources_by_model.png", p1, width = 10, height = 6)
ggsave("temporal_evolution.png", p2, width = 10, height = 6)  
ggsave("sources_by_category.png", p3, width = 12, height = 6)

# Export pour analyses statistiques avancées
write_csv(model_summary, "model_summary_stats.csv")
write_csv(temporal_stability, "temporal_stability_analysis.csv")

cat("\\n✅ Analyse terminée. Graphiques et exports sauvegardés.\\n")
'''
    
    r_file = output_path / "analysis_script.R"
    with open(r_file, 'w', encoding='utf-8') as f:
        f.write(r_script)
    
    print(f"✅ Script R généré: {r_file}")
    return r_file


def main():
    print("📊 ANALYSE DES DONNÉES D'EXPÉRIMENTATION GEO")
    print("=" * 60)
    
    # 1. Chargement des données
    df = load_data_from_db()
    if df is None:
        return
    
    # 2. Traitement des sources
    print("\n🔄 Traitement des données de sources...")
    df_sources = process_sources_data(df)
    
    # 3. Statistiques descriptives
    stats = generate_summary_stats(df, df_sources)
    
    # 4. Exports CSV pour RStudio
    print(f"\n📤 Export des données...")
    csv_files = export_to_csv(df, df_sources)
    
    # 5. Visualisations
    print(f"\n📈 Génération des graphiques...")
    try:
        plot_file = create_visualizations(df_sources)
    except Exception as e:
        print(f"⚠️  Erreur lors de la génération des graphiques: {e}")
    
    # 6. Script R
    print(f"\n🔧 Génération du script R...")
    r_file = generate_r_analysis_script(csv_files)
    
    print(f"\n" + "="*60)
    print("🎉 ANALYSE TERMINÉE")
    print("="*60)
    print(f"📁 Tous les fichiers sont dans: analysis_exports/")
    print(f"📊 Pour RStudio, utilisez: {r_file}")
    print(f"📈 Graphiques Python générés")
    
    print(f"\n📋 PROCHAINES ÉTAPES POUR RSTUDIO:")
    print(f"1. Ouvrir RStudio")
    print(f"2. Définir le répertoire: setwd('{Path.cwd()}/analysis_exports')")
    print(f"3. Exécuter: source('analysis_script.R')")


if __name__ == "__main__":
    main()