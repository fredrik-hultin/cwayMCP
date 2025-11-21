"""Unit tests for GraphQL client with per-user token support."""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from src.infrastructure.graphql_client import CwayGraphQLClient
from src.infrastructure.auth.token_provider import StaticTokenProvider


class TestGraphQLClientPerUser:
    """Test GraphQL client with per-user authentication."""
    
    @pytest.mark.asyncio
    async def test_client_accepts_direct_api_token(self):
        """Test that client accepts api_token parameter for per-user auth."""
        user_token = "user_specific_jwt_token"
        
        client = CwayGraphQLClient(api_token=user_token)
        
        assert client.token_provider is not None
        assert isinstance(client.token_provider, StaticTokenProvider)
        
        # Verify token is used correctly
        token = await client.token_provider.get_token()
        assert token == user_token
    
    @pytest.mark.asyncio
    async def test_different_users_have_different_clients(self):
        """Test that different users can have separate client instances."""
        user1_token = "user1_token"
        user2_token = "user2_token"
        
        client1 = CwayGraphQLClient(api_token=user1_token)
        client2 = CwayGraphQLClient(api_token=user2_token)
        
        token1 = await client1.token_provider.get_token()
        token2 = await client2.token_provider.get_token()
        
        assert token1 == user1_token
        assert token2 == user2_token
        assert token1 != token2
    
    @pytest.mark.asyncio
    async def test_client_without_token_falls_back_to_settings(self):
        """Test that client without api_token uses settings (backward compat)."""
        with patch('src.infrastructure.graphql_client.settings') as mock_settings:
            mock_settings.cway_api_url = "https://api.test.com"
            mock_settings.cway_api_token = "settings_token"
            mock_settings.auth_method = "static"
            mock_settings.request_timeout = 30
            
            client = CwayGraphQLClient()
            
            assert client.token_provider is not None
            token = await client.token_provider.get_token()
            assert token == "settings_token"
    
    @pytest.mark.asyncio
    async def test_api_token_has_priority_over_settings(self):
        """Test that api_token parameter takes priority over settings."""
        user_token = "per_user_token"
        
        with patch('src.infrastructure.graphql_client.settings') as mock_settings:
            mock_settings.cway_api_url = "https://api.test.com"
            mock_settings.cway_api_token = "settings_token"
            mock_settings.auth_method = "static"
            mock_settings.request_timeout = 30
            
            client = CwayGraphQLClient(api_token=user_token)
            
            token = await client.token_provider.get_token()
            assert token == user_token  # Should use provided token, not settings
    
    @pytest.mark.asyncio
    async def test_client_with_custom_token_provider(self):
        """Test that client accepts custom token provider (advanced use)."""
        custom_provider = Mock(spec=StaticTokenProvider)
        custom_provider.get_token = AsyncMock(return_value="custom_token")
        
        client = CwayGraphQLClient(token_provider=custom_provider)
        
        assert client.token_provider == custom_provider
        token = await client.token_provider.get_token()
        assert token == "custom_token"
    
    @pytest.mark.asyncio
    async def test_client_priority_api_token_over_token_provider(self):
        """Test that api_token has priority over token_provider."""
        custom_provider = Mock(spec=StaticTokenProvider)
        custom_provider.get_token = AsyncMock(return_value="custom_token")
        
        direct_token = "direct_token"
        
        client = CwayGraphQLClient(
            api_token=direct_token,
            token_provider=custom_provider
        )
        
        # Should use api_token, not custom_provider
        token = await client.token_provider.get_token()
        assert token == direct_token
    
    @pytest.mark.asyncio
    async def test_connect_uses_provided_token(self):
        """Test that connect() uses the provided api_token."""
        user_token = "test_user_token"
        
        with patch('src.infrastructure.graphql_client.AIOHTTPTransport') as MockTransport, \
             patch('src.infrastructure.graphql_client.Client') as MockClient:
            
            client = CwayGraphQLClient(api_token=user_token)
            await client.connect()
            
            # Verify transport was created with correct authorization header
            MockTransport.assert_called_once()
            call_kwargs = MockTransport.call_args.kwargs
            headers = call_kwargs['headers']
            
            assert headers['Authorization'] == f"Bearer {user_token}"
    
    @pytest.mark.asyncio
    async def test_oauth2_mode_warns_when_no_token_provided(self):
        """Test that oauth2 mode without api_token shows warning."""
        with patch('src.infrastructure.graphql_client.settings') as mock_settings, \
             patch('src.infrastructure.graphql_client.logger') as mock_logger, \
             patch('src.infrastructure.graphql_client.OAuth2TokenProvider') as MockOAuth2:
            
            # Mock OAuth2TokenProvider to avoid actual MSAL calls
            mock_oauth2_instance = Mock()
            MockOAuth2.return_value = mock_oauth2_instance
            
            mock_settings.cway_api_url = "https://api.test.com"
            mock_settings.auth_method = "oauth2"
            mock_settings.azure_tenant_id = "tenant_id"
            mock_settings.azure_client_id = "client_id"
            mock_settings.azure_client_secret = "client_secret"
            mock_settings.oauth2_scope = "scope"
            mock_settings.use_device_code_flow = False
            mock_settings.validate_auth_config = Mock()
            
            client = CwayGraphQLClient()
            
            # Should log warning about missing api_token
            mock_logger.warning.assert_called()
            warning_msg = mock_logger.warning.call_args[0][0]
            assert "api_token" in warning_msg.lower()
            assert "per-user authentication" in warning_msg.lower()
