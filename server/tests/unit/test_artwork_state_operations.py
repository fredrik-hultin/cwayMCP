"""Unit tests for artwork state change operation handlers."""
import pytest
from unittest.mock import AsyncMock, Mock

from src.application.artwork_state_operations import (
    prepare_approve_artwork,
    confirm_approve_artwork,
    prepare_reject_artwork,
    confirm_reject_artwork,
    prepare_submit_artwork,
    confirm_submit_artwork,
    prepare_request_changes,
    confirm_request_changes,
    prepare_restore_version,
    confirm_restore_version,
    prepare_bulk_update_status,
    confirm_bulk_update_status
)
from src.infrastructure.confirmation_token_manager import ConfirmationTokenManager


class TestApproveArtwork:
    """Tests for approve_artwork operations."""
    
    @pytest.fixture
    def token_manager(self):
        return ConfirmationTokenManager()
    
    @pytest.fixture
    def mock_artwork_repo(self):
        repo = Mock()
        repo.get_artwork = AsyncMock()
        repo.approve_artwork = AsyncMock()
        return repo
    
    @pytest.mark.asyncio
    async def test_prepare_approve_artwork(self, token_manager, mock_artwork_repo):
        """Test preparing to approve artwork."""
        mock_artwork = Mock()
        mock_artwork.id = "art-123"
        mock_artwork.name = "Logo"
        mock_artwork.status = "PENDING_APPROVAL"
        mock_artwork_repo.get_artwork.return_value = mock_artwork
        
        result = await prepare_approve_artwork(
            artwork_id="art-123",
            artwork_repo=mock_artwork_repo,
            token_manager=token_manager
        )
        
        assert result["preview"]["artwork_name"] == "Logo"
        assert result["preview"]["current_status"] == "PENDING_APPROVAL"
        assert result["preview"]["new_status"] == "APPROVED"
    
    @pytest.mark.asyncio
    async def test_confirm_approve_artwork(self, token_manager, mock_artwork_repo):
        """Test confirming approval."""
        token_id = token_manager.create_token(
            operation="approve_artwork",
            arguments={"artwork_id": "art-123"},
            preview_data={}
        )
        
        result = await confirm_approve_artwork(
            confirmation_token=token_id,
            artwork_id="art-123",
            artwork_repo=mock_artwork_repo,
            token_manager=token_manager
        )
        
        assert result["success"] is True
        mock_artwork_repo.approve_artwork.assert_called_once_with("art-123")


class TestRejectArtwork:
    """Tests for reject_artwork operations."""
    
    @pytest.fixture
    def token_manager(self):
        return ConfirmationTokenManager()
    
    @pytest.fixture
    def mock_artwork_repo(self):
        repo = Mock()
        repo.get_artwork = AsyncMock()
        repo.reject_artwork = AsyncMock()
        return repo
    
    @pytest.mark.asyncio
    async def test_prepare_reject_artwork(self, token_manager, mock_artwork_repo):
        """Test preparing to reject artwork."""
        mock_artwork = Mock()
        mock_artwork.id = "art-123"
        mock_artwork.name = "Logo"
        mock_artwork.status = "PENDING_APPROVAL"
        mock_artwork_repo.get_artwork.return_value = mock_artwork
        
        result = await prepare_reject_artwork(
            artwork_id="art-123",
            reason="Colors don't match brand",
            artwork_repo=mock_artwork_repo,
            token_manager=token_manager
        )
        
        assert result["preview"]["artwork_name"] == "Logo"
        assert result["preview"]["reason"] == "Colors don't match brand"
    
    @pytest.mark.asyncio
    async def test_confirm_reject_artwork(self, token_manager, mock_artwork_repo):
        """Test confirming rejection."""
        token_id = token_manager.create_token(
            operation="reject_artwork",
            arguments={"artwork_id": "art-123", "reason": "Bad colors"},
            preview_data={}
        )
        
        result = await confirm_reject_artwork(
            confirmation_token=token_id,
            artwork_id="art-123",
            reason="Bad colors",
            artwork_repo=mock_artwork_repo,
            token_manager=token_manager
        )
        
        assert result["success"] is True
        mock_artwork_repo.reject_artwork.assert_called_once_with("art-123", "Bad colors")


class TestSubmitArtwork:
    """Tests for submit_artwork_for_review operations."""
    
    @pytest.fixture
    def token_manager(self):
        return ConfirmationTokenManager()
    
    @pytest.fixture
    def mock_artwork_repo(self):
        repo = Mock()
        repo.get_artwork = AsyncMock()
        repo.submit_for_review = AsyncMock()
        return repo
    
    @pytest.mark.asyncio
    async def test_prepare_submit_artwork(self, token_manager, mock_artwork_repo):
        """Test preparing to submit artwork."""
        mock_artwork = Mock()
        mock_artwork.id = "art-123"
        mock_artwork.name = "Logo"
        mock_artwork.status = "IN_PROGRESS"
        mock_artwork_repo.get_artwork.return_value = mock_artwork
        
        result = await prepare_submit_artwork(
            artwork_id="art-123",
            artwork_repo=mock_artwork_repo,
            token_manager=token_manager
        )
        
        assert result["preview"]["current_status"] == "IN_PROGRESS"
        assert result["preview"]["new_status"] == "PENDING_APPROVAL"


class TestRequestChanges:
    """Tests for request_artwork_changes operations."""
    
    @pytest.fixture
    def token_manager(self):
        return ConfirmationTokenManager()
    
    @pytest.fixture
    def mock_artwork_repo(self):
        repo = Mock()
        repo.get_artwork = AsyncMock()
        repo.request_changes = AsyncMock()
        return repo
    
    @pytest.mark.asyncio
    async def test_prepare_request_changes(self, token_manager, mock_artwork_repo):
        """Test preparing to request changes."""
        mock_artwork = Mock()
        mock_artwork.id = "art-123"
        mock_artwork.name = "Logo"
        mock_artwork_repo.get_artwork.return_value = mock_artwork
        
        result = await prepare_request_changes(
            artwork_id="art-123",
            reason="Need higher resolution",
            artwork_repo=mock_artwork_repo,
            token_manager=token_manager
        )
        
        assert result["preview"]["reason"] == "Need higher resolution"


class TestRestoreVersion:
    """Tests for restore_artwork_version operations."""
    
    @pytest.fixture
    def token_manager(self):
        return ConfirmationTokenManager()
    
    @pytest.fixture
    def mock_artwork_repo(self):
        repo = Mock()
        repo.get_artwork = AsyncMock()
        repo.get_version = AsyncMock()
        repo.restore_version = AsyncMock()
        return repo
    
    @pytest.mark.asyncio
    async def test_prepare_restore_version(self, token_manager, mock_artwork_repo):
        """Test preparing to restore version."""
        mock_artwork = Mock()
        mock_artwork.id = "art-123"
        mock_artwork.name = "Logo"
        mock_artwork.current_version = 5
        mock_artwork_repo.get_artwork.return_value = mock_artwork
        
        mock_version = Mock()
        mock_version.version_number = 3
        mock_version.created_at = "2024-01-01"
        mock_artwork_repo.get_version.return_value = mock_version
        
        result = await prepare_restore_version(
            artwork_id="art-123",
            version_id="ver-456",
            artwork_repo=mock_artwork_repo,
            token_manager=token_manager
        )
        
        assert result["preview"]["current_version"] == 5
        assert result["preview"]["restore_to_version"] == 3
        warnings = result["preview"]["warnings"]
        assert any("lose version 4 and 5" in w.lower() for w in warnings)


class TestBulkUpdateStatus:
    """Tests for bulk_update_artwork_status operations."""
    
    @pytest.fixture
    def token_manager(self):
        return ConfirmationTokenManager()
    
    @pytest.fixture
    def mock_artwork_repo(self):
        repo = Mock()
        repo.get_artworks = AsyncMock()
        repo.bulk_update_status = AsyncMock()
        return repo
    
    @pytest.mark.asyncio
    async def test_prepare_bulk_update(self, token_manager, mock_artwork_repo):
        """Test preparing bulk status update."""
        mock_artworks = [
            Mock(id="art-1", name="Logo 1", status="IN_PROGRESS"),
            Mock(id="art-2", name="Logo 2", status="IN_PROGRESS"),
            Mock(id="art-3", name="Logo 3", status="PENDING_APPROVAL")
        ]
        mock_artwork_repo.get_artworks.return_value = mock_artworks
        
        result = await prepare_bulk_update_status(
            artwork_ids=["art-1", "art-2", "art-3"],
            new_status="COMPLETED",
            artwork_repo=mock_artwork_repo,
            token_manager=token_manager
        )
        
        assert result["preview"]["artwork_count"] == 3
        assert result["preview"]["new_status"] == "COMPLETED"
        assert len(result["preview"]["artworks"]) == 3
    
    @pytest.mark.asyncio
    async def test_confirm_bulk_update(self, token_manager, mock_artwork_repo):
        """Test confirming bulk update."""
        token_id = token_manager.create_token(
            operation="bulk_update_status",
            arguments={"artwork_ids": ["art-1", "art-2"], "status": "COMPLETED"},
            preview_data={}
        )
        
        result = await confirm_bulk_update_status(
            confirmation_token=token_id,
            artwork_ids=["art-1", "art-2"],
            status="COMPLETED",
            artwork_repo=mock_artwork_repo,
            token_manager=token_manager
        )
        
        assert result["success"] is True
        assert result["updated_count"] == 2
        mock_artwork_repo.bulk_update_status.assert_called_once()
