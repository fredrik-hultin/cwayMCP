"""
Integration tests for MCP server handlers to increase coverage.
Tests all tool handlers and resource handlers.
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from src.presentation.cway_mcp_server import CwayMCPServer
from src.infrastructure.cway_repositories import (
    CwayProjectRepository,
    CwayUserRepository,
    CwaySystemRepository
)
from src.domain.cway_entities import PlannerProject, ProjectState, CwayUser
from datetime import datetime


@pytest.fixture
def mock_graphql_client():
    """Create a mock GraphQL client."""
    client = AsyncMock()
    client.execute_query = AsyncMock()
    client.execute_mutation = AsyncMock()
    return client


@pytest.fixture
def project_repo(mock_graphql_client):
    """Create project repository with mocked client."""
    return CwayProjectRepository(mock_graphql_client)


@pytest.fixture
def user_repo(mock_graphql_client):
    """Create user repository with mocked client."""
    return CwayUserRepository(mock_graphql_client)


@pytest.fixture
def system_repo(mock_graphql_client):
    """Create system repository with mocked client."""
    return CwaySystemRepository(mock_graphql_client)


@pytest.fixture
async def mcp_server(project_repo, user_repo, system_repo):
    """Create MCP server instance for testing."""
    server = CwayMCPServer()
    server.project_repo = project_repo
    server.user_repo = user_repo
    server.system_repo = system_repo
    server.indexing_service = AsyncMock()
    server.temporal_kpi_calculator = AsyncMock()
    return server


class TestListProjectsHandler:
    """Test list_projects tool handler."""
    
    @pytest.mark.asyncio
    async def test_list_projects_success(self, mcp_server, mock_graphql_client):
        """Test listing all projects."""
        # Arrange
        mock_graphql_client.execute_query.return_value = {
            "plannerProjects": [
                {
                    "id": "proj-1",
                    "name": "Project 1",
                    "state": "IN_PROGRESS",
                    "percentageDone": 0.5,
                    "startDate": "2024-01-01",
                    "endDate": "2024-12-31"
                }
            ]
        }
        
        # Act
        result = await mcp_server._execute_tool("list_projects", {})
        
        # Assert
        assert "projects" in result
        assert len(result["projects"]) == 1
        assert result["projects"][0]["name"] == "Project 1"
        assert result["projects"][0]["state"] == "IN_PROGRESS"


class TestGetProjectHandler:
    """Test get_project tool handler."""
    
    @pytest.mark.asyncio
    async def test_get_project_found(self, mcp_server, mock_graphql_client):
        """Test getting a project that exists."""
        # Arrange
        mock_graphql_client.execute_query.return_value = {
            "plannerProjects": [
                {
                    "id": "proj-1",
                    "name": "Test Project",
                    "state": "COMPLETED",
                    "percentageDone": 1.0,
                    "startDate": "2024-01-01",
                    "endDate": "2024-12-31"
                }
            ]
        }
        
        # Act
        result = await mcp_server._execute_tool("get_project", {"project_id": "proj-1"})
        
        # Assert
        assert result["project"] is not None
        assert result["project"]["name"] == "Test Project"
        assert result["project"]["state"] == "COMPLETED"
    
    @pytest.mark.asyncio
    async def test_get_project_not_found(self, mcp_server, mock_graphql_client):
        """Test getting a project that doesn't exist."""
        # Arrange
        mock_graphql_client.execute_query.return_value = {
            "plannerProjects": []
        }
        
        # Act
        result = await mcp_server._execute_tool("get_project", {"project_id": "nonexistent"})
        
        # Assert
        assert result["project"] is None
        assert "message" in result


class TestGetActiveProjectsHandler:
    """Test get_active_projects tool handler."""
    
    @pytest.mark.asyncio
    async def test_get_active_projects(self, mcp_server, mock_graphql_client):
        """Test getting active projects."""
        # Arrange
        mock_graphql_client.execute_query.return_value = {
            "plannerProjects": [
                {
                    "id": "proj-1",
                    "name": "Active Project 1",
                    "state": "IN_PROGRESS",
                    "percentageDone": 0.3,
                    "startDate": "2024-01-01",
                    "endDate": "2024-12-31"
                },
                {
                    "id": "proj-2",
                    "name": "Active Project 2",
                    "state": "IN_PROGRESS",
                    "percentageDone": 0.7,
                    "startDate": "2024-02-01",
                    "endDate": "2024-11-30"
                }
            ]
        }
        
        # Act
        result = await mcp_server._execute_tool("get_active_projects", {})
        
        # Assert
        assert "projects" in result
        assert len(result["projects"]) == 2


class TestGetCompletedProjectsHandler:
    """Test get_completed_projects tool handler."""
    
    @pytest.mark.asyncio
    async def test_get_completed_projects(self, mcp_server, mock_graphql_client):
        """Test getting completed projects."""
        # Arrange
        mock_graphql_client.execute_query.return_value = {
            "plannerProjects": [
                {
                    "id": "proj-1",
                    "name": "Completed Project",
                    "state": "COMPLETED",
                    "percentageDone": 1.0,
                    "startDate": "2023-01-01",
                    "endDate": "2023-12-31"
                }
            ]
        }
        
        # Act
        result = await mcp_server._execute_tool("get_completed_projects", {})
        
        # Assert
        assert "projects" in result
        assert len(result["projects"]) == 1


class TestListUsersHandler:
    """Test list_users tool handler."""
    
    @pytest.mark.asyncio
    async def test_list_users(self, mcp_server, mock_graphql_client):
        """Test listing all users."""
        # Arrange
        mock_graphql_client.execute_query.return_value = {
            "findUsers": [
                {
                    "id": "user-1",
                    "name": "John Doe",
                    "email": "john@test.com",
                    "username": "johndoe",
                    "firstName": "John",
                    "lastName": "Doe",
                    "enabled": True,
                    "avatar": False,
                    "acceptedTerms": True,
                    "earlyAccessProgram": False,
                    "isSSO": False
                }
            ]
        }
        
        # Act
        result = await mcp_server._execute_tool("list_users", {})
        
        # Assert
        assert "users" in result
        assert len(result["users"]) == 1
        assert result["users"][0]["username"] == "johndoe"


class TestGetUserHandler:
    """Test get_user tool handler."""
    
    @pytest.mark.asyncio
    async def test_get_user_found(self, mcp_server, mock_graphql_client):
        """Test getting a user that exists."""
        # Arrange
        mock_graphql_client.execute_query.return_value = {
            "findUsers": [
                {
                    "id": "user-1",
                    "name": "John Doe",
                    "email": "john@test.com",
                    "username": "johndoe",
                    "firstName": "John",
                    "lastName": "Doe",
                    "enabled": True,
                    "avatar": False,
                    "acceptedTerms": True,
                    "earlyAccessProgram": False,
                    "isSSO": False,
                    "createdAt": "2024-01-01T00:00:00Z"
                }
            ]
        }
        
        # Act
        result = await mcp_server._execute_tool("get_user", {"user_id": "user-1"})
        
        # Assert
        assert result["user"] is not None
        assert result["user"]["username"] == "johndoe"
    
    @pytest.mark.asyncio
    async def test_get_user_not_found(self, mcp_server, mock_graphql_client):
        """Test getting a user that doesn't exist."""
        # Arrange
        mock_graphql_client.execute_query.return_value = {
            "findUsers": []
        }
        
        # Act
        result = await mcp_server._execute_tool("get_user", {"user_id": "nonexistent"})
        
        # Assert
        assert result["user"] is None


class TestFindUserByEmailHandler:
    """Test find_user_by_email tool handler."""
    
    @pytest.mark.asyncio
    async def test_find_user_by_email_found(self, mcp_server, mock_graphql_client):
        """Test finding a user by email."""
        # Arrange
        mock_graphql_client.execute_query.return_value = {
            "findUsers": [
                {
                    "id": "user-1",
                    "name": "John Doe",
                    "email": "john@test.com",
                    "username": "johndoe",
                    "firstName": "John",
                    "lastName": "Doe",
                    "enabled": True,
                    "avatar": False,
                    "acceptedTerms": True,
                    "earlyAccessProgram": False,
                    "isSSO": False
                }
            ]
        }
        
        # Act
        result = await mcp_server._execute_tool("find_user_by_email", {"email": "john@test.com"})
        
        # Assert
        assert result["user"] is not None
        assert result["user"]["email"] == "john@test.com"
    
    @pytest.mark.asyncio
    async def test_find_user_by_email_not_found(self, mcp_server, mock_graphql_client):
        """Test finding a user that doesn't exist."""
        # Arrange
        mock_graphql_client.execute_query.return_value = {
            "findUsers": []
        }
        
        # Act
        result = await mcp_server._execute_tool("find_user_by_email", {"email": "nonexistent@test.com"})
        
        # Assert
        assert result["user"] is None


class TestGetUsersPageHandler:
    """Test get_users_page tool handler."""
    
    @pytest.mark.asyncio
    async def test_get_users_page(self, mcp_server, mock_graphql_client):
        """Test getting paginated users."""
        # Arrange
        mock_graphql_client.execute_query.return_value = {
            "findUsersPage": {
                "users": [
                    {
                        "id": "user-1",
                        "name": "User 1",
                        "email": "user1@test.com",
                        "username": "user1",
                        "firstName": "User",
                        "lastName": "One",
                        "enabled": True
                    }
                ],
                "page": 0,
                "totalHits": 1
            }
        }
        
        # Act
        result = await mcp_server._execute_tool("get_users_page", {"page": 0, "size": 10})
        
        # Assert
        assert "users" in result
        assert result["page"] == 0
        assert result["totalHits"] == 1


class TestGetSystemStatusHandler:
    """Test get_system_status tool handler."""
    
    @pytest.mark.asyncio
    async def test_get_system_status(self, mcp_server, mock_graphql_client):
        """Test getting system status."""
        # Arrange
        mock_graphql_client.execute_query.side_effect = [
            {"__typename": "Query"},  # validate_connection
            {"loginInfo": {"id": "user-1", "email": "user@test.com"}}  # get_login_info
        ]
        
        # Act
        result = await mcp_server._execute_tool("get_system_status", {})
        
        # Assert
        assert "status" in result
        assert result["connected"] is True
        assert "login_info" in result


class TestUnknownToolHandler:
    """Test unknown tool handling."""
    
    @pytest.mark.asyncio
    async def test_unknown_tool_raises_error(self, mcp_server):
        """Test that unknown tools raise ValueError."""
        # Act & Assert
        with pytest.raises(ValueError, match="Unknown tool"):
            await mcp_server._execute_tool("nonexistent_tool", {})


class TestIndexingTools:
    """Test indexing-related tool handlers."""
    
    @pytest.mark.asyncio
    async def test_index_all_content(self, mcp_server):
        """Test index_all_content tool."""
        # Arrange
        mock_result = MagicMock()
        mock_result.job_id = "job-123"
        mock_result.success = True
        mock_result.message = "Indexed successfully"
        mock_result.documents_indexed = 10
        mock_result.duration_seconds = 5.5
        mock_result.targets_completed = ["target1"]
        mock_result.targets_failed = []
        mock_result.started_at = datetime(2024, 1, 1, 12, 0, 0)
        mock_result.completed_at = datetime(2024, 1, 1, 12, 0, 5)
        
        mcp_server.indexing_service.index_all_content = AsyncMock(return_value=mock_result)
        
        # Act
        result = await mcp_server._execute_tool("index_all_content", {"targets": ["target1"]})
        
        # Assert
        assert "indexing_result" in result
        assert result["indexing_result"]["success"] is True
        assert result["indexing_result"]["documents_indexed"] == 10
    
    @pytest.mark.asyncio
    async def test_quick_backup(self, mcp_server):
        """Test quick_backup tool."""
        # Arrange
        mock_result = MagicMock()
        mock_result.job_id = "backup-123"
        mock_result.success = True
        mock_result.message = "Backup complete"
        mock_result.documents_indexed = 5
        mock_result.duration_seconds = 2.0
        mock_result.started_at = datetime(2024, 1, 1, 12, 0, 0)
        mock_result.completed_at = datetime(2024, 1, 1, 12, 0, 2)
        
        mcp_server.indexing_service.quick_backup = AsyncMock(return_value=mock_result)
        
        # Act
        result = await mcp_server._execute_tool("quick_backup", {})
        
        # Assert
        assert "backup_result" in result
        assert result["backup_result"]["success"] is True
    
    @pytest.mark.asyncio
    async def test_index_project_content(self, mcp_server):
        """Test index_project_content tool."""
        # Arrange
        mock_result = MagicMock()
        mock_result.job_id = "proj-job-123"
        mock_result.success = True
        mock_result.message = "Project indexed"
        mock_result.documents_indexed = 3
        mock_result.duration_seconds = 1.5
        mock_result.targets_completed = ["target1"]
        mock_result.targets_failed = []
        mock_result.started_at = datetime(2024, 1, 1, 12, 0, 0)
        mock_result.completed_at = datetime(2024, 1, 1, 12, 0, 1)
        
        mcp_server.indexing_service.index_project_documents = AsyncMock(return_value=mock_result)
        
        # Act
        result = await mcp_server._execute_tool("index_project_content", {
            "project_id": "proj-123",
            "targets": ["target1"]
        })
        
        # Assert
        assert "project_indexing_result" in result
        assert result["project_indexing_result"]["success"] is True
    
    @pytest.mark.asyncio
    async def test_configure_indexing_target_new(self, mcp_server):
        """Test configuring a new indexing target."""
        # Arrange
        mcp_server.indexing_service.add_target = MagicMock(return_value=True)
        
        # Act
        result = await mcp_server._execute_tool("configure_indexing_target", {
            "name": "new_target",
            "platform": "elasticsearch",
            "description": "Test target",
            "config": {"url": "http://localhost:9200"},
            "enabled": True
        })
        
        # Assert
        assert result["configuration_result"]["success"] is True
        assert result["configuration_result"]["action"] == "created"
    
    @pytest.mark.asyncio
    async def test_configure_indexing_target_update(self, mcp_server):
        """Test updating an existing indexing target."""
        # Arrange
        mcp_server.indexing_service.add_target = MagicMock(return_value=False)
        mcp_server.indexing_service.update_target = MagicMock(return_value=True)
        
        # Act
        result = await mcp_server._execute_tool("configure_indexing_target", {
            "name": "existing_target",
            "platform": "elasticsearch",
            "description": "Updated target"
        })
        
        # Assert
        assert result["configuration_result"]["success"] is True
        assert result["configuration_result"]["action"] == "updated"
    
    @pytest.mark.asyncio
    async def test_get_indexing_job_status_found(self, mcp_server):
        """Test getting indexing job status."""
        # Arrange
        mcp_server.indexing_service.get_job_status = MagicMock(return_value={
            "job_id": "job-123",
            "status": "completed"
        })
        
        # Act
        result = await mcp_server._execute_tool("get_indexing_job_status", {"job_id": "job-123"})
        
        # Assert
        assert result["job_status"] is not None
        assert result["job_status"]["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_get_indexing_job_status_not_found(self, mcp_server):
        """Test getting non-existent job status."""
        # Arrange
        mcp_server.indexing_service.get_job_status = MagicMock(return_value=None)
        
        # Act
        result = await mcp_server._execute_tool("get_indexing_job_status", {"job_id": "nonexistent"})
        
        # Assert
        assert result["job_status"] is None
        assert "message" in result
