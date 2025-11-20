"""OAuth2 flows for different deployment scenarios."""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

import httpx
from msal import ConfidentialClientApplication

from .token_cache import TokenCache


logger = logging.getLogger(__name__)


class OnBehalfOfTokenProvider:
    """
    Token provider using OAuth2 On-Behalf-Of (OBO) flow.
    
    This is used when the MCP server is deployed online and receives
    requests from clients who have already authenticated. The server
    exchanges the client's token for a new token with appropriate scopes.
    """
    
    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        target_scope: str = "https://graph.microsoft.com/.default",
    ):
        """
        Initialize OBO token provider.
        
        Args:
            tenant_id: Azure AD tenant ID
            client_id: Application (client) ID of the MCP server
            client_secret: Client secret for the MCP server
            target_scope: Scope for the target API (Cway API)
        """
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.target_scope = target_scope
        
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        self.app = ConfidentialClientApplication(
            client_id=client_id,
            client_credential=client_secret,
            authority=authority,
        )
        
        # Cache tokens per user
        self._token_cache: Dict[str, Dict[str, Any]] = {}
        
        logger.info("Initialized OnBehalfOfTokenProvider for online deployment")
    
    async def get_token_for_user(self, user_token: str) -> str:
        """
        Get access token on behalf of the user.
        
        Args:
            user_token: The user's access token from the client
            
        Returns:
            Access token for the target API
        """
        # Extract user ID from token for caching (you may want to decode JWT properly)
        user_key = user_token[:50]  # Simple cache key
        
        # Check cache
        if user_key in self._token_cache:
            cached = self._token_cache[user_key]
            if datetime.now() < cached["expiry"]:
                logger.debug("Using cached OBO token")
                return cached["token"]
        
        # Acquire token on behalf of user
        result = await asyncio.to_thread(
            self.app.acquire_token_on_behalf_of,
            user_assertion=user_token,
            scopes=[self.target_scope]
        )
        
        if "access_token" not in result:
            error_msg = result.get("error_description", result.get("error", "Unknown error"))
            raise AuthenticationError(f"OBO token acquisition failed: {error_msg}")
        
        # Cache the token
        expires_in = result.get("expires_in", 3600)
        self._token_cache[user_key] = {
            "token": result["access_token"],
            "expiry": datetime.now() + timedelta(seconds=expires_in - 300)  # 5 min buffer
        }
        
        logger.info("✅ Acquired OBO token for user")
        return result["access_token"]


class ClientCredentialsProvider:
    """
    Token provider using OAuth2 Client Credentials flow.
    
    Best for server-to-server scenarios where the MCP server
    accesses the API with its own identity (not on behalf of users).
    """
    
    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        scope: str = "https://graph.microsoft.com/.default",
        cache: Optional[TokenCache] = None,
    ):
        """
        Initialize client credentials provider.
        
        Args:
            tenant_id: Azure AD tenant ID
            client_id: Application (client) ID
            client_secret: Client secret
            scope: OAuth2 scope
            cache: Token cache
        """
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self.cache = cache or TokenCache()
        
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        self.app = ConfidentialClientApplication(
            client_id=client_id,
            client_credential=client_secret,
            authority=authority,
            token_cache=self.cache.msal_cache,
        )
        
        self._current_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        
        logger.info("Initialized ClientCredentialsProvider")
    
    async def get_token(self) -> str:
        """Get a valid access token."""
        # Check cache
        if self._current_token and self._token_expiry:
            if datetime.now() < self._token_expiry - timedelta(minutes=5):
                logger.debug("Using cached token")
                return self._current_token
        
        # Acquire new token
        result = await asyncio.to_thread(
            self.app.acquire_token_for_client,
            scopes=[self.scope]
        )
        
        if "access_token" not in result:
            error_msg = result.get("error_description", result.get("error", "Unknown error"))
            raise AuthenticationError(f"Token acquisition failed: {error_msg}")
        
        self._current_token = result["access_token"]
        expires_in = result.get("expires_in", 3600)
        self._token_expiry = datetime.now() + timedelta(seconds=expires_in)
        
        logger.info("✅ Acquired client credentials token")
        self.cache.save()
        
        return self._current_token
    
    async def refresh_token(self) -> str:
        """Force refresh the token."""
        self._current_token = None
        return await self.get_token()


class AuthenticationError(Exception):
    """Exception raised for authentication failures."""
    pass
