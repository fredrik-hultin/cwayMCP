"""Tests for infrastructure GraphQL repositories."""

from datetime import datetime
from unittest.mock import AsyncMock, patch
import pytest

from src.infrastructure.repositories import (
    GraphQLProjectRepository, 
    GraphQLUserRepository,
    _parse_datetime
)
from src.infrastructure.graphql_client import CwayGraphQLClient, CwayAPIError
from src.domain.entities import Project, User


class TestParseDateTime:
    """Test the _parse_datetime utility function."""
    
    def test_parse_datetime_iso_format(self) -> None:
        """Test parsing ISO datetime string."""
        dt_str = "2024-01-15T10:30:00"
        result = _parse_datetime(dt_str)
        expected = datetime(2024, 1, 15, 10, 30, 0)
        assert result == expected
        
    def test_parse_datetime_with_z(self) -> None:
        """Test parsing datetime with Z timezone."""
        dt_str = "2024-01-15T10:30:00Z"
        result = _parse_datetime(dt_str)
        expected = datetime(2024, 1, 15, 10, 30, 0, tzinfo=datetime.fromisoformat("2024-01-15T10:30:00+00:00").tzinfo)
        assert result == expected
        
    def test_parse_datetime_invalid_format(self) -> None:
        """Test parsing invalid datetime string falls back to current time."""
        dt_str = "invalid-datetime"
        
        with patch('src.infrastructure.repositories.datetime') as mock_datetime:
            with patch('src.infrastructure.repositories.logger') as mock_logger:
                mock_now = datetime(2024, 1, 1, 12, 0, 0)
                mock_datetime.now.return_value = mock_now
                # Also mock fromisoformat to raise an exception
                mock_datetime.fromisoformat.side_effect = ValueError("Invalid format")
                
                result = _parse_datetime(dt_str)
                
                assert result == mock_now
                mock_logger.warning.assert_called_once_with(f"Failed to parse datetime: {dt_str}")


class TestGraphQLProjectRepository:
    """Test GraphQLProjectRepository."""
    
    @pytest.fixture
    def mock_client(self) -> AsyncMock:
        """Create mock GraphQL client."""
        return AsyncMock(spec=CwayGraphQLClient)
    
    @pytest.fixture
    def repository(self, mock_client: AsyncMock) -> GraphQLProjectRepository:
        """Create repository with mock client."""
        return GraphQLProjectRepository(mock_client)
    
    @pytest.fixture
    def sample_project_data(self) -> dict:
        """Sample project data from GraphQL response."""
        return {
            "id": "proj-123",
            "name": "Test Project",
            "description": "A test project",
            "status": "active",
            "createdAt": "2024-01-01T10:00:00Z",
            "updatedAt": "2024-01-01T11:00:00Z"
        }
    
    def test_init(self, repository: GraphQLProjectRepository, mock_client: AsyncMock) -> None:
        """Test repository initialization."""
        assert repository.graphql_client == mock_client
    
    @pytest.mark.asyncio
    async def test_get_all_success(self, repository: GraphQLProjectRepository, mock_client: AsyncMock, sample_project_data: dict) -> None:
        """Test successfully getting all projects."""
        mock_client.execute_query.return_value = {
            "projects": [sample_project_data]
        }
        
        result = await repository.get_all()
        
        assert len(result) == 1
        project = result[0]
        assert isinstance(project, Project)
        assert project.id == sample_project_data["id"]
        assert project.name == sample_project_data["name"]
        assert project.description == sample_project_data["description"]
        assert project.status == sample_project_data["status"]
        
        mock_client.execute_query.assert_called_once()
        query_arg = mock_client.execute_query.call_args[0][0]
        assert "projects" in query_arg
    
    @pytest.mark.asyncio
    async def test_get_all_empty(self, repository: GraphQLProjectRepository, mock_client: AsyncMock) -> None:
        """Test getting all projects when none exist."""
        mock_client.execute_query.return_value = {"projects": []}
        
        result = await repository.get_all()
        
        assert result == []
        mock_client.execute_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_all_missing_optional_fields(self, repository: GraphQLProjectRepository, mock_client: AsyncMock) -> None:
        """Test getting projects with missing optional fields."""
        minimal_data = {
            "id": "proj-456",
            "name": "Minimal Project",
            "createdAt": "2024-01-01T10:00:00Z",
            "updatedAt": "2024-01-01T11:00:00Z"
        }
        
        mock_client.execute_query.return_value = {
            "projects": [minimal_data]
        }
        
        result = await repository.get_all()
        
        assert len(result) == 1
        project = result[0]
        assert project.description is None  # Should be None when missing
        assert project.status == "active"  # Should use default
    
    @pytest.mark.asyncio
    async def test_get_all_api_error(self, repository: GraphQLProjectRepository, mock_client: AsyncMock) -> None:
        """Test handling API errors when getting all projects."""
        mock_client.execute_query.side_effect = Exception("API error")
        
        with pytest.raises(CwayAPIError, match="Failed to fetch projects"):
            await repository.get_all()
    
    @pytest.mark.asyncio
    async def test_get_by_id_found(self, repository: GraphQLProjectRepository, mock_client: AsyncMock, sample_project_data: dict) -> None:
        """Test getting project by ID when it exists."""
        mock_client.execute_query.return_value = {
            "project": sample_project_data
        }
        
        result = await repository.get_by_id("proj-123")
        
        assert result is not None
        assert result.id == "proj-123"
        assert result.name == "Test Project"
        
        mock_client.execute_query.assert_called_once()
        call_args = mock_client.execute_query.call_args
        assert "project(id: $id)" in call_args[0][0]
        assert call_args[0][1]["id"] == "proj-123"
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository: GraphQLProjectRepository, mock_client: AsyncMock) -> None:
        """Test getting project by ID when it doesn't exist."""
        mock_client.execute_query.return_value = {"project": None}
        
        result = await repository.get_by_id("proj-nonexistent")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_by_id_api_error(self, repository: GraphQLProjectRepository, mock_client: AsyncMock) -> None:
        """Test handling API errors when getting project by ID."""
        mock_client.execute_query.side_effect = Exception("API error")
        
        with pytest.raises(CwayAPIError, match="Failed to fetch project"):
            await repository.get_by_id("proj-123")
    
    @pytest.mark.asyncio
    async def test_create_success(self, repository: GraphQLProjectRepository, mock_client: AsyncMock) -> None:
        """Test successfully creating a project."""
        project = Project(
            id="proj-new",
            name="New Project",
            description="A new project",
            status="active",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        created_data = {
            "id": "proj-created",
            "name": "New Project",
            "description": "A new project",
            "status": "active",
            "createdAt": "2024-01-01T10:00:00Z",
            "updatedAt": "2024-01-01T11:00:00Z"
        }
        
        mock_client.execute_mutation.return_value = {
            "createProject": created_data
        }
        
        result = await repository.create(project)
        
        assert result.id == "proj-created"
        assert result.name == "New Project"
        assert result.description == "A new project"
        
        mock_client.execute_mutation.assert_called_once()
        call_args = mock_client.execute_mutation.call_args
        assert "createProject" in call_args[0][0]
        
        input_data = call_args[0][1]["input"]
        assert input_data["name"] == "New Project"
        assert input_data["description"] == "A new project"
        assert input_data["status"] == "active"
    
    @pytest.mark.asyncio
    async def test_create_api_error(self, repository: GraphQLProjectRepository, mock_client: AsyncMock) -> None:
        """Test handling API errors when creating project."""
        project = Project(
            id="proj-new",
            name="New Project",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        mock_client.execute_mutation.side_effect = Exception("Create error")
        
        with pytest.raises(CwayAPIError, match="Failed to create project"):
            await repository.create(project)
    
    @pytest.mark.asyncio
    async def test_update_success(self, repository: GraphQLProjectRepository, mock_client: AsyncMock) -> None:
        """Test successfully updating a project."""
        project = Project(
            id="proj-123",
            name="Updated Project",
            description="Updated description",
            status="inactive",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        updated_data = {
            "id": "proj-123",
            "name": "Updated Project",
            "description": "Updated description",
            "status": "inactive",
            "createdAt": "2024-01-01T10:00:00Z",
            "updatedAt": "2024-01-01T12:00:00Z"
        }
        
        mock_client.execute_mutation.return_value = {
            "updateProject": updated_data
        }
        
        result = await repository.update(project)
        
        assert result.id == "proj-123"
        assert result.name == "Updated Project"
        assert result.status == "inactive"
        
        mock_client.execute_mutation.assert_called_once()
        call_args = mock_client.execute_mutation.call_args
        assert "updateProject" in call_args[0][0]
        assert call_args[0][1]["id"] == "proj-123"
    
    @pytest.mark.asyncio
    async def test_update_api_error(self, repository: GraphQLProjectRepository, mock_client: AsyncMock) -> None:
        """Test handling API errors when updating project."""
        project = Project(
            id="proj-123",
            name="Updated Project",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        mock_client.execute_mutation.side_effect = Exception("Update error")
        
        with pytest.raises(CwayAPIError, match="Failed to update project"):
            await repository.update(project)
    
    @pytest.mark.asyncio
    async def test_delete_success(self, repository: GraphQLProjectRepository, mock_client: AsyncMock) -> None:
        """Test successfully deleting a project."""
        mock_client.execute_mutation.return_value = {
            "deleteProject": {"success": True}
        }
        
        result = await repository.delete("proj-123")
        
        assert result is True
        
        mock_client.execute_mutation.assert_called_once()
        call_args = mock_client.execute_mutation.call_args
        assert "deleteProject" in call_args[0][0]
        assert call_args[0][1]["id"] == "proj-123"
    
    @pytest.mark.asyncio
    async def test_delete_failure(self, repository: GraphQLProjectRepository, mock_client: AsyncMock) -> None:
        """Test failed project deletion."""
        mock_client.execute_mutation.return_value = {
            "deleteProject": {"success": False}
        }
        
        result = await repository.delete("proj-123")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_missing_response(self, repository: GraphQLProjectRepository, mock_client: AsyncMock) -> None:
        """Test delete with missing response data."""
        mock_client.execute_mutation.return_value = {}
        
        result = await repository.delete("proj-123")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_api_error(self, repository: GraphQLProjectRepository, mock_client: AsyncMock) -> None:
        """Test handling API errors when deleting project."""
        mock_client.execute_mutation.side_effect = Exception("Delete error")
        
        with pytest.raises(CwayAPIError, match="Failed to delete project"):
            await repository.delete("proj-123")


class TestGraphQLUserRepository:
    """Test GraphQLUserRepository."""
    
    @pytest.fixture
    def mock_client(self) -> AsyncMock:
        """Create mock GraphQL client."""
        return AsyncMock(spec=CwayGraphQLClient)
    
    @pytest.fixture
    def repository(self, mock_client: AsyncMock) -> GraphQLUserRepository:
        """Create repository with mock client."""
        return GraphQLUserRepository(mock_client)
    
    @pytest.fixture
    def sample_user_data(self) -> dict:
        """Sample user data from GraphQL response."""
        return {
            "id": "user-123",
            "email": "test@example.com",
            "name": "Test User",
            "role": "admin",
            "createdAt": "2024-01-01T10:00:00Z",
            "updatedAt": "2024-01-01T11:00:00Z"
        }
    
    def test_init(self, repository: GraphQLUserRepository, mock_client: AsyncMock) -> None:
        """Test repository initialization."""
        assert repository.graphql_client == mock_client
    
    @pytest.mark.asyncio
    async def test_get_all_success(self, repository: GraphQLUserRepository, mock_client: AsyncMock, sample_user_data: dict) -> None:
        """Test successfully getting all users."""
        mock_client.execute_query.return_value = {
            "users": [sample_user_data]
        }
        
        result = await repository.get_all()
        
        assert len(result) == 1
        user = result[0]
        assert isinstance(user, User)
        assert user.id == sample_user_data["id"]
        assert user.email == sample_user_data["email"]
        assert user.name == sample_user_data["name"]
        assert user.role == sample_user_data["role"]
    
    @pytest.mark.asyncio
    async def test_get_all_with_defaults(self, repository: GraphQLUserRepository, mock_client: AsyncMock) -> None:
        """Test getting users with missing optional fields."""
        minimal_data = {
            "id": "user-456",
            "email": "minimal@example.com",
            "createdAt": "2024-01-01T10:00:00Z",
            "updatedAt": "2024-01-01T11:00:00Z"
        }
        
        mock_client.execute_query.return_value = {
            "users": [minimal_data]
        }
        
        result = await repository.get_all()
        
        assert len(result) == 1
        user = result[0]
        assert user.name is None  # Should be None when missing
        assert user.role == "user"  # Should use default
    
    @pytest.mark.asyncio
    async def test_get_all_api_error(self, repository: GraphQLUserRepository, mock_client: AsyncMock) -> None:
        """Test handling API errors when getting all users."""
        mock_client.execute_query.side_effect = Exception("API error")
        
        with pytest.raises(CwayAPIError, match="Failed to fetch users"):
            await repository.get_all()
    
    @pytest.mark.asyncio
    async def test_get_by_id_found(self, repository: GraphQLUserRepository, mock_client: AsyncMock, sample_user_data: dict) -> None:
        """Test getting user by ID when it exists."""
        mock_client.execute_query.return_value = {
            "user": sample_user_data
        }
        
        result = await repository.get_by_id("user-123")
        
        assert result is not None
        assert result.id == "user-123"
        assert result.email == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository: GraphQLUserRepository, mock_client: AsyncMock) -> None:
        """Test getting user by ID when it doesn't exist."""
        mock_client.execute_query.return_value = {"user": None}
        
        result = await repository.get_by_id("user-nonexistent")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_by_id_api_error(self, repository: GraphQLUserRepository, mock_client: AsyncMock) -> None:
        """Test handling API errors when getting user by ID."""
        mock_client.execute_query.side_effect = Exception("API error")
        
        with pytest.raises(CwayAPIError, match="Failed to fetch user"):
            await repository.get_by_id("user-123")
    
    @pytest.mark.asyncio
    async def test_get_by_email_found(self, repository: GraphQLUserRepository, mock_client: AsyncMock, sample_user_data: dict) -> None:
        """Test getting user by email when it exists."""
        mock_client.execute_query.return_value = {
            "userByEmail": sample_user_data
        }
        
        result = await repository.get_by_email("test@example.com")
        
        assert result is not None
        assert result.email == "test@example.com"
        assert result.id == "user-123"
        
        call_args = mock_client.execute_query.call_args
        assert "userByEmail" in call_args[0][0]
        assert call_args[0][1]["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_get_by_email_not_found(self, repository: GraphQLUserRepository, mock_client: AsyncMock) -> None:
        """Test getting user by email when it doesn't exist."""
        mock_client.execute_query.return_value = {"userByEmail": None}
        
        result = await repository.get_by_email("nonexistent@example.com")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_by_email_api_error(self, repository: GraphQLUserRepository, mock_client: AsyncMock) -> None:
        """Test handling API errors when getting user by email."""
        mock_client.execute_query.side_effect = Exception("API error")
        
        with pytest.raises(CwayAPIError, match="Failed to fetch user by email"):
            await repository.get_by_email("test@example.com")
    
    @pytest.mark.asyncio
    async def test_create_success(self, repository: GraphQLUserRepository, mock_client: AsyncMock) -> None:
        """Test successfully creating a user."""
        user = User(
            id="user-new",
            email="new@example.com",
            name="New User",
            role="viewer",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        created_data = {
            "id": "user-created",
            "email": "new@example.com",
            "name": "New User",
            "role": "viewer",
            "createdAt": "2024-01-01T10:00:00Z",
            "updatedAt": "2024-01-01T11:00:00Z"
        }
        
        mock_client.execute_mutation.return_value = {
            "createUser": created_data
        }
        
        result = await repository.create(user)
        
        assert result.id == "user-created"
        assert result.email == "new@example.com"
        assert result.name == "New User"
        assert result.role == "viewer"
        
        call_args = mock_client.execute_mutation.call_args
        input_data = call_args[0][1]["input"]
        assert input_data["email"] == "new@example.com"
        assert input_data["name"] == "New User"
        assert input_data["role"] == "viewer"
    
    @pytest.mark.asyncio
    async def test_create_api_error(self, repository: GraphQLUserRepository, mock_client: AsyncMock) -> None:
        """Test handling API errors when creating user."""
        user = User(
            id="user-new",
            email="new@example.com",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        mock_client.execute_mutation.side_effect = Exception("Create error")
        
        with pytest.raises(CwayAPIError, match="Failed to create user"):
            await repository.create(user)
    
    @pytest.mark.asyncio
    async def test_update_success(self, repository: GraphQLUserRepository, mock_client: AsyncMock) -> None:
        """Test successfully updating a user."""
        user = User(
            id="user-123",
            email="updated@example.com",
            name="Updated User",
            role="admin",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        updated_data = {
            "id": "user-123",
            "email": "updated@example.com",
            "name": "Updated User",
            "role": "admin",
            "createdAt": "2024-01-01T10:00:00Z",
            "updatedAt": "2024-01-01T12:00:00Z"
        }
        
        mock_client.execute_mutation.return_value = {
            "updateUser": updated_data
        }
        
        result = await repository.update(user)
        
        assert result.id == "user-123"
        assert result.email == "updated@example.com"
        assert result.name == "Updated User"
        assert result.role == "admin"
        
        call_args = mock_client.execute_mutation.call_args
        assert call_args[0][1]["id"] == "user-123"
    
    @pytest.mark.asyncio
    async def test_update_api_error(self, repository: GraphQLUserRepository, mock_client: AsyncMock) -> None:
        """Test handling API errors when updating user."""
        user = User(
            id="user-123",
            email="test@example.com",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        mock_client.execute_mutation.side_effect = Exception("Update error")
        
        with pytest.raises(CwayAPIError, match="Failed to update user"):
            await repository.update(user)
    
    @pytest.mark.asyncio
    async def test_delete_success(self, repository: GraphQLUserRepository, mock_client: AsyncMock) -> None:
        """Test successfully deleting a user."""
        mock_client.execute_mutation.return_value = {
            "deleteUser": {"success": True}
        }
        
        result = await repository.delete("user-123")
        
        assert result is True
        
        call_args = mock_client.execute_mutation.call_args
        assert "deleteUser" in call_args[0][0]
        assert call_args[0][1]["id"] == "user-123"
    
    @pytest.mark.asyncio
    async def test_delete_failure(self, repository: GraphQLUserRepository, mock_client: AsyncMock) -> None:
        """Test failed user deletion."""
        mock_client.execute_mutation.return_value = {
            "deleteUser": {"success": False}
        }
        
        result = await repository.delete("user-123")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_api_error(self, repository: GraphQLUserRepository, mock_client: AsyncMock) -> None:
        """Test handling API errors when deleting user."""
        mock_client.execute_mutation.side_effect = Exception("Delete error")
        
        with pytest.raises(CwayAPIError, match="Failed to delete user"):
            await repository.delete("user-123")