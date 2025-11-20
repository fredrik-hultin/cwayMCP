"""GraphQL client for Cway API with authentication and error handling."""

import asyncio
import logging
import time
from typing import Any, Dict, Optional

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.exceptions import TransportError
from graphql import DocumentNode

from config.settings import settings
from ..utils.logging_config import log_api_call, log_performance, log_request_flow
from .auth import TokenProvider, OAuth2TokenProvider, StaticTokenProvider


logger = logging.getLogger(__name__)


class CwayGraphQLClient:
    """GraphQL client for Cway API with bearer token authentication."""
    
    def __init__(
        self,
        api_url: Optional[str] = None,
        api_token: Optional[str] = None,
        token_provider: Optional[TokenProvider] = None,
    ) -> None:
        """
        Initialize the GraphQL client.
        
        Args:
            api_url: GraphQL endpoint URL (defaults to settings)
            api_token: Bearer token (deprecated, use token_provider)
            token_provider: Token provider for authentication
        """
        self.api_url = api_url or settings.cway_api_url
        self._client: Optional[Client] = None
        
        # Initialize token provider
        if token_provider:
            self.token_provider = token_provider
        elif api_token:
            # Legacy static token support
            self.token_provider = StaticTokenProvider(api_token)
        else:
            # Auto-configure based on settings
            self.token_provider = self._create_token_provider_from_settings()
        
    def _create_token_provider_from_settings(self) -> TokenProvider:
        """Create token provider based on settings configuration."""
        if settings.auth_method == "oauth2":
            if not settings.azure_tenant_id or not settings.azure_client_id:
                raise ValueError(
                    "OAuth2 authentication requires AZURE_TENANT_ID and AZURE_CLIENT_ID"
                )
            
            logger.info("Initializing OAuth2 authentication")
            return OAuth2TokenProvider(
                tenant_id=settings.azure_tenant_id,
                client_id=settings.azure_client_id,
                client_secret=settings.azure_client_secret,
                scope=settings.oauth2_scope,
                use_device_code_flow=settings.use_device_code_flow,
            )
        else:
            # Default to static token
            if not settings.cway_api_token:
                raise ValueError(
                    "Static authentication requires CWAY_API_TOKEN in environment"
                )
            logger.info("Using static token authentication")
            return StaticTokenProvider(settings.cway_api_token)
    
    async def __aenter__(self) -> "CwayGraphQLClient":
        """Async context manager entry."""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.disconnect()
        
    async def connect(self) -> None:
        """Establish connection to GraphQL endpoint."""
        start_time = time.time()
        log_request_flow("GraphQL Connection", f"Connecting to {self.api_url}")
        
        try:
            # Get initial token
            token = await self.token_provider.get_token()
            
            headers = {
                "Authorization": f"Bearer {token[:10]}..." if token else "None",  # Mask token for logging
                "Content-Type": "application/json",
                "User-Agent": "Cway-MCP-Server/1.0.0"
            }
            
            transport = AIOHTTPTransport(
                url=self.api_url,
                headers={
                    "Authorization": f"Bearer {token}",  # Use full token for actual request
                    "Content-Type": "application/json",
                    "User-Agent": "Cway-MCP-Server/1.0.0"
                },
                timeout=settings.request_timeout
            )
            
            self._client = Client(
                transport=transport,
                fetch_schema_from_transport=False  # Skip schema introspection for performance
            )
            
            duration_ms = (time.time() - start_time) * 1000
            logger.info(f"✅ Connected to Cway GraphQL API at {self.api_url}")
            log_performance("GraphQL Connection", duration_ms, f"URL: {self.api_url}")
            log_request_flow("GraphQL Connected", f"Ready to execute queries")
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"❌ Failed to connect to Cway GraphQL API: {e}")
            log_performance("GraphQL Connection Failed", duration_ms, f"Error: {e}")
            raise
        
    async def disconnect(self) -> None:
        """Close the GraphQL client connection."""
        if self._client and self._client.transport:
            await self._client.transport.close()
        logger.info("Disconnected from Cway GraphQL API")
        
    async def execute_query(
        self, 
        query: str, 
        variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a GraphQL query with error handling and retries.
        
        Args:
            query: GraphQL query string
            variables: Query variables
            
        Returns:
            Query response data
            
        Raises:
            CwayAPIError: For API-related errors
            ConnectionError: For connection issues
        """
        if not self._client:
            await self.connect()
            
        gql_query = gql(query)
        
        for attempt in range(settings.max_retries):
            try:
                logger.debug(f"Executing GraphQL query (attempt {attempt + 1})")
                result = await self._client.execute_async(gql_query, variable_values=variables)
                logger.debug("GraphQL query executed successfully")
                return result
                
            except TransportError as e:
                logger.warning(f"Transport error on attempt {attempt + 1}: {e}")
                if attempt == settings.max_retries - 1:
                    raise ConnectionError(f"Failed to connect to Cway API after {settings.max_retries} attempts") from e
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
            except Exception as e:
                logger.error(f"Unexpected error in GraphQL query: {e}")
                raise CwayAPIError(f"GraphQL query failed: {e}") from e
                
        raise ConnectionError("Max retries exceeded")
        
    async def execute_mutation(
        self, 
        mutation: str, 
        variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a GraphQL mutation.
        
        Args:
            mutation: GraphQL mutation string
            variables: Mutation variables
            
        Returns:
            Mutation response data
        """
        return await self.execute_query(mutation, variables)
        
    async def get_schema(self) -> Optional[str]:
        """
        Get the GraphQL schema via introspection.
        
        Returns:
            Schema string or None if introspection fails
        """
        introspection_query = """
        query IntrospectionQuery {
            __schema {
                types {
                    name
                    description
                    fields {
                        name
                        description
                        type {
                            name
                        }
                    }
                }
            }
        }
        """
        
        try:
            result = await self.execute_query(introspection_query)
            return result.get("__schema")
        except Exception as e:
            logger.warning(f"Schema introspection failed: {e}")
            return None
            

class CwayAPIError(Exception):
    """Exception raised for Cway API related errors."""
    pass