import asyncio
import os
import uuid
import time
from typing import List, Dict, Any

from src.config import ExperimentConfig, ModelConfig, QueryConfig
from src.database import get_db_session, ExperimentResult
from . import get_client

class ExperimentRunner:
    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.session_id = str(uuid.uuid4())
        self.clients = self._initialize_clients()

    def _initialize_clients(self) -> Dict[str, Any]:
        clients = {}
        for model_config in self.config.models:
            if model_config.enabled:
                try:
                    client = get_client(model_config)
                    clients[model_config.name] = client
                except Exception as e:
                    print(f"Erreur lors de l'initialisation du client {model_config.name}: {e}")
        return clients

    async def run(self):
        print(f"Démarrage de l'expérimentation '{self.config.experiment_name}' avec la session {self.session_id}")
        
        for iteration in range(self.config.iterations_per_query):
            print(f"--- Itération {iteration + 1}/{self.config.iterations_per_query} ---")
            queries_to_run = self.config.queries
            if self.config.randomize_query_order:
                import random
                random.shuffle(queries_to_run)

            for query in queries_to_run:
                for model_config in self.config.models:
                    if model_config.enabled and model_config.name in self.clients:
                        client = self.clients[model_config.name]
                        print(f"Exécution de la requête '{query.text}' avec le modèle '{model_config.name}'")
                        
                        try:
                            start_time = time.time()
                            response_data = await client.query(query.text, self.session_id)
                            end_time = time.time()
                            response_time_ms = int((end_time - start_time) * 1000)

                            result = ExperimentResult(
                                id=str(uuid.uuid4()),
                                experiment_id=self.config.experiment_name,
                                session_id=self.session_id,
                                query_id=query.id,
                                query_text=query.text,
                                query_category=query.category,
                                iteration=iteration + 1,
                                model_name=model_config.name,
                                model_type=model_config.type,
                                response_raw=response_data.get("response_raw"),
                                sources_extracted=response_data.get("sources_extracted", {}),
                                chain_of_thought=response_data.get("chain_of_thought"),
                                response_time_ms=response_time_ms,
                                extra_metadata=query.metadata  # Utilisation de extra_metadata
                            )
                            
                            with get_db_session() as session:
                                session.add(result)
                                session.commit()
                            print(f"Résultat enregistré pour {model_config.name} et {query.id}")

                        except Exception as e:
                            print(f"Erreur lors de l'exécution de la requête {query.id} avec {model_config.name}: {e}")
                
                if self.config.delay_between_iterations_seconds > 0:
                    await asyncio.sleep(self.config.delay_between_iterations_seconds)

        print(f"Expérimentation '{self.config.experiment_name}' terminée.")

