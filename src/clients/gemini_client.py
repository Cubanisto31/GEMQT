import time
import re
import json
from typing import Dict, Any, List
import aiohttp

from .base_client import BaseClient
from src.config import ModelConfig
from src.utils import async_retry, is_retryable_error, APIConnectionError, RateLimitError


class GeminiClient(BaseClient):
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def __init__(self, config: ModelConfig):
        super().__init__(config)

    @async_retry(
        max_retries=3,
        base_delay=1.0,
        retry_exceptions=(RateLimitError, APIConnectionError, aiohttp.ClientError)
    )
    async def query(self, text: str, session_id: str) -> Dict[str, Any]:
        if not self.api_key:
            return self._handle_error("Client Gemini non initialisé. Veuillez définir GEMINI_API_KEY.")
        
        try:
            params = self.config.parameters
            model_name = params.model_name or "gemini-pro"
            url = self.BASE_URL.format(model=model_name)
            
            headers = {
                "Content-Type": "application/json"
            }
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": text
                    }]
                }],
                "generationConfig": {
                    "temperature": params.temperature,
                    "maxOutputTokens": params.max_tokens,
                    "topK": 40,
                    "topP": 0.95,
                }
            }
            
            timeout = aiohttp.ClientTimeout(total=60)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{url}?key={self.api_key}",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 429:
                        raise APIConnectionError("Rate limit dépassé pour Gemini API")
                    elif response.status >= 500:
                        raise APIConnectionError(f"Erreur serveur Gemini ({response.status})")
                    
                    response.raise_for_status()
                    data = await response.json()
                    
                    # Extraire le texte de la réponse
                    response_text = ""
                    if "candidates" in data and data["candidates"]:
                        candidate = data["candidates"][0]
                        if "content" in candidate and "parts" in candidate["content"]:
                            parts = candidate["content"]["parts"]
                            response_text = " ".join(part.get("text", "") for part in parts)
                    
                    return {
                        'response_raw': response_text,
                        'sources_extracted': self._extract_sources(response_text),
                        'chain_of_thought': self._extract_chain_of_thought(response_text),
                        'metadata': {
                            "model": model_name,
                            "session_id": session_id,
                            "usage": data.get("usageMetadata", {})
                        }
                    }
        except aiohttp.ClientTimeout as e:
            raise APIConnectionError(f"Timeout Gemini: {str(e)}")
        except aiohttp.ClientError as e:
            if is_retryable_error(e):
                raise APIConnectionError(f"Erreur réseau Gemini: {str(e)}")
            return self._handle_error(f"Erreur Gemini: {str(e)}")
        except Exception as e:
            if is_retryable_error(e):
                raise APIConnectionError(f"Erreur inattendue Gemini: {str(e)}")
            return self._handle_error(f"Erreur inattendue: {str(e)}")

    def _handle_error(self, error_message: str) -> Dict[str, Any]:
        return {
            'response_raw': f"ERROR: {error_message}",
            'sources_extracted': [], 
            'chain_of_thought': "",
            'metadata': {'error': error_message}
        }

    def _extract_sources(self, response_text: str) -> List[Dict[str, Any]]:
        # Gemini sans recherche web ne cite généralement pas de sources
        # Retourner une liste vide par défaut
        return []