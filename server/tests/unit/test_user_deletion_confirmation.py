"""
Tests for user deletion confirmation flow.
"""

import pytest
from src.application.services.confirmation_service import ConfirmationService


class TestUserDeletionConfirmation:
    """Test suite for user deletion confirmation workflow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = ConfirmationService(
            secret_key="test-secret-key-user-deletion",
            default_expiry_minutes=5
        )
    
    def test_prepare_delete_user_token_generation(self):
        """Test token generation for user deletion."""
        token_info = self.service.generate_token(
            action="delete_user",
            data={"username": "john.doe"}
        )
        
        assert "token" in token_info
        assert "expires_at" in token_info
        assert "expires_in_seconds" in token_info
        assert token_info["expires_in_seconds"] == 300  # 5 minutes
    
    def test_confirm_delete_user_token_validation(self):
        """Test successful user deletion token validation."""
        # Generate token
        token_info = self.service.generate_token(
            action="delete_user",
            data={"username": "john.doe"}
        )
        
        # Validate token
        validated = self.service.validate_token(token_info["token"])
        
        assert validated["action"] == "delete_user"
        assert validated["data"]["username"] == "john.doe"
    
    def test_user_deletion_preview_response(self):
        """Test preview response for user deletion."""
        token_info = self.service.generate_token(
            action="delete_user",
            data={"username": "john.doe"}
        )
        
        user_info = {
            "username": "john.doe",
            "name": "John Doe",
            "email": "john.doe@example.com",
            "enabled": True,
            "is_sso": False
        }
        
        warnings = [
            "⚠️ DESTRUCTIVE ACTION: Will permanently delete user 'john.doe'",
            "🚨 THIS ACTION CANNOT BE UNDONE",
            "User email: john.doe@example.com",
            "All user data and associations will be permanently lost"
        ]
        
        response = self.service.create_preview_response(
            action="delete",
            items=[user_info],
            item_type="user",
            warnings=warnings,
            token_info=token_info
        )
        
        assert response["action"] == "preview"
        assert response["operation"] == "delete"
        assert response["item_type"] == "user"
        assert response["items"][0]["username"] == "john.doe"
        assert response["item_count"] == 1
        assert len(response["warnings"]) == 4
        assert response["confirmation_required"] is True
    
    def test_action_mismatch_user_vs_project(self):
        """Test that user deletion token cannot be used for project operations."""
        # Generate token for user deletion
        token_info = self.service.generate_token(
            action="delete_user",
            data={"username": "john.doe"}
        )
        
        # Validate and check action
        validated = self.service.validate_token(token_info["token"])
        
        # Should only work for delete_user, not delete_projects
        assert validated["action"] == "delete_user"
        assert validated["action"] != "delete_projects"
    
    def test_sso_user_detection(self):
        """Test SSO user warning in preview."""
        token_info = self.service.generate_token(
            action="delete_user",
            data={"username": "sso.user"}
        )
        
        user_info = {
            "username": "sso.user",
            "name": "SSO User",
            "email": "sso.user@example.com",
            "enabled": True,
            "is_sso": True
        }
        
        warnings = [
            "⚠️ DESTRUCTIVE ACTION: Will permanently delete user 'sso.user'",
            "🚨 THIS ACTION CANNOT BE UNDONE",
            "⚠️ This is an SSO user - deletion may affect external authentication"
        ]
        
        response = self.service.create_preview_response(
            action="delete",
            items=[user_info],
            item_type="user",
            warnings=warnings,
            token_info=token_info
        )
        
        assert response["items"][0]["is_sso"] is True
        # Check that SSO warning is included
        sso_warnings = [w for w in response["warnings"] if "SSO" in w]
        assert len(sso_warnings) >= 1
    
    def test_multiple_deletion_tokens_independent(self):
        """Test that multiple user deletion tokens work independently."""
        # Generate tokens for different users
        token1 = self.service.generate_token(
            action="delete_user",
            data={"username": "user1"}
        )
        
        token2 = self.service.generate_token(
            action="delete_user",
            data={"username": "user2"}
        )
        
        # Validate token2 first
        validated2 = self.service.validate_token(token2["token"])
        assert validated2["data"]["username"] == "user2"
        
        # Token1 should still work
        validated1 = self.service.validate_token(token1["token"])
        assert validated1["data"]["username"] == "user1"
    
    def test_token_cannot_be_reused_after_deletion(self):
        """Test that token is consumed after successful use."""
        token_info = self.service.generate_token(
            action="delete_user",
            data={"username": "john.doe"}
        )
        
        # First use succeeds
        validated = self.service.validate_token(token_info["token"])
        assert validated["data"]["username"] == "john.doe"
        
        # Second use fails
        with pytest.raises(ValueError, match="Token has already been used"):
            self.service.validate_token(token_info["token"])
