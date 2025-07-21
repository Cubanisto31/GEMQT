import os
from abc import ABC, abstractmethod
from typing import Dict, Any, List

from src.config import ModelConfig

class BaseClient(ABC):
    def __init__(self, config: ModelConfig):
        self.config = config
        self.api_key = self._get_api_key(config.api_key_env_var)
        if not self.api_key:
            print(f"⚠️  Avertissement: La variable d'environnement '{config.api_key_env_var}' n'est pas définie pour le client '{config.name}'.")

    def _get_api_key(self, env_var_name: str) -> str | None:
        return os.environ.get(env_var_name)

    @abstractmethod
    async def query(self, text: str, session_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def _extract_sources(self, response: Any) -> List[Dict[str, Any]]:
        pass

    def _extract_chain_of_thought(self, response_text: str) -> str:
        import re
        cot_patterns = [r"<thinking>(.*?)</thinking>", r"<reasoning>(.*?)</reasoning>"]
        for pattern in cot_patterns:
            match = re.search(pattern, response_text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ""