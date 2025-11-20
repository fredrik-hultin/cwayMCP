"""
Tests for Phase 3.1: Media Center Management Tools
Tests 6 tools with comprehensive coverage
"""
import pytest
from unittest.mock import AsyncMock
from src.infrastructure.cway_repositories import CwayProjectRepository
from src.infrastructure.graphql_client import CwayAPIError


@pytest.fixture
def mock_graphql_client():
    """Create a mock GraphQL client"""
    mock = AsyncMock()
    mock.execute_query = AsyncMock()
    mock.execute_mutation = AsyncMock()
    return mock


@pytest.fixture
def project_repo(mock_graphql_client):
    """Create a CwayProjectRepository with mocked client"""
    return CwayProjectRepository(mock_graphql_client)


# ========================================
# create_folder Tests
# ========================================

@pytest.mark.asyncio
async def test_create_folder_success(project_repo, mock_graphql_client):
    """Test successful folder creation"""
    mock_folder = {
        "id": "folder-123",
        "name": "My New Folder",
        "description": "Test folder",
        "parentId": None,
        "created": "2024-01-01T10:00:00Z"
    }
    mock_graphql_client.execute_mutation.return_value = {
        "createFolder": mock_folder
    }
    
    result = await project_repo.create_folder("My New Folder", description="Test folder")
    
    assert result["name"] == "My New Folder"
    assert result["id"] == "folder-123"


@pytest.mark.asyncio
async def test_create_folder_with_parent(project_repo, mock_graphql_client):
    """Test creating folder with parent folder"""
    mock_folder = {
        "id": "subfolder-123",
        "name": "Subfolder",
        "parentId": "parent-folder-id",
        "created": "2024-01-01T10:00:00Z"
    }
    mock_graphql_client.execute_mutation.return_value = {
        "createFolder": mock_folder
    }
    
    result = await project_repo.create_folder("Subfolder", parent_folder_id="parent-folder-id")
    
    assert result["parentId"] == "parent-folder-id"
    assert result["name"] == "Subfolder"


@pytest.mark.asyncio
async def test_create_folder_minimal(project_repo, mock_graphql_client):
    """Test creating folder with only name"""
    mock_folder = {"id": "folder-min", "name": "Simple", "parentId": None}
    mock_graphql_client.execute_mutation.return_value = {
        "createFolder": mock_folder
    }
    
    result = await project_repo.create_folder("Simple")
    
    assert result["name"] == "Simple"


@pytest.mark.asyncio
async def test_create_folder_error(project_repo, mock_graphql_client):
    """Test error handling when creating folder"""
    mock_graphql_client.execute_mutation.side_effect = Exception("API error")
    
    with pytest.raises(CwayAPIError, match="Failed to create folder"):
        await project_repo.create_folder("Test")


# ========================================
# rename_file Tests
# ========================================

@pytest.mark.asyncio
async def test_rename_file_success(project_repo, mock_graphql_client):
    """Test successful file rename"""
    mock_file = {
        "id": "file-123",
        "name": "newname.jpg",
        "fileSize": 1024,
        "mimeType": "image/jpeg"
    }
    mock_graphql_client.execute_mutation.return_value = {
        "renameFile": mock_file
    }
    
    result = await project_repo.rename_file("file-123", "newname.jpg")
    
    assert result["name"] == "newname.jpg"
    assert result["id"] == "file-123"


@pytest.mark.asyncio
async def test_rename_file_with_extension(project_repo, mock_graphql_client):
    """Test renaming file with different extension"""
    mock_file = {"id": "file-pdf", "name": "document.pdf", "mimeType": "application/pdf"}
    mock_graphql_client.execute_mutation.return_value = {
        "renameFile": mock_file
    }
    
    result = await project_repo.rename_file("file-pdf", "document.pdf")
    
    assert result["name"] == "document.pdf"


@pytest.mark.asyncio
async def test_rename_file_error(project_repo, mock_graphql_client):
    """Test error handling when renaming file"""
    mock_graphql_client.execute_mutation.side_effect = Exception("File not found")
    
    with pytest.raises(CwayAPIError, match="Failed to rename file"):
        await project_repo.rename_file("file-123", "newname.txt")


# ========================================
# rename_folder Tests
# ========================================

@pytest.mark.asyncio
async def test_rename_folder_success(project_repo, mock_graphql_client):
    """Test successful folder rename"""
    mock_folder = {
        "id": "folder-123",
        "name": "Renamed Folder",
        "description": "Old description",
        "parentId": "parent-id"
    }
    mock_graphql_client.execute_mutation.return_value = {
        "renameFolder": mock_folder
    }
    
    result = await project_repo.rename_folder("folder-123", "Renamed Folder")
    
    assert result["name"] == "Renamed Folder"
    assert result["id"] == "folder-123"


@pytest.mark.asyncio
async def test_rename_folder_preserves_structure(project_repo, mock_graphql_client):
    """Test that folder rename preserves other properties"""
    mock_folder = {
        "id": "folder-abc",
        "name": "New Name",
        "description": "Important folder",
        "parentId": "root"
    }
    mock_graphql_client.execute_mutation.return_value = {
        "renameFolder": mock_folder
    }
    
    result = await project_repo.rename_folder("folder-abc", "New Name")
    
    assert result["description"] == "Important folder"
    assert result["parentId"] == "root"


@pytest.mark.asyncio
async def test_rename_folder_error(project_repo, mock_graphql_client):
    """Test error handling when renaming folder"""
    mock_graphql_client.execute_mutation.side_effect = Exception("Folder not found")
    
    with pytest.raises(CwayAPIError, match="Failed to rename folder"):
        await project_repo.rename_folder("folder-123", "New Name")


# ========================================
# move_files Tests
# ========================================

@pytest.mark.asyncio
async def test_move_files_success(project_repo, mock_graphql_client):
    """Test successful file move"""
    mock_result = {"success": True, "movedCount": 3}
    mock_graphql_client.execute_mutation.return_value = {
        "moveFiles": mock_result
    }
    
    result = await project_repo.move_files(
        ["file1", "file2", "file3"],
        "target-folder"
    )
    
    assert result["success"] is True
    assert result["movedCount"] == 3


@pytest.mark.asyncio
async def test_move_files_single(project_repo, mock_graphql_client):
    """Test moving single file"""
    mock_result = {"success": True, "movedCount": 1}
    mock_graphql_client.execute_mutation.return_value = {
        "moveFiles": mock_result
    }
    
    result = await project_repo.move_files(["file1"], "target-folder")
    
    assert result["movedCount"] == 1


@pytest.mark.asyncio
async def test_move_files_failure(project_repo, mock_graphql_client):
    """Test move files when operation fails"""
    mock_result = {"success": False, "movedCount": 0}
    mock_graphql_client.execute_mutation.return_value = {
        "moveFiles": mock_result
    }
    
    result = await project_repo.move_files(["file1"], "target")
    
    assert result["success"] is False
    assert result["movedCount"] == 0


@pytest.mark.asyncio
async def test_move_files_error(project_repo, mock_graphql_client):
    """Test error handling when moving files"""
    mock_graphql_client.execute_mutation.side_effect = Exception("Permission denied")
    
    with pytest.raises(CwayAPIError, match="Failed to move files"):
        await project_repo.move_files(["file1"], "target")


# ========================================
# delete_file Tests
# ========================================

@pytest.mark.asyncio
async def test_delete_file_success(project_repo, mock_graphql_client):
    """Test successful file deletion"""
    mock_graphql_client.execute_mutation.return_value = {
        "deleteFile": True
    }
    
    result = await project_repo.delete_file("file-123")
    
    assert result is True


@pytest.mark.asyncio
async def test_delete_file_failure(project_repo, mock_graphql_client):
    """Test file deletion when operation fails"""
    mock_graphql_client.execute_mutation.return_value = {
        "deleteFile": False
    }
    
    result = await project_repo.delete_file("file-123")
    
    assert result is False


@pytest.mark.asyncio
async def test_delete_file_error(project_repo, mock_graphql_client):
    """Test error handling when deleting file"""
    mock_graphql_client.execute_mutation.side_effect = Exception("File in use")
    
    with pytest.raises(CwayAPIError, match="Failed to delete file"):
        await project_repo.delete_file("file-123")


# ========================================
# delete_folder Tests
# ========================================

@pytest.mark.asyncio
async def test_delete_folder_success(project_repo, mock_graphql_client):
    """Test successful folder deletion"""
    mock_graphql_client.execute_mutation.return_value = {
        "deleteFolder": True
    }
    
    result = await project_repo.delete_folder("folder-123")
    
    assert result is True


@pytest.mark.asyncio
async def test_delete_folder_with_force(project_repo, mock_graphql_client):
    """Test force delete non-empty folder"""
    mock_graphql_client.execute_mutation.return_value = {
        "deleteFolder": True
    }
    
    result = await project_repo.delete_folder("folder-123", force=True)
    
    assert result is True
    # Verify force parameter was passed
    call_args = mock_graphql_client.execute_mutation.call_args
    assert call_args[0][1]["force"] is True


@pytest.mark.asyncio
async def test_delete_folder_failure(project_repo, mock_graphql_client):
    """Test folder deletion when operation fails"""
    mock_graphql_client.execute_mutation.return_value = {
        "deleteFolder": False
    }
    
    result = await project_repo.delete_folder("folder-123")
    
    assert result is False


@pytest.mark.asyncio
async def test_delete_folder_not_empty_without_force(project_repo, mock_graphql_client):
    """Test deleting non-empty folder without force"""
    mock_graphql_client.execute_mutation.return_value = {
        "deleteFolder": False
    }
    
    result = await project_repo.delete_folder("folder-123", force=False)
    
    assert result is False


@pytest.mark.asyncio
async def test_delete_folder_error(project_repo, mock_graphql_client):
    """Test error handling when deleting folder"""
    mock_graphql_client.execute_mutation.side_effect = Exception("Folder not found")
    
    with pytest.raises(CwayAPIError, match="Failed to delete folder"):
        await project_repo.delete_folder("folder-123")
