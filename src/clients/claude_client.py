import time
import re
from typing import Dict, Any, List
from anthropic import AsyncAnthropic, AnthropicError

from .base_client import BaseClient
from src.config import ModelConfig

class ClaudeClient(BaseClient):
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        if self.api_key:
            self.client = AsyncAnthropic(api_key=self.api_key)

    async def query(self, text: str, session_id: str) -> Dict[str, Any]:
        if not hasattr(self, 'client'):
            return self._handle_error("Client Anthropic non initialisé.")
        try:
            params = self.config.parameters
            response = await self.client.messages.create(
                model=params.model_name,
                messages=[{"role": "user", "content": text}],
                temperature=params.temperature,
                max_tokens=params.max_tokens,
            )
            response_text = response.content[0].text or ""
            return {
                'response_raw': response_text,
                'sources_extracted': self._extract_sources(response_text),
                'chain_of_thought': self._extract_chain_of_thought(response_text),
                'metadata': {"usage": response.usage.dict() if response.usage else {}}
            }
        except AnthropicError as e:
            return self._handle_error(str(e))

    def _handle_error(self, error_message: str) -> Dict[str, Any]:
        return {
            'response_raw': f"ERROR: {error_message}",
            'sources_extracted': [], 
            'chain_of_thought': "",
            'metadata': {'error': error_message}
        }

    def _extract_sources(self, response_text: str) -> List[Dict[str, Any]]:
        # Add Claude-specific source extraction logic here
        return []