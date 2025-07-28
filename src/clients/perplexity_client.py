import time
import re
import json
from typing import Dict, Any, List
import aiohttp

from .base_client import BaseClient
from src.config import ModelConfig
from src.utils import async_retry, is_retryable_error, APIConnectionError, RateLimitError


class PerplexityClient(BaseClient):
    BASE_URL = "https://api.perplexity.ai/chat/completions"

    def __init__(self, config: ModelConfig):
        super().__init__(config)

    @async_retry(
        max_retries=3,
        base_delay=1.0,
        retry_exceptions=(RateLimitError, APIConnectionError, aiohttp.ClientError)
    )
    async def query(self, text: str, session_id: str) -> Dict[str, Any]:
        if not self.api_key:
            return self._handle_error("Client Perplexity non initialisé. Veuillez définir PERPLEXITY_API_KEY.")
        
        try:
            params = self.config.parameters
            model_name = params.model_name or "pplx-7b-online"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                "temperature": params.temperature,
                "max_tokens": params.max_tokens,
                "search_domain_filter": params.search_domain_filter if hasattr(params, 'search_domain_filter') else None,
                "return_citations": True,
                "search_recency_filter": params.search_recency_filter if hasattr(params, 'search_recency_filter') else None
            }
            
            # Supprimer les clés None du payload
            payload = {k: v for k, v in payload.items() if v is not None}
            
            timeout = aiohttp.ClientTimeout(total=60)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    self.BASE_URL,
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 429:
                        raise APIConnectionError("Rate limit dépassé pour Perplexity API")
                    elif response.status >= 500:
                        raise APIConnectionError(f"Erreur serveur Perplexity ({response.status})")
                    
                    response.raise_for_status()
                    data = await response.json()
                    
                    # Extraire le texte de la réponse
                    response_text = ""
                    citations = []
                    if "choices" in data and data["choices"]:
                        choice = data["choices"][0]
                        if "message" in choice:
                            response_text = choice["message"].get("content", "")
                        
                        # Perplexity retourne les citations dans un format spécial
                        if "citations" in choice.get("message", {}):
                            citations = choice["message"]["citations"]
                    
                    return {
                        'response_raw': response_text,
                        'sources_extracted': self._extract_sources_with_citations(response_text, citations),
                        'chain_of_thought': self._extract_chain_of_thought(response_text),
                        'metadata': {
                            "model": model_name,
                            "session_id": session_id,
                            "usage": data.get("usage", {}),
                            "citations": citations
                        }
                    }
        except aiohttp.ClientTimeout as e:
            raise APIConnectionError(f"Timeout Perplexity: {str(e)}")
        except aiohttp.ClientError as e:
            if is_retryable_error(e):
                raise APIConnectionError(f"Erreur réseau Perplexity: {str(e)}")
            return self._handle_error(f"Erreur Perplexity: {str(e)}")
        except Exception as e:
            if is_retryable_error(e):
                raise APIConnectionError(f"Erreur inattendue Perplexity: {str(e)}")
            return self._handle_error(f"Erreur inattendue: {str(e)}")

    def _handle_error(self, error_message: str) -> Dict[str, Any]:
        return {
            'response_raw': f"ERROR: {error_message}",
            'sources_extracted': [], 
            'chain_of_thought': "",
            'metadata': {'error': error_message}
        }

    def _extract_sources_with_citations(self, response_text: str, citations: List[Dict]) -> List[Dict[str, Any]]:
        sources = []
        
        # D'abord, ajouter les citations officielles de Perplexity
        for i, citation in enumerate(citations):
            sources.append({
                'type': 'perplexity_citation',
                'url': citation.get('url', ''),
                'title': citation.get('title', ''),
                'snippet': citation.get('snippet', ''),
                'position': i,
                'extraction_method': 'perplexity_api_citations'
            })
        
        # Ensuite, extraire les sources du texte comme d'habitude
        
        # Pattern 1: Liens markdown [texte](url)
        markdown_links = re.findall(r'\[([^\]]+)\]\((https?://[^)]+)\)', response_text)
        for i, (text, url) in enumerate(markdown_links):
            if not any(source.get('url') == url for source in sources):
                sources.append({
                    'type': 'markdown_link', 
                    'text': text.strip(), 
                    'url': url.strip(), 
                    'position': len(sources),
                    'extraction_method': 'markdown_pattern'
                })
        
        # Pattern 2: URLs brutes
        raw_urls = re.findall(r'(?<!\()\b(https?://[^\s)]+)', response_text)
        for i, url in enumerate(raw_urls):
            if not any(source.get('url') == url for source in sources):
                sources.append({
                    'type': 'raw_url', 
                    'url': url.strip(), 
                    'position': len(sources),
                    'extraction_method': 'raw_url_pattern'
                })
        
        # Pattern 3: Citations numérotées [1], [2], etc.
        citation_pattern = re.findall(r'\[(\d+)\]', response_text)
        for i, citation_num in enumerate(citation_pattern):
            # Essayer de mapper aux citations officielles
            citation_idx = int(citation_num) - 1
            if 0 <= citation_idx < len(citations):
                sources.append({
                    'type': 'numbered_citation_mapped',
                    'citation_number': citation_num,
                    'url': citations[citation_idx].get('url', ''),
                    'title': citations[citation_idx].get('title', ''),
                    'position': len(sources),
                    'extraction_method': 'numbered_citation_with_mapping'
                })
            else:
                sources.append({
                    'type': 'numbered_citation', 
                    'citation_number': citation_num, 
                    'position': len(sources),
                    'extraction_method': 'numbered_citation'
                })
        
        return sources
    
    def _extract_sources(self, response_text: str) -> List[Dict[str, Any]]:
        """Implémentation de la méthode abstraite _extract_sources"""
        return self._extract_sources_with_citations(response_text, [])