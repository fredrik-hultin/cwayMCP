"""
Integration tests for project workflow MCP tools following TDD approach.
Tests for close_projects, reopen_projects, and delete_projects.
"""
import pytest
from unittest.mock import AsyncMock
from src.presentation.cway_mcp_server import CwayMCPServer


@pytest.fixture
def mock_graphql_client():
    """Create a mock GraphQL client."""
    client = AsyncMock()
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


class TestCloseProjects:
    """Test close_projects tool."""
    
    @pytest.mark.asyncio
    async def test_close_single_project(self, mcp_server, mock_graphql_client):
        """Test closing a single project."""
        # Arrange
        project_ids = ["project-123"]
        mcp_server.project_repo.close_projects.return_value = True
        
        # Act
        result = await mcp_server._execute_tool("close_projects", {
            "project_ids": project_ids
        })
        
        # Assert
        assert "success" in result
        assert result["success"] is True
        assert "closed_count" in result
        assert result["closed_count"] == 1
        mcp_server.project_repo.close_projects.assert_called_once_with(project_ids, False)
        
    @pytest.mark.asyncio
    async def test_close_multiple_projects(self, mcp_server, mock_graphql_client):
        """Test closing multiple projects."""
        # Arrange
        project_ids = ["project-1", "project-2", "project-3"]
        mcp_server.project_repo.close_projects.return_value = True
        
        # Act
        result = await mcp_server._execute_tool("close_projects", {
            "project_ids": project_ids
        })
        
        # Assert
        assert result["success"] is True
        assert result["closed_count"] == 3
        mcp_server.project_repo.close_projects.assert_called_once_with(project_ids, False)
        
    @pytest.mark.asyncio
    async def test_close_projects_with_force(self, mcp_server, mock_graphql_client):
        """Test force closing projects."""
        # Arrange
        project_ids = ["project-123"]
        mcp_server.project_repo.close_projects.return_value = True
        
        # Act
        result = await mcp_server._execute_tool("close_projects", {
            "project_ids": project_ids,
            "force": True
        })
        
        # Assert
        assert result["success"] is True
        mcp_server.project_repo.close_projects.assert_called_once_with(project_ids, True)
        
    @pytest.mark.asyncio
    async def test_close_projects_failure(self, mcp_server, mock_graphql_client):
        """Test handling of failed project closure."""
        # Arrange
        project_ids = ["project-123"]
        mcp_server.project_repo.close_projects.return_value = False
        
        # Act
        result = await mcp_server._execute_tool("close_projects", {
            "project_ids": project_ids
        })
        
        # Assert
        assert result["success"] is False
        assert "message" in result


class TestReopenProjects:
    """Test reopen_projects tool."""
    
    @pytest.mark.asyncio
    async def test_reopen_single_project(self, mcp_server, mock_graphql_client):
        """Test reopening a single project."""
        # Arrange
        project_ids = ["project-123"]
        mcp_server.project_repo.reopen_projects.return_value = True
        
        # Act
        result = await mcp_server._execute_tool("reopen_projects", {
            "project_ids": project_ids
        })
        
        # Assert
        assert "success" in result
        assert result["success"] is True
        assert "reopened_count" in result
        assert result["reopened_count"] == 1
        mcp_server.project_repo.reopen_projects.assert_called_once_with(project_ids)
        
    @pytest.mark.asyncio
    async def test_reopen_multiple_projects(self, mcp_server, mock_graphql_client):
        """Test reopening multiple projects."""
        # Arrange
        project_ids = ["project-1", "project-2"]
        mcp_server.project_repo.reopen_projects.return_value = True
        
        # Act
        result = await mcp_server._execute_tool("reopen_projects", {
            "project_ids": project_ids
        })
        
        # Assert
        assert result["success"] is True
        assert result["reopened_count"] == 2
        mcp_server.project_repo.reopen_projects.assert_called_once_with(project_ids)
        
    @pytest.mark.asyncio
    async def test_reopen_projects_failure(self, mcp_server, mock_graphql_client):
        """Test handling of failed project reopening."""
        # Arrange
        project_ids = ["project-123"]
        mcp_server.project_repo.reopen_projects.return_value = False
        
        # Act
        result = await mcp_server._execute_tool("reopen_projects", {
            "project_ids": project_ids
        })
        
        # Assert
        assert result["success"] is False
        assert "message" in result


class TestDeleteProjects:
    """Test delete_projects tool."""
    
    @pytest.mark.asyncio
    async def test_delete_single_project(self, mcp_server, mock_graphql_client):
        """Test deleting a single project."""
        # Arrange
        project_ids = ["project-123"]
        mcp_server.project_repo.delete_projects.return_value = True
        
        # Act
        result = await mcp_server._execute_tool("delete_projects", {
            "project_ids": project_ids
        })
        
        # Assert
        assert "success" in result
        assert result["success"] is True
        assert "deleted_count" in result
        assert result["deleted_count"] == 1
        mcp_server.project_repo.delete_projects.assert_called_once_with(project_ids, False)
        
    @pytest.mark.asyncio
    async def test_delete_multiple_projects(self, mcp_server, mock_graphql_client):
        """Test deleting multiple projects."""
        # Arrange
        project_ids = ["project-1", "project-2", "project-3"]
        mcp_server.project_repo.delete_projects.return_value = True
        
        # Act
        result = await mcp_server._execute_tool("delete_projects", {
            "project_ids": project_ids
        })
        
        # Assert
        assert result["success"] is True
        assert result["deleted_count"] == 3
        mcp_server.project_repo.delete_projects.assert_called_once_with(project_ids, False)
        
    @pytest.mark.asyncio
    async def test_delete_projects_with_force(self, mcp_server, mock_graphql_client):
        """Test force deleting projects."""
        # Arrange
        project_ids = ["project-123"]
        mcp_server.project_repo.delete_projects.return_value = True
        
        # Act
        result = await mcp_server._execute_tool("delete_projects", {
            "project_ids": project_ids,
            "force": True
        })
        
        # Assert
        assert result["success"] is True
        mcp_server.project_repo.delete_projects.assert_called_once_with(project_ids, True)
        
    @pytest.mark.asyncio
    async def test_delete_projects_failure(self, mcp_server, mock_graphql_client):
        """Test handling of failed project deletion."""
        # Arrange
        project_ids = ["project-123"]
        mcp_server.project_repo.delete_projects.return_value = False
        
        # Act
        result = await mcp_server._execute_tool("delete_projects", {
            "project_ids": project_ids
        })
        
        # Assert
        assert result["success"] is False
        assert "message" in result
