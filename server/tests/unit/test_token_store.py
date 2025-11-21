"""Unit tests for TokenStore."""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

from src.infrastructure.auth.token_store import TokenStore, TokenStoreError


class TestTokenStore:
    """Test TokenStore functionality."""
    
    @pytest.fixture
    def temp_storage_dir(self):
        """Create temporary storage directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def token_store(self, temp_storage_dir):
        """Create TokenStore instance with temp directory."""
        return TokenStore(storage_dir=temp_storage_dir / "tokens")
    
    def test_initialize_creates_storage_directory(self, temp_storage_dir):
        """Test that TokenStore creates storage directory."""
        storage_dir = temp_storage_dir / "tokens"
        assert not storage_dir.exists()
        
        TokenStore(storage_dir=storage_dir)
        
        assert storage_dir.exists()
        assert storage_dir.is_dir()
    
    def test_save_tokens_creates_encrypted_file(self, token_store):
        """Test saving tokens creates encrypted file."""
        username = "test@example.com"
        
        token_store.save_tokens(
            username=username,
            access_token="access_token_123",
            refresh_token="refresh_token_456",
            expires_in=3600,
        )
        
        # Check file was created
        token_file = token_store._get_token_file(username)
        assert token_file.exists()
        
        # Check file permissions (Unix only)
        import os
        if hasattr(os, 'stat'):
            stat_info = token_file.stat()
            # Should be 0o600 (owner read/write only)
            assert stat_info.st_mode & 0o777 == 0o600
    
    def test_save_and_retrieve_tokens(self, token_store):
        """Test saving and retrieving tokens."""
        username = "test@example.com"
        access_token = "access_token_123"
        refresh_token = "refresh_token_456"
        
        token_store.save_tokens(
            username=username,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=3600,
        )
        
        retrieved = token_store.get_tokens(username)
        
        assert retrieved is not None
        assert retrieved["username"] == username
        assert retrieved["access_token"] == access_token
        assert retrieved["refresh_token"] == refresh_token
        assert "expires_at" in retrieved
        assert "created_at" in retrieved
    
    def test_get_tokens_nonexistent_user_returns_none(self, token_store):
        """Test retrieving tokens for nonexistent user."""
        result = token_store.get_tokens("nonexistent@example.com")
        assert result is None
    
    def test_tokens_are_encrypted(self, token_store, temp_storage_dir):
        """Test that tokens are encrypted on disk."""
        username = "test@example.com"
        access_token = "secret_access_token"
        
        token_store.save_tokens(
            username=username,
            access_token=access_token,
            refresh_token="refresh",
            expires_in=3600,
        )
        
        # Read raw file content
        token_file = token_store._get_token_file(username)
        raw_content = token_file.read_bytes()
        
        # Should not contain plaintext token
        assert access_token.encode() not in raw_content
        assert b"access_token" not in raw_content
    
    def test_is_token_valid_with_valid_token(self, token_store):
        """Test is_token_valid returns True for valid token."""
        username = "test@example.com"
        
        token_store.save_tokens(
            username=username,
            access_token="token",
            refresh_token="refresh",
            expires_in=3600,  # 1 hour
        )
        
        assert token_store.is_token_valid(username) is True
    
    def test_is_token_valid_with_expired_token(self, token_store):
        """Test is_token_valid returns False for expired token."""
        username = "test@example.com"
        
        token_store.save_tokens(
            username=username,
            access_token="token",
            refresh_token="refresh",
            expires_in=1,  # 1 second
        )
        
        import time
        time.sleep(2)
        
        assert token_store.is_token_valid(username) is False
    
    def test_is_token_valid_nonexistent_user(self, token_store):
        """Test is_token_valid returns False for nonexistent user."""
        assert token_store.is_token_valid("nonexistent@example.com") is False
    
    def test_delete_tokens(self, token_store):
        """Test deleting tokens."""
        username = "test@example.com"
        
        # Save tokens
        token_store.save_tokens(
            username=username,
            access_token="token",
            refresh_token="refresh",
            expires_in=3600,
        )
        
        assert token_store.get_tokens(username) is not None
        
        # Delete tokens
        result = token_store.delete_tokens(username)
        
        assert result is True
        assert token_store.get_tokens(username) is None
    
    def test_delete_tokens_nonexistent_user(self, token_store):
        """Test deleting tokens for nonexistent user."""
        result = token_store.delete_tokens("nonexistent@example.com")
        assert result is False
    
    def test_list_stored_users(self, token_store):
        """Test listing users with stored tokens."""
        users = ["user1@example.com", "user2@example.com", "user3@example.com"]
        
        for user in users:
            token_store.save_tokens(
                username=user,
                access_token=f"token_{user}",
                refresh_token=f"refresh_{user}",
                expires_in=3600,
            )
        
        stored_users = token_store.list_stored_users()
        
        assert len(stored_users) == 3
        assert set(stored_users) == set(users)
    
    def test_clear_all_tokens(self, token_store):
        """Test clearing all tokens."""
        # Save multiple tokens
        for i in range(3):
            token_store.save_tokens(
                username=f"user{i}@example.com",
                access_token=f"token_{i}",
                refresh_token=f"refresh_{i}",
                expires_in=3600,
            )
        
        # Clear all
        count = token_store.clear_all_tokens()
        
        assert count == 3
        assert len(token_store.list_stored_users()) == 0
    
    def test_username_to_filename_is_consistent(self, token_store):
        """Test username to filename conversion is deterministic."""
        username = "test@example.com"
        
        filename1 = token_store._username_to_filename(username)
        filename2 = token_store._username_to_filename(username)
        
        assert filename1 == filename2
    
    def test_different_usernames_get_different_files(self, token_store):
        """Test different usernames get different files."""
        user1 = "user1@example.com"
        user2 = "user2@example.com"
        
        filename1 = token_store._username_to_filename(user1)
        filename2 = token_store._username_to_filename(user2)
        
        assert filename1 != filename2
    
    def test_corrupted_file_returns_none(self, token_store):
        """Test that corrupted token file returns None."""
        username = "test@example.com"
        
        # Create corrupted file
        token_file = token_store._get_token_file(username)
        token_file.write_bytes(b"corrupted data")
        
        result = token_store.get_tokens(username)
        
        assert result is None
        # File should be deleted
        assert not token_file.exists()
    
    def test_update_tokens_for_same_user(self, token_store):
        """Test updating tokens for the same user."""
        username = "test@example.com"
        
        # Save initial tokens
        token_store.save_tokens(
            username=username,
            access_token="old_token",
            refresh_token="old_refresh",
            expires_in=3600,
        )
        
        # Update with new tokens
        token_store.save_tokens(
            username=username,
            access_token="new_token",
            refresh_token="new_refresh",
            expires_in=7200,
        )
        
        retrieved = token_store.get_tokens(username)
        
        assert retrieved["access_token"] == "new_token"
        assert retrieved["refresh_token"] == "new_refresh"
