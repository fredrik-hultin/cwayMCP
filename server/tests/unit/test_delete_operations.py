"""Unit tests for DELETE operation prepare/confirm handlers."""
import pytest
from unittest.mock import AsyncMock, Mock, patch

from src.application.delete_operations import (
    prepare_delete_file,
    confirm_delete_file,
    prepare_delete_folder,
    confirm_delete_folder,
    prepare_delete_share,
    confirm_delete_share
)
from src.infrastructure.confirmation_token_manager import ConfirmationTokenManager


class TestDeleteFileOperations:
    """Tests for delete_file prepare/confirm pattern."""
    
    @pytest.fixture
    def token_manager(self):
        """Create fresh token manager."""
        return ConfirmationTokenManager()
    
    @pytest.fixture
    def mock_media_repo(self):
        """Create mock media repository."""
        repo = Mock()
        repo.get_file = AsyncMock()
        repo.delete_file = AsyncMock()
        return repo
    
    @pytest.mark.asyncio
    async def test_prepare_delete_file_basic(self, token_manager, mock_media_repo):
        """Test preparing to delete a file."""
        # Setup mock file
        mock_file = Mock()
        mock_file.id = "file-123"
        mock_file.name = "test.pdf"
        mock_file.size = 1024
        mock_file.content_type = "application/pdf"
        mock_file.created_at = "2024-01-01T00:00:00Z"
        mock_file.is_shared = False
        mock_file.reference_count = 0
        mock_media_repo.get_file.return_value = mock_file
        
        # Prepare delete
        result = await prepare_delete_file(
            file_id="file-123",
            media_repo=mock_media_repo,
            token_manager=token_manager
        )
        
        # Verify
        assert "preview" in result
        assert "confirmation_token" in result
        assert result["preview"]["file_name"] == "test.pdf"
        assert result["preview"]["file_size"] == 1024
        assert isinstance(result["confirmation_token"], str)
        
        # Verify token was created
        token = token_manager.get_token(result["confirmation_token"])
        assert token is not None
        assert token.operation == "delete_file"
        assert token.arguments["file_id"] == "file-123"
    
    @pytest.mark.asyncio
    async def test_prepare_delete_file_with_warnings(self, token_manager, mock_media_repo):
        """Test prepare shows warnings for shared files."""
        # Setup mock file with warnings
        mock_file = Mock()
        mock_file.id = "file-123"
        mock_file.name = "shared.pdf"
        mock_file.size = 2048
        mock_file.content_type = "application/pdf"
        mock_file.created_at = "2024-01-01T00:00:00Z"
        mock_file.is_shared = True
        mock_file.reference_count = 3
        mock_media_repo.get_file.return_value = mock_file
        
        # Prepare delete
        result = await prepare_delete_file(
            file_id="file-123",
            media_repo=mock_media_repo,
            token_manager=token_manager
        )
        
        # Verify warnings
        assert "warnings" in result["preview"]
        warnings = result["preview"]["warnings"]
        assert any("shared" in w.lower() for w in warnings)
        assert any("3" in w and "referenced" in w.lower() for w in warnings)
    
    @pytest.mark.asyncio
    async def test_confirm_delete_file_success(self, token_manager, mock_media_repo):
        """Test confirming file deletion with valid token."""
        # Create token
        token_id = token_manager.create_token(
            operation="delete_file",
            arguments={"file_id": "file-123"},
            preview_data={"file_name": "test.pdf"}
        )
        
        # Confirm delete
        result = await confirm_delete_file(
            confirmation_token=token_id,
            file_id="file-123",
            media_repo=mock_media_repo,
            token_manager=token_manager
        )
        
        # Verify
        assert result["success"] is True
        assert result["file_id"] == "file-123"
        mock_media_repo.delete_file.assert_called_once_with("file-123")
        
        # Verify token was invalidated
        assert token_manager.get_token(token_id) is None
    
    @pytest.mark.asyncio
    async def test_confirm_delete_file_invalid_token(self, token_manager, mock_media_repo):
        """Test confirmation fails with invalid token."""
        with pytest.raises(ValueError, match="Invalid or expired"):
            await confirm_delete_file(
                confirmation_token="fake-token",
                file_id="file-123",
                media_repo=mock_media_repo,
                token_manager=token_manager
            )
        
        # Verify delete was NOT called
        mock_media_repo.delete_file.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_confirm_delete_file_mismatched_file_id(self, token_manager, mock_media_repo):
        """Test confirmation fails when file_id doesn't match token."""
        # Create token for different file
        token_id = token_manager.create_token(
            operation="delete_file",
            arguments={"file_id": "file-123"},
            preview_data={}
        )
        
        # Try to confirm with different file_id
        with pytest.raises(ValueError, match="Invalid or expired"):
            await confirm_delete_file(
                confirmation_token=token_id,
                file_id="file-999",  # Wrong file!
                media_repo=mock_media_repo,
                token_manager=token_manager
            )
        
        # Verify delete was NOT called
        mock_media_repo.delete_file.assert_not_called()


class TestDeleteFolderOperations:
    """Tests for delete_folder prepare/confirm pattern."""
    
    @pytest.fixture
    def token_manager(self):
        return ConfirmationTokenManager()
    
    @pytest.fixture
    def mock_media_repo(self):
        repo = Mock()
        repo.get_folder = AsyncMock()
        repo.delete_folder = AsyncMock()
        return repo
    
    @pytest.mark.asyncio
    async def test_prepare_delete_folder_empty(self, token_manager, mock_media_repo):
        """Test preparing to delete empty folder."""
        mock_folder = Mock()
        mock_folder.id = "folder-123"
        mock_folder.name = "Empty Folder"
        mock_folder.item_count = 0
        mock_folder.created_at = "2024-01-01T00:00:00Z"
        mock_media_repo.get_folder.return_value = mock_folder
        
        result = await prepare_delete_folder(
            folder_id="folder-123",
            force=False,
            media_repo=mock_media_repo,
            token_manager=token_manager
        )
        
        assert result["preview"]["folder_name"] == "Empty Folder"
        assert result["preview"]["item_count"] == 0
        assert len(result["preview"]["warnings"]) == 0
    
    @pytest.mark.asyncio
    async def test_prepare_delete_folder_with_items(self, token_manager, mock_media_repo):
        """Test preparing to delete folder with items requires force."""
        mock_folder = Mock()
        mock_folder.id = "folder-123"
        mock_folder.name = "Full Folder"
        mock_folder.item_count = 5
        mock_folder.created_at = "2024-01-01T00:00:00Z"
        mock_media_repo.get_folder.return_value = mock_folder
        
        result = await prepare_delete_folder(
            folder_id="folder-123",
            force=False,
            media_repo=mock_media_repo,
            token_manager=token_manager
        )
        
        warnings = result["preview"]["warnings"]
        assert any("5 items" in w for w in warnings)
        assert any("force=true" in w.lower() for w in warnings)


class TestDeleteShareOperations:
    """Tests for delete_share prepare/confirm pattern."""
    
    @pytest.fixture
    def token_manager(self):
        return ConfirmationTokenManager()
    
    @pytest.fixture
    def mock_share_repo(self):
        repo = Mock()
        repo.get_share = AsyncMock()
        repo.delete_share = AsyncMock()
        return repo
    
    @pytest.mark.asyncio
    async def test_prepare_delete_share(self, token_manager, mock_share_repo):
        """Test preparing to delete a share."""
        mock_share = Mock()
        mock_share.id = "share-123"
        mock_share.name = "Project Files"
        mock_share.file_count = 3
        mock_share.download_count = 10
        mock_share.created_at = "2024-01-01T00:00:00Z"
        mock_share_repo.get_share.return_value = mock_share
        
        result = await prepare_delete_share(
            share_id="share-123",
            share_repo=mock_share_repo,
            token_manager=token_manager
        )
        
        assert result["preview"]["share_name"] == "Project Files"
        assert result["preview"]["file_count"] == 3
        assert result["preview"]["download_count"] == 10
    
    @pytest.mark.asyncio
    async def test_confirm_delete_share_success(self, token_manager, mock_share_repo):
        """Test confirming share deletion."""
        token_id = token_manager.create_token(
            operation="delete_share",
            arguments={"share_id": "share-123"},
            preview_data={}
        )
        
        result = await confirm_delete_share(
            confirmation_token=token_id,
            share_id="share-123",
            share_repo=mock_share_repo,
            token_manager=token_manager
        )
        
        assert result["success"] is True
        mock_share_repo.delete_share.assert_called_once_with("share-123")
