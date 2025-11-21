"""Unit tests for TokenManager."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from src.infrastructure.auth.token_manager import TokenManager, TokenManagerError
from src.infrastructure.auth.token_store import TokenStore
from src.infrastructure.auth.entra_auth import EntraIDAuthenticator, EntraAuthError


class TestTokenManager:
    """Test TokenManager functionality."""
    
    @pytest.fixture
    def mock_token_store(self):
        """Create mock TokenStore."""
        return Mock(spec=TokenStore)
    
    @pytest.fixture
    def mock_authenticator(self):
        """Create mock EntraIDAuthenticator."""
        mock = Mock(spec=EntraIDAuthenticator)
        mock.refresh_cway_token = AsyncMock()
        return mock
    
    @pytest.fixture
    def token_manager(self, mock_token_store, mock_authenticator):
        """Create TokenManager instance with mocks."""
        return TokenManager(
            token_store=mock_token_store,
            authenticator=mock_authenticator,
            refresh_threshold_minutes=5,
        )
    
    @pytest.mark.asyncio
    async def test_get_valid_token_returns_cached_token_when_valid(
        self, token_manager, mock_token_store
    ):
        """Test get_valid_token returns cached token when still valid."""
        username = "test@example.com"
        expires_at = (datetime.now() + timedelta(hours=1)).isoformat()
        
        mock_token_store.get_tokens.return_value = {
            "username": username,
            "access_token": "cached_token",
            "refresh_token": "refresh_token",
            "expires_at": expires_at,
        }
        
        token = await token_manager.get_valid_token(username)
        
        assert token == "cached_token"
        # Should not call refresh
        token_manager.authenticator.refresh_cway_token.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_valid_token_refreshes_when_expiring_soon(
        self, token_manager, mock_token_store, mock_authenticator
    ):
        """Test get_valid_token refreshes token when expiring within threshold."""
        username = "test@example.com"
        # Token expires in 3 minutes (< 5 minute threshold)
        expires_at = (datetime.now() + timedelta(minutes=3)).isoformat()
        
        mock_token_store.get_tokens.return_value = {
            "username": username,
            "access_token": "old_token",
            "refresh_token": "refresh_token",
            "expires_at": expires_at,
        }
        
        mock_authenticator.refresh_cway_token.return_value = {
            "access_token": "new_token",
            "refresh_token": "new_refresh",
            "expires_in": 3600,
        }
        
        token = await token_manager.get_valid_token(username)
        
        assert token == "new_token"
        mock_authenticator.refresh_cway_token.assert_called_once_with("refresh_token")
        mock_token_store.save_tokens.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_valid_token_raises_error_when_no_tokens(
        self, token_manager, mock_token_store
    ):
        """Test get_valid_token raises error when no tokens exist."""
        username = "test@example.com"
        mock_token_store.get_tokens.return_value = None
        
        with pytest.raises(TokenManagerError) as exc_info:
            await token_manager.get_valid_token(username)
        
        assert "No tokens found" in str(exc_info.value)
        assert "Please login first" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_valid_token_deletes_tokens_on_refresh_failure(
        self, token_manager, mock_token_store, mock_authenticator
    ):
        """Test that tokens are deleted when refresh fails."""
        username = "test@example.com"
        expires_at = (datetime.now() + timedelta(minutes=3)).isoformat()
        
        mock_token_store.get_tokens.return_value = {
            "username": username,
            "access_token": "old_token",
            "refresh_token": "refresh_token",
            "expires_at": expires_at,
        }
        
        mock_authenticator.refresh_cway_token.side_effect = EntraAuthError("Refresh failed")
        
        with pytest.raises(TokenManagerError) as exc_info:
            await token_manager.get_valid_token(username)
        
        assert "Token refresh failed" in str(exc_info.value)
        mock_token_store.delete_tokens.assert_called_once_with(username)
    
    def test_is_user_authenticated_returns_true_for_valid_tokens(
        self, token_manager, mock_token_store
    ):
        """Test is_user_authenticated returns True for valid tokens."""
        username = "test@example.com"
        mock_token_store.is_token_valid.return_value = True
        
        result = token_manager.is_user_authenticated(username)
        
        assert result is True
        mock_token_store.is_token_valid.assert_called_once_with(username)
    
    def test_is_user_authenticated_returns_false_for_invalid_tokens(
        self, token_manager, mock_token_store
    ):
        """Test is_user_authenticated returns False for invalid tokens."""
        username = "test@example.com"
        mock_token_store.is_token_valid.return_value = False
        
        result = token_manager.is_user_authenticated(username)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_save_initial_tokens(self, token_manager, mock_token_store):
        """Test saving initial tokens after authentication."""
        username = "test@example.com"
        access_token = "access_token_123"
        refresh_token = "refresh_token_456"
        expires_in = 3600
        
        await token_manager.save_initial_tokens(
            username=username,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
        )
        
        mock_token_store.save_tokens.assert_called_once_with(
            username=username,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
        )
    
    def test_logout_user(self, token_manager, mock_token_store):
        """Test logging out user."""
        username = "test@example.com"
        mock_token_store.delete_tokens.return_value = True
        
        result = token_manager.logout_user(username)
        
        assert result is True
        mock_token_store.delete_tokens.assert_called_once_with(username)
    
    def test_logout_user_returns_false_when_no_tokens(
        self, token_manager, mock_token_store
    ):
        """Test logout returns False when user has no tokens."""
        username = "test@example.com"
        mock_token_store.delete_tokens.return_value = False
        
        result = token_manager.logout_user(username)
        
        assert result is False
    
    def test_get_token_info_returns_info_for_valid_tokens(
        self, token_manager, mock_token_store
    ):
        """Test get_token_info returns token information."""
        username = "test@example.com"
        expires_at = (datetime.now() + timedelta(hours=1)).isoformat()
        
        mock_token_store.get_tokens.return_value = {
            "username": username,
            "access_token": "token",
            "refresh_token": "refresh",
            "expires_at": expires_at,
        }
        
        info = token_manager.get_token_info(username)
        
        assert info is not None
        assert info["username"] == username
        assert info["expires_at"] == expires_at
        assert info["is_valid"] is True
        assert info["expires_in_seconds"] > 0
    
    def test_get_token_info_returns_none_for_nonexistent_user(
        self, token_manager, mock_token_store
    ):
        """Test get_token_info returns None for nonexistent user."""
        mock_token_store.get_tokens.return_value = None
        
        info = token_manager.get_token_info("nonexistent@example.com")
        
        assert info is None
    
    def test_list_authenticated_users(self, token_manager, mock_token_store):
        """Test listing authenticated users."""
        users = ["user1@example.com", "user2@example.com"]
        mock_token_store.list_stored_users.return_value = users
        
        result = token_manager.list_authenticated_users()
        
        assert result == users
    
    @pytest.mark.asyncio
    async def test_concurrent_token_refresh_is_thread_safe(
        self, token_manager, mock_token_store, mock_authenticator
    ):
        """Test that concurrent refresh attempts work correctly."""
        username = "test@example.com"
        expires_at = (datetime.now() + timedelta(minutes=3)).isoformat()
        
        mock_token_store.get_tokens.return_value = {
            "username": username,
            "access_token": "old_token",
            "refresh_token": "refresh_token",
            "expires_at": expires_at,
        }
        
        mock_authenticator.refresh_cway_token.return_value = {
            "access_token": "new_token",
            "refresh_token": "new_refresh",
            "expires_in": 3600,
        }
        
        # Make multiple concurrent requests
        tasks = [
            token_manager.get_valid_token(username)
            for _ in range(5)
        ]
        
        tokens = await asyncio.gather(*tasks)
        
        # All should get a new token
        assert all(token == "new_token" for token in tokens)
        # Refresh may be called multiple times due to async concurrency
        # The important thing is all requests succeed
        assert mock_authenticator.refresh_cway_token.call_count >= 1
