"""
Integration tests for artwork MCP tools following TDD approach.
"""
import pytest
from unittest.mock import AsyncMock
from src.presentation.cway_mcp_server import CwayMCPServer


@pytest.fixture
def mock_graphql_client():
    """Create a mock GraphQL client."""
    client = AsyncMock()
    client.execute_query = AsyncMock()
    client.execute_mutation = AsyncMock()
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


class TestGetArtwork:
    """Test get_artwork tool."""
    
    @pytest.mark.asyncio
    async def test_get_artwork_success(self, mcp_server, mock_graphql_client):
        """Test getting an artwork by ID."""
        # Arrange
        artwork_id = "artwork-uuid-123"
        mock_artwork = {
            "id": artwork_id,
            "name": "Test Artwork",
            "description": "A test artwork",
            "state": "IN_PROGRESS",
            "revisions": []
        }
        mcp_server.project_repo.get_artwork.return_value = mock_artwork
        
        # Act
        result = await mcp_server._execute_tool("get_artwork", {"artwork_id": artwork_id})
        
        # Assert
        assert "artwork" in result
        assert result["artwork"]["id"] == artwork_id
        assert result["artwork"]["name"] == "Test Artwork"
        mcp_server.project_repo.get_artwork.assert_called_once_with(artwork_id)
        
    @pytest.mark.asyncio
    async def test_get_artwork_not_found(self, mcp_server, mock_graphql_client):
        """Test getting a non-existent artwork."""
        # Arrange
        mcp_server.project_repo.get_artwork.return_value = None
        
        # Act
        result = await mcp_server._execute_tool("get_artwork", {"artwork_id": "nonexistent"})
        
        # Assert
        assert result["artwork"] is None
        assert "message" in result


class TestCreateArtwork:
    """Test create_artwork tool."""
    
    @pytest.mark.asyncio
    async def test_create_artwork_success(self, mcp_server, mock_graphql_client):
        """Test creating a new artwork."""
        # Arrange
        project_id = "project-123"
        artwork_name = "New Artwork"
        mock_artwork = {
            "id": "artwork-new-123",
            "name": artwork_name,
            "state": "NOT_STARTED"
        }
        mcp_server.project_repo.create_artwork.return_value = mock_artwork
        
        # Act
        result = await mcp_server._execute_tool("create_artwork", {
            "project_id": project_id,
            "name": artwork_name,
            "description": "Test description"
        })
        
        # Assert
        assert "artwork" in result
        assert result["artwork"]["name"] == artwork_name
        assert "success" in result
        assert result["success"] is True
        mcp_server.project_repo.create_artwork.assert_called_once_with(
            project_id, artwork_name, "Test description"
        )
        
    @pytest.mark.asyncio
    async def test_create_artwork_without_description(self, mcp_server, mock_graphql_client):
        """Test creating artwork without optional description."""
        # Arrange
        project_id = "project-123"
        artwork_name = "New Artwork"
        mock_artwork = {
            "id": "artwork-new-123",
            "name": artwork_name,
            "state": "NOT_STARTED"
        }
        mcp_server.project_repo.create_artwork.return_value = mock_artwork
        
        # Act
        result = await mcp_server._execute_tool("create_artwork", {
            "project_id": project_id,
            "name": artwork_name
        })
        
        # Assert
        assert "artwork" in result
        assert result["success"] is True
        mcp_server.project_repo.create_artwork.assert_called_once_with(
            project_id, artwork_name, None
        )


class TestApproveArtwork:
    """Test approve_artwork tool."""
    
    @pytest.mark.asyncio
    async def test_approve_artwork_success(self, mcp_server, mock_graphql_client):
        """Test approving an artwork."""
        # Arrange
        artwork_id = "artwork-123"
        mock_artwork = {
            "id": artwork_id,
            "name": "Test Artwork",
            "state": "APPROVED"
        }
        mcp_server.project_repo.approve_artwork.return_value = mock_artwork
        
        # Act
        result = await mcp_server._execute_tool("approve_artwork", {"artwork_id": artwork_id})
        
        # Assert
        assert "artwork" in result
        assert result["artwork"]["state"] == "APPROVED"
        assert "success" in result
        assert result["success"] is True
        mcp_server.project_repo.approve_artwork.assert_called_once_with(artwork_id)
        
    @pytest.mark.asyncio
    async def test_approve_artwork_not_found(self, mcp_server, mock_graphql_client):
        """Test approving a non-existent artwork."""
        # Arrange
        mcp_server.project_repo.approve_artwork.return_value = None
        
        # Act
        result = await mcp_server._execute_tool("approve_artwork", {"artwork_id": "nonexistent"})
        
        # Assert
        assert "artwork" in result
        assert result["artwork"] is None
        assert result["success"] is False


class TestRejectArtwork:
    """Test reject_artwork tool."""
    
    @pytest.mark.asyncio
    async def test_reject_artwork_with_reason(self, mcp_server, mock_graphql_client):
        """Test rejecting an artwork with a reason."""
        # Arrange
        artwork_id = "artwork-123"
        reason = "Quality issues"
        mock_artwork = {
            "id": artwork_id,
            "name": "Test Artwork",
            "state": "REJECTED"
        }
        mcp_server.project_repo.reject_artwork.return_value = mock_artwork
        
        # Act
        result = await mcp_server._execute_tool("reject_artwork", {
            "artwork_id": artwork_id,
            "reason": reason
        })
        
        # Assert
        assert "artwork" in result
        assert result["artwork"]["state"] == "REJECTED"
        assert "success" in result
        assert result["success"] is True
        mcp_server.project_repo.reject_artwork.assert_called_once_with(artwork_id, reason)
        
    @pytest.mark.asyncio
    async def test_reject_artwork_without_reason(self, mcp_server, mock_graphql_client):
        """Test rejecting an artwork without a reason."""
        # Arrange
        artwork_id = "artwork-123"
        mock_artwork = {
            "id": artwork_id,
            "name": "Test Artwork",
            "state": "REJECTED"
        }
        mcp_server.project_repo.reject_artwork.return_value = mock_artwork
        
        # Act
        result = await mcp_server._execute_tool("reject_artwork", {"artwork_id": artwork_id})
        
        # Assert
        assert "artwork" in result
        assert result["artwork"]["state"] == "REJECTED"
        assert result["success"] is True
        mcp_server.project_repo.reject_artwork.assert_called_once_with(artwork_id, None)
