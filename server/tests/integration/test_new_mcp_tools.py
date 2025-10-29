"""
Integration tests for new MCP tools following TDD approach.
Tests query and mutation tools based on GraphQL schema introspection.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.presentation.cway_mcp_server import CwayMCPServer
from src.infrastructure.cway_repositories import (
    CwayProjectRepository,
    CwayUserRepository,
    CwaySystemRepository
)


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
    # Inject mocked repositories
    server.project_repo = project_repo
    server.user_repo = user_repo
    server.system_repo = system_repo
    # Mock the indexing service and temporal KPI calculator
    server.indexing_service = AsyncMock()
    server.temporal_kpi_calculator = AsyncMock()
    return server


class TestLoginInfoQuery:
    """Test get_login_info MCP tool."""
    
    @pytest.mark.asyncio
    async def test_get_login_info_success(self, mcp_server, mock_graphql_client):
        """Test successful retrieval of login info."""
        # Arrange
        mock_graphql_client.execute_query.return_value = {
            "loginInfo": {
                "username": "test_user",
                "email": "test@example.com",
                "organisation": {
                    "id": "org-123",
                    "name": "Test Org"
                },
                "permissions": ["READ", "WRITE"]
            }
        }
        
        # Act
        result = await mcp_server._execute_tool("get_login_info", {})
        
        # Assert
        assert result is not None
        assert "login_info" in result
        assert result["login_info"]["username"] == "test_user"
        assert result["login_info"]["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_get_login_info_tool_listed(self, mcp_server):
        """Test that get_login_info tool handler exists."""
        # Act
        result = await mcp_server._execute_tool("get_login_info", {})
        
        # Assert - should return login_info key
        assert "login_info" in result


class TestSearchUsersQuery:
    """Test search_users MCP tool."""
    
    @pytest.mark.asyncio
    async def test_search_users_with_query(self, mcp_server, mock_graphql_client):
        """Test searching users with a query string."""
        # Arrange
        mock_graphql_client.execute_query.return_value = {
            "findUsers": [
                {
                    "id": "user-1",
                    "name": "John Doe",
                    "username": "johndoe",
                    "email": "john@example.com",
                    "firstName": "John",
                    "lastName": "Doe",
                    "enabled": True
                },
                {
                    "id": "user-2",
                    "name": "Jane Doe",
                    "username": "janedoe",
                    "email": "jane@example.com",
                    "firstName": "Jane",
                    "lastName": "Doe",
                    "enabled": True
                }
            ]
        }
        
        # Act
        result = await mcp_server._execute_tool("search_users", {"query": "doe"})
        
        # Assert
        assert "users" in result
        assert len(result["users"]) == 2
        assert result["users"][0]["username"] == "johndoe"
    
    @pytest.mark.asyncio
    async def test_search_users_no_results(self, mcp_server, mock_graphql_client):
        """Test searching users with no results."""
        # Arrange
        mock_graphql_client.execute_query.return_value = {
            "findUsers": []
        }
        
        # Act
        result = await mcp_server._execute_tool("search_users", {"query": "nonexistent"})
        
        # Assert
        assert "users" in result
        assert len(result["users"]) == 0


class TestSearchProjectsQuery:
    """Test search_projects MCP tool."""
    
    @pytest.mark.asyncio
    async def test_search_projects_success(self, mcp_server, mock_graphql_client):
        """Test searching projects."""
        # Arrange
        mock_graphql_client.execute_query.return_value = {
            "projects": {
                "items": [
                    {
                        "id": "proj-1",
                        "name": "Test Project 1",
                        "description": "Description 1",
                        "createdAt": "2024-01-01T00:00:00Z"
                    }
                ],
                "totalHits": 1
            }
        }
        
        # Act
        result = await mcp_server._execute_tool("search_projects", {
            "query": "test",
            "limit": 10
        })
        
        # Assert
        assert "projects" in result
        assert len(result["projects"]) == 1
        assert result["total_hits"] == 1


class TestGetProjectByIdQuery:
    """Test get_project_by_id MCP tool for regular projects (not planner)."""
    
    @pytest.mark.asyncio
    async def test_get_project_by_id_success(self, mcp_server, mock_graphql_client):
        """Test getting a project by ID."""
        # Arrange
        project_id = "550e8400-e29b-41d4-a716-446655440000"
        mock_graphql_client.execute_query.return_value = {
            "project": {
                "id": project_id,
                "name": "Test Project",
                "description": "A test project",
                "createdAt": "2024-01-01T00:00:00Z"
            }
        }
        
        # Act
        result = await mcp_server._execute_tool("get_project_by_id", {
            "project_id": project_id
        })
        
        # Assert
        assert "project" in result
        assert result["project"]["id"] == project_id
        assert result["project"]["name"] == "Test Project"
    
    @pytest.mark.asyncio
    async def test_get_project_by_id_not_found(self, mcp_server, mock_graphql_client):
        """Test getting a non-existent project."""
        # Arrange
        mock_graphql_client.execute_query.return_value = {
            "project": None
        }
        
        # Act
        result = await mcp_server._execute_tool("get_project_by_id", {
            "project_id": "nonexistent-id"
        })
        
        # Assert
        assert result["project"] is None


class TestUserMutations:
    """Test user mutation MCP tools."""
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, mcp_server, mock_graphql_client):
        """Test creating a new user."""
        # Arrange
        mock_graphql_client.execute_mutation.return_value = {
            "createUser": {
                "id": "new-user-id",
                "name": "New User",
                "username": "newuser",
                "email": "newuser@example.com",
                "enabled": True
            }
        }
        
        # Act
        result = await mcp_server._execute_tool("create_user", {
            "email": "newuser@example.com",
            "username": "newuser",
            "first_name": "New",
            "last_name": "User"
        })
        
        # Assert
        assert "user" in result
        assert result["user"]["username"] == "newuser"
        assert result["user"]["email"] == "newuser@example.com"
    
    @pytest.mark.asyncio
    async def test_update_user_real_name(self, mcp_server, mock_graphql_client):
        """Test updating user's real name."""
        # Arrange
        mock_graphql_client.execute_mutation.return_value = {
            "setUserRealName": {
                "id": "user-id",
                "username": "testuser",
                "firstName": "Updated",
                "lastName": "Name",
                "name": "Updated Name",
                "email": "testuser@example.com",
                "enabled": True
            }
        }
        
        # Act
        result = await mcp_server._execute_tool("update_user_name", {
            "username": "testuser",
            "first_name": "Updated",
            "last_name": "Name"
        })
        
        # Assert
        assert "user" in result
        assert result["user"]["firstName"] == "Updated"
        assert result["user"]["lastName"] == "Name"
    
    @pytest.mark.asyncio
    async def test_delete_user_success(self, mcp_server, mock_graphql_client):
        """Test deleting a user."""
        # Arrange
        mock_graphql_client.execute_mutation.return_value = {
            "deleteUsers": True
        }
        
        # Act
        result = await mcp_server._execute_tool("delete_user", {
            "username": "userToDelete"
        })
        
        # Assert
        assert result["success"] is True


class TestProjectMutations:
    """Test project mutation MCP tools."""
    
    @pytest.mark.asyncio
    async def test_create_project_success(self, mcp_server, mock_graphql_client):
        """Test creating a new project."""
        # Arrange
        mock_graphql_client.execute_mutation.return_value = {
            "createProject": {
                "id": "new-proj-id",
                "name": "New Project",
                "description": "Test project",
                "createdAt": "2024-01-01T00:00:00Z"
            }
        }
        
        # Act
        result = await mcp_server._execute_tool("create_project", {
            "name": "New Project",
            "description": "Test project"
        })
        
        # Assert
        assert "project" in result
        assert result["project"]["name"] == "New Project"
    
    @pytest.mark.asyncio
    async def test_update_project_success(self, mcp_server, mock_graphql_client):
        """Test updating an existing project."""
        # Arrange
        project_id = "existing-proj-id"
        mock_graphql_client.execute_mutation.return_value = {
            "updateProject": {
                "id": project_id,
                "name": "Updated Project",
                "description": "Updated description"
            }
        }
        
        # Act
        result = await mcp_server._execute_tool("update_project", {
            "project_id": project_id,
            "name": "Updated Project",
            "description": "Updated description"
        })
        
        # Assert
        assert "project" in result
        assert result["project"]["name"] == "Updated Project"
