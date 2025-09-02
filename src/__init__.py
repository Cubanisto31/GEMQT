from typing import Dict, Type
from src.config import ModelConfig
from .clients.base_client import BaseClient
from .clients.openai_client import OpenAIClient
from .clients.openai_search_client import OpenAISearchClient
from .clients.claude_client import ClaudeClient
from .clients.claude_search_client import ClaudeSearchClient
from .clients.search_clients import GoogleSearchClient, BingSearchClient
from .clients.gemini_client import GeminiClient
from .clients.gemini_search_client import GeminiSearchClient
from .clients.perplexity_client import PerplexityClient
from .clients.perplexity_search_client import PerplexitySearchClient

CLIENT_REGISTRY: Dict[str, Type[BaseClient]] = {
    "openai": OpenAIClient,
    "openai_search": OpenAISearchClient,
    "claude": ClaudeClient,
    "claude_search": ClaudeSearchClient,
    "google_search": GoogleSearchClient,
    "bing_search": BingSearchClient,
    "gemini": GeminiClient,
    "gemini_search": GeminiSearchClient,
    "perplexity": PerplexityClient,
    "perplexity_search": PerplexitySearchClient,
}

def get_client(config: ModelConfig) -> BaseClient:
    client_class = CLIENT_REGISTRY.get(config.client)
    if not client_class:
        raise ValueError(f"Client non reconnu '{config.client}'.")
    return client_class(config)