"""Tests for application use cases."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Optional, List
import pytest

from src.application.use_cases import ProjectUseCases, UserUseCases
from src.domain.entities import Project, User, ProjectState
from src.domain.repositories import ProjectRepository, UserRepository


class TestProjectUseCases:
    """Test ProjectUseCases."""
    
    @pytest.fixture
    def mock_repository(self) -> AsyncMock:
        """Create a mock project repository."""
        return AsyncMock(spec=ProjectRepository)
    
    @pytest.fixture
    def use_cases(self, mock_repository: AsyncMock) -> ProjectUseCases:
        """Create ProjectUseCases with mock repository."""
        return ProjectUseCases(mock_repository)
    
    @pytest.fixture
    def sample_project(self) -> Project:
        """Create a sample project for testing."""
        return Project(
            id="proj-123",
            name="Test Project",
            description="A test project",
            status="ACTIVE",
            created_at=datetime(2024, 1, 1, 10, 0, 0),
            updated_at=datetime(2024, 1, 1, 10, 0, 0)
        )
    
    @pytest.mark.asyncio
    async def test_list_projects(self, use_cases: ProjectUseCases, mock_repository: AsyncMock, sample_project: Project) -> None:
        """Test listing all projects."""
        expected_projects = [sample_project]
        mock_repository.get_all.return_value = expected_projects
        
        with patch('src.application.use_cases.logger') as mock_logger:
            result = await use_cases.list_projects()
        
        assert result == expected_projects
        mock_repository.get_all.assert_called_once()
        mock_logger.info.assert_any_call("Fetching all projects")
        mock_logger.info.assert_any_call("Found 1 projects")
    
    @pytest.mark.asyncio
    async def test_list_projects_empty(self, use_cases: ProjectUseCases, mock_repository: AsyncMock) -> None:
        """Test listing projects when none exist."""
        mock_repository.get_all.return_value = []
        
        with patch('src.application.use_cases.logger') as mock_logger:
            result = await use_cases.list_projects()
        
        assert result == []
        mock_repository.get_all.assert_called_once()
        mock_logger.info.assert_any_call("Found 0 projects")
    
    @pytest.mark.asyncio
    async def test_get_project_found(self, use_cases: ProjectUseCases, mock_repository: AsyncMock, sample_project: Project) -> None:
        """Test getting a project that exists."""
        project_id = "proj-123"
        mock_repository.get_by_id.return_value = sample_project
        
        with patch('src.application.use_cases.logger') as mock_logger:
            result = await use_cases.get_project(project_id)
        
        assert result == sample_project
        mock_repository.get_by_id.assert_called_once_with(project_id)
        mock_logger.info.assert_any_call(f"Fetching project with ID: {project_id}")
        mock_logger.info.assert_any_call(f"Found project: {sample_project.name}")
    
    @pytest.mark.asyncio
    async def test_get_project_not_found(self, use_cases: ProjectUseCases, mock_repository: AsyncMock) -> None:
        """Test getting a project that doesn't exist."""
        project_id = "proj-nonexistent"
        mock_repository.get_by_id.return_value = None
        
        with patch('src.application.use_cases.logger') as mock_logger:
            result = await use_cases.get_project(project_id)
        
        assert result is None
        mock_repository.get_by_id.assert_called_once_with(project_id)
        mock_logger.warning.assert_called_once_with(f"Project not found: {project_id}")
    
    @pytest.mark.asyncio
    async def test_create_project_minimal(self, use_cases: ProjectUseCases, mock_repository: AsyncMock) -> None:
        """Test creating a project with minimal parameters."""
        project_name = "New Project"
        
        # Mock the created project
        created_project = Project(
            id=f"proj_{project_name.lower().replace(' ', '_')}",
            name=project_name,
            description=None,
            status="ACTIVE",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_repository.create.return_value = created_project
        
        from datetime import datetime as dt
        with patch('src.application.use_cases.logger') as mock_logger:
            with patch('datetime.datetime') as mock_datetime:
                mock_now = dt(2024, 1, 1, 12, 0, 0)
                mock_datetime.now.return_value = mock_now
                
                result = await use_cases.create_project(project_name)
        
        assert result == created_project
        mock_repository.create.assert_called_once()
        
        # Verify the project passed to create has correct structure
        create_call_args = mock_repository.create.call_args[0][0]
        assert create_call_args.name == project_name
        assert create_call_args.description is None
        assert create_call_args.status == ProjectState.ACTIVE
        
        mock_logger.info.assert_any_call(f"Creating new project: {project_name}")
        mock_logger.info.assert_any_call(f"Created project: {created_project.id}")
    
    @pytest.mark.asyncio
    async def test_create_project_full(self, use_cases: ProjectUseCases, mock_repository: AsyncMock) -> None:
        """Test creating a project with all parameters."""
        project_name = "Full Project"
        description = "A complete project"
        status = "INACTIVE"
        
        created_project = Project(
            id="proj_full_project",
            name=project_name,
            description=description,
            status=status,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_repository.create.return_value = created_project
        
        result = await use_cases.create_project(project_name, description, status)
        
        assert result == created_project
        create_call_args = mock_repository.create.call_args[0][0]
        assert create_call_args.name == project_name
        assert create_call_args.description == description
        # Status is converted to enum in __post_init__
        assert create_call_args.status == ProjectState.INACTIVE
    
    @pytest.mark.asyncio
    async def test_update_project_found(self, use_cases: ProjectUseCases, mock_repository: AsyncMock, sample_project: Project) -> None:
        """Test updating an existing project."""
        project_id = "proj-123"
        new_name = "Updated Project"
        new_description = "Updated description"
        new_status = "INACTIVE"
        
        mock_repository.get_by_id.return_value = sample_project
        
        updated_project = Project(
            id=project_id,
            name=new_name,
            description=new_description,
            status=new_status,
            created_at=sample_project.created_at,
            updated_at=datetime.now()
        )
        mock_repository.update.return_value = updated_project
        
        from datetime import datetime as dt
        with patch('datetime.datetime') as mock_datetime:
            mock_now = dt(2024, 1, 2, 10, 0, 0)
            mock_datetime.now.return_value = mock_now
            
            result = await use_cases.update_project(project_id, new_name, new_description, new_status)
        
        assert result == updated_project
        mock_repository.get_by_id.assert_called_once_with(project_id)
        mock_repository.update.assert_called_once()
        
        # Verify the updated project structure
        update_call_args = mock_repository.update.call_args[0][0]
        assert update_call_args.name == new_name
        assert update_call_args.description == new_description
        # Status is converted to enum in __post_init__
        assert update_call_args.status == ProjectState.INACTIVE
        assert update_call_args.created_at == sample_project.created_at
        # updated_at will be set to current time (don't check exact value due to timing)
        assert update_call_args.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_update_project_partial(self, use_cases: ProjectUseCases, mock_repository: AsyncMock, sample_project: Project) -> None:
        """Test updating a project with only some fields."""
        project_id = "proj-123"
        new_name = "Updated Name"
        
        mock_repository.get_by_id.return_value = sample_project
        
        updated_project = Project(
            id=project_id,
            name=new_name,
            description=sample_project.description,  # Should remain unchanged
            status=sample_project.status,  # Should remain unchanged
            created_at=sample_project.created_at,
            updated_at=datetime.now()
        )
        mock_repository.update.return_value = updated_project
        
        result = await use_cases.update_project(project_id, name=new_name)
        
        assert result == updated_project
        update_call_args = mock_repository.update.call_args[0][0]
        assert update_call_args.name == new_name
        assert update_call_args.description == sample_project.description
        # Both should be ProjectState enums
        assert update_call_args.status == sample_project.status
    
    @pytest.mark.asyncio
    async def test_update_project_not_found(self, use_cases: ProjectUseCases, mock_repository: AsyncMock) -> None:
        """Test updating a project that doesn't exist."""
        project_id = "proj-nonexistent"
        mock_repository.get_by_id.return_value = None
        
        with patch('src.application.use_cases.logger') as mock_logger:
            result = await use_cases.update_project(project_id, name="New Name")
        
        assert result is None
        mock_repository.get_by_id.assert_called_once_with(project_id)
        mock_repository.update.assert_not_called()
        mock_logger.warning.assert_called_once_with(f"Project not found for update: {project_id}")
    
    @pytest.mark.asyncio
    async def test_delete_project_success(self, use_cases: ProjectUseCases, mock_repository: AsyncMock) -> None:
        """Test successfully deleting a project."""
        project_id = "proj-123"
        mock_repository.delete.return_value = True
        
        with patch('src.application.use_cases.logger') as mock_logger:
            result = await use_cases.delete_project(project_id)
        
        assert result is True
        mock_repository.delete.assert_called_once_with(project_id)
        mock_logger.info.assert_any_call(f"Deleting project: {project_id}")
        mock_logger.info.assert_any_call(f"Deleted project: {project_id}")
    
    @pytest.mark.asyncio
    async def test_delete_project_failure(self, use_cases: ProjectUseCases, mock_repository: AsyncMock) -> None:
        """Test failed project deletion."""
        project_id = "proj-123"
        mock_repository.delete.return_value = False
        
        with patch('src.application.use_cases.logger') as mock_logger:
            result = await use_cases.delete_project(project_id)
        
        assert result is False
        mock_repository.delete.assert_called_once_with(project_id)
        mock_logger.warning.assert_called_once_with(f"Failed to delete project: {project_id}")


class TestUserUseCases:
    """Test UserUseCases."""
    
    @pytest.fixture
    def mock_repository(self) -> AsyncMock:
        """Create a mock user repository."""
        return AsyncMock(spec=UserRepository)
    
    @pytest.fixture
    def use_cases(self, mock_repository: AsyncMock) -> UserUseCases:
        """Create UserUseCases with mock repository."""
        return UserUseCases(mock_repository)
    
    @pytest.fixture
    def sample_user(self) -> User:
        """Create a sample user for testing."""
        return User(
            id="user-123",
            email="test@example.com",
            name="Test User",
            role="user",
            created_at=datetime(2024, 1, 1, 10, 0, 0),
            updated_at=datetime(2024, 1, 1, 10, 0, 0)
        )
    
    @pytest.mark.asyncio
    async def test_list_users(self, use_cases: UserUseCases, mock_repository: AsyncMock, sample_user: User) -> None:
        """Test listing all users."""
        expected_users = [sample_user]
        mock_repository.get_all.return_value = expected_users
        
        with patch('src.application.use_cases.logger') as mock_logger:
            result = await use_cases.list_users()
        
        assert result == expected_users
        mock_repository.get_all.assert_called_once()
        mock_logger.info.assert_any_call("Fetching all users")
        mock_logger.info.assert_any_call("Found 1 users")
    
    @pytest.mark.asyncio
    async def test_get_user_found(self, use_cases: UserUseCases, mock_repository: AsyncMock, sample_user: User) -> None:
        """Test getting a user that exists."""
        user_id = "user-123"
        mock_repository.get_by_id.return_value = sample_user
        
        with patch('src.application.use_cases.logger') as mock_logger:
            result = await use_cases.get_user(user_id)
        
        assert result == sample_user
        mock_repository.get_by_id.assert_called_once_with(user_id)
        mock_logger.info.assert_any_call(f"Fetching user with ID: {user_id}")
        mock_logger.info.assert_any_call(f"Found user: {sample_user.email}")
    
    @pytest.mark.asyncio
    async def test_get_user_not_found(self, use_cases: UserUseCases, mock_repository: AsyncMock) -> None:
        """Test getting a user that doesn't exist."""
        user_id = "user-nonexistent"
        mock_repository.get_by_id.return_value = None
        
        with patch('src.application.use_cases.logger') as mock_logger:
            result = await use_cases.get_user(user_id)
        
        assert result is None
        mock_repository.get_by_id.assert_called_once_with(user_id)
        mock_logger.warning.assert_called_once_with(f"User not found: {user_id}")
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_found(self, use_cases: UserUseCases, mock_repository: AsyncMock, sample_user: User) -> None:
        """Test getting a user by email that exists."""
        email = "test@example.com"
        mock_repository.get_by_email.return_value = sample_user
        
        with patch('src.application.use_cases.logger') as mock_logger:
            result = await use_cases.get_user_by_email(email)
        
        assert result == sample_user
        mock_repository.get_by_email.assert_called_once_with(email)
        mock_logger.info.assert_any_call(f"Fetching user with email: {email}")
        mock_logger.info.assert_any_call(f"Found user: {sample_user.id}")
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, use_cases: UserUseCases, mock_repository: AsyncMock) -> None:
        """Test getting a user by email that doesn't exist."""
        email = "nonexistent@example.com"
        mock_repository.get_by_email.return_value = None
        
        with patch('src.application.use_cases.logger') as mock_logger:
            result = await use_cases.get_user_by_email(email)
        
        assert result is None
        mock_repository.get_by_email.assert_called_once_with(email)
        mock_logger.warning.assert_called_once_with(f"User not found: {email}")
    
    @pytest.mark.asyncio
    async def test_create_user_minimal(self, use_cases: UserUseCases, mock_repository: AsyncMock) -> None:
        """Test creating a user with minimal parameters."""
        email = "new@example.com"
        
        # Mock that user doesn't exist
        mock_repository.get_by_email.return_value = None
        
        created_user = User(
            id="user_new",
            email=email,
            name=None,
            role="user",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_repository.create.return_value = created_user
        
        from datetime import datetime as dt
        with patch('src.application.use_cases.logger') as mock_logger:
            with patch('datetime.datetime') as mock_datetime:
                mock_now = dt(2024, 1, 1, 12, 0, 0)
                mock_datetime.now.return_value = mock_now
                
                result = await use_cases.create_user(email)
        
        assert result == created_user
        mock_repository.get_by_email.assert_called_once_with(email)
        mock_repository.create.assert_called_once()
        
        # Verify the user passed to create has correct structure
        create_call_args = mock_repository.create.call_args[0][0]
        assert create_call_args.email == email
        assert create_call_args.name is None
        assert create_call_args.role == "user"
        
        mock_logger.info.assert_any_call(f"Creating new user: {email}")
        mock_logger.info.assert_any_call(f"Created user: {created_user.id}")
    
    @pytest.mark.asyncio
    async def test_create_user_full(self, use_cases: UserUseCases, mock_repository: AsyncMock) -> None:
        """Test creating a user with all parameters."""
        email = "admin@example.com"
        name = "Admin User"
        role = "admin"
        
        # Mock that user doesn't exist
        mock_repository.get_by_email.return_value = None
        
        created_user = User(
            id="user_admin",
            email=email,
            name=name,
            role=role,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_repository.create.return_value = created_user
        
        result = await use_cases.create_user(email, name, role)
        
        assert result == created_user
        create_call_args = mock_repository.create.call_args[0][0]
        assert create_call_args.email == email
        assert create_call_args.name == name
        assert create_call_args.role == role
    
    @pytest.mark.asyncio
    async def test_create_user_already_exists(self, use_cases: UserUseCases, mock_repository: AsyncMock, sample_user: User) -> None:
        """Test creating a user that already exists."""
        email = "test@example.com"
        
        # Mock that user already exists
        mock_repository.get_by_email.return_value = sample_user
        
        with patch('src.application.use_cases.logger') as mock_logger:
            with pytest.raises(ValueError, match=f"User with email {email} already exists"):
                await use_cases.create_user(email)
        
        mock_repository.get_by_email.assert_called_once_with(email)
        mock_repository.create.assert_not_called()
        mock_logger.warning.assert_called_once_with(f"User already exists: {email}")
    
    @pytest.mark.asyncio
    async def test_create_user_id_generation(self, use_cases: UserUseCases, mock_repository: AsyncMock) -> None:
        """Test that user ID is generated correctly from email."""
        email = "complex.email+tag@example.com"
        
        mock_repository.get_by_email.return_value = None
        
        created_user = User(
            id="user_complex.email",  # Should be based on part before @
            email=email,
            name=None,
            role="user",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_repository.create.return_value = created_user
        
        await use_cases.create_user(email)
        
        create_call_args = mock_repository.create.call_args[0][0]
        # The actual implementation uses the full part before @ 
        assert create_call_args.id == "user_complex.email+tag"
