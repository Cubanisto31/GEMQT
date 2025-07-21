import time
import json
import os
from typing import Dict, Any, List
import aiohttp

from .base_client import BaseClient
from src.config import ModelConfig

class GoogleSearchClient(BaseClient):
    BASE_URL = "https://www.googleapis.com/customsearch/v1"

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.search_engine_id = os.environ.get(config.search_engine_id_env_var)

    async def query(self, text: str, session_id: str) -> Dict[str, Any]:
        if not self.api_key or not self.search_engine_id:
            return self._handle_error("Client Google non initialisé.")
        params = {"key": self.api_key, "cx": self.search_engine_id, "q": text, "num": self.config.parameters.num_results or 10}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.BASE_URL, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return {
                        'response_raw': json.dumps(data, indent=2),
                        'sources_extracted': self._extract_sources(data),
                        'chain_of_thought': "",
                        'metadata': data.get("searchInformation", {})
                    }
        except aiohttp.ClientError as e:
            return self._handle_error(str(e))

    def _handle_error(self, error_message: str) -> Dict[str, Any]:
        return {
            'response_raw': f"ERROR: {error_message}",
            'sources_extracted': [], 
            'chain_of_thought': "",
            'metadata': {'error': error_message}
        }
        
    def _extract_sources(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        sources = []
        items = response_data.get("items", [])
        for i, item in enumerate(items):
            sources.append({
                "type": "search_result", "position": i + 1, "title": item.get("title"),
                "url": item.get("link"), "snippet": item.get("snippet")
            })
        return sources