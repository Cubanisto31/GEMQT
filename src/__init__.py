from typing import Dict, Type
from src.config import ModelConfig
from .clients.base_client import BaseClient
from .clients.openai_client import OpenAIClient
from .clients.claude_client import ClaudeClient
from .clients.search_clients import GoogleSearchClient

CLIENT_REGISTRY: Dict[str, Type[BaseClient]] = {
    "openai": OpenAIClient,
    "claude": ClaudeClient,
    "google_search": GoogleSearchClient,
}

def get_client(config: ModelConfig) -> BaseClient:
    client_class = CLIENT_REGISTRY.get(config.client)
    if not client_class:
        raise ValueError(f"Client non reconnu '{config.client}'.")
    return client_class(config)