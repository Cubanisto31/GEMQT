# Script R pour l'analyse des données GEO
# Généré automatiquement le 2025-08-22 11:22:56

library(tidyverse)
library(readr)
library(ggplot2)
library(dplyr)
library(corrplot)

# Chargement des données
main_data <- read_csv("experiment_data_20250822_110236.csv")
sources_data <- read_csv("sources_detail_20250822_110236.csv")
aggregated_data <- read_csv("aggregated_data_20250822_110236.csv")
temporal_data <- read_csv("temporal_analysis_20250822_110236.csv")

# Vérification des données
cat("=== RÉSUMÉ DES DONNÉES ===\n")
cat("Enregistrements principaux:", nrow(main_data), "\n")
cat("Sources détaillées:", nrow(sources_data), "\n")
cat("Données agrégées:", nrow(aggregated_data), "\n")

# Statistiques descriptives
summary(aggregated_data)

# Analyse par modèle
cat("\n=== ANALYSE PAR MODÈLE ===\n")
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
cat("\n=== HYPOTHÈSE 2a : CORRÉLATION ENTRE MODÈLES ===\n")
if(length(unique(aggregated_data$model_name)) >= 2) {
  correlation_data <- aggregated_data %>%
    select(query_id, model_name, total_sources) %>%
    pivot_wider(names_from = model_name, values_from = total_sources)
  
  if(ncol(correlation_data) >= 3) {
    cor_matrix <- cor(correlation_data[,-1], use = "complete.obs")
    print(cor_matrix)
    
    # Test de corrélation
    if(ncol(correlation_data) == 3) {
      cor_test <- cor.test(correlation_data[[2]], correlation_data[[3]])
      cat("Corrélation p-value:", cor_test$p.value, "\n")
    }
  }
}

# Analyse temporelle (Hypothèse 1)
cat("\n=== HYPOTHÈSE 1 : STABILITÉ TEMPORELLE ===\n")
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

cat("\n✅ Analyse terminée. Graphiques et exports sauvegardés.\n")
