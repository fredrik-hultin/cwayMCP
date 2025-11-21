"""Integration tests for multi-user per-user authentication."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil

from src.infrastructure.auth.token_store import TokenStore
from src.infrastructure.auth.token_manager import TokenManager
from src.application.auth_use_cases import AuthUseCases


class TestMultiUserAuthentication:
    """Test multi-user authentication scenarios."""
    
    @pytest.fixture
    def temp_token_dir(self):
        """Create temporary directory for token storage."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def token_store(self, temp_token_dir):
        """Create TokenStore with temporary directory."""
        return TokenStore(storage_dir=temp_token_dir / "tokens")
    
    @pytest.fixture
    def mock_entra_auth(self):
        """Create mock EntraIDAuthenticator."""
        mock = Mock()
        mock.exchange_code_for_cway_tokens = AsyncMock(return_value={
            "access_token": "access_token_123",
            "refresh_token": "refresh_token_123",
            "expires_in": 3600
        })
        mock.refresh_cway_token = AsyncMock(return_value={
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 3600
        })
        return mock
    
    @pytest.fixture
    def token_manager(self, token_store, mock_entra_auth):
        """Create TokenManager with mocked auth."""
        manager = TokenManager(
            token_store=token_store,
            authenticator=mock_entra_auth,
            refresh_threshold_minutes=5
        )
        return manager
    
    @pytest.mark.asyncio
    async def test_multiple_users_separate_token_storage(self, token_store):
        """Test that multiple users have separate encrypted token files."""
        users = ["user1@example.com", "user2@example.com", "user3@example.com"]
        
        # Store tokens for multiple users
        for i, user in enumerate(users):
            token_store.save_tokens(
                username=user,
                access_token=f"access_token_{i}",
                refresh_token=f"refresh_token_{i}",
                expires_in=3600
            )
        
        # Verify each user has their own file
        stored_users = token_store.list_stored_users()
        assert len(stored_users) == 3
        assert set(stored_users) == set(users)
        
        # Verify tokens are isolated
        for i, user in enumerate(users):
            tokens = token_store.get_tokens(user)
            assert tokens["username"] == user
            assert tokens["access_token"] == f"access_token_{i}"
            assert tokens["refresh_token"] == f"refresh_token_{i}"
    
    @pytest.mark.asyncio
    async def test_concurrent_token_refresh_per_user(self, token_manager, token_store):
        """Test that concurrent requests from same user don't cause race conditions."""
        username = "user@example.com"
        
        # Store token that's about to expire
        token_store.save_tokens(
            username=username,
            access_token="old_token",
            refresh_token="refresh_token",
            expires_in=60  # 1 minute - will trigger refresh
        )
        
        # Simulate concurrent requests from same user
        tasks = [
            token_manager.get_valid_token(username)
            for _ in range(10)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All should get the same token (refreshed once)
        assert len(set(results)) == 1  # All same token
        
        # Refresh should only happen once
        assert token_manager.authenticator.refresh_cway_token.call_count <= 1
    
    @pytest.mark.asyncio
    async def test_concurrent_different_users_no_interference(
        self, token_manager, token_store
    ):
        """Test that concurrent requests from different users are isolated."""
        users = [f"user{i}@example.com" for i in range(5)]
        
        # Store tokens for all users
        for i, user in enumerate(users):
            token_store.save_tokens(
                username=user,
                access_token=f"access_{i}",
                refresh_token=f"refresh_{i}",
                expires_in=3600
            )
        
        # Concurrent requests from different users
        async def get_token_for_user(user):
            return await token_manager.get_valid_token(user)
        
        tasks = [get_token_for_user(user) for user in users]
        results = await asyncio.gather(*tasks)
        
        # Each user should get their own token
        assert len(results) == 5
        for i, token in enumerate(results):
            assert token == f"access_{i}"
    
    @pytest.mark.asyncio
    async def test_user_logout_does_not_affect_other_users(
        self, token_store, token_manager
    ):
        """Test that logging out one user doesn't affect others."""
        users = ["alice@example.com", "bob@example.com", "charlie@example.com"]
        
        # Authenticate all users
        for i, user in enumerate(users):
            token_store.save_tokens(
                username=user,
                access_token=f"token_{i}",
                refresh_token=f"refresh_{i}",
                expires_in=3600
            )
        
        # Verify all authenticated
        assert len(token_store.list_stored_users()) == 3
        
        # Logout Bob
        auth_use_cases = AuthUseCases(token_manager)
        result = await auth_use_cases.logout("bob@example.com")
        
        assert result["success"] is True
        
        # Alice and Charlie still authenticated
        remaining_users = token_store.list_stored_users()
        assert len(remaining_users) == 2
        assert "alice@example.com" in remaining_users
        assert "charlie@example.com" in remaining_users
        assert "bob@example.com" not in remaining_users
        
        # Alice and Charlie can still get tokens
        alice_token = await token_manager.get_valid_token("alice@example.com")
        assert alice_token == "token_0"
        
        charlie_token = await token_manager.get_valid_token("charlie@example.com")
        assert charlie_token == "token_2"
    
    @pytest.mark.asyncio
    async def test_token_refresh_per_user_independence(
        self, token_manager, token_store, mock_entra_auth
    ):
        """Test that token refresh for one user doesn't affect others."""
        # User 1: Token about to expire (needs refresh)
        token_store.save_tokens(
            username="user1@example.com",
            access_token="old_token_1",
            refresh_token="refresh_1",
            expires_in=60  # 1 minute
        )
        
        # User 2: Fresh token (no refresh needed)
        token_store.save_tokens(
            username="user2@example.com",
            access_token="token_2",
            refresh_token="refresh_2",
            expires_in=3600  # 1 hour
        )
        
        # Get token for user1 (triggers refresh)
        mock_entra_auth.refresh_cway_token.return_value = {
            "access_token": "new_token_1",
            "refresh_token": "new_refresh_1",
            "expires_in": 3600
        }
        
        token1 = await token_manager.get_valid_token("user1@example.com")
        assert token1 == "new_token_1"
        
        # Get token for user2 (no refresh)
        token2 = await token_manager.get_valid_token("user2@example.com")
        assert token2 == "token_2"  # Still original token
        
        # Verify user2's tokens unchanged
        user2_tokens = token_store.get_tokens("user2@example.com")
        assert user2_tokens["access_token"] == "token_2"
    
    @pytest.mark.asyncio
    async def test_token_expiry_per_user(self, token_store, token_manager):
        """Test that expired tokens are handled correctly per user."""
        # User 1: Expired token
        expired_time = datetime.now() - timedelta(hours=2)
        token_store.save_tokens(
            username="user1@example.com",
            access_token="expired_token",
            refresh_token="refresh_1",
            expires_in=-7200  # Expired 2 hours ago
        )
        
        # User 2: Valid token
        token_store.save_tokens(
            username="user2@example.com",
            access_token="valid_token",
            refresh_token="refresh_2",
            expires_in=3600
        )
        
        # User 1 triggers refresh
        await token_manager.get_valid_token("user1@example.com")
        assert token_manager.authenticator.refresh_cway_token.called
        
        # User 2 doesn't trigger refresh
        token_manager.authenticator.refresh_cway_token.reset_mock()
        token = await token_manager.get_valid_token("user2@example.com")
        assert token == "valid_token"
        assert not token_manager.authenticator.refresh_cway_token.called
    
    @pytest.mark.asyncio
    async def test_authentication_state_isolation(self, token_store, token_manager):
        """Test that authentication state is isolated between users."""
        auth_use_cases = AuthUseCases(token_manager)
        
        # User 1: Authenticated
        token_store.save_tokens(
            username="user1@example.com",
            access_token="token_1",
            refresh_token="refresh_1",
            expires_in=3600
        )
        
        # User 2: Not authenticated (no tokens)
        
        # Check user 1
        result1 = await auth_use_cases.whoami("user1@example.com")
        assert result1.authenticated is True
        assert result1.username == "user1@example.com"
        
        # Check user 2
        result2 = await auth_use_cases.whoami("user2@example.com")
        assert result2.authenticated is False
        assert result2.username == "user2@example.com"
    
    @pytest.mark.asyncio
    async def test_large_number_of_concurrent_users(
        self, token_manager, token_store
    ):
        """Test system handles many concurrent users efficiently."""
        num_users = 50
        users = [f"user{i}@example.com" for i in range(num_users)]
        
        # Setup tokens for all users
        for i, user in enumerate(users):
            token_store.save_tokens(
                username=user,
                access_token=f"token_{i}",
                refresh_token=f"refresh_{i}",
                expires_in=3600
            )
        
        # Concurrent token retrieval
        tasks = [token_manager.get_valid_token(user) for user in users]
        results = await asyncio.gather(*tasks)
        
        # Verify all succeeded
        assert len(results) == num_users
        for i, token in enumerate(results):
            assert token == f"token_{i}"
    
    @pytest.mark.asyncio
    async def test_token_file_permissions(self, token_store):
        """Test that token files have correct permissions (600)."""
        import os
        import stat
        
        username = "secure@example.com"
        token_store.save_tokens(
            username=username,
            access_token="secure_token",
            refresh_token="secure_refresh",
            expires_in=3600
        )
        
        token_file = token_store._get_token_file(username)
        file_stats = os.stat(token_file)
        
        # Check permissions are 600 (owner read/write only)
        mode = stat.filemode(file_stats.st_mode)
        assert mode == "-rw-------"
    
    @pytest.mark.asyncio
    async def test_corrupted_token_file_isolation(self, token_store):
        """Test that corrupted token file for one user doesn't affect others."""
        # Store valid tokens for user1
        token_store.save_tokens(
            username="user1@example.com",
            access_token="token_1",
            refresh_token="refresh_1",
            expires_in=3600
        )
        
        # Store valid tokens for user2
        token_store.save_tokens(
            username="user2@example.com",
            access_token="token_2",
            refresh_token="refresh_2",
            expires_in=3600
        )
        
        # Corrupt user1's token file
        user1_file = token_store._get_token_file("user1@example.com")
        user1_file.write_bytes(b"corrupted_data")
        
        # User1 tokens should return None
        user1_tokens = token_store.get_tokens("user1@example.com")
        assert user1_tokens is None
        
        # User2 tokens should still work
        user2_tokens = token_store.get_tokens("user2@example.com")
        assert user2_tokens is not None
        assert user2_tokens["access_token"] == "token_2"


class TestTokenLifecycle:
    """Test complete token lifecycle for multiple users."""
    
    @pytest.fixture
    def temp_token_dir(self):
        """Create temporary directory for token storage."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def token_store(self, temp_token_dir):
        """Create TokenStore with temporary directory."""
        return TokenStore(storage_dir=temp_token_dir / "tokens")
    
    @pytest.mark.asyncio
    async def test_full_authentication_lifecycle(self, token_store):
        """Test complete lifecycle: login → use → refresh → logout."""
        username = "lifecycle@example.com"
        
        # 1. Login (store initial tokens)
        token_store.save_tokens(
            username=username,
            access_token="initial_token",
            refresh_token="initial_refresh",
            expires_in=3600
        )
        
        # 2. Use (retrieve tokens)
        tokens = token_store.get_tokens(username)
        assert tokens is not None
        assert tokens["access_token"] == "initial_token"
        
        # 3. Update (simulate refresh)
        token_store.save_tokens(
            username=username,
            access_token="refreshed_token",
            refresh_token="refreshed_refresh",
            expires_in=3600
        )
        
        # 4. Verify updated
        tokens = token_store.get_tokens(username)
        assert tokens["access_token"] == "refreshed_token"
        
        # 5. Logout (delete tokens)
        success = token_store.delete_tokens(username)
        assert success is True
        
        # 6. Verify removed
        tokens = token_store.get_tokens(username)
        assert tokens is None
    
    @pytest.mark.asyncio
    async def test_token_expiry_timeline(self, token_store):
        """Test token validity over time."""
        username = "timeline@example.com"
        
        # Store token expiring in 10 minutes
        token_store.save_tokens(
            username=username,
            access_token="token",
            refresh_token="refresh",
            expires_in=600  # 10 minutes
        )
        
        # Should be valid
        assert token_store.is_token_valid(username) is True
        
        # Simulate token near expiry (< 1 min remaining)
        token_store.save_tokens(
            username=username,
            access_token="token",
            refresh_token="refresh",
            expires_in=30  # 30 seconds
        )
        
        # Should be invalid (< 1 min threshold)
        assert token_store.is_token_valid(username) is False
