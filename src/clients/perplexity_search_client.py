"""
Enhanced Perplexity Client with comprehensive source extraction
Optimized for extracting all available citations and search results
"""

import os
import requests
from typing import Dict, List, Optional, Any
from .base_client import BaseClient
from src.config import ModelConfig

class PerplexitySearchClient(BaseClient):
    """Enhanced Perplexity client with comprehensive source extraction"""
    
    def __init__(self, config: ModelConfig):
        """Initialize Perplexity Search client"""
        super().__init__(config)
        
        self.base_url = "https://api.perplexity.ai"
        if self.api_key:
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        else:
            self.headers = None
        
        # Use Sonar Pro for maximum citations
        self.model = config.parameters.model_name or "sonar-pro"
        
    async def query(self, text: str, session_id: str) -> Dict[str, Any]:
        """
        Execute query with comprehensive source extraction
        """
        if not self.api_key or not self.headers:
            return {
                "status": "error",
                "response_raw": "Perplexity API key not configured",
                "sources_extracted": [],
                "metadata": {"session_id": session_id}
            }
        
        try:
            # Prepare request payload
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                "temperature": self.config.parameters.temperature or 0.7,
                "max_tokens": self.config.parameters.max_tokens or 4096,
                "return_citations": True,  # Ensure citations are returned
                "return_images": getattr(self.config.parameters, 'return_images', False),
                "return_related_questions": getattr(self.config.parameters, 'return_related_questions', False),
                "web_search_options": {
                    "search_context_size": "high",  # Get more context
                    "latest_updated": getattr(self.config.parameters, 'latest_updated', None)
                }
            }
            
            # Add academic filter if requested
            if getattr(self.config.parameters, 'academic', False):
                payload["web_search_options"]["search_mode"] = "academic"
            
            # Make API request
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            # Extract response text
            response_text = self._extract_text(data)
            
            # Extract all available sources
            sources = self._extract_sources(data)
            
            # Extract cost information if available
            cost_info = self._extract_cost_info(data)
            
            return {
                "status": "success",
                "response_raw": response_text,
                "sources_extracted": sources,
                "chain_of_thought": self._extract_chain_of_thought(response_text),
                "metadata": {"cost": cost_info, "session_id": session_id}
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "response_raw": f"API request error: {str(e)}",
                "sources_extracted": [],
                "metadata": {"session_id": session_id}
            }
        except Exception as e:
            return {
                "status": "error",
                "response_raw": f"Error with Perplexity Search: {str(e)}",
                "sources_extracted": [],
                "metadata": {"session_id": session_id}
            }
    
    def _extract_text(self, data: Dict) -> str:
        """Extract text content from Perplexity response"""
        try:
            if 'choices' in data and data['choices']:
                choice = data['choices'][0]
                if 'message' in choice:
                    return choice['message'].get('content', '')
                elif 'text' in choice:
                    return choice['text']
            return ""
        except Exception as e:
            return f"Error extracting text: {str(e)}"
    
    def _extract_sources(self, data: Dict) -> List[Dict[str, Any]]:
        """Extract all available sources from Perplexity response"""
        sources = []
        
        try:
            # Primary method: search_results field (new API structure)
            if 'search_results' in data and isinstance(data['search_results'], list):
                for result in data['search_results']:
                    if isinstance(result, dict):
                        source = {
                            "url": result.get('url', ''),
                            "title": result.get('title', ''),
                            "snippet": result.get('snippet', ''),
                            "published_date": result.get('published_date', ''),
                            "source": "search_results",
                            "score": result.get('score', 0.0)
                        }
                        sources.append(source)
            
            # Alternative method: citations field (for compatibility)
            if 'citations' in data and isinstance(data['citations'], list):
                for citation in data['citations']:
                    if isinstance(citation, dict):
                        # Check if not already added
                        url = citation.get('url', '')
                        if not any(s['url'] == url for s in sources):
                            source = {
                                "url": url,
                                "title": citation.get('title', ''),
                                "snippet": citation.get('excerpt', ''),
                                "published_date": citation.get('date', ''),
                                "source": "citations",
                                "score": citation.get('relevance_score', 0.0)
                            }
                            sources.append(source)
            
            # Extract from message metadata if available
            if 'choices' in data and data['choices']:
                choice = data['choices'][0]
                if 'message' in choice and 'metadata' in choice['message']:
                    metadata = choice['message']['metadata']
                    
                    # Extract web results
                    if 'web_results' in metadata and isinstance(metadata['web_results'], list):
                        for result in metadata['web_results']:
                            if isinstance(result, dict):
                                url = result.get('url', '')
                                if not any(s['url'] == url for s in sources):
                                    source = {
                                        "url": url,
                                        "title": result.get('title', ''),
                                        "snippet": result.get('snippet', ''),
                                        "published_date": result.get('date', ''),
                                        "source": "metadata",
                                        "score": result.get('score', 0.0)
                                    }
                                    sources.append(source)
                    
                    # Extract search queries used
                    if 'search_queries' in metadata:
                        # Store for analysis but don't add as sources
                        search_queries = metadata['search_queries']
                        # Could be added to response for debugging
            
            # Sort sources by relevance score if available
            sources.sort(key=lambda x: x.get('score', 0), reverse=True)
            
        except Exception as e:
            print(f"Error extracting sources: {e}")
        
        return sources
    
    def _extract_cost_info(self, data: Dict) -> Dict:
        """Extract cost information from response"""
        cost = {}
        try:
            if 'usage' in data:
                usage = data['usage']
                cost['input_tokens'] = usage.get('prompt_tokens', 0)
                cost['output_tokens'] = usage.get('completion_tokens', 0)
                cost['total_tokens'] = usage.get('total_tokens', 0)
                
                # Extract monetary costs if available
                if 'cost' in usage:
                    cost['input_cost'] = usage['cost'].get('input_tokens_cost', 0)
                    cost['output_cost'] = usage['cost'].get('output_tokens_cost', 0)
                    cost['search_cost'] = usage['cost'].get('search_cost', 0)
                    cost['total_cost'] = usage['cost'].get('total_cost', 0)
        except Exception:
            pass
        return cost
    
    async def query_academic(self, text: str, session_id: str) -> Dict:
        """Query with academic filter for scholarly sources"""
        # Temporarily set academic filter
        original_academic = getattr(self.config.parameters, 'academic', False)
        self.config.parameters.academic = True
        
        result = await self.query(text, session_id)
        
        # Restore original setting
        self.config.parameters.academic = original_academic
        return result
    
    async def query_recent(self, text: str, session_id: str, days: int = 7) -> Dict:
        """Query with recency filter"""
        from datetime import datetime, timedelta
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Temporarily set recency filter
        original_updated = getattr(self.config.parameters, 'latest_updated', None)
        self.config.parameters.latest_updated = cutoff_date
        
        result = await self.query(text, session_id)
        
        # Restore original setting
        self.config.parameters.latest_updated = original_updated
        return result