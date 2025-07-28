#!/usr/bin/env python3
"""
Script d'export des données d'expérience de SQLite vers CSV pour analyse R
"""

import sqlite3
import pandas as pd
import json
from datetime import datetime
import os

def export_experiment_to_csv(db_path="experiment_results/experiment_data.db", 
                           output_dir="analysis_exports"):
    """
    Exporte les données d'expérience vers plusieurs fichiers CSV
    """
    
    # Créer le dossier de sortie
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        conn = sqlite3.connect(db_path)
        
        # 1. Export principal : toutes les données
        print("📊 Export des données principales...")
        main_query = """
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
        ORDER BY timestamp DESC
        """
        
        df_main = pd.read_sql_query(main_query, conn)
        
        # Ajouter des colonnes calculées pour R
        df_main['response_length'] = df_main['response_raw'].str.len()
        df_main['has_sources'] = df_main['sources_extracted'].apply(
            lambda x: 1 if x and x != '[]' and x != 'null' else 0
        )
        
        # Compter le nombre de sources
        def count_sources(sources_json):
            try:
                if sources_json and sources_json != 'null':
                    sources = json.loads(sources_json)
                    return len(sources) if isinstance(sources, list) else 0
                return 0
            except:
                return 0
        
        df_main['sources_count'] = df_main['sources_extracted'].apply(count_sources)
        
        # Extraire la date et l'heure
        df_main['date'] = pd.to_datetime(df_main['timestamp']).dt.date
        df_main['hour'] = pd.to_datetime(df_main['timestamp']).dt.hour
        
        main_file = f"{output_dir}/experiment_data_{timestamp}.csv"
        df_main.to_csv(main_file, index=False, encoding='utf-8')
        print(f"✅ Données principales exportées: {main_file}")
        
        # 2. Export détaillé des sources
        print("📚 Export des sources détaillées...")
        sources_data = []
        
        for _, row in df_main.iterrows():
            try:
                if row['sources_extracted'] and row['sources_extracted'] != 'null':
                    sources = json.loads(row['sources_extracted'])
                    if isinstance(sources, list):
                        for i, source in enumerate(sources, 1):
                            source_row = {
                                'result_id': row['id'],
                                'session_id': row['session_id'],
                                'query_id': row['query_id'],
                                'model_name': row['model_name'],
                                'source_rank': i,
                                'source_title': source.get('title', ''),
                                'source_url': source.get('url', ''),
                                'source_snippet': source.get('snippet', ''),
                                'source_displayLink': source.get('displayLink', ''),
                                'timestamp': row['timestamp']
                            }
                            sources_data.append(source_row)
            except:
                continue
        
        if sources_data:
            df_sources = pd.DataFrame(sources_data)
            sources_file = f"{output_dir}/sources_detail_{timestamp}.csv"
            df_sources.to_csv(sources_file, index=False, encoding='utf-8')
            print(f"✅ Sources détaillées exportées: {sources_file}")
        else:
            print("⚠️  Aucune source détaillée trouvée")
        
        # 3. Export agrégé par modèle et requête
        print("📈 Export des données agrégées...")
        agg_data = df_main.groupby(['model_name', 'query_id', 'query_category']).agg({
            'response_length': ['mean', 'std', 'min', 'max'],
            'response_time_ms': ['mean', 'std', 'min', 'max'],
            'sources_count': ['mean', 'sum', 'max'],
            'has_sources': ['sum', 'count'],
            'id': 'count'
        }).round(2)
        
        # Aplatir les colonnes multi-niveaux
        agg_data.columns = ['_'.join(col).strip() for col in agg_data.columns.values]
        agg_data = agg_data.reset_index()
        
        # Calculer le pourcentage de réponses avec sources
        agg_data['sources_percentage'] = (agg_data['has_sources_sum'] / agg_data['has_sources_count'] * 100).round(2)
        
        agg_file = f"{output_dir}/aggregated_data_{timestamp}.csv"
        agg_data.to_csv(agg_file, index=False, encoding='utf-8')
        print(f"✅ Données agrégées exportées: {agg_file}")
        
        # 4. Export pour analyse temporelle
        print("⏰ Export pour analyse temporelle...")
        temporal_data = df_main.groupby(['model_name', 'date', 'hour']).agg({
            'response_length': 'mean',
            'response_time_ms': 'mean',
            'sources_count': 'mean',
            'id': 'count'
        }).round(2).reset_index()
        
        temporal_file = f"{output_dir}/temporal_analysis_{timestamp}.csv"
        temporal_data.to_csv(temporal_file, index=False, encoding='utf-8')
        print(f"✅ Analyse temporelle exportée: {temporal_file}")
        
        conn.close()
        
        # 5. Créer un script R de base pour commencer l'analyse
        print("📝 Génération du script R de démarrage...")
        r_script = f"""
# Script R d'analyse des données d'expérience
# Généré automatiquement le {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

library(readr)
library(dplyr)
library(ggplot2)
library(tidyr)

# Chargement des données
main_data <- read_csv("{main_file}")
aggregated_data <- read_csv("{agg_file}")
temporal_data <- read_csv("{temporal_file}")
{f'sources_data <- read_csv("{sources_file}")' if sources_data else '# Pas de données de sources détaillées'}

# Aperçu des données
cat("=== APERCU DES DONNEES ===\\n")
cat("Nombre total d'enregistrements:", nrow(main_data), "\\n")
cat("Modèles testés:", paste(unique(main_data$model_name), collapse=", "), "\\n")
cat("Requêtes testées:", paste(unique(main_data$query_id), collapse=", "), "\\n")
cat("Période:", min(main_data$timestamp), "à", max(main_data$timestamp), "\\n\\n")

print(summary(main_data))

# Graphique 1: Longueur des réponses par modèle
p1 <- ggplot(main_data, aes(x=model_name, y=response_length, fill=model_name)) +
  geom_boxplot() +
  theme_minimal() +
  labs(title="Distribution de la longueur des réponses par modèle",
       x="Modèle", y="Longueur (caractères)") +
  theme(axis.text.x = element_text(angle=45, hjust=1))

print(p1)

# Graphique 2: Temps de réponse par modèle
p2 <- ggplot(main_data, aes(x=model_name, y=response_time_ms, fill=model_name)) +
  geom_boxplot() +
  theme_minimal() +
  labs(title="Distribution du temps de réponse par modèle",
       x="Modèle", y="Temps (ms)") +
  theme(axis.text.x = element_text(angle=45, hjust=1))

print(p2)

# Graphique 3: Pourcentage de réponses avec sources
p3 <- ggplot(aggregated_data, aes(x=model_name, y=sources_percentage, fill=model_name)) +
  geom_col() +
  theme_minimal() +
  labs(title="Pourcentage de réponses avec sources citées",
       x="Modèle", y="% avec sources") +
  theme(axis.text.x = element_text(angle=45, hjust=1))

print(p3)

# Analyse par type de requête
cat("\\n=== ANALYSE PAR TYPE DE REQUETE ===\\n")
query_analysis <- main_data %>%
  group_by(query_category, model_name) %>%
  summarise(
    nb_reponses = n(),
    longueur_moyenne = mean(response_length, na.rm=TRUE),
    temps_moyen = mean(response_time_ms, na.rm=TRUE),
    sources_moyennes = mean(sources_count, na.rm=TRUE),
    .groups = 'drop'
  )

print(query_analysis)

# Sauvegarder les graphiques
ggsave("analysis_plots_{timestamp}.png", 
       gridExtra::grid.arrange(p1, p2, p3, ncol=1), 
       width=12, height=15, dpi=300)

cat("\\n✅ Analyse terminée. Graphiques sauvegardés dans analysis_plots_{timestamp}.png\\n")
"""
        
        r_file = f"{output_dir}/analysis_script.R"
        with open(r_file, 'w', encoding='utf-8') as f:
            f.write(r_script)
        print(f"✅ Script R généré: {r_file}")
        
        print(f"\n🎉 Export terminé!")
        print(f"📁 Fichiers générés dans le dossier: {output_dir}/")
        print(f"   - Données principales: experiment_data_{timestamp}.csv")
        print(f"   - Données agrégées: aggregated_data_{timestamp}.csv")
        print(f"   - Analyse temporelle: temporal_analysis_{timestamp}.csv")
        if sources_data:
            print(f"   - Sources détaillées: sources_detail_{timestamp}.csv")
        print(f"   - Script R: analysis_script.R")
        print(f"\n💡 Pour commencer l'analyse R: Rscript {output_dir}/analysis_script.R")
        
        return {
            'main_file': main_file,
            'agg_file': agg_file,
            'temporal_file': temporal_file,
            'sources_file': sources_file if sources_data else None,
            'r_script': r_file,
            'record_count': len(df_main)
        }
        
    except Exception as e:
        print(f"❌ Erreur lors de l'export: {e}")
        return None

def main():
    """Fonction principale"""
    print("🔄 EXPORT DES DONNÉES D'EXPÉRIENCE VERS CSV")
    print("=" * 60)
    
    result = export_experiment_to_csv()
    
    if result:
        print(f"\n📊 {result['record_count']} enregistrements exportés avec succès!")
        print("\n🔍 Prochaines étapes recommandées:")
        print("1. Ouvrir RStudio ou R")
        print("2. Définir le répertoire de travail sur ce projet")
        print("3. Exécuter le script analysis_script.R")
        print("4. Personnaliser l'analyse selon vos besoins")
    else:
        print("\n❌ Échec de l'export")

if __name__ == "__main__":
    main()