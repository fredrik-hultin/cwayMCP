"""
Tests for confirmation service.
"""

import time
import pytest
from src.application.services.confirmation_service import ConfirmationService


class TestConfirmationService:
    """Test suite for ConfirmationService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = ConfirmationService(
            secret_key="test-secret-key-12345",
            default_expiry_minutes=5
        )
    
    def test_generate_token_success(self):
        """Test successful token generation."""
        token_info = self.service.generate_token(
            action="delete_projects",
            data={"project_ids": ["proj-1", "proj-2"]}
        )
        
        assert "token" in token_info
        assert "expires_at" in token_info
        assert "expires_in_seconds" in token_info
        assert token_info["expires_in_seconds"] == 300  # 5 minutes
        assert "|" in token_info["token"]  # Contains signature separator
    
    def test_generate_token_custom_expiry(self):
        """Test token generation with custom expiry."""
        token_info = self.service.generate_token(
            action="close_projects",
            data={"project_ids": ["proj-1"]},
            expires_minutes=10
        )
        
        assert token_info["expires_in_seconds"] == 600  # 10 minutes
    
    def test_validate_token_success(self):
        """Test successful token validation."""
        # Generate token
        token_info = self.service.generate_token(
            action="delete_projects",
            data={"project_ids": ["proj-1", "proj-2"], "force": True}
        )
        
        # Validate token
        validated = self.service.validate_token(token_info["token"])
        
        assert validated["action"] == "delete_projects"
        assert validated["data"]["project_ids"] == ["proj-1", "proj-2"]
        assert validated["data"]["force"] is True
    
    def test_validate_token_invalid_format(self):
        """Test validation fails with invalid token format."""
        with pytest.raises(ValueError, match="Invalid token format"):
            self.service.validate_token("invalid-token")
    
    def test_validate_token_invalid_signature(self):
        """Test validation fails with tampered token."""
        # Generate valid token
        token_info = self.service.generate_token(
            action="delete_projects",
            data={"project_ids": ["proj-1"]}
        )
        
        # Tamper with token
        parts = token_info["token"].split("|")
        tampered_token = parts[0] + "|invalid_signature"
        
        with pytest.raises(ValueError, match="Invalid token signature"):
            self.service.validate_token(tampered_token)
    
    def test_validate_token_already_used(self):
        """Test validation fails when token is reused."""
        # Generate and validate token once
        token_info = self.service.generate_token(
            action="delete_projects",
            data={"project_ids": ["proj-1"]}
        )
        
        # First validation should succeed
        self.service.validate_token(token_info["token"])
        
        # Second validation should fail
        with pytest.raises(ValueError, match="Token has already been used"):
            self.service.validate_token(token_info["token"])
    
    def test_validate_token_expired(self):
        """Test validation fails with expired token."""
        # Create service with very short expiry
        service = ConfirmationService(
            secret_key="test-key",
            default_expiry_minutes=0  # Will expire immediately
        )
        
        token_info = service.generate_token(
            action="delete_projects",
            data={"project_ids": ["proj-1"]},
            expires_minutes=0  # Expires immediately
        )
        
        # Wait a moment to ensure expiration
        time.sleep(0.1)
        
        with pytest.raises(ValueError, match="Token has expired"):
            service.validate_token(token_info["token"])
    
    def test_create_preview_response(self):
        """Test preview response creation."""
        token_info = self.service.generate_token(
            action="delete_projects",
            data={"project_ids": ["proj-1", "proj-2"]}
        )
        
        items = [
            {"id": "proj-1", "name": "Project 1"},
            {"id": "proj-2", "name": "Project 2"}
        ]
        
        warnings = [
            "This will delete 2 projects",
            "This action cannot be undone"
        ]
        
        response = self.service.create_preview_response(
            action="delete",
            items=items,
            item_type="projects",
            warnings=warnings,
            token_info=token_info
        )
        
        assert response["action"] == "preview"
        assert response["operation"] == "delete"
        assert response["item_type"] == "projects"
        assert response["items"] == items
        assert response["item_count"] == 2
        assert response["warnings"] == warnings
        assert response["confirmation_required"] is True
        assert "confirmation_token" in response
        assert "token_expires_at" in response
        assert "next_step" in response
    
    def test_token_cleanup(self):
        """Test that old used tokens are cleaned up."""
        # Generate and use multiple tokens
        for i in range(10):
            token_info = self.service.generate_token(
                action="test",
                data={"test": i}
            )
            self.service.validate_token(token_info["token"])
        
        # Verify tokens are tracked
        assert len(self.service._used_tokens) == 10
        
        # Manually set old timestamps to trigger cleanup
        cutoff_time = time.time() - 7200  # 2 hours ago
        for token_hash in list(self.service._used_tokens.keys())[:5]:
            self.service._used_tokens[token_hash] = cutoff_time
        
        # Trigger cleanup by validating a new token
        new_token_info = self.service.generate_token(
            action="test",
            data={"test": "cleanup"}
        )
        self.service.validate_token(new_token_info["token"])
        
        # Old tokens should be cleaned up (5 old + 1 new = 6 remaining)
        assert len(self.service._used_tokens) == 6
    
    def test_different_actions(self):
        """Test tokens work for different action types."""
        actions = ["delete_projects", "close_projects", "delete_users"]
        
        for action in actions:
            token_info = self.service.generate_token(
                action=action,
                data={"test": "data"}
            )
            validated = self.service.validate_token(token_info["token"])
            assert validated["action"] == action
    
    def test_action_mismatch_detection(self):
        """Test that action type is preserved and can be validated."""
        # Generate token for delete
        token_info = self.service.generate_token(
            action="delete_projects",
            data={"project_ids": ["proj-1"]}
        )
        
        # Validate and check action
        validated = self.service.validate_token(token_info["token"])
        
        # Application should check action matches expected
        assert validated["action"] == "delete_projects"
        # If application expected "close_projects", it should reject
        assert validated["action"] != "close_projects"
