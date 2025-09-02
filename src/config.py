from pydantic import BaseModel, Field, FilePath
from typing import List, Dict, Any, Optional, Union
from pathlib import Path


class QueryConfig(BaseModel):
    id: str
    text: str
    category: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ModelParameters(BaseModel):
    model_name: Optional[str] = None
    model: Optional[str] = None  # Alias pour model_name
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 4000
    num_results: Optional[int] = 10
    
    # Paramètres pour les clients de recherche
    enable_search: Optional[bool] = True
    return_images: Optional[bool] = False
    return_related_questions: Optional[bool] = False
    academic: Optional[bool] = False
    latest_updated: Optional[str] = None
    search_recency_filter: Optional[str] = None

class ModelConfig(BaseModel):
    name: str = Field(..., description="Nom unique pour le modèle (ex: 'GPT-4o')")
    type: str = Field(..., description="'llm' ou 'search_engine'")
    client: str = Field(..., description="Identifiant du client à utiliser (ex: 'openai', 'google_search')")
    enabled: bool = True
    api_key_env_var: str = Field(..., description="Variable d'environnement pour la clé API")
    search_engine_id_env_var: Optional[str] = None
    parameters: ModelParameters = Field(default_factory=ModelParameters)

class ExperimentConfig(BaseModel):
    experiment_name: str
    duration_days: int = 14
    iterations_per_query: int = 30
    delay_between_iterations_seconds: int = 5
    randomize_query_order: bool = True
    use_different_sessions: bool = True
    database_url: str = "sqlite:///experiment_results/experiment_data.db"
    
    models: List[ModelConfig]
    queries: List[QueryConfig]

    @classmethod
    def from_yaml(cls, path: str, queries_file: Optional[Union[str, Path]] = None) -> 'ExperimentConfig':
        import yaml
        from .query_loader import QueryLoader
        
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Si un fichier de requêtes externe est spécifié, l'utiliser
        if queries_file:
            data['queries'] = [query.dict() for query in QueryLoader.load_queries(path, queries_file)]
        
        return cls(**data)