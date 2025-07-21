import time
import re
from typing import Dict, Any, List
from anthropic import AsyncAnthropic, AnthropicError

from .base_client import BaseClient
from src.config import ModelConfig
from src.utils import async_retry, is_retryable_error, APIConnectionError, RateLimitError

class ClaudeClient(BaseClient):
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        if self.api_key:
            self.client = AsyncAnthropic(api_key=self.api_key)

    @async_retry(
        max_retries=3,
        base_delay=1.0,
        retry_exceptions=(RateLimitError, APIConnectionError, AnthropicError)
    )
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
            response_text = response.content[0].text if response.content else ""
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
                raise APIConnectionError(f"Rate limit Claude: {str(e)}")
            return self._handle_error(f"Rate limit Claude: {str(e)}")
        except AnthropicError as e:
            if is_retryable_error(e):
                raise APIConnectionError(f"Erreur Anthropic: {str(e)}")
            return self._handle_error(f"Erreur Anthropic: {str(e)}")
        except Exception as e:
            if is_retryable_error(e):
                raise APIConnectionError(f"Erreur inattendue Claude: {str(e)}")
            return self._handle_error(f"Erreur inattendue: {str(e)}")

    def _handle_error(self, error_message: str) -> Dict[str, Any]:
        return {
            'response_raw': f"ERROR: {error_message}",
            'sources_extracted': [], 
            'chain_of_thought': "",
            'metadata': {'error': error_message}
        }

    def _extract_sources(self, response_text: str) -> List[Dict[str, Any]]:
        sources = []
        
        # Pattern 1: Liens markdown [texte](url)
        markdown_links = re.findall(r'\[([^\]]+)\]\((https?://[^)]+)\)', response_text)
        for i, (text, url) in enumerate(markdown_links):
            sources.append({
                'type': 'markdown_link', 
                'text': text.strip(), 
                'url': url.strip(), 
                'position': i,
                'extraction_method': 'markdown_pattern'
            })
        
        # Pattern 2: URLs brutes
        raw_urls = re.findall(r'(?<!\()\b(https?://[^\s)]+)', response_text)
        for i, url in enumerate(raw_urls):
            # Éviter les doublons avec les liens markdown
            if not any(source['url'] == url for source in sources):
                sources.append({
                    'type': 'raw_url', 
                    'url': url.strip(), 
                    'position': i,
                    'extraction_method': 'raw_url_pattern'
                })
        
        # Pattern 3: Citations numérotées [1], [2], etc.
        citation_pattern = re.findall(r'\[(\d+)\]', response_text)
        for i, citation_num in enumerate(citation_pattern):
            sources.append({
                'type': 'numbered_citation', 
                'citation_number': citation_num, 
                'position': i,
                'extraction_method': 'numbered_citation'
            })
        
        # Pattern 4: Citations avec sources explicites (Source: ...)
        source_mentions = re.findall(r'(?:Source|Selon|D\'après)\s*:\s*([^.\n]+)', response_text, re.IGNORECASE)
        for i, source_text in enumerate(source_mentions):
            sources.append({
                'type': 'explicit_source', 
                'source_text': source_text.strip(), 
                'position': i,
                'extraction_method': 'explicit_source_mention'
            })
        
        # Pattern 5: Mentions d'organisations, sites web, études
        entity_pattern = re.findall(r'\b(?:selon|d\'après|rapporte|indique)\s+([A-Z][a-zA-Z\s&-]+(?:\.com|\.org|\.fr|\.net|University|Institute|Organization|Agency|WHO|NASA|Google|Microsoft|OpenAI|Anthropic))\b', response_text, re.IGNORECASE)
        for i, entity in enumerate(entity_pattern):
            sources.append({
                'type': 'entity_mention', 
                'entity_name': entity.strip(), 
                'position': i,
                'extraction_method': 'entity_pattern'
            })
        
        return sources