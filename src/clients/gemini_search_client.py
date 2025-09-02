"""
Gemini Search Client with Google Search Grounding
Extends Gemini to extract web sources when grounding is enabled
"""

import os
import json
from typing import Dict, List, Optional, Any
from .base_client import BaseClient
from src.config import ModelConfig

try:
    import google.generativeai as genai
    GOOGLE_AVAILABLE = True
except ImportError:
    genai = None
    GOOGLE_AVAILABLE = False

class GeminiSearchClient(BaseClient):
    """Gemini client with Google Search grounding for web citations"""
    
    def __init__(self, config: ModelConfig):
        """Initialize Gemini Search client with grounding capabilities"""
        super().__init__(config)
        if not GOOGLE_AVAILABLE:
            print(f"⚠️  Google AI SDK not available for {config.name}. Install with: pip install google-generativeai")
        elif self.api_key:
            genai.configure(api_key=self.api_key)
        self.model_name = config.parameters.model or config.parameters.model_name or "gemini-1.5-flash"
        
    def create_grounded_model(self):
        """Create a model with Google Search grounding enabled"""
        # Configure the model with grounding
        tools = {
            "google_search_retrieval": {
                "dynamic_retrieval_config": {
                    "mode": "MODE_DYNAMIC",  # or "MODE_UNSPECIFIED" for always-on
                    "dynamic_threshold": 0.3  # Adjust confidence threshold
                }
            }
        }
        
        # Create model with tools configuration
        model = genai.GenerativeModel(
            model_name=self.model_name,
            tools=tools
        )
        return model
    
    async def query(self, text: str, session_id: str) -> Dict[str, Any]:
        """Execute query with Google Search grounding"""
        if not GOOGLE_AVAILABLE:
            return {
                "status": "error",
                "response_raw": "Google AI SDK not available. Install with: pip install google-generativeai",
                "sources_extracted": [],
                "metadata": {"session_id": session_id}
            }
            
        try:
            # Create grounded model
            model = self.create_grounded_model()
            
            # Generate response with grounding
            response = model.generate_content(text)
            
            # Extract response text
            response_text = response.text if hasattr(response, 'text') else str(response)
            
            # Extract grounding metadata
            sources = self._extract_sources(response)
            
            return {
                "status": "success",
                "response_raw": response_text,
                "sources_extracted": sources,
                "chain_of_thought": self._extract_chain_of_thought(response_text),
                "model": self.model_name,
                "grounding_enabled": True,
                "metadata": {"grounding_enabled": True, "session_id": session_id}
            }
            
        except Exception as e:
            return {
                "status": "error",
                "response_raw": f"Error with Gemini Search grounding: {str(e)}",
                "sources_extracted": [],
                "model": self.model_name,
                "grounding_enabled": True
            }
    
    def _extract_sources(self, response: Any) -> List[Dict[str, Any]]:
        """Extract grounding sources from Gemini response"""
        sources = []
        
        try:
            # Check if response has grounding metadata
            if hasattr(response, 'grounding_metadata'):
                metadata = response.grounding_metadata
                
                # Extract grounding chunks (web sources)
                if hasattr(metadata, 'grounding_chunks'):
                    for chunk in metadata.grounding_chunks:
                        source = {
                            "url": chunk.web.uri if hasattr(chunk, 'web') else "",
                            "title": chunk.web.title if hasattr(chunk, 'web') else "",
                            "confidence": getattr(chunk, 'confidence_score', 0.0)
                        }
                        if source["url"]:
                            sources.append(source)
                
                # Alternative: check for search_entry_point
                if hasattr(metadata, 'search_entry_point'):
                    entry_point = metadata.search_entry_point
                    if hasattr(entry_point, 'rendered_content'):
                        # Parse rendered content for additional sources
                        pass
            
            # Alternative structure for some API versions
            elif hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'grounding_attributions'):
                        for attribution in candidate.grounding_attributions:
                            if hasattr(attribution, 'source_id'):
                                source = {
                                    "url": getattr(attribution.source_id, 'url', ''),
                                    "title": getattr(attribution.source_id, 'title', ''),
                                    "confidence": getattr(attribution, 'confidence_score', 0.0)
                                }
                                if source["url"]:
                                    sources.append(source)
                    
                    # Check for web_search_queries in metadata
                    if hasattr(candidate, 'grounding_metadata'):
                        metadata = candidate.grounding_metadata
                        if hasattr(metadata, 'web_search_queries'):
                            # Store search queries for reference
                            search_queries = [q for q in metadata.web_search_queries]
                            # These could be added to the response for analysis
        
        except Exception as e:
            print(f"Error extracting grounding sources: {e}")
            
            # Debug: print response structure
            if hasattr(response, '__dict__'):
                print("Response attributes:", response.__dict__.keys())
        
        return sources
    
    async def query_with_enhanced_grounding(self, text: str, session_id: str) -> Dict:
        """
        Enhanced query with explicit grounding request
        Forces the model to search and cite sources
        """
        # Enhance prompt to encourage grounding
        enhanced_prompt = f"""
        {text}
        
        Please search the web for current information and provide citations for your sources.
        Include relevant URLs and references in your response.
        """
        
        return await self.query(enhanced_prompt, session_id)