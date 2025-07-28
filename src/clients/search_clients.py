import time
import json
import os
from typing import Dict, Any, List
import aiohttp

from .base_client import BaseClient
from src.config import ModelConfig
from src.utils import async_retry, is_retryable_error, APIConnectionError

class GoogleSearchClient(BaseClient):
    BASE_URL = "https://www.googleapis.com/customsearch/v1"

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.search_engine_id = os.environ.get(config.search_engine_id_env_var)

    @async_retry(
        max_retries=3,
        base_delay=2.0,
        retry_exceptions=(APIConnectionError, aiohttp.ClientError)
    )
    async def query(self, text: str, session_id: str) -> Dict[str, Any]:
        if not self.api_key or not self.search_engine_id:
            return self._handle_error("Client Google non initialisé.")
        
        params = {
            "key": self.api_key, 
            "cx": self.search_engine_id, 
            "q": text, 
            "num": self.config.parameters.num_results or 10
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.BASE_URL, params=params) as response:
                    if response.status == 429:
                        raise APIConnectionError("Rate limit dépassé pour Google Search API")
                    elif response.status >= 500:
                        raise APIConnectionError(f"Erreur serveur Google ({response.status})")
                    
                    response.raise_for_status()
                    data = await response.json()
                    
                    return {
                        'response_raw': json.dumps(data, indent=2),
                        'sources_extracted': self._extract_sources(data),
                        'chain_of_thought': "",
                        'metadata': {
                            **data.get("searchInformation", {}),
                            "session_id": session_id,
                            "query": text
                        }
                    }
        except aiohttp.ClientTimeout as e:
            raise APIConnectionError(f"Timeout Google Search: {str(e)}")
        except aiohttp.ClientError as e:
            if is_retryable_error(e):
                raise APIConnectionError(f"Erreur réseau Google Search: {str(e)}")
            return self._handle_error(f"Erreur Google Search: {str(e)}")
        except Exception as e:
            if is_retryable_error(e):
                raise APIConnectionError(f"Erreur inattendue Google Search: {str(e)}")
            return self._handle_error(f"Erreur inattendue: {str(e)}")

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


class BingSearchClient(BaseClient):
    BASE_URL = "https://api.bing.microsoft.com/v7.0/search"

    def __init__(self, config: ModelConfig):
        super().__init__(config)

    @async_retry(
        max_retries=3,
        base_delay=2.0,
        retry_exceptions=(APIConnectionError, aiohttp.ClientError)
    )
    async def query(self, text: str, session_id: str) -> Dict[str, Any]:
        if not self.api_key:
            return self._handle_error("Client Bing non initialisé. Veuillez définir BING_API_KEY.")
        
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Accept": "application/json"
        }
        
        params = {
            "q": text,
            "count": self.config.parameters.num_results or 10,
            "mkt": "fr-FR",
            "safeSearch": "Moderate"
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.BASE_URL, headers=headers, params=params) as response:
                    if response.status == 401:
                        return self._handle_error("Clé API Bing invalide. Vérifiez votre clé BING_API_KEY.")
                    elif response.status == 403:
                        return self._handle_error("Accès refusé. Vérifiez les permissions de votre clé API Bing.")
                    elif response.status == 429:
                        raise APIConnectionError("Rate limit dépassé pour Bing Search API")
                    elif response.status >= 500:
                        raise APIConnectionError(f"Erreur serveur Bing ({response.status})")
                    
                    response.raise_for_status()
                    data = await response.json()
                    
                    return {
                        'response_raw': json.dumps(data, indent=2),
                        'sources_extracted': self._extract_sources(data),
                        'chain_of_thought': "",
                        'metadata': {
                            "totalEstimatedMatches": data.get("webPages", {}).get("totalEstimatedMatches", 0),
                            "session_id": session_id,
                            "query": text
                        }
                    }
        except aiohttp.ClientTimeout as e:
            raise APIConnectionError(f"Timeout Bing Search: {str(e)}")
        except aiohttp.ClientError as e:
            if is_retryable_error(e):
                raise APIConnectionError(f"Erreur réseau Bing Search: {str(e)}")
            return self._handle_error(f"Erreur Bing Search: {str(e)}")
        except Exception as e:
            if is_retryable_error(e):
                raise APIConnectionError(f"Erreur inattendue Bing Search: {str(e)}")
            return self._handle_error(f"Erreur inattendue: {str(e)}")

    def _handle_error(self, error_message: str) -> Dict[str, Any]:
        return {
            'response_raw': f"ERROR: {error_message}",
            'sources_extracted': [], 
            'chain_of_thought': "",
            'metadata': {'error': error_message}
        }
        
    def _extract_sources(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        sources = []
        web_pages = response_data.get("webPages", {})
        results = web_pages.get("value", [])
        
        for i, result in enumerate(results):
            sources.append({
                "type": "search_result",
                "position": i + 1,
                "title": result.get("name"),
                "url": result.get("url"),
                "snippet": result.get("snippet"),
                "displayUrl": result.get("displayUrl")
            })
        return sources