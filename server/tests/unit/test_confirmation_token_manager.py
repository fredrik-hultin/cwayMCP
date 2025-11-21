"""Unit tests for ConfirmationTokenManager."""
import time
from datetime import datetime, timedelta
import pytest

from src.infrastructure.confirmation_token_manager import (
    ConfirmationToken,
    ConfirmationTokenManager
)


class TestConfirmationToken:
    """Tests for ConfirmationToken dataclass."""
    
    def test_token_creation(self):
        """Test basic token creation."""
        token = ConfirmationToken(
            token_id="test-123",
            operation="delete_file",
            arguments={"file_id": "abc"},
            preview_data={"file_name": "test.txt"}
        )
        
        assert token.token_id == "test-123"
        assert token.operation == "delete_file"
        assert token.arguments == {"file_id": "abc"}
        assert token.preview_data == {"file_name": "test.txt"}
        assert isinstance(token.created_at, datetime)
        assert isinstance(token.expires_at, datetime)
    
    def test_token_expires_in_5_minutes(self):
        """Test token expiry is set to 5 minutes from creation."""
        token = ConfirmationToken(
            token_id="test-123",
            operation="delete_file",
            arguments={},
            preview_data={}
        )
        
        expected_expiry = token.created_at + timedelta(minutes=5)
        assert token.expires_at == expected_expiry
    
    def test_token_not_expired_initially(self):
        """Test newly created token is not expired."""
        token = ConfirmationToken(
            token_id="test-123",
            operation="delete_file",
            arguments={},
            preview_data={}
        )
        
        assert not token.is_expired()
    
    def test_token_expired_after_5_minutes(self):
        """Test token expires after 5 minutes."""
        token = ConfirmationToken(
            token_id="test-123",
            operation="delete_file",
            arguments={},
            preview_data={}
        )
        
        # Manually set created_at to 6 minutes ago
        token.created_at = datetime.utcnow() - timedelta(minutes=6)
        token.expires_at = token.created_at + timedelta(minutes=5)
        
        assert token.is_expired()
    
    def test_token_matches_operation_only(self):
        """Test matching by operation name only."""
        token = ConfirmationToken(
            token_id="test-123",
            operation="delete_file",
            arguments={"file_id": "abc"},
            preview_data={}
        )
        
        assert token.matches("delete_file")
        assert not token.matches("delete_folder")
    
    def test_token_matches_with_arguments(self):
        """Test matching with operation and arguments."""
        token = ConfirmationToken(
            token_id="test-123",
            operation="delete_file",
            arguments={"file_id": "abc", "force": True},
            preview_data={}
        )
        
        # Matches with subset of arguments
        assert token.matches("delete_file", {"file_id": "abc"})
        
        # Matches with all arguments
        assert token.matches("delete_file", {"file_id": "abc", "force": True})
        
        # Doesn't match with wrong argument value
        assert not token.matches("delete_file", {"file_id": "xyz"})
        
        # Doesn't match with wrong operation
        assert not token.matches("delete_folder", {"file_id": "abc"})


class TestConfirmationTokenManager:
    """Tests for ConfirmationTokenManager."""
    
    @pytest.fixture
    def manager(self):
        """Create a fresh token manager for each test."""
        return ConfirmationTokenManager()
    
    def test_manager_initialization(self, manager):
        """Test manager initializes empty."""
        stats = manager.get_stats()
        assert stats["total_tokens"] == 0
        assert stats["active_tokens"] == 0
    
    def test_create_token(self, manager):
        """Test creating a confirmation token."""
        token_id = manager.create_token(
            operation="delete_file",
            arguments={"file_id": "abc"},
            preview_data={"file_name": "test.txt"}
        )
        
        assert isinstance(token_id, str)
        assert len(token_id) == 36  # UUID format
        
        stats = manager.get_stats()
        assert stats["total_tokens"] == 1
        assert stats["active_tokens"] == 1
    
    def test_validate_token_success(self, manager):
        """Test validating a valid token."""
        token_id = manager.create_token(
            operation="delete_file",
            arguments={"file_id": "abc"},
            preview_data={}
        )
        
        assert manager.validate_token(token_id, "delete_file", {"file_id": "abc"})
    
    def test_validate_token_not_found(self, manager):
        """Test validating non-existent token."""
        assert not manager.validate_token("fake-id", "delete_file")
    
    def test_validate_token_expired(self, manager):
        """Test validating expired token."""
        token_id = manager.create_token(
            operation="delete_file",
            arguments={"file_id": "abc"},
            preview_data={}
        )
        
        # Manually expire the token
        token = manager.get_token(token_id)
        token.created_at = datetime.utcnow() - timedelta(minutes=6)
        token.expires_at = token.created_at + timedelta(minutes=5)
        
        assert not manager.validate_token(token_id, "delete_file")
    
    def test_validate_token_operation_mismatch(self, manager):
        """Test validating token with wrong operation."""
        token_id = manager.create_token(
            operation="delete_file",
            arguments={"file_id": "abc"},
            preview_data={}
        )
        
        assert not manager.validate_token(token_id, "delete_folder")
    
    def test_validate_token_arguments_mismatch(self, manager):
        """Test validating token with wrong arguments."""
        token_id = manager.create_token(
            operation="delete_file",
            arguments={"file_id": "abc"},
            preview_data={}
        )
        
        assert not manager.validate_token(token_id, "delete_file", {"file_id": "xyz"})
    
    def test_get_token(self, manager):
        """Test retrieving a token."""
        token_id = manager.create_token(
            operation="delete_file",
            arguments={"file_id": "abc"},
            preview_data={"file_name": "test.txt"}
        )
        
        token = manager.get_token(token_id)
        assert token is not None
        assert token.token_id == token_id
        assert token.operation == "delete_file"
    
    def test_get_token_not_found(self, manager):
        """Test retrieving non-existent token."""
        token = manager.get_token("fake-id")
        assert token is None
    
    def test_invalidate_token(self, manager):
        """Test invalidating a token (single-use)."""
        token_id = manager.create_token(
            operation="delete_file",
            arguments={"file_id": "abc"},
            preview_data={}
        )
        
        manager.invalidate_token(token_id)
        
        # Token should be gone
        assert manager.get_token(token_id) is None
        assert not manager.validate_token(token_id, "delete_file")
    
    def test_invalidate_token_not_found(self, manager):
        """Test invalidating non-existent token doesn't error."""
        # Should not raise exception
        manager.invalidate_token("fake-id")
    
    def test_cleanup_expired_tokens(self, manager):
        """Test cleanup removes expired tokens."""
        # Create fresh token
        fresh_id = manager.create_token(
            operation="delete_file",
            arguments={"file_id": "fresh"},
            preview_data={}
        )
        
        # Create expired token
        expired_id = manager.create_token(
            operation="delete_folder",
            arguments={"folder_id": "old"},
            preview_data={}
        )
        
        # Manually expire the second token
        token = manager.get_token(expired_id)
        token.created_at = datetime.utcnow() - timedelta(minutes=6)
        token.expires_at = token.created_at + timedelta(minutes=5)
        
        # Cleanup
        cleaned = manager.cleanup_expired()
        
        assert cleaned == 1
        assert manager.get_token(fresh_id) is not None
        assert manager.get_token(expired_id) is None
    
    def test_get_stats(self, manager):
        """Test getting token statistics."""
        # Create 2 tokens for delete_file
        manager.create_token("delete_file", {"file_id": "1"}, {})
        manager.create_token("delete_file", {"file_id": "2"}, {})
        
        # Create 1 token for delete_folder
        manager.create_token("delete_folder", {"folder_id": "1"}, {})
        
        stats = manager.get_stats()
        assert stats["total_tokens"] == 3
        assert stats["active_tokens"] == 3
        assert stats["expired_tokens"] == 0
        assert stats["operations"]["delete_file"] == 2
        assert stats["operations"]["delete_folder"] == 1
    
    def test_tokens_expire_independently(self, manager):
        """Test that tokens expire independently."""
        token1_id = manager.create_token("delete_file", {"file_id": "1"}, {})
        
        # Wait a tiny bit
        time.sleep(0.01)
        
        token2_id = manager.create_token("delete_file", {"file_id": "2"}, {})
        
        # Both should be valid
        assert manager.validate_token(token1_id, "delete_file", {"file_id": "1"})
        assert manager.validate_token(token2_id, "delete_file", {"file_id": "2"})
