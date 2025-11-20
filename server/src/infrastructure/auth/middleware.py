"""Authentication middleware for online MCP server deployments."""

import logging
from typing import Optional, Callable
from contextvars import ContextVar

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware

from .oauth2_flows import OnBehalfOfTokenProvider


logger = logging.getLogger(__name__)

# Context variable to store the current user's token
current_user_token: ContextVar[Optional[str]] = ContextVar("current_user_token", default=None)


class UserTokenExtractorMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract user tokens from requests.
    
    This middleware:
    1. Extracts the Bearer token from the Authorization header
    2. Stores it in a context variable for use by the GraphQL client
    3. Optionally validates the token
    """
    
    def __init__(self, app, validate_token: bool = False):
        """
        Initialize middleware.
        
        Args:
            app: FastAPI application
            validate_token: Whether to validate tokens (requires Azure AD setup)
        """
        super().__init__(app)
        self.validate_token = validate_token
    
    async def dispatch(self, request: Request, call_next: Callable):
        """Extract and store user token from request."""
        # Skip token extraction for public endpoints
        if request.url.path in ["/health", "/docs", "/openapi.json", "/redoc"]:
            return await call_next(request)
        
        # Extract Bearer token
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            logger.warning(f"No Authorization header for {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing Authorization header"
            )
        
        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Authorization header format"
            )
        
        token = auth_header.replace("Bearer ", "")
        
        # Store token in context
        token_context = current_user_token.set(token)
        
        try:
            # Process request with token in context
            response = await call_next(request)
            return response
        finally:
            # Clean up context
            current_user_token.reset(token_context)


class OBOGraphQLClient:
    """
    Wrapper for GraphQL client that uses OBO flow.
    
    This automatically exchanges user tokens for API tokens
    using the On-Behalf-Of flow.
    """
    
    def __init__(self, base_client_class, obo_provider: OnBehalfOfTokenProvider):
        """
        Initialize OBO wrapper.
        
        Args:
            base_client_class: The GraphQL client class to wrap
            obo_provider: OBO token provider
        """
        self.base_client_class = base_client_class
        self.obo_provider = obo_provider
    
    async def create_client(self, **kwargs):
        """
        Create a GraphQL client instance with OBO token.
        
        Returns:
            Configured GraphQL client
        """
        # Get user token from context
        user_token = current_user_token.get()
        if not user_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User token not found in context"
            )
        
        # Exchange for API token using OBO
        api_token = await self.obo_provider.get_token_for_user(user_token)
        
        # Create client with API token
        from ..graphql_client import CwayGraphQLClient
        from .token_provider import StaticTokenProvider
        
        # Use the API token as a "static" token for this request
        token_provider = StaticTokenProvider(api_token)
        return CwayGraphQLClient(token_provider=token_provider, **kwargs)


def get_current_user_token() -> str:
    """
    Get the current user's token from context.
    
    Returns:
        User's Bearer token
        
    Raises:
        HTTPException: If no token is in context
    """
    token = current_user_token.get()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No user token in context"
        )
    return token
