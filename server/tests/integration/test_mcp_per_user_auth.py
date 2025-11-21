"""Integration tests for MCP server with per-user authentication."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from src.presentation.cway_mcp_server import CwayMCPServer
from src.infrastructure.auth.token_manager import TokenManager, TokenManagerError


class TestMCPServerPerUserAuth:
    """Test MCP server with per-user authentication."""
    
    @pytest.fixture
    def mock_token_manager(self):
        """Create mock TokenManager."""
        mock = Mock(spec=TokenManager)
        mock.get_valid_token = AsyncMock()
        mock.is_user_authenticated = Mock()
        return mock
    
    @pytest.fixture
    def mcp_server_with_auth(self, mock_token_manager):
        """Create MCP server instance with mock auth."""
        server = CwayMCPServer()
        server.token_manager = mock_token_manager
        return server
    
    @pytest.mark.asyncio
    async def test_execute_tool_gets_valid_token_for_user(
        self, mcp_server_with_auth, mock_token_manager
    ):
        """Test that _execute_tool gets valid token for authenticated user."""
        username = "test@example.com"
        mock_token_manager.get_valid_token.return_value = "valid_access_token"
        mock_token_manager.is_user_authenticated.return_value = True
        
        # Mock GraphQL client creation
        with patch.object(
            mcp_server_with_auth, '_create_graphql_client_for_user'
        ) as mock_create_client:
            mock_client = Mock()
            mock_create_client.return_value = mock_client
            
            # This should get a valid token
            client = await mcp_server_with_auth._get_authenticated_client(username)
            
            assert client == mock_client
            mock_token_manager.get_valid_token.assert_called_once_with(username)
            mock_create_client.assert_called_once_with("valid_access_token")
    
    @pytest.mark.asyncio
    async def test_execute_tool_raises_error_when_user_not_authenticated(
        self, mcp_server_with_auth, mock_token_manager
    ):
        """Test that error is raised when user is not authenticated."""
        username = "test@example.com"
        mock_token_manager.get_valid_token.side_effect = TokenManagerError(
            "No tokens found"
        )
        
        with pytest.raises(TokenManagerError) as exc_info:
            await mcp_server_with_auth._get_authenticated_client(username)
        
        assert "No tokens found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_token_refresh_happens_transparently(
        self, mcp_server_with_auth, mock_token_manager
    ):
        """Test that token refresh happens transparently during tool execution."""
        username = "test@example.com"
        
        # First call returns old token, second returns new token (after refresh)
        mock_token_manager.get_valid_token.side_effect = [
            "old_token",
            "new_token",
        ]
        
        with patch.object(
            mcp_server_with_auth, '_create_graphql_client_for_user'
        ) as mock_create_client:
            mock_create_client.return_value = Mock()
            
            # First call
            await mcp_server_with_auth._get_authenticated_client(username)
            
            # Second call (token should be refreshed)
            await mcp_server_with_auth._get_authenticated_client(username)
            
            assert mock_token_manager.get_valid_token.call_count == 2
    
    @pytest.mark.asyncio
    async def test_different_users_get_different_tokens(
        self, mcp_server_with_auth, mock_token_manager
    ):
        """Test that different users get their own tokens."""
        user1 = "user1@example.com"
        user2 = "user2@example.com"
        
        mock_token_manager.get_valid_token.side_effect = lambda u: f"token_for_{u}"
        
        with patch.object(
            mcp_server_with_auth, '_create_graphql_client_for_user'
        ) as mock_create_client:
            mock_create_client.return_value = Mock()
            
            await mcp_server_with_auth._get_authenticated_client(user1)
            await mcp_server_with_auth._get_authenticated_client(user2)
            
            # Should have been called with different tokens
            calls = mock_create_client.call_args_list
            assert calls[0][0][0] == f"token_for_{user1}"
            assert calls[1][0][0] == f"token_for_{user2}"
    
    def test_get_current_username_from_settings(self, mcp_server_with_auth):
        """Test getting current username from settings/config."""
        # This will be used to determine which user's tokens to use
        # For now, can use environment variable or default
        username = mcp_server_with_auth._get_current_username()
        
        assert username is not None
        assert "@" in username or username == "default"
    
    @pytest.mark.asyncio
    async def test_mcp_server_works_without_auth_for_backward_compat(
        self, mcp_server_with_auth
    ):
        """Test that MCP server still works without per-user auth (backward compat)."""
        # Remove token manager to simulate old behavior
        mcp_server_with_auth.token_manager = None
        
        # Should fall back to static token from settings
        with patch('config.settings.settings') as mock_settings:
            mock_settings.cway_api_token = "static_token"
            mock_settings.auth_method = "static"
            
            # This should work with static token
            await mcp_server_with_auth._ensure_initialized()
            
            assert mcp_server_with_auth.graphql_client is not None
