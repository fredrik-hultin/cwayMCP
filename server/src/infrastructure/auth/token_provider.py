"""Token provider implementations for authentication."""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import httpx
from msal import ConfidentialClientApplication, PublicClientApplication

from .token_cache import TokenCache


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
    """Token provider for static bearer tokens from environment."""
    
    def __init__(self, token: str):
        """
        Initialize with static token.
        
        Args:
            token: Bearer token string
        """
        self._token = token
        logger.info("Initialized StaticTokenProvider")
    
    async def get_token(self) -> str:
        """Get the static token."""
        return self._token
    
    async def refresh_token(self) -> str:
        """Static tokens cannot be refreshed."""
        return self._token


class OAuth2TokenProvider(TokenProvider):
    """Token provider using OAuth2 flow with Microsoft Identity Platform."""
    
    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: Optional[str] = None,
        scope: str = "https://graph.microsoft.com/.default",
        cache: Optional[TokenCache] = None,
        use_device_code_flow: bool = False,
    ):
        """
        Initialize OAuth2 token provider.
        
        Args:
            tenant_id: Azure AD tenant ID
            client_id: Application (client) ID
            client_secret: Client secret (for confidential client flow)
            scope: OAuth2 scope
            cache: Token cache implementation
            use_device_code_flow: Use device code flow for public clients
        """
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self.cache = cache or TokenCache()
        self.use_device_code_flow = use_device_code_flow
        
        # Initialize MSAL application
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        
        if client_secret:
            # Confidential client (server-to-server)
            self.app = ConfidentialClientApplication(
                client_id=client_id,
                client_credential=client_secret,
                authority=authority,
                token_cache=self.cache.msal_cache,
            )
            logger.info("Initialized OAuth2TokenProvider (Confidential Client)")
        else:
            # Public client (device code flow)
            self.app = PublicClientApplication(
                client_id=client_id,
                authority=authority,
                token_cache=self.cache.msal_cache,
            )
            logger.info("Initialized OAuth2TokenProvider (Public Client)")
        
        self._current_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
    
    async def get_token(self) -> str:
        """
        Get a valid access token, using cache if available.
        
        Returns:
            Valid bearer token string
        """
        # Check if cached token is still valid
        if self._current_token and self._token_expiry:
            if datetime.now() < self._token_expiry - timedelta(minutes=5):
                logger.debug("Using cached access token")
                return self._current_token
        
        # Try to acquire token from cache
        accounts = self.app.get_accounts()
        if accounts:
            logger.debug(f"Found {len(accounts)} cached accounts")
            result = await asyncio.to_thread(
                self.app.acquire_token_silent,
                scopes=[self.scope],
                account=accounts[0]
            )
            if result and "access_token" in result:
                logger.info("✅ Acquired token from cache")
                self._update_token_from_result(result)
                return self._current_token
        
        # No cached token, acquire new one
        return await self.refresh_token()
    
    async def refresh_token(self) -> str:
        """
        Force acquire a new access token.
        
        Returns:
            New valid bearer token string
        """
        logger.info("Acquiring new access token...")
        
        if self.client_secret:
            # Client credentials flow (server-to-server)
            result = await asyncio.to_thread(
                self.app.acquire_token_for_client,
                scopes=[self.scope]
            )
        elif self.use_device_code_flow:
            # Device code flow (interactive)
            flow = await asyncio.to_thread(
                self.app.initiate_device_flow,
                scopes=[self.scope]
            )
            
            if "user_code" not in flow:
                raise AuthenticationError("Failed to create device flow")
            
            logger.info(f"Device code flow initiated: {flow['message']}")
            print(f"\n{flow['message']}\n")
            
            result = await asyncio.to_thread(
                self.app.acquire_token_by_device_flow,
                flow
            )
        else:
            raise AuthenticationError(
                "No authentication method available. "
                "Provide client_secret or enable use_device_code_flow"
            )
        
        if "access_token" not in result:
            error_msg = result.get("error_description", result.get("error", "Unknown error"))
            raise AuthenticationError(f"Failed to acquire token: {error_msg}")
        
        logger.info("✅ Successfully acquired new access token")
        self._update_token_from_result(result)
        return self._current_token
    
    def _update_token_from_result(self, result: Dict[str, Any]) -> None:
        """Update internal token state from MSAL result."""
        self._current_token = result["access_token"]
        
        # Calculate expiry time
        expires_in = result.get("expires_in", 3600)
        self._token_expiry = datetime.now() + timedelta(seconds=expires_in)
        
        logger.debug(f"Token expires at: {self._token_expiry}")
        self.cache.save()


class AuthenticationError(Exception):
    """Exception raised for authentication failures."""
    pass
