"""Integration tests for the actual Cway MCP server."""

import json
from datetime import datetime, date
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any, Dict

import pytest

from src.presentation.cway_mcp_server import CwayMCPServer
from src.domain.cway_entities import PlannerProject, CwayUser, ProjectState
from src.infrastructure.graphql_client import CwayAPIError


@pytest.fixture
def sample_cway_project() -> PlannerProject:
    """Create a sample Cway project for testing."""
    return PlannerProject(
        id="proj-uuid-123",
        name="Sample Project",
        state=ProjectState.IN_PROGRESS,
        percentageDone=0.75,
        startDate=date(2023, 1, 1),
        endDate=date(2023, 12, 31)
    )


@pytest.fixture 
def sample_cway_user() -> CwayUser:
    """Create a sample Cway user for testing."""
    return CwayUser(
        id="user-uuid-123",
        name="Test User",
        email="test@example.com",
        username="testuser",
        firstName="Test",
        lastName="User",
        enabled=True,
        avatar=False,
        isSSO=False,
        acceptedTerms=True,
        earlyAccessProgram=False
    )


class TestCwayMCPServerInitialization:
    """Test CwayMCPServer initialization and setup."""
    
    def test_server_initialization(self) -> None:
        """Test that the server initializes correctly."""
        server = CwayMCPServer()
        
        assert server.server.name == "cway-mcp-server"
        assert server.graphql_client is None
        assert server.user_repo is None
        assert server.project_repo is None
        assert server.system_repo is None
        
    @patch('src.presentation.cway_mcp_server.CwayGraphQLClient')
    @patch('src.presentation.cway_mcp_server.CwayUserRepository')
    @patch('src.presentation.cway_mcp_server.CwayProjectRepository') 
    @patch('src.presentation.cway_mcp_server.CwaySystemRepository')
    async def test_ensure_initialized(
        self,
        mock_system_repo: MagicMock,
        mock_project_repo: MagicMock,
        mock_user_repo: MagicMock,
        mock_client: MagicMock
    ) -> None:
        """Test server initialization with dependencies."""
        # Setup mocks
        mock_client_instance = AsyncMock()
        mock_client.return_value = mock_client_instance
        
        server = CwayMCPServer()
        await server._ensure_initialized()
        
        # Verify client connection
        mock_client.assert_called_once()
        mock_client_instance.connect.assert_called_once()
        
        # Verify repositories were created
        mock_user_repo.assert_called_once_with(mock_client_instance)
        mock_project_repo.assert_called_once_with(mock_client_instance)
        mock_system_repo.assert_called_once_with(mock_client_instance)
        
        # Verify server state
        assert server.graphql_client == mock_client_instance
        assert server.user_repo is not None
        assert server.project_repo is not None
        assert server.system_repo is not None
        
    @patch('src.presentation.cway_mcp_server.CwayGraphQLClient')
    async def test_ensure_initialized_only_once(self, mock_client: MagicMock) -> None:
        """Test that initialization only happens once."""
        mock_client_instance = AsyncMock()
        mock_client.return_value = mock_client_instance
        
        server = CwayMCPServer()
        
        # Call twice
        await server._ensure_initialized()
        await server._ensure_initialized()
        
        # Client should only be created once
        mock_client.assert_called_once()
        mock_client_instance.connect.assert_called_once()


# We'll focus on testing the server business logic instead of MCP internals
# since those are implementation details that may change


class TestServerBusinessLogic:
    """Test the server's core business logic methods."""
    
    @pytest.fixture
    async def server_with_mocks(self) -> CwayMCPServer:
        """Create server with mocked dependencies."""
        server = CwayMCPServer()
        
        # Mock repositories
        server.user_repo = AsyncMock()
        server.project_repo = AsyncMock()
        server.system_repo = AsyncMock()
        
        return server
    
    async def test_execute_list_projects(
        self,
        server_with_mocks: CwayMCPServer,
        sample_cway_project: PlannerProject
    ) -> None:
        """Test executing list_projects tool."""
        server_with_mocks.project_repo.get_planner_projects.return_value = [sample_cway_project]
        
        result = await server_with_mocks._execute_tool("list_projects", {})
        
        assert "projects" in result
        assert len(result["projects"]) == 1
        project_data = result["projects"][0]
        assert project_data["id"] == "proj-uuid-123"
        assert project_data["name"] == "Sample Project"
        assert project_data["state"] == "IN_PROGRESS"
        assert project_data["percentageDone"] == 0.75
        assert project_data["isActive"] is True  # IN_PROGRESS state should be active
        
    async def test_execute_get_project(
        self,
        server_with_mocks: CwayMCPServer,
        sample_cway_project: PlannerProject
    ) -> None:
        """Test executing get_project tool."""
        server_with_mocks.project_repo.find_project_by_id.return_value = sample_cway_project
        
        result = await server_with_mocks._execute_tool("get_project", {"project_id": "proj-uuid-123"})
        
        assert "project" in result
        project_data = result["project"]
        assert project_data["id"] == "proj-uuid-123"
        assert project_data["name"] == "Sample Project"
        assert project_data["state"] == "IN_PROGRESS"
        
    async def test_execute_get_project_not_found(self, server_with_mocks: CwayMCPServer) -> None:
        """Test executing get_project tool when project not found."""
        server_with_mocks.project_repo.find_project_by_id.return_value = None
        
        result = await server_with_mocks._execute_tool("get_project", {"project_id": "invalid"})
        
        assert result["project"] is None
        assert "Project not found" in result["message"]
        
    async def test_execute_get_active_projects(
        self,
        server_with_mocks: CwayMCPServer,
        sample_cway_project: PlannerProject
    ) -> None:
        """Test executing get_active_projects tool."""
        server_with_mocks.project_repo.get_active_projects.return_value = [sample_cway_project]
        
        result = await server_with_mocks._execute_tool("get_active_projects", {})
        
        assert "projects" in result
        assert len(result["projects"]) == 1
        assert result["projects"][0]["name"] == "Sample Project"
        
    async def test_execute_get_completed_projects(self, server_with_mocks: CwayMCPServer) -> None:
        """Test executing get_completed_projects tool."""
        completed_project = PlannerProject(
            id="completed-123",
            name="Completed Project",
            state=ProjectState.COMPLETED,
            percentageDone=1.0,
            startDate=date(2023, 1, 1),
            endDate=date(2023, 6, 30)
        )
        server_with_mocks.project_repo.get_completed_projects.return_value = [completed_project]
        
        result = await server_with_mocks._execute_tool("get_completed_projects", {})
        
        assert "projects" in result
        assert len(result["projects"]) == 1
        assert result["projects"][0]["name"] == "Completed Project"
        
    async def test_execute_list_users(
        self,
        server_with_mocks: CwayMCPServer,
        sample_cway_user: CwayUser
    ) -> None:
        """Test executing list_users tool."""
        server_with_mocks.user_repo.find_all_users.return_value = [sample_cway_user]
        
        result = await server_with_mocks._execute_tool("list_users", {})
        
        assert "users" in result
        assert len(result["users"]) == 1
        user_data = result["users"][0]
        assert user_data["id"] == "user-uuid-123"
        assert user_data["fullName"] == "Test User"
        assert user_data["email"] == "test@example.com"
        assert user_data["enabled"] is True
        
    async def test_execute_get_user(
        self,
        server_with_mocks: CwayMCPServer,
        sample_cway_user: CwayUser
    ) -> None:
        """Test executing get_user tool."""
        server_with_mocks.user_repo.find_user_by_id.return_value = sample_cway_user
        
        result = await server_with_mocks._execute_tool("get_user", {"user_id": "user-uuid-123"})
        
        assert "user" in result
        user_data = result["user"]
        assert user_data["id"] == "user-uuid-123"
        assert user_data["fullName"] == "Test User"
        assert user_data["acceptedTerms"] is True
        assert user_data["earlyAccessProgram"] is False
        
    async def test_execute_get_user_not_found(self, server_with_mocks: CwayMCPServer) -> None:
        """Test executing get_user tool when user not found."""
        server_with_mocks.user_repo.find_user_by_id.return_value = None
        
        result = await server_with_mocks._execute_tool("get_user", {"user_id": "invalid"})
        
        assert result["user"] is None
        assert "User not found" in result["message"]
        
    async def test_execute_find_user_by_email(
        self,
        server_with_mocks: CwayMCPServer,
        sample_cway_user: CwayUser
    ) -> None:
        """Test executing find_user_by_email tool."""
        server_with_mocks.user_repo.find_user_by_email.return_value = sample_cway_user
        
        result = await server_with_mocks._execute_tool(
            "find_user_by_email", 
            {"email": "test@example.com"}
        )
        
        assert "user" in result
        user_data = result["user"]
        assert user_data["email"] == "test@example.com"
        assert user_data["fullName"] == "Test User"
        
    async def test_execute_find_user_by_email_not_found(self, server_with_mocks: CwayMCPServer) -> None:
        """Test executing find_user_by_email tool when user not found."""
        server_with_mocks.user_repo.find_user_by_email.return_value = None
        
        result = await server_with_mocks._execute_tool(
            "find_user_by_email",
            {"email": "invalid@example.com"}
        )
        
        assert result["user"] is None
        assert "User not found" in result["message"]
        
    async def test_execute_get_users_page(
        self,
        server_with_mocks: CwayMCPServer,
        sample_cway_user: CwayUser
    ) -> None:
        """Test executing get_users_page tool."""
        page_data = {
            "users": [sample_cway_user],
            "page": 0,
            "totalHits": 1
        }
        server_with_mocks.user_repo.find_users_page.return_value = page_data
        
        result = await server_with_mocks._execute_tool(
            "get_users_page",
            {"page": 0, "size": 10}
        )
        
        assert "users" in result
        assert len(result["users"]) == 1
        assert result["page"] == 0
        assert result["totalHits"] == 1
        assert result["users"][0]["fullName"] == "Test User"
        
    async def test_execute_get_users_page_with_defaults(
        self,
        server_with_mocks: CwayMCPServer,
        sample_cway_user: CwayUser
    ) -> None:
        """Test executing get_users_page tool with default values."""
        page_data = {
            "users": [sample_cway_user],
            "page": 0,
            "totalHits": 1
        }
        server_with_mocks.user_repo.find_users_page.return_value = page_data
        
        result = await server_with_mocks._execute_tool("get_users_page", {})
        
        # Verify default values were used
        server_with_mocks.user_repo.find_users_page.assert_called_with(page=0, size=10)
        assert "users" in result
        
    async def test_execute_get_system_status(self, server_with_mocks: CwayMCPServer) -> None:
        """Test executing get_system_status tool."""
        server_with_mocks.system_repo.validate_connection.return_value = True
        server_with_mocks.system_repo.get_login_info.return_value = {"user": "admin"}
        
        result = await server_with_mocks._execute_tool("get_system_status", {})
        
        assert "status" in result
        assert result["connected"] is True
        assert "user" in result["login_info"]
        assert "api_url" in result
        
    async def test_execute_unknown_tool(self, server_with_mocks: CwayMCPServer) -> None:
        """Test executing unknown tool raises error."""
        with pytest.raises(ValueError, match="Unknown tool: unknown_tool"):
            await server_with_mocks._execute_tool("unknown_tool", {})


class TestServerLifecycle:
    """Test server lifecycle methods."""
    
    @patch('src.presentation.cway_mcp_server.CwayGraphQLClient')
    async def test_cleanup(self, mock_client: MagicMock) -> None:
        """Test server cleanup."""
        mock_client_instance = AsyncMock()
        mock_client.return_value = mock_client_instance
        
        server = CwayMCPServer()
        await server._ensure_initialized()
        
        # Call cleanup
        await server._cleanup()
        
        # Verify disconnect was called
        mock_client_instance.disconnect.assert_called_once()
        
    async def test_cleanup_without_client(self) -> None:
        """Test cleanup when no client is initialized."""
        server = CwayMCPServer()
        
        # Should not raise error
        await server._cleanup()
        
    @patch('src.presentation.cway_mcp_server.asyncio.run')
    def test_main_function(self, mock_asyncio_run: MagicMock) -> None:
        """Test main function creates and runs server."""
        from src.presentation.cway_mcp_server import main
        
        main()
        
        mock_asyncio_run.assert_called_once()
        # The function should call asyncio.run with a coroutine
        call_args = mock_asyncio_run.call_args[0]
        assert len(call_args) == 1  # Should have one argument
