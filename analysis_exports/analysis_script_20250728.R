
# Script R d'analyse des données d'expérience
# Généré manuellement le 2025-07-28 16:02

library(readr)
library(dplyr)
library(ggplot2)
library(tidyr)

# Chargement des données
main_data <- read_csv("experiment_data_20250728_134606.csv")
aggregated_data <- read_csv("aggregated_data_20250728_134606.csv")
temporal_data <- read_csv("temporal_analysis_20250728_134606.csv")
sources_data <- read_csv("sources_detail_20250728_134606.csv")

# Aperçu des données
cat("=== APERCU DES DONNEES ===\n")
cat("Nombre total d'enregistrements:", nrow(main_data), "\n")
cat("Modèles testés:", paste(unique(main_data$model_name), collapse=", "), "\n")
cat("Requêtes testées:", paste(unique(main_data$query_id), collapse=", "), "\n")
cat("Période:", min(main_data$timestamp), "à", max(main_data$timestamp), "\n\n")

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
cat("\n=== ANALYSE PAR TYPE DE REQUETE ===\n")
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
ggsave("analysis_plots_20250728_134606.png", 
       gridExtra::grid.arrange(p1, p2, p3, ncol=1), 
       width=12, height=15, dpi=300)

cat("\n✅ Analyse terminée. Graphiques sauvegardés dans analysis_plots_20250728_134606.png\n")
