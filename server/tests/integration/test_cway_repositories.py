"""Integration tests for Cway repositories."""

from datetime import date
from unittest.mock import AsyncMock, patch
import pytest

from src.infrastructure.cway_repositories import (
    CwayUserRepository, 
    CwayProjectRepository, 
    CwaySystemRepository
)
from src.infrastructure.graphql_client import CwayGraphQLClient, CwayAPIError
from src.domain.cway_entities import CwayUser, PlannerProject, ProjectState


class TestCwayUserRepository:
    """Test CwayUserRepository with mocked GraphQL client."""
    
    @pytest.fixture
    def mock_client(self) -> AsyncMock:
        """Create a mock GraphQL client."""
        return AsyncMock(spec=CwayGraphQLClient)
    
    @pytest.fixture
    def repository(self, mock_client: AsyncMock) -> CwayUserRepository:
        """Create repository with mock client."""
        return CwayUserRepository(mock_client)
    
    @pytest.fixture
    def sample_user_data(self) -> dict:
        """Sample user data from GraphQL response."""
        return {
            "id": "user-123",
            "name": "John Doe",
            "email": "john@example.com",
            "username": "johndoe",
            "firstName": "John",
            "lastName": "Doe",
            "enabled": True,
            "avatar": False,
            "acceptedTerms": True,
            "earlyAccessProgram": False,
            "isSSO": False,
            "createdAt": 1640995200
        }
    
    @pytest.mark.asyncio
    async def test_find_all_users_success(self, repository: CwayUserRepository, mock_client: AsyncMock, sample_user_data: dict) -> None:
        """Test successfully finding all users."""
        mock_client.execute_query.return_value = {
            "findUsers": [sample_user_data]
        }
        
        result = await repository.find_all_users()
        
        assert len(result) == 1
        user = result[0]
        assert isinstance(user, CwayUser)
        assert user.id == sample_user_data["id"]
        assert user.name == sample_user_data["name"]
        assert user.email == sample_user_data["email"]
        assert user.username == sample_user_data["username"]
        assert user.enabled == sample_user_data["enabled"]
        
        # Verify the query was called correctly
        mock_client.execute_query.assert_called_once()
        query_arg = mock_client.execute_query.call_args[0][0]
        assert "findUsers" in query_arg
    
    @pytest.mark.asyncio
    async def test_find_all_users_empty(self, repository: CwayUserRepository, mock_client: AsyncMock) -> None:
        """Test finding users when none exist."""
        mock_client.execute_query.return_value = {"findUsers": []}
        
        result = await repository.find_all_users()
        
        assert result == []
        mock_client.execute_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find_all_users_partial_data(self, repository: CwayUserRepository, mock_client: AsyncMock) -> None:
        """Test finding users with minimal data."""
        minimal_user_data = {
            "id": "user-456",
            "name": "Jane Smith",
            "email": "jane@example.com",
            "username": "janesmith",
            "firstName": "Jane",
            "lastName": "Smith"
            # Missing optional fields - should use defaults
        }
        
        mock_client.execute_query.return_value = {
            "findUsers": [minimal_user_data]
        }
        
        result = await repository.find_all_users()
        
        assert len(result) == 1
        user = result[0]
        assert user.enabled is True  # Default value
        assert user.avatar is False  # Default value
        assert user.acceptedTerms is False  # Default value
    
    @pytest.mark.asyncio
    async def test_find_all_users_api_error(self, repository: CwayUserRepository, mock_client: AsyncMock) -> None:
        """Test handling API errors when finding users."""
        mock_client.execute_query.side_effect = Exception("Network error")
        
        with pytest.raises(CwayAPIError, match="Failed to fetch users"):
            await repository.find_all_users()
    
    @pytest.mark.asyncio
    async def test_find_user_by_id_found(self, repository: CwayUserRepository, mock_client: AsyncMock, sample_user_data: dict) -> None:
        """Test finding a user by ID when it exists."""
        mock_client.execute_query.return_value = {
            "findUsers": [sample_user_data]
        }
        
        result = await repository.find_user_by_id("user-123")
        
        assert result is not None
        assert result.id == "user-123"
        assert result.email == "john@example.com"
    
    @pytest.mark.asyncio
    async def test_find_user_by_id_not_found(self, repository: CwayUserRepository, mock_client: AsyncMock) -> None:
        """Test finding a user by ID when it doesn't exist."""
        mock_client.execute_query.return_value = {"findUsers": []}
        
        result = await repository.find_user_by_id("user-nonexistent")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_find_user_by_email_found(self, repository: CwayUserRepository, mock_client: AsyncMock, sample_user_data: dict) -> None:
        """Test finding a user by email when it exists."""
        mock_client.execute_query.return_value = {
            "findUsers": [sample_user_data]
        }
        
        result = await repository.find_user_by_email("john@example.com")
        
        assert result is not None
        assert result.email == "john@example.com"
        assert result.id == "user-123"
    
    @pytest.mark.asyncio
    async def test_find_user_by_email_case_insensitive(self, repository: CwayUserRepository, mock_client: AsyncMock, sample_user_data: dict) -> None:
        """Test finding a user by email is case insensitive."""
        mock_client.execute_query.return_value = {
            "findUsers": [sample_user_data]
        }
        
        result = await repository.find_user_by_email("JOHN@EXAMPLE.COM")
        
        assert result is not None
        assert result.email == "john@example.com"
    
    @pytest.mark.asyncio
    async def test_find_users_page_success(self, repository: CwayUserRepository, mock_client: AsyncMock, sample_user_data: dict) -> None:
        """Test finding users with pagination."""
        mock_client.execute_query.return_value = {
            "findUsersPage": {
                "users": [sample_user_data],
                "page": 0,
                "totalHits": 1
            }
        }
        
        result = await repository.find_users_page(page=0, size=10)
        
        assert "users" in result
        assert "page" in result
        assert "totalHits" in result
        assert len(result["users"]) == 1
        assert result["page"] == 0
        assert result["totalHits"] == 1
        
        # Verify query was called with correct variables
        mock_client.execute_query.assert_called_once()
        call_args = mock_client.execute_query.call_args
        # Arguments are passed as positional, not keyword args
        variables = call_args[0][1]  # Second argument is variables
        assert variables["page"] == 0
        assert variables["size"] == 10
    
    @pytest.mark.asyncio
    async def test_find_users_page_api_error(self, repository: CwayUserRepository, mock_client: AsyncMock) -> None:
        """Test handling API errors in paginated user search."""
        mock_client.execute_query.side_effect = Exception("API error")
        
        with pytest.raises(CwayAPIError, match="Failed to fetch users page"):
            await repository.find_users_page()


class TestCwayProjectRepository:
    """Test CwayProjectRepository with mocked GraphQL client."""
    
    @pytest.fixture
    def mock_client(self) -> AsyncMock:
        """Create a mock GraphQL client."""
        return AsyncMock(spec=CwayGraphQLClient)
    
    @pytest.fixture
    def repository(self, mock_client: AsyncMock) -> CwayProjectRepository:
        """Create repository with mock client."""
        return CwayProjectRepository(mock_client)
    
    @pytest.fixture
    def sample_project_data(self) -> dict:
        """Sample project data from GraphQL response."""
        return {
            "id": "proj-123",
            "name": "Test Project",
            "state": "IN_PROGRESS",
            "percentageDone": 45.5,
            "startDate": "2024-01-01",
            "endDate": "2024-12-31"
        }
    
    @pytest.mark.asyncio
    async def test_get_planner_projects_success(self, repository: CwayProjectRepository, mock_client: AsyncMock, sample_project_data: dict) -> None:
        """Test successfully getting planner projects."""
        mock_client.execute_query.return_value = {
            "plannerProjects": [sample_project_data]
        }
        
        result = await repository.get_planner_projects()
        
        assert len(result) == 1
        project = result[0]
        assert isinstance(project, PlannerProject)
        assert project.id == sample_project_data["id"]
        assert project.name == sample_project_data["name"]
        assert project.state == ProjectState.IN_PROGRESS
        assert project.percentageDone == 45.5
        assert project.startDate == date(2024, 1, 1)
        assert project.endDate == date(2024, 12, 31)
        
        # Verify the query was called correctly
        mock_client.execute_query.assert_called_once()
        query_arg = mock_client.execute_query.call_args[0][0]
        assert "plannerProjects" in query_arg
    
    @pytest.mark.asyncio
    async def test_get_planner_projects_minimal_data(self, repository: CwayProjectRepository, mock_client: AsyncMock) -> None:
        """Test getting projects with minimal data."""
        minimal_project_data = {
            "id": "proj-456",
            "name": "Minimal Project",
            "state": "PLANNED"
            # Missing optional fields
        }
        
        mock_client.execute_query.return_value = {
            "plannerProjects": [minimal_project_data]
        }
        
        result = await repository.get_planner_projects()
        
        assert len(result) == 1
        project = result[0]
        assert project.percentageDone == 0.0  # Default value
        assert project.startDate is None
        assert project.endDate is None
        assert project.state == ProjectState.PLANNED
    
    @pytest.mark.asyncio
    async def test_get_planner_projects_empty(self, repository: CwayProjectRepository, mock_client: AsyncMock) -> None:
        """Test getting projects when none exist."""
        mock_client.execute_query.return_value = {"plannerProjects": []}
        
        result = await repository.get_planner_projects()
        
        assert result == []
        mock_client.execute_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_planner_projects_api_error(self, repository: CwayProjectRepository, mock_client: AsyncMock) -> None:
        """Test handling API errors when getting projects."""
        mock_client.execute_query.side_effect = Exception("Database error")
        
        with pytest.raises(CwayAPIError, match="Failed to fetch planner projects"):
            await repository.get_planner_projects()
    
    @pytest.mark.asyncio
    async def test_find_project_by_id_found(self, repository: CwayProjectRepository, mock_client: AsyncMock, sample_project_data: dict) -> None:
        """Test finding a project by ID when it exists."""
        mock_client.execute_query.return_value = {
            "plannerProjects": [sample_project_data]
        }
        
        result = await repository.find_project_by_id("proj-123")
        
        assert result is not None
        assert result.id == "proj-123"
        assert result.name == "Test Project"
    
    @pytest.mark.asyncio
    async def test_find_project_by_id_not_found(self, repository: CwayProjectRepository, mock_client: AsyncMock) -> None:
        """Test finding a project by ID when it doesn't exist."""
        mock_client.execute_query.return_value = {"plannerProjects": []}
        
        result = await repository.find_project_by_id("proj-nonexistent")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_projects_by_state(self, repository: CwayProjectRepository, mock_client: AsyncMock) -> None:
        """Test filtering projects by state."""
        projects_data = [
            {"id": "proj-1", "name": "Active Project", "state": "IN_PROGRESS"},
            {"id": "proj-2", "name": "Completed Project", "state": "COMPLETED"},
            {"id": "proj-3", "name": "Another Active", "state": "IN_PROGRESS"}
        ]
        
        mock_client.execute_query.return_value = {
            "plannerProjects": projects_data
        }
        
        result = await repository.get_projects_by_state(ProjectState.IN_PROGRESS)
        
        assert len(result) == 2
        assert all(p.state == ProjectState.IN_PROGRESS for p in result)
        assert result[0].id == "proj-1"
        assert result[1].id == "proj-3"
    
    @pytest.mark.asyncio
    async def test_get_active_projects(self, repository: CwayProjectRepository, mock_client: AsyncMock) -> None:
        """Test getting active projects."""
        projects_data = [
            {"id": "proj-1", "name": "Active Project", "state": "IN_PROGRESS"},
            {"id": "proj-2", "name": "Completed Project", "state": "COMPLETED"}
        ]
        
        mock_client.execute_query.return_value = {
            "plannerProjects": projects_data
        }
        
        result = await repository.get_active_projects()
        
        assert len(result) == 1
        assert result[0].id == "proj-1"
        assert result[0].state == ProjectState.IN_PROGRESS
    
    @pytest.mark.asyncio
    async def test_get_completed_projects(self, repository: CwayProjectRepository, mock_client: AsyncMock) -> None:
        """Test getting completed projects."""
        projects_data = [
            {"id": "proj-1", "name": "Active Project", "state": "IN_PROGRESS"},
            {"id": "proj-2", "name": "Completed Project", "state": "COMPLETED"}
        ]
        
        mock_client.execute_query.return_value = {
            "plannerProjects": projects_data
        }
        
        result = await repository.get_completed_projects()
        
        assert len(result) == 1
        assert result[0].id == "proj-2"
        assert result[0].state == ProjectState.COMPLETED


class TestCwaySystemRepository:
    """Test CwaySystemRepository with mocked GraphQL client."""
    
    @pytest.fixture
    def mock_client(self) -> AsyncMock:
        """Create a mock GraphQL client."""
        return AsyncMock(spec=CwayGraphQLClient)
    
    @pytest.fixture
    def repository(self, mock_client: AsyncMock) -> CwaySystemRepository:
        """Create repository with mock client."""
        return CwaySystemRepository(mock_client)
    
    @pytest.mark.asyncio
    async def test_get_login_info_success(self, repository: CwaySystemRepository, mock_client: AsyncMock) -> None:
        """Test successfully getting login info."""
        login_data = {
            "id": "user-123",
            "email": "user@example.com"
        }
        
        mock_client.execute_query.return_value = {
            "loginInfo": login_data
        }
        
        result = await repository.get_login_info()
        
        assert result == login_data
        mock_client.execute_query.assert_called_once()
        query_arg = mock_client.execute_query.call_args[0][0]
        assert "loginInfo" in query_arg
    
    @pytest.mark.asyncio
    async def test_get_login_info_no_data(self, repository: CwaySystemRepository, mock_client: AsyncMock) -> None:
        """Test getting login info when no data is available."""
        mock_client.execute_query.return_value = {}
        
        result = await repository.get_login_info()
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_login_info_api_error(self, repository: CwaySystemRepository, mock_client: AsyncMock) -> None:
        """Test handling API errors when getting login info."""
        mock_client.execute_query.side_effect = Exception("Auth error")
        
        with patch('src.infrastructure.cway_repositories.logger') as mock_logger:
            result = await repository.get_login_info()
        
        assert result is None
        mock_logger.error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_connection_success(self, repository: CwaySystemRepository, mock_client: AsyncMock) -> None:
        """Test successful connection validation."""
        mock_client.execute_query.return_value = {
            "__typename": "Query"
        }
        
        result = await repository.validate_connection()
        
        assert result is True
        mock_client.execute_query.assert_called_once_with("{ __typename }")
    
    @pytest.mark.asyncio
    async def test_validate_connection_wrong_typename(self, repository: CwaySystemRepository, mock_client: AsyncMock) -> None:
        """Test connection validation with wrong typename."""
        mock_client.execute_query.return_value = {
            "__typename": "Mutation"
        }
        
        result = await repository.validate_connection()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_validate_connection_no_typename(self, repository: CwaySystemRepository, mock_client: AsyncMock) -> None:
        """Test connection validation when no typename is returned."""
        mock_client.execute_query.return_value = {}
        
        result = await repository.validate_connection()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_validate_connection_api_error(self, repository: CwaySystemRepository, mock_client: AsyncMock) -> None:
        """Test connection validation with API error."""
        mock_client.execute_query.side_effect = Exception("Connection failed")
        
        with patch('src.infrastructure.cway_repositories.logger') as mock_logger:
            result = await repository.validate_connection()
        
        assert result is False
        mock_logger.error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_connection_cway_api_error(self, repository: CwaySystemRepository, mock_client: AsyncMock) -> None:
        """Test connection validation with CwayAPIError."""
        mock_client.execute_query.side_effect = CwayAPIError("API unavailable")
        
        result = await repository.validate_connection()
        
        assert result is False