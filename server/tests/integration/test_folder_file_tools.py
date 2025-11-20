"""
Integration tests for folder and file MCP tools following TDD approach.
"""
import pytest
from unittest.mock import AsyncMock
from src.presentation.cway_mcp_server import CwayMCPServer


@pytest.fixture
def mock_graphql_client():
    """Create a mock GraphQL client."""
    client = AsyncMock()
    client.execute_query = AsyncMock()
    return client


@pytest.fixture
async def mcp_server(mock_graphql_client):
    """Create MCP server instance for testing."""
    server = CwayMCPServer()
    # Mock repositories
    server.project_repo = AsyncMock()
    server.user_repo = AsyncMock()
    server.system_repo = AsyncMock()
    server.indexing_service = AsyncMock()
    server.temporal_kpi_calculator = AsyncMock()
    # Store the mock client for test access
    server.graphql_client = mock_graphql_client
    return server


class TestFolderTree:
    """Test get_folder_tree tool."""
    
    @pytest.mark.asyncio
    async def test_get_folder_tree_success(self, mcp_server, mock_graphql_client):
        """Test getting the complete folder tree."""
        # Arrange
        mock_folders = [
            {
                "id": "folder-1",
                "name": "Root Folder 1",
                "children": []
            },
            {
                "id": "folder-2",
                "name": "Root Folder 2",
                "children": [
                    {
                        "id": "folder-2-1",
                        "name": "Subfolder 1"
                    }
                ]
            }
        ]
        mcp_server.project_repo.get_folder_tree.return_value = mock_folders
        
        # Act
        result = await mcp_server._execute_tool("get_folder_tree", {})
        
        # Assert
        assert "folders" in result
        assert len(result["folders"]) == 2
        assert result["folders"][0]["name"] == "Root Folder 1"
        mcp_server.project_repo.get_folder_tree.assert_called_once()


class TestGetFolder:
    """Test get_folder tool."""
    
    @pytest.mark.asyncio
    async def test_get_folder_success(self, mcp_server, mock_graphql_client):
        """Test getting a specific folder by ID."""
        # Arrange
        folder_id = "folder-uuid-123"
        mock_folder = {
            "id": folder_id,
            "name": "Test Folder",
            "description": "A test folder",
            "parentId": None
        }
        mcp_server.project_repo.get_folder.return_value = mock_folder
        
        # Act
        result = await mcp_server._execute_tool("get_folder", {"folder_id": folder_id})
        
        # Assert
        assert "folder" in result
        assert result["folder"]["id"] == folder_id
        assert result["folder"]["name"] == "Test Folder"
        mcp_server.project_repo.get_folder.assert_called_once_with(folder_id)
        
    @pytest.mark.asyncio
    async def test_get_folder_not_found(self, mcp_server, mock_graphql_client):
        """Test getting a non-existent folder."""
        # Arrange
        mcp_server.project_repo.get_folder.return_value = None
        
        # Act
        result = await mcp_server._execute_tool("get_folder", {"folder_id": "nonexistent"})
        
        # Assert
        assert result["folder"] is None
        assert "message" in result


class TestGetFolderItems:
    """Test get_folder_items tool."""
    
    @pytest.mark.asyncio
    async def test_get_folder_items_success(self, mcp_server, mock_graphql_client):
        """Test getting items in a folder with default pagination."""
        # Arrange
        folder_id = "folder-123"
        mock_result = {
            "items": [
                {"id": "item-1", "name": "Item 1", "type": "ARTWORK"},
                {"id": "item-2", "name": "Item 2", "type": "FILE"}
            ],
            "totalHits": 2,
            "page": 0
        }
        mcp_server.project_repo.get_folder_items.return_value = mock_result
        
        # Act
        result = await mcp_server._execute_tool("get_folder_items", {"folder_id": folder_id})
        
        # Assert
        assert "items" in result
        assert len(result["items"]) == 2
        assert result["total_hits"] == 2
        assert result["page"] == 0
        mcp_server.project_repo.get_folder_items.assert_called_once_with(folder_id, 0, 20)
        
    @pytest.mark.asyncio
    async def test_get_folder_items_with_pagination(self, mcp_server, mock_graphql_client):
        """Test getting items in a folder with custom pagination."""
        # Arrange
        folder_id = "folder-123"
        mock_result = {
            "items": [
                {"id": "item-3", "name": "Item 3", "type": "ARTWORK"}
            ],
            "totalHits": 50,
            "page": 2
        }
        mcp_server.project_repo.get_folder_items.return_value = mock_result
        
        # Act
        result = await mcp_server._execute_tool("get_folder_items", {
            "folder_id": folder_id,
            "page": 2,
            "size": 10
        })
        
        # Assert
        assert "items" in result
        assert len(result["items"]) == 1
        assert result["total_hits"] == 50
        assert result["page"] == 2
        mcp_server.project_repo.get_folder_items.assert_called_once_with(folder_id, 2, 10)
        
    @pytest.mark.asyncio
    async def test_get_folder_items_empty_folder(self, mcp_server, mock_graphql_client):
        """Test getting items from an empty folder."""
        # Arrange
        folder_id = "folder-empty"
        mock_result = {
            "items": [],
            "totalHits": 0,
            "page": 0
        }
        mcp_server.project_repo.get_folder_items.return_value = mock_result
        
        # Act
        result = await mcp_server._execute_tool("get_folder_items", {"folder_id": folder_id})
        
        # Assert
        assert "items" in result
        assert len(result["items"]) == 0
        assert result["total_hits"] == 0
        mcp_server.project_repo.get_folder_items.assert_called_once_with(folder_id, 0, 20)


class TestGetFile:
    """Test get_file tool."""
    
    @pytest.mark.asyncio
    async def test_get_file_success(self, mcp_server, mock_graphql_client):
        """Test getting a file by ID."""
        # Arrange
        file_id = "file-uuid-123"
        mock_file = {
            "id": file_id,
            "filename": "test_document.pdf",
            "size": 1024000,
            "mimeType": "application/pdf",
            "createdAt": "2024-01-01T10:00:00Z"
        }
        mcp_server.project_repo.get_file.return_value = mock_file
        
        # Act
        result = await mcp_server._execute_tool("get_file", {"file_id": file_id})
        
        # Assert
        assert "file" in result
        assert result["file"]["id"] == file_id
        assert result["file"]["filename"] == "test_document.pdf"
        mcp_server.project_repo.get_file.assert_called_once_with(file_id)
        
    @pytest.mark.asyncio
    async def test_get_file_not_found(self, mcp_server, mock_graphql_client):
        """Test getting a non-existent file."""
        # Arrange
        mcp_server.project_repo.get_file.return_value = None
        
        # Act
        result = await mcp_server._execute_tool("get_file", {"file_id": "nonexistent"})
        
        # Assert
        assert result["file"] is None
        assert "message" in result
