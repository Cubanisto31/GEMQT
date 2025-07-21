import asyncio
import random
from functools import wraps
from typing import Callable, Any, Tuple, Type
import logging

logger = logging.getLogger(__name__)

async def retry_with_exponential_backoff(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    retry_exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Any:
    """
    Retry une fonction avec backoff exponentiel et jitter.
    
    Args:
        func: Fonction à retry
        max_retries: Nombre maximum de tentatives
        base_delay: Délai de base en secondes
        max_delay: Délai maximum en secondes
        backoff_factor: Facteur de multiplication du délai
        jitter: Ajouter du bruit aléatoire au délai
        retry_exceptions: Tuple des exceptions pour lesquelles retry
    
    Returns:
        Résultat de la fonction ou lève la dernière exception
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func()
            else:
                return func()
                
        except retry_exceptions as e:
            last_exception = e
            
            if attempt == max_retries:
                logger.error(f"Échec final après {max_retries + 1} tentatives: {e}")
                raise e
                
            delay = min(base_delay * (backoff_factor ** attempt), max_delay)
            if jitter:
                delay *= (0.5 + random.random())  # Ajoute 50-100% de jitter
                
            logger.warning(f"Tentative {attempt + 1}/{max_retries + 1} échouée: {e}. Retry dans {delay:.2f}s")
            await asyncio.sleep(delay)
    
    raise last_exception


def async_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    retry_exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Décorateur pour retry automatique avec backoff exponentiel.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async def _func():
                return await func(*args, **kwargs)
            
            return await retry_with_exponential_backoff(
                _func,
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay,
                backoff_factor=backoff_factor,
                jitter=jitter,
                retry_exceptions=retry_exceptions
            )
        return wrapper
    return decorator


class RateLimitError(Exception):
    """Exception levée lors d'un dépassement de limite de taux."""
    pass


class APIConnectionError(Exception):
    """Exception levée lors de problèmes de connexion API."""
    pass


def is_retryable_error(exception: Exception) -> bool:
    """
    Détermine si une exception justifie un retry.
    
    Returns:
        True si l'exception est retryable, False sinon
    """
    retryable_keywords = [
        'rate limit', 'timeout', 'connection', 'network', 
        'temporary', 'unavailable', '429', '500', '502', '503', '504'
    ]
    
    error_message = str(exception).lower()
    return any(keyword in error_message for keyword in retryable_keywords)