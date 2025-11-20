"""
Comprehensive tests for new Cway GraphQL MCP tools.

Following TDD principles - tests written before implementation.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from typing import List, Dict, Any

from src.presentation.cway_mcp_server import CwayMCPServer
from src.domain.cway_entities import CwayUser, PlannerProject, ProjectState


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
        acceptedTerms=True,
        earlyAccessProgram=False,
        isSSO=False,
        createdAt="2024-01-01T10:00:00Z"
    )


@pytest.fixture
def sample_planner_project() -> PlannerProject:
    """Create a sample planner project for testing."""
    return PlannerProject(
        id="proj-uuid-456",
        name="Test Project",
        state=ProjectState.IN_PROGRESS,
        percentageDone=50.0,
        startDate=datetime(2024, 1, 1),
        endDate=datetime(2024, 12, 31)
    )


@pytest.fixture
async def server_with_mocks() -> CwayMCPServer:
    """Create server with mocked dependencies."""
    server = CwayMCPServer()
    
    # Mock repositories (use correct attribute names from server)
    server.user_repo = AsyncMock()
    server.project_repo = AsyncMock()
    server.system_repo = AsyncMock()
    
    return server


class TestListAllUsersTool:
    """Test the list_all_users MCP tool."""
    
    async def test_list_all_users_success(
        self,
        server_with_mocks: CwayMCPServer,
        sample_cway_user: CwayUser
    ) -> None:
        """Test successful listing of all users."""
        server_with_mocks.user_repo.find_all_users.return_value = [sample_cway_user]
        
        result = await server_with_mocks._execute_tool("list_all_users", {})
        
        assert "users" in result
        assert len(result["users"]) == 1
        assert result["users"][0]["id"] == "user-uuid-123"
        assert result["users"][0]["email"] == "test@example.com"
        assert result["users"][0]["username"] == "testuser"
        
    async def test_list_all_users_empty(
        self,
        server_with_mocks: CwayMCPServer
    ) -> None:
        """Test listing users when none exist."""
        server_with_mocks.user_repo.find_all_users.return_value = []
        
        result = await server_with_mocks._execute_tool("list_all_users", {})
        
        assert "users" in result
        assert len(result["users"]) == 0


class TestGetUsersPageTool:
    """Test the get_users_page MCP tool."""
    
    async def test_get_users_page_default(
        self,
        server_with_mocks: CwayMCPServer,
        sample_cway_user: CwayUser
    ) -> None:
        """Test getting users page with default parameters."""
        server_with_mocks.user_repo.find_users_page.return_value = {
            "users": [sample_cway_user],
            "page": 0,
            "totalHits": 1
        }
        
        result = await server_with_mocks._execute_tool("get_users_page", {})
        
        assert "users" in result
        assert result["page"] == 0
        assert result["totalHits"] == 1
        
    async def test_get_users_page_with_pagination(
        self,
        server_with_mocks: CwayMCPServer,
        sample_cway_user: CwayUser
    ) -> None:
        """Test getting users page with specific page and size."""
        server_with_mocks.user_repo.find_users_page.return_value = {
            "users": [sample_cway_user],
            "page": 2,
            "totalHits": 50
        }
        
        result = await server_with_mocks._execute_tool("get_users_page", {
            "page": 2,
            "size": 10
        })
        
        assert result["page"] == 2
        assert result["totalHits"] == 50


class TestSearchUsersTool:
    """Test the search_users MCP tool."""
    
    async def test_search_users_with_query(
        self,
        server_with_mocks: CwayMCPServer,
        sample_cway_user: CwayUser
    ) -> None:
        """Test searching for users with a query."""
        server_with_mocks.user_repo.search_users.return_value = [sample_cway_user]
        
        result = await server_with_mocks._execute_tool("search_users", {
            "query": "testuser"
        })
        
        assert "users" in result
        assert len(result["users"]) == 1
        assert result["users"][0]["username"] == "testuser"


class TestGetPlannerProjectsTool:
    """Test the get_planner_projects MCP tool."""
    
    async def test_get_planner_projects_success(
        self,
        server_with_mocks: CwayMCPServer,
        sample_planner_project: PlannerProject
    ) -> None:
        """Test successful listing of planner projects."""
        server_with_mocks.project_repo.get_planner_projects.return_value = [
            sample_planner_project
        ]
        
        result = await server_with_mocks._execute_tool("get_planner_projects", {})
        
        assert "projects" in result
        assert len(result["projects"]) == 1
        assert result["projects"][0]["id"] == "proj-uuid-456"
        assert result["projects"][0]["name"] == "Test Project"
        assert result["projects"][0]["state"] == "IN_PROGRESS"
        assert result["projects"][0]["percentageDone"] == 50.0


class TestGetActiveProjectsTool:
    """Test the get_active_projects MCP tool."""
    
    async def test_get_active_projects_success(
        self,
        server_with_mocks: CwayMCPServer,
        sample_planner_project: PlannerProject
    ) -> None:
        """Test getting active projects."""
        server_with_mocks.project_repo.get_active_projects.return_value = [
            sample_planner_project
        ]
        
        result = await server_with_mocks._execute_tool("get_active_projects", {})
        
        assert "projects" in result
        assert len(result["projects"]) == 1
        assert result["projects"][0]["state"] == "IN_PROGRESS"


class TestGetCompletedProjectsTool:
    """Test the get_completed_projects MCP tool."""
    
    async def test_get_completed_projects_success(
        self,
        server_with_mocks: CwayMCPServer
    ) -> None:
        """Test getting completed projects."""
        completed_project = PlannerProject(
            id="proj-completed",
            name="Completed Project",
            state=ProjectState.COMPLETED,
            percentageDone=100.0
        )
        
        server_with_mocks.project_repo.get_completed_projects.return_value = [
            completed_project
        ]
        
        result = await server_with_mocks._execute_tool("get_completed_projects", {})
        
        assert "projects" in result
        assert len(result["projects"]) == 1
        assert result["projects"][0]["state"] == "COMPLETED"
        assert result["projects"][0]["percentageDone"] == 100.0


class TestSearchProjectsTool:
    """Test the search_projects MCP tool."""
    
    async def test_search_projects_with_query(
        self,
        server_with_mocks: CwayMCPServer
    ) -> None:
        """Test searching projects with a query."""
        server_with_mocks.project_repo.search_projects.return_value = {
            "projects": [
                {"id": "proj-1", "name": "Test Project", "description": "A test"}
            ],
            "total_hits": 1
        }
        
        result = await server_with_mocks._execute_tool("search_projects", {
            "query": "test",
            "limit": 10
        })
        
        assert "projects" in result
        assert "total_hits" in result
        assert result["total_hits"] == 1


class TestGetProjectDetailsTool:
    """Test the get_project_details MCP tool."""
    
    async def test_get_project_details_success(
        self,
        server_with_mocks: CwayMCPServer
    ) -> None:
        """Test getting project details by ID."""
        server_with_mocks.project_repo.get_project_by_id.return_value = {
            "id": "proj-123",
            "name": "Test Project",
            "description": "A detailed project",
            "createdAt": "2024-01-01T10:00:00Z"
        }
        
        result = await server_with_mocks._execute_tool("get_project_details", {
            "project_id": "proj-123"
        })
        
        assert "project" in result
        assert result["project"]["id"] == "proj-123"
        assert result["project"]["name"] == "Test Project"
        
    async def test_get_project_details_not_found(
        self,
        server_with_mocks: CwayMCPServer
    ) -> None:
        """Test getting project details when not found."""
        server_with_mocks.project_repo.get_project_by_id.return_value = None
        
        result = await server_with_mocks._execute_tool("get_project_details", {
            "project_id": "nonexistent"
        })
        
        assert result["project"] is None
        assert "not found" in result["message"].lower()


class TestCreateCwayUserTool:
    """Test the create_cway_user MCP tool."""
    
    async def test_create_user_success(
        self,
        server_with_mocks: CwayMCPServer,
        sample_cway_user: CwayUser
    ) -> None:
        """Test successful user creation."""
        server_with_mocks.user_repo.create_user.return_value = sample_cway_user
        
        result = await server_with_mocks._execute_tool("create_cway_user", {
            "email": "test@example.com",
            "username": "testuser",
            "firstName": "Test",
            "lastName": "User"
        })
        
        assert "user" in result
        assert result["user"]["email"] == "test@example.com"
        assert result["user"]["username"] == "testuser"
        assert "successfully" in result["message"].lower()


class TestUpdateUserNameTool:
    """Test the update_user_name MCP tool."""
    
    async def test_update_user_name_success(
        self,
        server_with_mocks: CwayMCPServer,
        sample_cway_user: CwayUser
    ) -> None:
        """Test successful user name update."""
        updated_user = CwayUser(
            id=sample_cway_user.id,
            name="Updated User",
            email=sample_cway_user.email,
            username=sample_cway_user.username,
            firstName="Updated",
            lastName="User",
            enabled=True
        )
        
        server_with_mocks.user_repo.update_user_name.return_value = updated_user
        
        result = await server_with_mocks._execute_tool("update_user_name", {
            "username": "testuser",
            "firstName": "Updated",
            "lastName": "User"
        })
        
        assert "user" in result
        assert result["user"]["firstName"] == "Updated"
        assert result["user"]["lastName"] == "User"


class TestDeleteUserTool:
    """Test the delete_user MCP tool."""
    
    async def test_delete_user_success(
        self,
        server_with_mocks: CwayMCPServer
    ) -> None:
        """Test successful user deletion."""
        server_with_mocks.user_repo.delete_user.return_value = True
        
        result = await server_with_mocks._execute_tool("delete_user", {
            "username": "testuser"
        })
        
        assert result["success"] is True
        assert "deleted" in result["message"].lower()
        
    async def test_delete_user_failure(
        self,
        server_with_mocks: CwayMCPServer
    ) -> None:
        """Test failed user deletion."""
        server_with_mocks.user_repo.delete_user.return_value = False
        
        result = await server_with_mocks._execute_tool("delete_user", {
            "username": "testuser"
        })
        
        assert result["success"] is False
        assert "failed" in result["message"].lower()


class TestCreateCwayProjectTool:
    """Test the create_cway_project MCP tool."""
    
    async def test_create_project_success(
        self,
        server_with_mocks: CwayMCPServer
    ) -> None:
        """Test successful project creation."""
        server_with_mocks.project_repo.create_project.return_value = {
            "id": "proj-new",
            "name": "New Project",
            "description": "A new test project",
            "createdAt": "2024-01-01T10:00:00Z"
        }
        
        result = await server_with_mocks._execute_tool("create_cway_project", {
            "name": "New Project",
            "description": "A new test project"
        })
        
        assert "project" in result
        assert result["project"]["name"] == "New Project"
        assert "successfully" in result["message"].lower()


class TestUpdateCwayProjectTool:
    """Test the update_cway_project MCP tool."""
    
    async def test_update_project_success(
        self,
        server_with_mocks: CwayMCPServer
    ) -> None:
        """Test successful project update."""
        server_with_mocks.project_repo.update_project.return_value = {
            "id": "proj-123",
            "name": "Updated Project",
            "description": "Updated description"
        }
        
        result = await server_with_mocks._execute_tool("update_cway_project", {
            "project_id": "proj-123",
            "name": "Updated Project",
            "description": "Updated description"
        })
        
        assert "project" in result
        assert result["project"]["name"] == "Updated Project"


class TestGetSystemStatusTool:
    """Test the get_system_status MCP tool."""
    
    async def test_get_system_status_connected(
        self,
        server_with_mocks: CwayMCPServer
    ) -> None:
        """Test getting system status when connected."""
        server_with_mocks.system_repo.validate_connection.return_value = True
        
        result = await server_with_mocks._execute_tool("get_system_status", {})
        
        assert result["connected"] is True
        assert result["status"] == "online"


class TestGetLoginInfoTool:
    """Test the get_login_info MCP tool."""
    
    async def test_get_login_info_success(
        self,
        server_with_mocks: CwayMCPServer
    ) -> None:
        """Test getting login info."""
        server_with_mocks.system_repo.get_login_info.return_value = {
            "id": "user-123",
            "email": "current@example.com"
        }
        
        result = await server_with_mocks._execute_tool("get_login_info", {})
        
        assert "login_info" in result
        assert result["login_info"]["email"] == "current@example.com"
        
    async def test_get_login_info_not_available(
        self,
        server_with_mocks: CwayMCPServer
    ) -> None:
        """Test getting login info when not available."""
        server_with_mocks.system_repo.get_login_info.return_value = None
        
        result = await server_with_mocks._execute_tool("get_login_info", {})
        
        assert result["login_info"] is None
        assert "not available" in result["message"].lower()
