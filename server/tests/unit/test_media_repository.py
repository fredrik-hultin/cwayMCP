"""Unit tests for MediaRepository.

Focus on critical operations:
- Folder management (create, rename, move, delete)
- File operations (rename, move, delete)
- Download job creation
- Error handling
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.infrastructure.repositories.media_repository import MediaRepository
from src.infrastructure.graphql_client import CwayAPIError


@pytest.fixture
def mock_graphql_client():
    """Create a mock GraphQL client."""
    client = MagicMock()
    client.execute_query = AsyncMock()
    client.execute_mutation = AsyncMock()
    return client


@pytest.fixture
def media_repository(mock_graphql_client):
    """Create a MediaRepository with mocked client."""
    repo = MediaRepository(mock_graphql_client)
    return repo


class TestCreateFolder:
    """Tests for create_folder method."""
    
    @pytest.mark.asyncio
    async def test_create_folder_in_root(self, media_repository, mock_graphql_client):
        """Test creating folder in root directory."""
        folder_name = "New Project Folder"
        description = "Project assets"
        
        mock_response = {
            "createFolder": {
                "id": "folder-new",
                "name": folder_name,
                "parentId": None,
                "description": description,
                "created": "2024-01-01T00:00:00Z"
            }
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await media_repository.create_folder(folder_name, None, description)
        
        assert result["id"] == "folder-new"
        assert result["name"] == folder_name
        assert result["parentId"] is None
        assert result["description"] == description
    
    @pytest.mark.asyncio
    async def test_create_folder_in_parent(self, media_repository, mock_graphql_client):
        """Test creating subfolder within parent folder."""
        folder_name = "Subfolder"
        parent_id = "folder-parent"
        
        mock_response = {
            "createFolder": {
                "id": "folder-sub",
                "name": folder_name,
                "parentId": parent_id,
                "description": None,
                "created": "2024-01-01T00:00:00Z"
            }
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await media_repository.create_folder(folder_name, parent_id)
        
        assert result["parentId"] == parent_id
        assert result["name"] == folder_name
    
    @pytest.mark.asyncio
    async def test_create_folder_empty_result(self, media_repository, mock_graphql_client):
        """Test creating folder with empty result."""
        mock_graphql_client.execute_mutation.return_value = {}
        
        result = await media_repository.create_folder("Test")
        
        assert result == {}


class TestRenameFile:
    """Tests for rename_file method."""
    
    @pytest.mark.asyncio
    async def test_rename_file_success(self, media_repository, mock_graphql_client):
        """Test successful file rename."""
        file_id = "file-123"
        new_name = "updated-logo.png"
        
        mock_response = {
            "renameFile": {
                "id": file_id,
                "name": new_name,
                "updated": "2024-01-02T00:00:00Z"
            }
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await media_repository.rename_file(file_id, new_name)
        
        assert result["id"] == file_id
        assert result["name"] == new_name
        assert "updated" in result
    
    @pytest.mark.asyncio
    async def test_rename_file_empty_result(self, media_repository, mock_graphql_client):
        """Test renaming file with empty result."""
        mock_graphql_client.execute_mutation.return_value = {}
        
        result = await media_repository.rename_file("nonexistent", "new-name.txt")
        
        assert result == {}


class TestRenameFolder:
    """Tests for rename_folder method."""
    
    @pytest.mark.asyncio
    async def test_rename_folder_success(self, media_repository, mock_graphql_client):
        """Test successful folder rename."""
        folder_id = "folder-123"
        new_name = "Renamed Folder"
        
        mock_response = {
            "renameFolder": {
                "id": folder_id,
                "name": new_name,
                "updated": "2024-01-02T00:00:00Z"
            }
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await media_repository.rename_folder(folder_id, new_name)
        
        assert result["id"] == folder_id
        assert result["name"] == new_name
    
    @pytest.mark.asyncio
    async def test_rename_folder_empty_result(self, media_repository, mock_graphql_client):
        """Test renaming folder with empty result."""
        mock_graphql_client.execute_mutation.return_value = {}
        
        result = await media_repository.rename_folder("folder-123", "New Name")
        
        assert result == {}


class TestMoveFiles:
    """Tests for move_files method - batch operation."""
    
    @pytest.mark.asyncio
    async def test_move_files_success_all(self, media_repository, mock_graphql_client):
        """Test moving all files successfully."""
        file_ids = ["file-1", "file-2", "file-3"]
        target_folder = "folder-target"
        
        mock_response = {
            "moveFiles": {
                "success": True,
                "movedCount": 3,
                "failedCount": 0
            }
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await media_repository.move_files(file_ids, target_folder)
        
        assert result["success"] is True
        assert result["movedCount"] == 3
        assert result["failedCount"] == 0
    
    @pytest.mark.asyncio
    async def test_move_files_partial_success(self, media_repository, mock_graphql_client):
        """Test moving files with some failures."""
        file_ids = ["file-1", "file-2", "file-invalid"]
        target_folder = "folder-target"
        
        mock_response = {
            "moveFiles": {
                "success": True,
                "movedCount": 2,
                "failedCount": 1
            }
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await media_repository.move_files(file_ids, target_folder)
        
        assert result["movedCount"] == 2
        assert result["failedCount"] == 1
    
    @pytest.mark.asyncio
    async def test_move_files_single_file(self, media_repository, mock_graphql_client):
        """Test moving single file (edge case)."""
        file_ids = ["file-1"]
        target_folder = "folder-target"
        
        mock_response = {
            "moveFiles": {
                "success": True,
                "movedCount": 1,
                "failedCount": 0
            }
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await media_repository.move_files(file_ids, target_folder)
        
        assert result["movedCount"] == 1
    
    @pytest.mark.asyncio
    async def test_move_files_empty_result(self, media_repository, mock_graphql_client):
        """Test moving files with empty result returns default values."""
        mock_graphql_client.execute_mutation.return_value = {}
        
        result = await media_repository.move_files(["file-1"], "folder-target")
        
        assert result["success"] is False
        assert result["movedCount"] == 0


class TestDeleteFile:
    """Tests for delete_file method."""
    
    @pytest.mark.asyncio
    async def test_delete_file_success(self, media_repository, mock_graphql_client):
        """Test successful file deletion."""
        file_id = "file-old"
        
        mock_response = {
            "deleteFile": True
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await media_repository.delete_file(file_id)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_delete_file_not_found(self, media_repository, mock_graphql_client):
        """Test deleting non-existent file."""
        mock_response = {
            "deleteFile": False
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await media_repository.delete_file("nonexistent")
        
        assert result is False


class TestDeleteFolder:
    """Tests for delete_folder method."""
    
    @pytest.mark.asyncio
    async def test_delete_empty_folder(self, media_repository, mock_graphql_client):
        """Test deleting empty folder."""
        folder_id = "folder-empty"
        
        mock_response = {
            "deleteFolder": True
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await media_repository.delete_folder(folder_id, force=False)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_delete_folder_force(self, media_repository, mock_graphql_client):
        """Test force deleting non-empty folder."""
        folder_id = "folder-nonempty"
        
        mock_response = {
            "deleteFolder": True
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await media_repository.delete_folder(folder_id, force=True)
        
        assert result is True
        
        # Verify force parameter was passed
        call_args = mock_graphql_client.execute_mutation.call_args
        assert call_args[0][1]["force"] is True
    
    @pytest.mark.asyncio
    async def test_delete_folder_not_empty_without_force(self, media_repository, mock_graphql_client):
        """Test error when trying to delete non-empty folder without force."""
        folder_id = "folder-nonempty"
        
        mock_response = {
            "deleteFolder": False
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await media_repository.delete_folder(folder_id, force=False)
        
        assert result is False


class TestDownloadOperations:
    """Tests for download job creation methods."""
    
    @pytest.mark.asyncio
    async def test_download_folder_contents(self, media_repository, mock_graphql_client):
        """Test creating download job for folder."""
        folder_id = "folder-123"
        zip_name = "project-files"
        
        # Mock get_folder_items call
        mock_graphql_client.execute_query.return_value = {
            "itemsForFolder": {
                "items": [
                    {"id": "file-1", "name": "doc.pdf", "type": "FILE"},
                    {"id": "file-2", "name": "image.png", "type": "FILE"}
                ],
                "totalHits": 2
            }
        }
        
        # Mock createDownloadJob mutation
        mock_graphql_client.execute_mutation.return_value = {
            "createDownloadJob": "job-abc-123"
        }
        
        result = await media_repository.download_folder_contents(folder_id, zip_name)
        
        assert result == "job-abc-123"
    


class TestGetFolderTree:
    """Tests for get_folder_tree method."""
    
    @pytest.mark.asyncio
    async def test_get_folder_tree_nested(self, media_repository, mock_graphql_client):
        """Test getting nested folder structure."""
        mock_response = {
            "tree": [
                {
                    "id": "folder-root",
                    "name": "Root",
                    "children": [
                        {
                            "id": "folder-sub1",
                            "name": "Subfolder 1"
                        },
                        {
                            "id": "folder-sub2",
                            "name": "Subfolder 2"
                        }
                    ]
                }
            ]
        }
        mock_graphql_client.execute_query.return_value = mock_response
        
        result = await media_repository.get_folder_tree()
        
        assert len(result) == 1
        assert result[0]["name"] == "Root"
        assert len(result[0]["children"]) == 2
    
    @pytest.mark.asyncio
    async def test_get_folder_tree_empty(self, media_repository, mock_graphql_client):
        """Test getting empty folder tree."""
        mock_graphql_client.execute_query.return_value = {}
        
        result = await media_repository.get_folder_tree()
        
        assert result == []


class TestSearchMediaCenter:
    """Tests for search_media_center method."""
    
    @pytest.mark.asyncio
    async def test_search_media_with_query(self, media_repository, mock_graphql_client):
        """Test searching media with query."""
        query_text = "logo"
        
        mock_response = {
            "itemsForOrganisation": {
                "items": [
                    {"id": "file-1", "name": "logo.png", "type": "FILE"},
                    {"id": "file-2", "name": "logo-alt.svg", "type": "FILE"}
                ],
                "totalHits": 2,
                "page": 0
            }
        }
        mock_graphql_client.execute_query.return_value = mock_response
        
        result = await media_repository.search_media_center(query_text=query_text)
        
        assert len(result["items"]) == 2
        assert result["total_hits"] == 2
        assert all("logo" in f["name"].lower() for f in result["items"])
    
    @pytest.mark.asyncio
    async def test_search_media_in_folder(self, media_repository, mock_graphql_client):
        """Test searching within specific folder."""
        folder_id = "folder-123"
        
        mock_response = {
            "itemsForFolder": {
                "items": [
                    {"id": "file-1", "name": "doc.pdf", "type": "FILE"}
                ],
                "totalHits": 1,
                "page": 0
            }
        }
        mock_graphql_client.execute_query.return_value = mock_response
        
        result = await media_repository.search_media_center(query_text=None, folder_id=folder_id)
        
        assert len(result["items"]) == 1
        assert result["total_hits"] == 1
    
    @pytest.mark.asyncio
    async def test_search_media_with_limit(self, media_repository, mock_graphql_client):
        """Test search with custom limit."""
        mock_response = {
            "itemsForOrganisation": {
                "items": [],
                "totalHits": 0,
                "page": 0
            }
        }
        mock_graphql_client.execute_query.return_value = mock_response
        
        await media_repository.search_media_center(query_text="test", limit=10)
        
        # Verify limit was passed in paging
        call_args = mock_graphql_client.execute_query.call_args
        assert call_args[0][1]["paging"]["pageSize"] == 10


class TestErrorHandling:
    """Tests for error handling across MediaRepository."""
    
    @pytest.mark.asyncio
    async def test_create_folder_permission_error(self, media_repository, mock_graphql_client):
        """Test handling permission errors."""
        mock_graphql_client.execute_mutation.side_effect = Exception("Permission denied")
        
        with pytest.raises(CwayAPIError, match="Failed to create folder"):
            await media_repository.create_folder("Test Folder")
    
    @pytest.mark.asyncio
    async def test_move_files_network_error(self, media_repository, mock_graphql_client):
        """Test handling network errors."""
        mock_graphql_client.execute_mutation.side_effect = Exception("Network timeout")
        
        with pytest.raises(CwayAPIError, match="Failed to move files"):
            await media_repository.move_files(["file-1"], "folder-target")
    
    @pytest.mark.asyncio
    async def test_search_error_propagation(self, media_repository, mock_graphql_client):
        """Test that search errors are properly wrapped."""
        mock_graphql_client.execute_query.side_effect = Exception("Search service error")
        
        with pytest.raises(CwayAPIError, match="Failed to search media center"):
            await media_repository.search_media_center(query_text="test")
