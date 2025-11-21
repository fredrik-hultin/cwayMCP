"""Unit tests for authentication use cases."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from src.application.auth_use_cases import (
    AuthUseCases,
    LoginInitiationResult,
    LoginCompletionResult,
    WhoAmIResult,
)
from src.infrastructure.auth.token_manager import TokenManager, TokenManagerError


class TestAuthUseCases:
    """Test authentication use cases."""
    
    @pytest.fixture
    def mock_token_manager(self):
        """Create mock TokenManager."""
        mock = Mock(spec=TokenManager)
        mock.entra_authenticator = Mock()
        mock.token_store = Mock()
        mock.get_valid_token = AsyncMock()
        mock.is_user_authenticated = Mock()
        return mock
    
    @pytest.fixture
    def auth_use_cases(self, mock_token_manager):
        """Create AuthUseCases instance."""
        return AuthUseCases(mock_token_manager)
    
    @pytest.mark.asyncio
    async def test_initiate_login_returns_authorization_url(
        self, auth_use_cases, mock_token_manager
    ):
        """Test that initiate_login generates authorization URL."""
        username = "test@example.com"
        expected_url = "https://login.microsoftonline.com/tenant/oauth2/v2.0/authorize?..."
        expected_state = "random_state_string"
        
        mock_token_manager.entra_authenticator.get_authorization_url.return_value = (
            expected_url,
            expected_state,
            "code_verifier"
        )
        
        result = await auth_use_cases.initiate_login(username)
        
        assert isinstance(result, LoginInitiationResult)
        assert result.authorization_url == expected_url
        assert result.state == expected_state
        assert result.success is True
        assert "Open this URL" in result.message
    
    @pytest.mark.asyncio
    async def test_complete_login_exchanges_code_for_tokens(
        self, auth_use_cases, mock_token_manager
    ):
        """Test that complete_login exchanges authorization code for tokens."""
        username = "test@example.com"
        code = "auth_code_123"
        state = "state_value"
        
        mock_token_manager.entra_authenticator.exchange_code_for_cway_tokens = AsyncMock(
            return_value={
                "access_token": "access_token_123",
                "refresh_token": "refresh_token_123",
                "expires_in": 3600
            }
        )
        
        result = await auth_use_cases.complete_login(username, code, state)
        
        assert isinstance(result, LoginCompletionResult)
        assert result.success is True
        assert result.username == username
        assert "successfully authenticated" in result.message.lower()
        
        # Verify tokens were stored
        mock_token_manager.entra_authenticator.exchange_code_for_cway_tokens.assert_called_once_with(
            code, state
        )
    
    @pytest.mark.asyncio
    async def test_complete_login_handles_invalid_code(
        self, auth_use_cases, mock_token_manager
    ):
        """Test that complete_login handles invalid authorization code."""
        username = "test@example.com"
        code = "invalid_code"
        state = "state_value"
        
        mock_token_manager.entra_authenticator.exchange_code_for_cway_tokens = AsyncMock(
            side_effect=TokenManagerError("Invalid authorization code")
        )
        
        result = await auth_use_cases.complete_login(username, code, state)
        
        assert isinstance(result, LoginCompletionResult)
        assert result.success is False
        assert "Invalid authorization code" in result.message
    
    @pytest.mark.asyncio
    async def test_logout_removes_tokens(self, auth_use_cases, mock_token_manager):
        """Test that logout removes stored tokens."""
        username = "test@example.com"
        
        result = await auth_use_cases.logout(username)
        
        assert result["success"] is True
        assert result["username"] == username
        assert "logged out" in result["message"].lower()
        
        # Verify tokens were deleted
        mock_token_manager.token_store.delete_tokens.assert_called_once_with(username)
    
    @pytest.mark.asyncio
    async def test_logout_handles_not_authenticated(
        self, auth_use_cases, mock_token_manager
    ):
        """Test that logout handles user not being authenticated."""
        username = "test@example.com"
        
        mock_token_manager.token_store.delete_tokens.side_effect = FileNotFoundError()
        
        result = await auth_use_cases.logout(username)
        
        assert result["success"] is True  # Logout is idempotent
        assert "not authenticated" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_whoami_returns_user_info(
        self, auth_use_cases, mock_token_manager
    ):
        """Test that whoami returns current user information."""
        username = "test@example.com"
        
        mock_token_manager.is_user_authenticated.return_value = True
        mock_token_manager.token_store.get_tokens.return_value = {
            "access_token": "token",
            "refresh_token": "refresh",
            "expires_at": (datetime.now() + timedelta(hours=1)).isoformat()
        }
        
        result = await auth_use_cases.whoami(username)
        
        assert isinstance(result, WhoAmIResult)
        assert result.authenticated is True
        assert result.username == username
        assert result.expires_in_minutes > 0
    
    @pytest.mark.asyncio
    async def test_whoami_handles_not_authenticated(
        self, auth_use_cases, mock_token_manager
    ):
        """Test that whoami handles user not being authenticated."""
        username = "test@example.com"
        
        mock_token_manager.is_user_authenticated.return_value = False
        
        result = await auth_use_cases.whoami(username)
        
        assert isinstance(result, WhoAmIResult)
        assert result.authenticated is False
        assert result.username == username
        assert result.expires_in_minutes is None
    
    @pytest.mark.asyncio
    async def test_whoami_shows_token_expiry_warning(
        self, auth_use_cases, mock_token_manager
    ):
        """Test that whoami warns when token is about to expire."""
        username = "test@example.com"
        
        mock_token_manager.is_user_authenticated.return_value = True
        mock_token_manager.token_store.get_tokens.return_value = {
            "access_token": "token",
            "refresh_token": "refresh",
            "expires_at": (datetime.now() + timedelta(minutes=3)).isoformat()
        }
        
        result = await auth_use_cases.whoami(username)
        
        assert result.authenticated is True
        assert result.expires_in_minutes < 5
        assert "expiring soon" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_list_authenticated_users(
        self, auth_use_cases, mock_token_manager
    ):
        """Test that list_authenticated_users returns all stored users."""
        mock_token_manager.token_store.list_stored_users.return_value = [
            "user1@example.com",
            "user2@example.com",
            "user3@example.com"
        ]
        
        result = await auth_use_cases.list_authenticated_users()
        
        assert result["success"] is True
        assert len(result["users"]) == 3
        assert "user1@example.com" in result["users"]
        assert result["count"] == 3
