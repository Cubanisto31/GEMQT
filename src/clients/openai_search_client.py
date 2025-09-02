import time
import re
import os
import requests
from typing import Dict, Any, List
from openai import AsyncOpenAI, OpenAIError

from .base_client import BaseClient
from src.config import ModelConfig
from src.utils import async_retry, is_retryable_error, APIConnectionError, RateLimitError

class OpenAISearchClient(BaseClient):
    """Client OpenAI avec recherche web activée (GPT-4 avec recherche)"""
    
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
            return self._handle_error("Client OpenAI avec recherche non initialisé.")
        
        try:
            params = self.config.parameters
            # Utiliser gpt-4-turbo ou gpt-4o qui supportent la recherche web
            model_name = params.model_name or "gpt-4-turbo"
            
            # Message système pour activer la recherche web
            messages = [
                {
                    "role": "system", 
                    "content": "You are a helpful assistant with access to web search. When answering questions, please search for current information and cite your sources when possible. Include URLs in your response when referencing specific websites or sources."
                },
                {"role": "user", "content": text}
            ]
            
            response = await self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=params.temperature,
                max_tokens=params.max_tokens,
                # Activer les outils de recherche si disponibles
                tools=[{
                    "type": "search"
                }] if self._check_search_capability(model_name) else None,
                tool_choice="auto" if self._check_search_capability(model_name) else None
            )
            
            response_text = response.choices[0].message.content if response.choices else ""
            
            # Extraire les sources depuis la réponse et les tool_calls si présents
            sources = self._extract_sources(response_text)
            
            return {
                'response_raw': response_text,
                'sources_extracted': sources,
                'chain_of_thought': self._extract_chain_of_thought(response_text),
                'metadata': {
                    "usage": response.usage.dict() if response.usage else {},
                    "model": model_name,
                    "session_id": session_id,
                    "search_enabled": True
                }
            }
        except RateLimitError as e:
            if is_retryable_error(e):
                raise APIConnectionError(f"Rate limit OpenAI Search: {str(e)}")
            return self._handle_error(f"Rate limit OpenAI Search: {str(e)}")
        except OpenAIError as e:
            if is_retryable_error(e):
                raise APIConnectionError(f"Erreur OpenAI Search: {str(e)}")
            return self._handle_error(f"Erreur OpenAI Search: {str(e)}")
        except Exception as e:
            if is_retryable_error(e):
                raise APIConnectionError(f"Erreur inattendue OpenAI Search: {str(e)}")
            return self._handle_error(f"Erreur inattendue: {str(e)}")
    
    def _check_search_capability(self, model_name: str) -> bool:
        """Vérifie si le modèle supporte la recherche web native"""
        # Pour l'instant, la recherche web n'est pas directement disponible via l'API
        # On utilise le prompt système pour encourager les citations
        return False
    
    def _handle_error(self, error_message: str) -> Dict[str, Any]:
        return {
            'response_raw': f"ERROR: {error_message}",
            'sources_extracted': [], 
            'chain_of_thought': "",
            'metadata': {'error': error_message}
        }

    def _extract_sources(self, response_text: str) -> List[Dict[str, Any]]:
        """Extrait les sources avec support spécial pour la recherche web"""
        sources = []
        
        # Pattern 1: Liens markdown [texte](url)
        markdown_links = re.findall(r'\[([^\]]+)\]\((https?://[^)]+)\)', response_text)
        for i, (text, url) in enumerate(markdown_links):
            sources.append({
                'type': 'markdown_link', 
                'text': text.strip(), 
                'url': url.strip(), 
                'position': i,
                'extraction_method': 'markdown_pattern_with_search'
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
                    'extraction_method': 'raw_url_pattern_with_search'
                })
        
        # Pattern 3: Citations numérotées [1], [2], etc.
        citation_pattern = re.findall(r'\[(\d+)\]', response_text)
        for i, citation_num in enumerate(citation_pattern):
            sources.append({
                'type': 'numbered_citation', 
                'citation_number': citation_num, 
                'position': i,
                'extraction_method': 'numbered_citation_with_search'
            })
        
        # Pattern 4: Citations avec sources explicites (Source: ...)
        source_mentions = re.findall(r'(?:Source|According to|Based on|From|Via)\s*:?\s*([^.\n]+)', response_text, re.IGNORECASE)
        for i, source_text in enumerate(source_mentions):
            # Vérifier si c'est une URL ou un nom de source
            if 'http' in source_text or 'www.' in source_text or '.com' in source_text or '.org' in source_text:
                sources.append({
                    'type': 'explicit_source', 
                    'source_text': source_text.strip(), 
                    'position': i,
                    'extraction_method': 'explicit_source_mention_with_search'
                })
        
        # Pattern 5: Références web communes
        web_references = re.findall(r'(?:website|site|webpage|web page|article at|found at|available at)\s+([^\s,.\n]+(?:\.[^\s,.\n]+)*)', response_text, re.IGNORECASE)
        for i, ref in enumerate(web_references):
            if ref and not any(ref in str(source) for source in sources):
                sources.append({
                    'type': 'web_reference',
                    'reference': ref.strip(),
                    'position': i,
                    'extraction_method': 'web_reference_pattern'
                })
        
        return sources