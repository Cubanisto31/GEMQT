from typing import List, Optional, Union
from pathlib import Path
import pandas as pd
import yaml
from .config import QueryConfig


class QueryLoader:
    """Classe pour charger les requêtes depuis différentes sources."""
    
    @staticmethod
    def load_from_excel(file_path: Union[str, Path]) -> List[QueryConfig]:
        """
        Charge les requêtes depuis un fichier Excel.
        
        Le fichier Excel doit contenir les colonnes suivantes:
        - id: Identifiant unique de la requête
        - text: Texte de la requête
        - category: Catégorie de la requête
        - Colonnes optionnelles pour les métadonnées (seront ajoutées au dict metadata)
        
        Args:
            file_path: Chemin vers le fichier Excel
            
        Returns:
            Liste des configurations de requêtes
        """
        df = pd.read_excel(file_path)
        
        required_columns = {'id', 'text', 'category'}
        if not required_columns.issubset(df.columns):
            missing = required_columns - set(df.columns)
            raise ValueError(f"Colonnes manquantes dans le fichier Excel: {missing}")
        
        queries = []
        metadata_columns = [col for col in df.columns if col not in required_columns]
        
        for _, row in df.iterrows():
            metadata = {}
            for col in metadata_columns:
                if pd.notna(row[col]):
                    metadata[col] = row[col]
            
            query = QueryConfig(
                id=str(row['id']),
                text=str(row['text']),
                category=str(row['category']),
                metadata=metadata
            )
            queries.append(query)
        
        return queries
    
    @staticmethod
    def load_from_csv(file_path: Union[str, Path]) -> List[QueryConfig]:
        """
        Charge les requêtes depuis un fichier CSV.
        
        Le fichier CSV doit contenir les colonnes suivantes:
        - id: Identifiant unique de la requête
        - text: Texte de la requête
        - category: Catégorie de la requête
        - Colonnes optionnelles pour les métadonnées
        
        Args:
            file_path: Chemin vers le fichier CSV
            
        Returns:
            Liste des configurations de requêtes
        """
        df = pd.read_csv(file_path)
        
        required_columns = {'id', 'text', 'category'}
        if not required_columns.issubset(df.columns):
            missing = required_columns - set(df.columns)
            raise ValueError(f"Colonnes manquantes dans le fichier CSV: {missing}")
        
        queries = []
        metadata_columns = [col for col in df.columns if col not in required_columns]
        
        for _, row in df.iterrows():
            metadata = {}
            for col in metadata_columns:
                if pd.notna(row[col]):
                    metadata[col] = row[col]
            
            query = QueryConfig(
                id=str(row['id']),
                text=str(row['text']),
                category=str(row['category']),
                metadata=metadata
            )
            queries.append(query)
        
        return queries
    
    @staticmethod
    def load_from_yaml(config_data: dict) -> List[QueryConfig]:
        """
        Charge les requêtes depuis un dictionnaire YAML.
        
        Args:
            config_data: Dictionnaire contenant la configuration
            
        Returns:
            Liste des configurations de requêtes
        """
        queries = []
        for query_data in config_data.get('queries', []):
            query = QueryConfig(**query_data)
            queries.append(query)
        return queries
    
    @staticmethod
    def load_queries(config_path: Union[str, Path], external_file: Optional[Union[str, Path]] = None) -> List[QueryConfig]:
        """
        Charge les requêtes depuis la source appropriée.
        
        Si external_file est spécifié, charge depuis ce fichier (Excel ou CSV).
        Sinon, charge depuis le fichier de configuration YAML.
        
        Args:
            config_path: Chemin vers le fichier de configuration YAML
            external_file: Chemin optionnel vers un fichier externe (Excel ou CSV)
            
        Returns:
            Liste des configurations de requêtes
        """
        if external_file:
            file_path = Path(external_file)
            if not file_path.exists():
                raise FileNotFoundError(f"Fichier de requêtes non trouvé: {external_file}")
            
            if file_path.suffix.lower() in ['.xlsx', '.xls']:
                return QueryLoader.load_from_excel(file_path)
            elif file_path.suffix.lower() == '.csv':
                return QueryLoader.load_from_csv(file_path)
            else:
                raise ValueError(f"Format de fichier non supporté: {file_path.suffix}")
        else:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            return QueryLoader.load_from_yaml(config_data)