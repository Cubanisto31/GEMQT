import time
import re
from typing import Dict, Any, List
from openai import AsyncOpenAI, OpenAIError

from .base_client import BaseClient
from src.config import ModelConfig

class OpenAIClient(BaseClient):
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        if self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key)

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
            response_text = response.choices[0].message.content or ""
            return {
                'response_raw': response_text,
                'sources_extracted': self._extract_sources(response_text),
                'chain_of_thought': self._extract_chain_of_thought(response_text),
                'metadata': {"usage": response.usage.dict() if response.usage else {}}
            }
        except OpenAIError as e:
            return self._handle_error(str(e))
    
    def _handle_error(self, error_message: str) -> Dict[str, Any]:
        return {
            'response_raw': f"ERROR: {error_message}",
            'sources_extracted': [], 
            'chain_of_thought': "",
            'metadata': {'error': error_message}
        }

    def _extract_sources(self, response_text: str) -> List[Dict[str, Any]]:
        sources = []
        markdown_links = re.findall(r'[([^]]+)]((https?://[^)]+))', response_text)
        for i, (text, url) in enumerate(markdown_links):
            sources.append({'type': 'markdown_link', 'text': text, 'url': url, 'position': i})
        raw_urls = re.findall(r'(?<!()https?://[^s)]+', response_text)
        for i, url in enumerate(raw_urls):
            sources.append({'type': 'raw_url', 'url': url, 'position': i})
        return sources