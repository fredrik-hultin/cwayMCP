"""Simplified integration tests for Cway MCP Server."""

from unittest.mock import AsyncMock, patch
import pytest

from src.presentation.cway_mcp_server import CwayMCPServer
from src.infrastructure.graphql_client import CwayAPIError
from src.domain.cway_entities import ProjectState


class TestCwayMCPServerCore:
    """Test core CwayMCPServer functionality."""
    
    @pytest.fixture
    def server(self) -> CwayMCPServer:
        """Create MCP server for testing."""
        return CwayMCPServer()
    
    @pytest.fixture
    def mock_graphql_client(self) -> AsyncMock:
        """Create mock GraphQL client."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_user_repo(self) -> AsyncMock:
        """Create mock user repository."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_project_repo(self) -> AsyncMock:
        """Create mock project repository."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_system_repo(self) -> AsyncMock:
        """Create mock system repository."""
        return AsyncMock()
    
    @pytest.fixture
    async def initialized_server(self, server: CwayMCPServer, mock_graphql_client: AsyncMock, 
                                 mock_user_repo: AsyncMock, mock_project_repo: AsyncMock, 
                                 mock_system_repo: AsyncMock) -> CwayMCPServer:
        """Create server with initialized dependencies."""
        server.graphql_client = mock_graphql_client
        server.user_repo = mock_user_repo
        server.project_repo = mock_project_repo
        server.system_repo = mock_system_repo
        return server
    
    def test_server_initialization(self, server: CwayMCPServer) -> None:
        """Test server initialization."""
        assert server.server is not None
        assert server.server.name == "cway-mcp-server"
        assert server.graphql_client is None
        assert server.user_repo is None
        assert server.project_repo is None
        assert server.system_repo is None
    
    @pytest.mark.asyncio
    async def test_ensure_initialized(self, server: CwayMCPServer) -> None:
        """Test server initialization."""
        with patch('src.presentation.cway_mcp_server.CwayGraphQLClient') as MockClient:
            with patch('src.presentation.cway_mcp_server.CwayUserRepository') as MockUserRepo:
                with patch('src.presentation.cway_mcp_server.CwayProjectRepository') as MockProjectRepo:
                    with patch('src.presentation.cway_mcp_server.CwaySystemRepository') as MockSystemRepo:
                        
                        mock_client_instance = AsyncMock()
                        MockClient.return_value = mock_client_instance
                        
                        await server._ensure_initialized()
                        
                        assert server.graphql_client == mock_client_instance
                        mock_client_instance.connect.assert_called_once()
                        MockUserRepo.assert_called_once_with(mock_client_instance)
                        MockProjectRepo.assert_called_once_with(mock_client_instance)
                        MockSystemRepo.assert_called_once_with(mock_client_instance)
    
    @pytest.mark.asyncio
    async def test_execute_tool_list_projects(self, initialized_server: CwayMCPServer, mock_project_repo: AsyncMock) -> None:
        """Test list_projects tool execution."""
        from src.domain.cway_entities import PlannerProject
        
        # Mock projects data
        mock_projects = [
            PlannerProject(
                id="proj-1",
                name="Test Project 1",
                state=ProjectState.IN_PROGRESS,
                percentageDone=50.0
            ),
            PlannerProject(
                id="proj-2", 
                name="Test Project 2",
                state=ProjectState.COMPLETED,
                percentageDone=100.0
            )
        ]
        mock_project_repo.get_planner_projects.return_value = mock_projects
        
        result = await initialized_server._execute_tool("list_projects", {})
        
        assert "projects" in result
        assert len(result["projects"]) == 2
        assert result["projects"][0]["id"] == "proj-1"
        assert result["projects"][0]["name"] == "Test Project 1"
        assert result["projects"][0]["state"] == "IN_PROGRESS"
        assert result["projects"][0]["isActive"] is True
        assert result["projects"][1]["isCompleted"] is True
        
        mock_project_repo.get_planner_projects.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_tool_get_project_found(self, initialized_server: CwayMCPServer, mock_project_repo: AsyncMock) -> None:
        """Test get_project tool when project exists."""
        from src.domain.cway_entities import PlannerProject
        
        mock_project = PlannerProject(
            id="proj-123",
            name="Found Project",
            state=ProjectState.IN_PROGRESS,
            percentageDone=75.0
        )
        mock_project_repo.find_project_by_id.return_value = mock_project
        
        result = await initialized_server._execute_tool("get_project", {"project_id": "proj-123"})
        
        assert "project" in result
        assert result["project"]["id"] == "proj-123"
        assert result["project"]["name"] == "Found Project"
        assert result["project"]["state"] == "IN_PROGRESS"
        assert result["project"]["percentageDone"] == 75.0
        
        mock_project_repo.find_project_by_id.assert_called_once_with("proj-123")
    
    @pytest.mark.asyncio
    async def test_execute_tool_get_project_not_found(self, initialized_server: CwayMCPServer, mock_project_repo: AsyncMock) -> None:
        """Test get_project tool when project doesn't exist."""
        mock_project_repo.find_project_by_id.return_value = None
        
        result = await initialized_server._execute_tool("get_project", {"project_id": "proj-nonexistent"})
        
        assert result["project"] is None
        assert "message" in result
        assert result["message"] == "Project not found"
    
    @pytest.mark.asyncio
    async def test_execute_tool_list_users(self, initialized_server: CwayMCPServer, mock_user_repo: AsyncMock) -> None:
        """Test list_users tool execution."""
        from src.domain.cway_entities import CwayUser
        
        mock_users = [
            CwayUser(
                id="user-1",
                name="John Doe",
                email="john@example.com",
                username="johndoe",
                firstName="John",
                lastName="Doe"
            ),
            CwayUser(
                id="user-2",
                name="Jane Smith",
                email="jane@example.com", 
                username="janesmith",
                firstName="Jane",
                lastName="Smith"
            )
        ]
        mock_user_repo.find_all_users.return_value = mock_users
        
        result = await initialized_server._execute_tool("list_users", {})
        
        assert "users" in result
        assert len(result["users"]) == 2
        assert result["users"][0]["id"] == "user-1"
        assert result["users"][0]["fullName"] == "John Doe"
        assert result["users"][0]["email"] == "john@example.com"
        assert result["users"][1]["id"] == "user-2"
        
        mock_user_repo.find_all_users.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_tool_get_system_status(self, initialized_server: CwayMCPServer, mock_system_repo: AsyncMock) -> None:
        """Test get_system_status tool execution."""
        mock_system_repo.validate_connection.return_value = True
        mock_system_repo.get_login_info.return_value = {"id": "user-123", "email": "user@example.com"}
        
        with patch('src.presentation.cway_mcp_server.settings') as mock_settings:
            mock_settings.cway_api_url = "https://api.cway.com"
            
            result = await initialized_server._execute_tool("get_system_status", {})
        
        assert "status" in result
        assert result["connected"] is True
        assert result["api_url"] == "https://api.cway.com"
        assert result["login_info"]["id"] == "user-123"
    
    @pytest.mark.asyncio
    async def test_execute_tool_unknown_tool(self, initialized_server: CwayMCPServer) -> None:
        """Test executing unknown tool raises error."""
        with pytest.raises(ValueError, match="Unknown tool"):
            await initialized_server._execute_tool("unknown_tool", {})
    
    @pytest.mark.asyncio
    async def test_server_cleanup(self, server: CwayMCPServer) -> None:
        """Test server cleanup functionality."""
        mock_client = AsyncMock()
        server.graphql_client = mock_client
        
        await server._cleanup()
        
        mock_client.disconnect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_server_cleanup_no_client(self, server: CwayMCPServer) -> None:
        """Test cleanup when no client is set."""
        server.graphql_client = None
        
        # Should not raise exception
        await server._cleanup()