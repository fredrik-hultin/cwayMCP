"""Integration tests for the Cway MCP server."""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any, Dict

import pytest

from src.presentation.mcp_server import CwayMCPServer
from src.domain.entities import Project, User
from src.infrastructure.graphql_client import CwayAPIError


@pytest.fixture
def mock_graphql_client() -> AsyncMock:
    """Create a mock GraphQL client."""
    client = AsyncMock()
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    client.get_schema = AsyncMock(return_value="type Query { projects: [Project] }")
    return client


@pytest.fixture
def sample_project() -> Project:
    """Create a sample project for testing."""
    return Project(
        id="proj-123",
        name="Test Project",
        description="A test project",
        status="active",
        created_at=datetime(2023, 1, 1, 12, 0, 0),
        updated_at=datetime(2023, 1, 2, 12, 0, 0)
    )


@pytest.fixture
def sample_user() -> User:
    """Create a sample user for testing."""
    return User(
        id="user-123",
        email="test@example.com",
        name="Test User",
        role="admin",
        created_at=datetime(2023, 1, 1, 12, 0, 0),
        updated_at=datetime(2023, 1, 2, 12, 0, 0)
    )


class TestCwayMCPServer:
    """Test the CwayMCPServer class."""
    
    def test_server_initialization(self) -> None:
        """Test that the server initializes correctly."""
        server = CwayMCPServer()
        
        assert server.server.name == "cway-mcp-server"
        assert server.graphql_client is None
        assert server.project_use_cases is None
        assert server.user_use_cases is None
        
    @patch('src.presentation.mcp_server.CwayGraphQLClient')
    @patch('src.presentation.mcp_server.GraphQLProjectRepository')
    @patch('src.presentation.mcp_server.GraphQLUserRepository')
    @patch('src.presentation.mcp_server.ProjectUseCases')
    @patch('src.presentation.mcp_server.UserUseCases')
    async def test_ensure_initialized(
        self, 
        mock_user_cases: MagicMock,
        mock_project_cases: MagicMock,
        mock_user_repo: MagicMock,
        mock_project_repo: MagicMock,
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
        mock_project_repo.assert_called_once_with(mock_client_instance)
        mock_user_repo.assert_called_once_with(mock_client_instance)
        
        # Verify use cases were created
        mock_project_cases.assert_called_once()
        mock_user_cases.assert_called_once()
        
        # Verify server state
        assert server.graphql_client == mock_client_instance
        assert server.project_use_cases is not None
        assert server.user_use_cases is not None
        
    @patch('src.presentation.mcp_server.CwayGraphQLClient')
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


class TestMCPHandlers:
    """Test MCP handler methods."""
    
    @pytest.fixture
    async def server_with_mocks(self) -> CwayMCPServer:
        """Create server with mocked dependencies."""
        server = CwayMCPServer()
        
        # Mock GraphQL client
        server.graphql_client = AsyncMock()
        server.graphql_client.get_schema.return_value = "schema { query: Query }"
        
        # Mock use cases
        server.project_use_cases = AsyncMock()
        server.user_use_cases = AsyncMock()
        
        return server
    
    async def test_list_resources(self, server_with_mocks: CwayMCPServer) -> None:
        """Test listing resources."""
        # Access the registered handler through the server
        handlers = server_with_mocks.server._resource_handlers
        list_handler = handlers.get("list")
        assert list_handler is not None
        
        result = await list_handler()
        
        assert len(result.resources) == 3
        assert result.resources[0].uri == "cway://projects"
        assert result.resources[0].name == "Cway Projects"
        assert result.resources[1].uri == "cway://users"
        assert result.resources[1].name == "Cway Users"
        assert result.resources[2].uri == "cway://schema"
        assert result.resources[2].name == "GraphQL Schema"
        
    async def test_read_resource_projects(
        self, 
        server_with_mocks: CwayMCPServer,
        sample_project: Project
    ) -> None:
        """Test reading projects resource."""
        server_with_mocks.project_use_cases.list_projects.return_value = [sample_project]
        
        # Access the registered handler
        handlers = server_with_mocks.server._resource_handlers
        read_handler = handlers.get("read")
        assert read_handler is not None
        
        result = await read_handler("cway://projects")
        
        assert len(result.contents) == 1
        content = result.contents[0].text
        assert "Test Project" in content
        assert "proj-123" in content
        assert "active" in content
        
    async def test_read_resource_users(
        self, 
        server_with_mocks: CwayMCPServer,
        sample_user: User
    ) -> None:
        """Test reading users resource."""
        server_with_mocks.user_use_cases.list_users.return_value = [sample_user]
        
        handlers = server_with_mocks.server._resource_handlers
        read_handler = handlers.get("read")
        assert read_handler is not None
        
        result = await read_handler("cway://users")
        
        assert len(result.contents) == 1
        content = result.contents[0].text
        assert "Test User" in content
        assert "test@example.com" in content
        assert "admin" in content
        
    async def test_read_resource_schema(self, server_with_mocks: CwayMCPServer) -> None:
        """Test reading schema resource."""
        handlers = server_with_mocks.server._resource_handlers
        read_handler = handlers.get("read")
        assert read_handler is not None
        
        result = await read_handler("cway://schema")
        
        assert len(result.contents) == 1
        content = result.contents[0].text
        assert "schema { query: Query }" in content
        
    async def test_read_resource_not_found(self, server_with_mocks: CwayMCPServer) -> None:
        """Test reading unknown resource."""
        handlers = server_with_mocks.server._resource_handlers
        read_handler = handlers.get("read")
        assert read_handler is not None
        
        result = await read_handler("cway://unknown")
        
        assert len(result.contents) == 1
        content = result.contents[0].text
        assert "Resource not found: cway://unknown" in content
        
    async def test_read_resource_error_handling(self, server_with_mocks: CwayMCPServer) -> None:
        """Test error handling in resource reading."""
        server_with_mocks.project_use_cases.list_projects.side_effect = Exception("API Error")
        
        handlers = server_with_mocks.server._resource_handlers
        read_handler = handlers.get("read")
        assert read_handler is not None
        
        result = await read_handler("cway://projects")
        
        assert len(result.contents) == 1
        content = result.contents[0].text
        assert "Error: API Error" in content
        
    async def test_list_tools(self, server_with_mocks: CwayMCPServer) -> None:
        """Test listing available tools."""
        handlers = server_with_mocks.server._tool_handlers
        list_handler = handlers.get("list")
        assert list_handler is not None
        
        result = await list_handler()
        
        assert len(result.tools) == 8
        tool_names = [tool.name for tool in result.tools]
        expected_tools = [
            "list_projects", "get_project", "create_project", "update_project",
            "list_users", "get_user", "get_user_by_email", "create_user"
        ]
        for tool_name in expected_tools:
            assert tool_name in tool_names


class TestToolExecution:
    """Test tool execution functionality."""
    
    @pytest.fixture
    async def server_with_mocks(self) -> CwayMCPServer:
        """Create server with mocked dependencies."""
        server = CwayMCPServer()
        
        # Mock use cases
        server.project_use_cases = AsyncMock()
        server.user_use_cases = AsyncMock()
        
        return server
    
    async def test_execute_list_projects(
        self, 
        server_with_mocks: CwayMCPServer,
        sample_project: Project
    ) -> None:
        """Test executing list_projects tool."""
        server_with_mocks.project_use_cases.list_projects.return_value = [sample_project]
        
        result = await server_with_mocks._execute_tool("list_projects", {})
        
        assert "projects" in result
        assert len(result["projects"]) == 1
        assert result["projects"][0]["id"] == "proj-123"
        assert result["projects"][0]["name"] == "Test Project"
        
    async def test_execute_get_project(
        self, 
        server_with_mocks: CwayMCPServer,
        sample_project: Project
    ) -> None:
        """Test executing get_project tool."""
        server_with_mocks.project_use_cases.get_project.return_value = sample_project
        
        result = await server_with_mocks._execute_tool("get_project", {"project_id": "proj-123"})
        
        assert "project" in result
        assert result["project"]["id"] == "proj-123"
        assert result["project"]["name"] == "Test Project"
        
    async def test_execute_get_project_not_found(self, server_with_mocks: CwayMCPServer) -> None:
        """Test executing get_project tool when project not found."""
        server_with_mocks.project_use_cases.get_project.return_value = None
        
        result = await server_with_mocks._execute_tool("get_project", {"project_id": "invalid"})
        
        assert result["project"] is None
        assert "Project not found" in result["message"]
        
    async def test_execute_create_project(
        self, 
        server_with_mocks: CwayMCPServer,
        sample_project: Project
    ) -> None:
        """Test executing create_project tool."""
        server_with_mocks.project_use_cases.create_project.return_value = sample_project
        
        result = await server_with_mocks._execute_tool(
            "create_project", 
            {"name": "Test Project", "description": "A test project", "status": "active"}
        )
        
        assert "project" in result
        assert result["project"]["name"] == "Test Project"
        assert "Project created successfully" in result["message"]
        
    async def test_execute_update_project(
        self, 
        server_with_mocks: CwayMCPServer,
        sample_project: Project
    ) -> None:
        """Test executing update_project tool."""
        server_with_mocks.project_use_cases.update_project.return_value = sample_project
        
        result = await server_with_mocks._execute_tool(
            "update_project", 
            {"project_id": "proj-123", "name": "Updated Project"}
        )
        
        assert "project" in result
        assert result["project"]["id"] == "proj-123"
        assert "Project updated successfully" in result["message"]
        
    async def test_execute_update_project_not_found(self, server_with_mocks: CwayMCPServer) -> None:
        """Test executing update_project tool when project not found."""
        server_with_mocks.project_use_cases.update_project.return_value = None
        
        result = await server_with_mocks._execute_tool(
            "update_project", 
            {"project_id": "invalid", "name": "Updated"}
        )
        
        assert result["project"] is None
        assert "Project not found" in result["message"]
        
    async def test_execute_list_users(
        self, 
        server_with_mocks: CwayMCPServer,
        sample_user: User
    ) -> None:
        """Test executing list_users tool."""
        server_with_mocks.user_use_cases.list_users.return_value = [sample_user]
        
        result = await server_with_mocks._execute_tool("list_users", {})
        
        assert "users" in result
        assert len(result["users"]) == 1
        assert result["users"][0]["email"] == "test@example.com"
        
    async def test_execute_get_user(
        self, 
        server_with_mocks: CwayMCPServer,
        sample_user: User
    ) -> None:
        """Test executing get_user tool."""
        server_with_mocks.user_use_cases.get_user.return_value = sample_user
        
        result = await server_with_mocks._execute_tool("get_user", {"user_id": "user-123"})
        
        assert "user" in result
        assert result["user"]["id"] == "user-123"
        assert result["user"]["email"] == "test@example.com"
        
    async def test_execute_get_user_not_found(self, server_with_mocks: CwayMCPServer) -> None:
        """Test executing get_user tool when user not found."""
        server_with_mocks.user_use_cases.get_user.return_value = None
        
        result = await server_with_mocks._execute_tool("get_user", {"user_id": "invalid"})
        
        assert result["user"] is None
        assert "User not found" in result["message"]
        
    async def test_execute_get_user_by_email(
        self, 
        server_with_mocks: CwayMCPServer,
        sample_user: User
    ) -> None:
        """Test executing get_user_by_email tool."""
        server_with_mocks.user_use_cases.get_user_by_email.return_value = sample_user
        
        result = await server_with_mocks._execute_tool(
            "get_user_by_email", 
            {"email": "test@example.com"}
        )
        
        assert "user" in result
        assert result["user"]["email"] == "test@example.com"
        
    async def test_execute_get_user_by_email_not_found(self, server_with_mocks: CwayMCPServer) -> None:
        """Test executing get_user_by_email tool when user not found."""
        server_with_mocks.user_use_cases.get_user_by_email.return_value = None
        
        result = await server_with_mocks._execute_tool(
            "get_user_by_email", 
            {"email": "invalid@example.com"}
        )
        
        assert result["user"] is None
        assert "User not found" in result["message"]
        
    async def test_execute_create_user(
        self, 
        server_with_mocks: CwayMCPServer,
        sample_user: User
    ) -> None:
        """Test executing create_user tool."""
        server_with_mocks.user_use_cases.create_user.return_value = sample_user
        
        result = await server_with_mocks._execute_tool(
            "create_user", 
            {"email": "test@example.com", "name": "Test User", "role": "admin"}
        )
        
        assert "user" in result
        assert result["user"]["email"] == "test@example.com"
        assert "User created successfully" in result["message"]
        
    async def test_execute_unknown_tool(self, server_with_mocks: CwayMCPServer) -> None:
        """Test executing unknown tool raises error."""
        with pytest.raises(ValueError, match="Unknown tool: unknown_tool"):
            await server_with_mocks._execute_tool("unknown_tool", {})


class TestCallTool:
    """Test the call_tool handler."""
    
    @pytest.fixture
    async def server_with_mocks(self) -> CwayMCPServer:
        """Create server with mocked dependencies."""
        server = CwayMCPServer()
        server.graphql_client = AsyncMock()
        server.project_use_cases = AsyncMock()
        server.user_use_cases = AsyncMock()
        return server
    
    async def test_call_tool_success(
        self, 
        server_with_mocks: CwayMCPServer,
        sample_project: Project
    ) -> None:
        """Test successful tool call."""
        server_with_mocks.project_use_cases.list_projects.return_value = [sample_project]
        
        # Access the call handler
        handlers = server_with_mocks.server._tool_handlers
        call_handler = handlers.get("call")
        assert call_handler is not None
        
        result = await call_handler("list_projects", {})
        
        assert not result.isError
        assert len(result.content) == 1
        
        # Parse the result content
        content_text = result.content[0].text
        assert "projects" in content_text
        
    async def test_call_tool_with_none_arguments(
        self, 
        server_with_mocks: CwayMCPServer,
        sample_project: Project
    ) -> None:
        """Test tool call with None arguments."""
        server_with_mocks.project_use_cases.list_projects.return_value = [sample_project]
        
        handlers = server_with_mocks.server._tool_handlers
        call_handler = handlers.get("call")
        assert call_handler is not None
        
        result = await call_handler("list_projects", None)
        
        assert not result.isError
        assert len(result.content) == 1
        
    async def test_call_tool_error_handling(self, server_with_mocks: CwayMCPServer) -> None:
        """Test error handling in tool call."""
        server_with_mocks.project_use_cases.list_projects.side_effect = Exception("API Error")
        
        handlers = server_with_mocks.server._tool_handlers
        call_handler = handlers.get("call")
        assert call_handler is not None
        
        result = await call_handler("list_projects", {})
        
        assert result.isError
        assert len(result.content) == 1
        assert "Error: API Error" in result.content[0].text


class TestServerLifecycle:
    """Test server lifecycle methods."""
    
    @patch('src.presentation.mcp_server.CwayGraphQLClient')
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
        
    @patch('src.presentation.mcp_server.asyncio.run')
    @patch.object(CwayMCPServer, 'run')
    def test_main_function(self, mock_run: MagicMock, mock_asyncio_run: MagicMock) -> None:
        """Test main function creates and runs server."""
        from src.presentation.mcp_server import main
        
        main()
        
        mock_asyncio_run.assert_called_once()
        # Verify a server instance was created (run method was called)
        args, _ = mock_asyncio_run.call_args
        assert callable(args[0])  # Should be server.run() coroutine