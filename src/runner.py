import asyncio
import os
import uuid
import time
import logging
from typing import List, Dict, Any

from src.config import ExperimentConfig, ModelConfig, QueryConfig
from src.database import get_db_session, ExperimentResult
from . import get_client

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('experiment.log')
    ]
)
logger = logging.getLogger(__name__)

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
                    logger.info(f"✅ Client {model_config.name} initialisé avec succès")
                except Exception as e:
                    logger.error(f"❌ Erreur lors de l'initialisation du client {model_config.name}: {e}")
        logger.info(f"📊 {len(clients)}/{len([m for m in self.config.models if m.enabled])} clients initialisés")
        return clients

    async def run(self):
        logger.info(f"🚀 Démarrage de l'expérimentation '{self.config.experiment_name}' avec la session {self.session_id}")
        total_queries = len(self.config.queries)
        total_models = len([m for m in self.config.models if m.enabled and m.name in self.clients])
        total_operations = self.config.iterations_per_query * total_queries * total_models
        completed_operations = 0
        
        for iteration in range(self.config.iterations_per_query):
            logger.info(f"🔄 Itération {iteration + 1}/{self.config.iterations_per_query}")
            queries_to_run = self.config.queries.copy()
            if self.config.randomize_query_order:
                import random
                random.shuffle(queries_to_run)

            for query in queries_to_run:
                for model_config in self.config.models:
                    if model_config.enabled and model_config.name in self.clients:
                        client = self.clients[model_config.name]
                        logger.info(f"🔍 [{completed_operations+1}/{total_operations}] Requête '{query.text[:50]}...' → {model_config.name}")
                        
                        try:
                            start_time = time.time()
                            response_data = await client.query(query.text, self.session_id)
                            end_time = time.time()
                            response_time_ms = int((end_time - start_time) * 1000)

                            # Validation de la réponse
                            if not response_data:
                                logger.warning(f"⚠️  Réponse vide pour {model_config.name} et {query.id}")
                                continue

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
                                sources_extracted=response_data.get("sources_extracted", []),
                                chain_of_thought=response_data.get("chain_of_thought"),
                                response_time_ms=response_time_ms,
                                extra_metadata={
                                    **query.metadata,
                                    "api_metadata": response_data.get("metadata", {})
                                }
                            )
                            
                            with get_db_session() as session:
                                session.add(result)
                                session.commit()
                            
                            sources_count = len(response_data.get("sources_extracted", []))
                            logger.info(f"✅ Sauvegardé: {model_config.name}/{query.id} ({response_time_ms}ms, {sources_count} sources)")

                        except Exception as e:
                            logger.error(f"❌ Erreur {query.id} avec {model_config.name}: {str(e)[:100]}...")
                        
                        completed_operations += 1
                
                if self.config.delay_between_iterations_seconds > 0:
                    await asyncio.sleep(self.config.delay_between_iterations_seconds)

        logger.info(f"🎉 Expérimentation '{self.config.experiment_name}' terminée. {completed_operations}/{total_operations} opérations réalisées.")

