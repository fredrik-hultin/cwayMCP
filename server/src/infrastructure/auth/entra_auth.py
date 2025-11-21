"""Entra ID (Azure AD) OAuth2 authentication with PKCE and Cway token exchange."""

import logging
import secrets
import hashlib
import base64
from typing import Optional, Dict, Any
from urllib.parse import urlencode, parse_qs, urlparse
import httpx

logger = logging.getLogger(__name__)


class EntraIDAuthenticator:
    """Handles Entra ID authentication and Cway token exchange."""
    
    def __init__(
        self,
        cway_api_url: str,
        azure_tenant_id: Optional[str] = None,
        azure_client_id: Optional[str] = None,
        redirect_uri: str = "http://localhost:8765/callback",
    ):
        """
        Initialize Entra ID authenticator.
        
        Args:
            cway_api_url: Base URL for Cway API (e.g., https://app.cway.se)
            azure_tenant_id: Azure AD tenant ID (optional, can use common)
            azure_client_id: Azure AD client ID (optional, for custom app)
            redirect_uri: OAuth2 redirect URI
        """
        self.cway_api_url = cway_api_url.rstrip("/")
        self.azure_tenant_id = azure_tenant_id or "common"
        self.azure_client_id = azure_client_id
        self.redirect_uri = redirect_uri
        
        # OAuth2 endpoints
        self.authorization_endpoint = (
            f"https://login.microsoftonline.com/{self.azure_tenant_id}/oauth2/v2.0/authorize"
        )
        self.token_exchange_endpoint = f"{self.cway_api_url}/oauth/token"
        
        logger.info(f"EntraIDAuthenticator initialized (tenant: {self.azure_tenant_id})")
    
    def generate_pkce_pair(self) -> tuple[str, str]:
        """
        Generate PKCE code verifier and challenge.
        
        Returns:
            Tuple of (code_verifier, code_challenge)
        """
        # Generate code verifier (43-128 characters)
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip("=")
        
        # Generate code challenge (SHA256 hash of verifier)
        challenge_bytes = hashlib.sha256(code_verifier.encode()).digest()
        code_challenge = base64.urlsafe_b64encode(challenge_bytes).decode().rstrip("=")
        
        return code_verifier, code_challenge
    
    def get_authorization_url(
        self,
        username: Optional[str] = None,
        state: Optional[str] = None,
    ) -> tuple[str, str, str]:
        """
        Generate Entra ID authorization URL.
        
        Args:
            username: Pre-fill login hint (optional)
            state: OAuth2 state parameter (generated if not provided)
            
        Returns:
            Tuple of (authorization_url, code_verifier, state)
        """
        # Generate PKCE pair
        code_verifier, code_challenge = self.generate_pkce_pair()
        
        # Generate state if not provided
        if not state:
            state = base64.urlsafe_b64encode(secrets.token_bytes(16)).decode().rstrip("=")
        
        # Build authorization params
        params = {
            "client_id": self.azure_client_id or "default",
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "response_mode": "query",
            "scope": "openid profile email User.Read",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "prompt": "select_account",
        }
        
        if username:
            params["login_hint"] = username
        
        authorization_url = f"{self.authorization_endpoint}?{urlencode(params)}"
        
        logger.info(f"Generated authorization URL for {username or 'user'}")
        return authorization_url, code_verifier, state
    
    async def exchange_code_for_cway_tokens(
        self,
        authorization_code: str,
        code_verifier: str,
        state: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Exchange Entra ID authorization code for Cway tokens.
        
        This calls Cway's /oauth/token endpoint with grant_type=azure,
        which validates the code with Microsoft and returns Cway JWT tokens.
        
        Args:
            authorization_code: OAuth2 authorization code from callback
            code_verifier: PKCE code verifier
            state: OAuth2 state (for validation, optional)
            
        Returns:
            Dict with {access_token, refresh_token, expires_in, username}
            
        Raises:
            EntraAuthError: If token exchange fails
        """
        # Prepare request to Cway's token endpoint
        # Based on cway-server's OauthCreationFilter.kt (grant_type=azure)
        payload = {
            "grant_type": "azure",
            "token": authorization_code,
            "state": state or "",
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.token_exchange_endpoint,
                    data=payload,
                    timeout=30.0,
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    
                    logger.info(f"Successfully exchanged code for Cway tokens")
                    logger.debug(f"Token response keys: {list(token_data.keys())}")
                    
                    # Cway returns: {access_token, refresh_token, expires_in, token_type}
                    return {
                        "access_token": token_data["access_token"],
                        "refresh_token": token_data["refresh_token"],
                        "expires_in": token_data.get("expires_in", 3600),
                        "token_type": token_data.get("token_type", "Bearer"),
                    }
                else:
                    error_body = response.text
                    logger.error(
                        f"Token exchange failed: {response.status_code} - {error_body}"
                    )
                    raise EntraAuthError(
                        f"Token exchange failed: {response.status_code} - {error_body}"
                    )
                    
        except httpx.TimeoutException:
            logger.error("Token exchange timed out")
            raise EntraAuthError("Token exchange timed out")
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during token exchange: {e}")
            raise EntraAuthError(f"HTTP error: {e}")
        except KeyError as e:
            logger.error(f"Missing expected field in token response: {e}")
            raise EntraAuthError(f"Invalid token response: {e}")
    
    async def refresh_cway_token(
        self,
        refresh_token: str,
    ) -> Dict[str, Any]:
        """
        Refresh Cway access token using refresh token.
        
        Calls Cway's /oauth/token with grant_type=refresh_token.
        
        Args:
            refresh_token: Cway refresh token
            
        Returns:
            Dict with {access_token, refresh_token, expires_in}
            
        Raises:
            EntraAuthError: If token refresh fails
        """
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.token_exchange_endpoint,
                    data=payload,
                    timeout=30.0,
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    
                    logger.info("Successfully refreshed Cway token")
                    
                    return {
                        "access_token": token_data["access_token"],
                        "refresh_token": token_data["refresh_token"],
                        "expires_in": token_data.get("expires_in", 3600),
                        "token_type": token_data.get("token_type", "Bearer"),
                    }
                else:
                    error_body = response.text
                    logger.error(f"Token refresh failed: {response.status_code} - {error_body}")
                    raise EntraAuthError(
                        f"Token refresh failed: {response.status_code} - {error_body}"
                    )
                    
        except httpx.TimeoutException:
            logger.error("Token refresh timed out")
            raise EntraAuthError("Token refresh timed out")
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during token refresh: {e}")
            raise EntraAuthError(f"HTTP error: {e}")
        except KeyError as e:
            logger.error(f"Missing expected field in refresh response: {e}")
            raise EntraAuthError(f"Invalid refresh response: {e}")
    
    @staticmethod
    def parse_callback_url(callback_url: str) -> Dict[str, str]:
        """
        Parse OAuth2 callback URL to extract code and state.
        
        Args:
            callback_url: Full callback URL with query params
            
        Returns:
            Dict with {code, state} or {error, error_description}
        """
        parsed = urlparse(callback_url)
        params = parse_qs(parsed.query)
        
        # Extract single values
        result = {}
        for key in ["code", "state", "error", "error_description"]:
            if key in params:
                result[key] = params[key][0]
        
        return result
    
    @staticmethod
    def extract_username_from_state(state: str) -> Optional[str]:
        """
        Extract username from state parameter if encoded.
        
        This is optional - state can just be a random token.
        """
        try:
            # State could be base64-encoded JSON with username
            decoded = base64.urlsafe_b64decode(state + "==").decode()
            import json
            data = json.loads(decoded)
            return data.get("username")
        except Exception:
            return None


class EntraAuthError(Exception):
    """Exception raised for Entra ID authentication errors."""
    pass
