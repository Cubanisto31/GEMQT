"""
Claude Search Client with Web Search capabilities
Extends Claude to extract web sources when web search is enabled
"""

import os
from typing import Dict, List, Optional, Any
from .base_client import BaseClient
from src.config import ModelConfig

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    Anthropic = None
    ANTHROPIC_AVAILABLE = False

class ClaudeSearchClient(BaseClient):
    """Claude client with web search and citations support"""
    
    def __init__(self, config: ModelConfig):
        """Initialize Claude Search client"""
        super().__init__(config)
        if not ANTHROPIC_AVAILABLE:
            print(f"⚠️  Anthropic SDK not available for {config.name}. Install with: pip install anthropic")
            self.client = None
        elif self.api_key:
            self.client = Anthropic(api_key=self.api_key)
        else:
            self.client = None
        self.model = config.parameters.model or config.parameters.model_name or "claude-3-5-sonnet-20241022"
        
    async def query(self, text: str, session_id: str) -> Dict[str, Any]:
        """
        Execute query with web search enabled
        """
        if not ANTHROPIC_AVAILABLE:
            return {
                "status": "error",
                "response_raw": "Anthropic SDK not available. Install with: pip install anthropic",
                "sources_extracted": [],
                "metadata": {"session_id": session_id}
            }
        
        if not self.client:
            return {
                "status": "error",
                "response_raw": "Claude API key not configured",
                "sources_extracted": [],
                "metadata": {"session_id": session_id}
            }
        
        try:
            enable_search = self.config.parameters.enable_search
            
            # Prepare messages
            messages = [
                {
                    "role": "user",
                    "content": text
                }
            ]
            
            # Configure tools if search is enabled
            tools = []
            if enable_search:
                tools.append({
                    "type": "web_search",
                    "web_search": {}
                })
            
            # Make API call with or without tools
            if tools:
                response = self.client.messages.create(
                    model=self.model,
                    messages=messages,
                    tools=tools,
                    max_tokens=4096,
                    temperature=self.config.parameters.temperature or 0.7
                )
            else:
                response = self.client.messages.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=4096,
                    temperature=self.config.parameters.temperature or 0.7
                )
            
            # Extract response content
            response_text = self._extract_text(response)
            
            # Extract sources if web search was used
            sources = self._extract_sources(response) if enable_search else []
            
            return {
                "status": "success",
                "response_raw": response_text,
                "sources_extracted": sources,
                "chain_of_thought": self._extract_chain_of_thought(response_text),
                "metadata": {"web_search_enabled": enable_search, "session_id": session_id}
            }
            
        except Exception as e:
            return {
                "status": "error",
                "response_raw": f"Error with Claude Search: {str(e)}",
                "sources_extracted": [],
                "metadata": {"web_search_enabled": enable_search, "session_id": session_id}
            }
    
    def _extract_text(self, response) -> str:
        """Extract text content from Claude response"""
        try:
            if hasattr(response, 'content'):
                # Handle different content structures
                if isinstance(response.content, list):
                    texts = []
                    for item in response.content:
                        if hasattr(item, 'text'):
                            texts.append(item.text)
                        elif isinstance(item, dict) and 'text' in item:
                            texts.append(item['text'])
                    return ' '.join(texts)
                elif hasattr(response.content, 'text'):
                    return response.content.text
                else:
                    return str(response.content)
            return str(response)
        except Exception as e:
            return f"Error extracting text: {str(e)}"
    
    def _extract_sources(self, response: Any) -> List[Dict[str, Any]]:
        """Extract web search sources from Claude response"""
        sources = []
        
        try:
            # Check for tool use results (web search)
            if hasattr(response, 'content'):
                for item in response.content:
                    # Check if item is a tool use result
                    if hasattr(item, 'type') and item.type == 'tool_use':
                        if hasattr(item, 'name') and item.name == 'web_search':
                            # Extract search results
                            if hasattr(item, 'input') and 'results' in item.input:
                                for result in item.input['results']:
                                    sources.append({
                                        "url": result.get('url', ''),
                                        "title": result.get('title', ''),
                                        "snippet": result.get('snippet', ''),
                                        "source": "web_search"
                                    })
            
            # Alternative: Check for citations in metadata
            if hasattr(response, 'metadata') and 'citations' in response.metadata:
                for citation in response.metadata['citations']:
                    sources.append({
                        "url": citation.get('url', ''),
                        "title": citation.get('title', ''),
                        "snippet": citation.get('excerpt', ''),
                        "source": "citation"
                    })
            
            # Parse inline citations from text (format: [1], [2], etc.)
            if hasattr(response, 'citations'):
                for citation in response.citations:
                    sources.append({
                        "url": citation.get('url', ''),
                        "title": citation.get('title', ''),
                        "snippet": citation.get('quote', ''),
                        "source": "inline"
                    })
                    
        except Exception as e:
            print(f"Error extracting sources: {e}")
            
            # Debug: print response structure
            if hasattr(response, '__dict__'):
                print("Response attributes:", response.__dict__.keys())
        
        return sources
    
    async def query_with_citations(self, text: str, session_id: str) -> Dict:
        """
        Query with explicit request for citations
        This method enhances the prompt to ensure citations are included
        """
        enhanced_prompt = f"""
        {text}
        
        Please provide your response with citations from web sources.
        Include specific URLs and references to support your statements.
        """
        
        return await self.query(enhanced_prompt, session_id)