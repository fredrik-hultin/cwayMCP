"""Token provider implementations for authentication."""

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class TokenProvider(ABC):
    """Abstract base class for token providers."""
    
    @abstractmethod
    async def get_token(self) -> str:
        """
        Get a valid access token.
        
        Returns:
            Valid bearer token string
            
        Raises:
            AuthenticationError: If token cannot be obtained
        """
        pass
    
    @abstractmethod
    async def refresh_token(self) -> str:
        """
        Force refresh the access token.
        
        Returns:
            New valid bearer token string
        """
        pass


class StaticTokenProvider(TokenProvider):
    """Token provider for static bearer tokens."""
    
    def __init__(self, token: str):
        """
        Initialize with static token.
        
        Args:
            token: Bearer token string
        """
        self._token = token
        logger.debug("Initialized StaticTokenProvider")
    
    async def get_token(self) -> str:
        """Get the static token."""
        return self._token
    
    async def refresh_token(self) -> str:
        """Static tokens cannot be refreshed, return same token."""
        return self._token
