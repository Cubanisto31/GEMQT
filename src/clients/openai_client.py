import time
import re
from typing import Dict, Any, List
from openai import AsyncOpenAI, OpenAIError

from .base_client import BaseClient
from src.config import ModelConfig
from src.utils import async_retry, is_retryable_error, APIConnectionError, RateLimitError

class OpenAIClient(BaseClient):
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        if self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key)

    @async_retry(
        max_retries=3,
        base_delay=1.0,
        retry_exceptions=(RateLimitError, APIConnectionError, OpenAIError)
    )
    async def query(self, text: str, session_id: str) -> Dict[str, Any]:
        if not hasattr(self, 'client'):
            return self._handle_error("Client OpenAI non initialisé.")
        
        try:
            params = self.config.parameters
            response = await self.client.chat.completions.create(
                model=params.model_name,
                messages=[{"role": "user", "content": text}],
                temperature=params.temperature,
                max_tokens=params.max_tokens,
            )
            response_text = response.choices[0].message.content if response.choices else ""
            return {
                'response_raw': response_text,
                'sources_extracted': self._extract_sources(response_text),
                'chain_of_thought': self._extract_chain_of_thought(response_text),
                'metadata': {
                    "usage": response.usage.dict() if response.usage else {},
                    "model": params.model_name,
                    "session_id": session_id
                }
            }
        except RateLimitError as e:
            if is_retryable_error(e):
                raise APIConnectionError(f"Rate limit OpenAI: {str(e)}")
            return self._handle_error(f"Rate limit OpenAI: {str(e)}")
        except OpenAIError as e:
            if is_retryable_error(e):
                raise APIConnectionError(f"Erreur OpenAI: {str(e)}")
            return self._handle_error(f"Erreur OpenAI: {str(e)}")
        except Exception as e:
            if is_retryable_error(e):
                raise APIConnectionError(f"Erreur inattendue OpenAI: {str(e)}")
            return self._handle_error(f"Erreur inattendue: {str(e)}")
    
    def _handle_error(self, error_message: str) -> Dict[str, Any]:
        return {
            'response_raw': f"ERROR: {error_message}",
            'sources_extracted': [], 
            'chain_of_thought': "",
            'metadata': {'error': error_message}
        }

    def _extract_sources(self, response_text: str) -> List[Dict[str, Any]]:
        # GPT-4 sans recherche web ne cite généralement pas de sources
        # Retourner une liste vide par défaut
        return []