"""Unit tests for ARCHIVE operation prepare/confirm handlers."""
import pytest
from unittest.mock import AsyncMock, Mock

from src.application.archive_operations import (
    prepare_archive_artwork,
    confirm_archive_artwork
)
from src.infrastructure.confirmation_token_manager import ConfirmationTokenManager


class TestArchiveArtworkOperations:
    """Tests for archive_artwork prepare/confirm pattern."""
    
    @pytest.fixture
    def token_manager(self):
        """Create fresh token manager."""
        return ConfirmationTokenManager()
    
    @pytest.fixture
    def mock_artwork_repo(self):
        """Create mock artwork repository."""
        repo = Mock()
        repo.get_artwork = AsyncMock()
        repo.archive_artwork = AsyncMock()
        return repo
    
    @pytest.mark.asyncio
    async def test_prepare_archive_artwork_basic(self, token_manager, mock_artwork_repo):
        """Test preparing to archive artwork."""
        # Setup mock artwork
        mock_artwork = Mock()
        mock_artwork.id = "artwork-123"
        mock_artwork.name = "Logo Design"
        mock_artwork.status = "IN_PROGRESS"
        mock_artwork.project_id = "project-456"
        mock_artwork.project_name = "Brand Redesign"
        mock_artwork.created_at = "2024-01-01T00:00:00Z"
        mock_artwork_repo.get_artwork.return_value = mock_artwork
        
        # Prepare archive
        result = await prepare_archive_artwork(
            artwork_id="artwork-123",
            artwork_repo=mock_artwork_repo,
            token_manager=token_manager
        )
        
        # Verify
        assert "preview" in result
        assert "confirmation_token" in result
        assert result["preview"]["artwork_name"] == "Logo Design"
        assert result["preview"]["status"] == "IN_PROGRESS"
        assert result["preview"]["project_name"] == "Brand Redesign"
        assert isinstance(result["confirmation_token"], str)
        
        # Verify token was created
        token = token_manager.get_token(result["confirmation_token"])
        assert token is not None
        assert token.operation == "archive_artwork"
        assert token.arguments["artwork_id"] == "artwork-123"
    
    @pytest.mark.asyncio
    async def test_prepare_archive_artwork_in_progress_warning(self, token_manager, mock_artwork_repo):
        """Test prepare shows warning for in-progress artwork."""
        mock_artwork = Mock()
        mock_artwork.id = "artwork-123"
        mock_artwork.name = "Logo Design"
        mock_artwork.status = "IN_PROGRESS"
        mock_artwork.project_id = "project-456"
        mock_artwork.project_name = "Brand Redesign"
        mock_artwork.created_at = "2024-01-01T00:00:00Z"
        mock_artwork_repo.get_artwork.return_value = mock_artwork
        
        result = await prepare_archive_artwork(
            artwork_id="artwork-123",
            artwork_repo=mock_artwork_repo,
            token_manager=token_manager
        )
        
        # Verify warning
        assert "warnings" in result["preview"]
        warnings = result["preview"]["warnings"]
        assert any("in progress" in w.lower() for w in warnings)
    
    @pytest.mark.asyncio
    async def test_prepare_archive_artwork_pending_approval_warning(self, token_manager, mock_artwork_repo):
        """Test prepare shows warning for artwork pending approval."""
        mock_artwork = Mock()
        mock_artwork.id = "artwork-123"
        mock_artwork.name = "Logo Design"
        mock_artwork.status = "PENDING_APPROVAL"
        mock_artwork.project_id = "project-456"
        mock_artwork.project_name = "Brand Redesign"
        mock_artwork.created_at = "2024-01-01T00:00:00Z"
        mock_artwork_repo.get_artwork.return_value = mock_artwork
        
        result = await prepare_archive_artwork(
            artwork_id="artwork-123",
            artwork_repo=mock_artwork_repo,
            token_manager=token_manager
        )
        
        # Verify warning
        warnings = result["preview"]["warnings"]
        assert any("pending approval" in w.lower() for w in warnings)
    
    @pytest.mark.asyncio
    async def test_confirm_archive_artwork_success(self, token_manager, mock_artwork_repo):
        """Test confirming artwork archival with valid token."""
        # Create token
        token_id = token_manager.create_token(
            operation="archive_artwork",
            arguments={"artwork_id": "artwork-123"},
            preview_data={"artwork_name": "Logo Design"}
        )
        
        # Confirm archive
        result = await confirm_archive_artwork(
            confirmation_token=token_id,
            artwork_id="artwork-123",
            artwork_repo=mock_artwork_repo,
            token_manager=token_manager
        )
        
        # Verify
        assert result["success"] is True
        assert result["artwork_id"] == "artwork-123"
        mock_artwork_repo.archive_artwork.assert_called_once_with("artwork-123")
        
        # Verify token was invalidated
        assert token_manager.get_token(token_id) is None
    
    @pytest.mark.asyncio
    async def test_confirm_archive_artwork_invalid_token(self, token_manager, mock_artwork_repo):
        """Test confirmation fails with invalid token."""
        with pytest.raises(ValueError, match="Invalid or expired"):
            await confirm_archive_artwork(
                confirmation_token="fake-token",
                artwork_id="artwork-123",
                artwork_repo=mock_artwork_repo,
                token_manager=token_manager
            )
        
        # Verify archive was NOT called
        mock_artwork_repo.archive_artwork.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_confirm_archive_artwork_mismatched_id(self, token_manager, mock_artwork_repo):
        """Test confirmation fails when artwork_id doesn't match token."""
        # Create token for different artwork
        token_id = token_manager.create_token(
            operation="archive_artwork",
            arguments={"artwork_id": "artwork-123"},
            preview_data={}
        )
        
        # Try to confirm with different artwork_id
        with pytest.raises(ValueError, match="Invalid or expired"):
            await confirm_archive_artwork(
                confirmation_token=token_id,
                artwork_id="artwork-999",  # Wrong artwork!
                artwork_repo=mock_artwork_repo,
                token_manager=token_manager
            )
        
        # Verify archive was NOT called
        mock_artwork_repo.archive_artwork.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_prepare_archive_artwork_completed_no_warning(self, token_manager, mock_artwork_repo):
        """Test prepare does not warn for completed artwork."""
        mock_artwork = Mock()
        mock_artwork.id = "artwork-123"
        mock_artwork.name = "Logo Design"
        mock_artwork.status = "COMPLETED"
        mock_artwork.project_id = "project-456"
        mock_artwork.project_name = "Brand Redesign"
        mock_artwork.created_at = "2024-01-01T00:00:00Z"
        mock_artwork_repo.get_artwork.return_value = mock_artwork
        
        result = await prepare_archive_artwork(
            artwork_id="artwork-123",
            artwork_repo=mock_artwork_repo,
            token_manager=token_manager
        )
        
        # No warnings for completed artwork
        assert len(result["preview"]["warnings"]) == 0
