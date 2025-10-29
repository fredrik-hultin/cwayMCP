"""
Unit tests for newly added repository methods.
Focuses on increasing coverage of cway_repositories.py
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.infrastructure.cway_repositories import (
    CwayUserRepository,
    CwayProjectRepository,
    CwaySystemRepository
)
from src.infrastructure.graphql_client import CwayAPIError
from src.domain.cway_entities import CwayUser


@pytest.fixture
def mock_graphql_client():
    """Create a mock GraphQL client."""
    client = AsyncMock()
    client.execute_query = AsyncMock()
    client.execute_mutation = AsyncMock()
    return client


class TestCwayUserRepositoryNewMethods:
    """Test newly added methods in CwayUserRepository."""
    
    @pytest.mark.asyncio
    async def test_search_users_with_query(self, mock_graphql_client):
        """Test searching users with a query string."""
        # Arrange
        repo = CwayUserRepository(mock_graphql_client)
        mock_graphql_client.execute_query.return_value = {
            "findUsers": [
                {
                    "id": "user-1",
                    "name": "John Doe",
                    "email": "john@test.com",
                    "username": "johndoe",
                    "firstName": "John",
                    "lastName": "Doe",
                    "enabled": True
                }
            ]
        }
        
        # Act
        users = await repo.search_users("john")
        
        # Assert
        assert len(users) == 1
        assert users[0].username == "johndoe"
        assert users[0].email == "john@test.com"
        mock_graphql_client.execute_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_users_no_query(self, mock_graphql_client):
        """Test searching users without a query."""
        # Arrange
        repo = CwayUserRepository(mock_graphql_client)
        mock_graphql_client.execute_query.return_value = {
            "findUsers": []
        }
        
        # Act
        users = await repo.search_users(None)
        
        # Assert
        assert len(users) == 0
    
    @pytest.mark.asyncio
    async def test_search_users_api_error(self, mock_graphql_client):
        """Test search_users handles API errors."""
        # Arrange
        repo = CwayUserRepository(mock_graphql_client)
        mock_graphql_client.execute_query.side_effect = Exception("API Error")
        
        # Act & Assert
        with pytest.raises(CwayAPIError, match="Failed to search users"):
            await repo.search_users("test")
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, mock_graphql_client):
        """Test creating a new user."""
        # Arrange
        repo = CwayUserRepository(mock_graphql_client)
        mock_graphql_client.execute_mutation.return_value = {
            "createUser": {
                "id": "new-user-id",
                "name": "New User",
                "email": "new@test.com",
                "username": "newuser",
                "firstName": "New",
                "lastName": "User",
                "enabled": True
            }
        }
        
        # Act
        user = await repo.create_user(
            email="new@test.com",
            username="newuser",
            first_name="New",
            last_name="User"
        )
        
        # Assert
        assert user.username == "newuser"
        assert user.email == "new@test.com"
        assert user.firstName == "New"
        assert user.lastName == "User"
        mock_graphql_client.execute_mutation.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_user_minimal_fields(self, mock_graphql_client):
        """Test creating a user with only required fields."""
        # Arrange
        repo = CwayUserRepository(mock_graphql_client)
        mock_graphql_client.execute_mutation.return_value = {
            "createUser": {
                "id": "new-user-id",
                "name": "testuser",
                "email": "test@test.com",
                "username": "testuser",
                "enabled": True
            }
        }
        
        # Act
        user = await repo.create_user(
            email="test@test.com",
            username="testuser"
        )
        
        # Assert
        assert user.username == "testuser"
        assert user.email == "test@test.com"
    
    @pytest.mark.asyncio
    async def test_create_user_api_error(self, mock_graphql_client):
        """Test create_user handles API errors."""
        # Arrange
        repo = CwayUserRepository(mock_graphql_client)
        mock_graphql_client.execute_mutation.side_effect = Exception("API Error")
        
        # Act & Assert
        with pytest.raises(CwayAPIError, match="Failed to create user"):
            await repo.create_user(email="test@test.com", username="test")
    
    @pytest.mark.asyncio
    async def test_update_user_name_success(self, mock_graphql_client):
        """Test updating a user's name."""
        # Arrange
        repo = CwayUserRepository(mock_graphql_client)
        mock_graphql_client.execute_mutation.return_value = {
            "setUserRealName": {
                "id": "user-id",
                "username": "testuser",
                "firstName": "Updated",
                "lastName": "Name",
                "name": "Updated Name",
                "email": "test@test.com",
                "enabled": True
            }
        }
        
        # Act
        user = await repo.update_user_name(
            username="testuser",
            first_name="Updated",
            last_name="Name"
        )
        
        # Assert
        assert user is not None
        assert user.firstName == "Updated"
        assert user.lastName == "Name"
        mock_graphql_client.execute_mutation.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_user_name_not_found(self, mock_graphql_client):
        """Test updating a user that doesn't exist."""
        # Arrange
        repo = CwayUserRepository(mock_graphql_client)
        mock_graphql_client.execute_mutation.return_value = {
            "setUserRealName": None
        }
        
        # Act
        user = await repo.update_user_name(
            username="nonexistent",
            first_name="Test",
            last_name="User"
        )
        
        # Assert
        assert user is None
    
    @pytest.mark.asyncio
    async def test_update_user_name_api_error(self, mock_graphql_client):
        """Test update_user_name handles API errors."""
        # Arrange
        repo = CwayUserRepository(mock_graphql_client)
        mock_graphql_client.execute_mutation.side_effect = Exception("API Error")
        
        # Act & Assert
        with pytest.raises(CwayAPIError, match="Failed to update user name"):
            await repo.update_user_name(username="test", first_name="Test")
    
    @pytest.mark.asyncio
    async def test_delete_user_success(self, mock_graphql_client):
        """Test deleting a user."""
        # Arrange
        repo = CwayUserRepository(mock_graphql_client)
        mock_graphql_client.execute_mutation.return_value = {
            "deleteUsers": True
        }
        
        # Act
        result = await repo.delete_user("testuser")
        
        # Assert
        assert result is True
        mock_graphql_client.execute_mutation.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_user_failure(self, mock_graphql_client):
        """Test delete_user when deletion fails."""
        # Arrange
        repo = CwayUserRepository(mock_graphql_client)
        mock_graphql_client.execute_mutation.return_value = {
            "deleteUsers": False
        }
        
        # Act
        result = await repo.delete_user("testuser")
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_user_api_error(self, mock_graphql_client):
        """Test delete_user handles API errors."""
        # Arrange
        repo = CwayUserRepository(mock_graphql_client)
        mock_graphql_client.execute_mutation.side_effect = Exception("API Error")
        
        # Act & Assert
        with pytest.raises(CwayAPIError, match="Failed to delete user"):
            await repo.delete_user("test")


class TestCwayProjectRepositoryNewMethods:
    """Test newly added methods in CwayProjectRepository."""
    
    @pytest.mark.asyncio
    async def test_search_projects_with_query(self, mock_graphql_client):
        """Test searching projects with a query."""
        # Arrange
        repo = CwayProjectRepository(mock_graphql_client)
        mock_graphql_client.execute_query.return_value = {
            "projects": {
                "items": [
                    {
                        "id": "proj-1",
                        "name": "Test Project",
                        "description": "A test project",
                        "createdAt": "2024-01-01T00:00:00Z"
                    }
                ],
                "totalHits": 1
            }
        }
        
        # Act
        result = await repo.search_projects("test", limit=10)
        
        # Assert
        assert "projects" in result
        assert "total_hits" in result
        assert len(result["projects"]) == 1
        assert result["total_hits"] == 1
        mock_graphql_client.execute_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_projects_no_query(self, mock_graphql_client):
        """Test searching projects without a query."""
        # Arrange
        repo = CwayProjectRepository(mock_graphql_client)
        mock_graphql_client.execute_query.return_value = {
            "projects": {
                "items": [],
                "totalHits": 0
            }
        }
        
        # Act
        result = await repo.search_projects(None, limit=5)
        
        # Assert
        assert len(result["projects"]) == 0
    
    @pytest.mark.asyncio
    async def test_search_projects_api_error(self, mock_graphql_client):
        """Test search_projects handles API errors."""
        # Arrange
        repo = CwayProjectRepository(mock_graphql_client)
        mock_graphql_client.execute_query.side_effect = Exception("API Error")
        
        # Act & Assert
        with pytest.raises(CwayAPIError, match="Failed to search projects"):
            await repo.search_projects("test")
    
    @pytest.mark.asyncio
    async def test_get_project_by_id_success(self, mock_graphql_client):
        """Test getting a project by ID."""
        # Arrange
        repo = CwayProjectRepository(mock_graphql_client)
        project_id = "550e8400-e29b-41d4-a716-446655440000"
        mock_graphql_client.execute_query.return_value = {
            "project": {
                "id": project_id,
                "name": "Test Project",
                "description": "A test",
                "createdAt": "2024-01-01T00:00:00Z"
            }
        }
        
        # Act
        project = await repo.get_project_by_id(project_id)
        
        # Assert
        assert project is not None
        assert project["id"] == project_id
        assert project["name"] == "Test Project"
    
    @pytest.mark.asyncio
    async def test_get_project_by_id_not_found(self, mock_graphql_client):
        """Test getting a non-existent project."""
        # Arrange
        repo = CwayProjectRepository(mock_graphql_client)
        mock_graphql_client.execute_query.return_value = {
            "project": None
        }
        
        # Act
        project = await repo.get_project_by_id("nonexistent")
        
        # Assert
        assert project is None
    
    @pytest.mark.asyncio
    async def test_get_project_by_id_api_error(self, mock_graphql_client):
        """Test get_project_by_id handles API errors."""
        # Arrange
        repo = CwayProjectRepository(mock_graphql_client)
        mock_graphql_client.execute_query.side_effect = Exception("API Error")
        
        # Act & Assert
        with pytest.raises(CwayAPIError, match="Failed to get project"):
            await repo.get_project_by_id("test")
    
    @pytest.mark.asyncio
    async def test_create_project_success(self, mock_graphql_client):
        """Test creating a new project."""
        # Arrange
        repo = CwayProjectRepository(mock_graphql_client)
        mock_graphql_client.execute_mutation.return_value = {
            "createProject": {
                "id": "new-proj-id",
                "name": "New Project",
                "description": "A new project",
                "createdAt": "2024-01-01T00:00:00Z"
            }
        }
        
        # Act
        project = await repo.create_project("New Project", "A new project")
        
        # Assert
        assert project["name"] == "New Project"
        assert project["description"] == "A new project"
        mock_graphql_client.execute_mutation.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_project_minimal(self, mock_graphql_client):
        """Test creating a project with only name."""
        # Arrange
        repo = CwayProjectRepository(mock_graphql_client)
        mock_graphql_client.execute_mutation.return_value = {
            "createProject": {
                "id": "new-proj-id",
                "name": "New Project",
                "createdAt": "2024-01-01T00:00:00Z"
            }
        }
        
        # Act
        project = await repo.create_project("New Project")
        
        # Assert
        assert project["name"] == "New Project"
    
    @pytest.mark.asyncio
    async def test_create_project_api_error(self, mock_graphql_client):
        """Test create_project handles API errors."""
        # Arrange
        repo = CwayProjectRepository(mock_graphql_client)
        mock_graphql_client.execute_mutation.side_effect = Exception("API Error")
        
        # Act & Assert
        with pytest.raises(CwayAPIError, match="Failed to create project"):
            await repo.create_project("Test Project")
    
    @pytest.mark.asyncio
    async def test_update_project_success(self, mock_graphql_client):
        """Test updating a project."""
        # Arrange
        repo = CwayProjectRepository(mock_graphql_client)
        project_id = "proj-id"
        mock_graphql_client.execute_mutation.return_value = {
            "updateProject": {
                "id": project_id,
                "name": "Updated Project",
                "description": "Updated description"
            }
        }
        
        # Act
        project = await repo.update_project(
            project_id,
            name="Updated Project",
            description="Updated description"
        )
        
        # Assert
        assert project["name"] == "Updated Project"
        assert project["description"] == "Updated description"
        mock_graphql_client.execute_mutation.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_project_name_only(self, mock_graphql_client):
        """Test updating only project name."""
        # Arrange
        repo = CwayProjectRepository(mock_graphql_client)
        project_id = "proj-id"
        mock_graphql_client.execute_mutation.return_value = {
            "updateProject": {
                "id": project_id,
                "name": "New Name"
            }
        }
        
        # Act
        project = await repo.update_project(project_id, name="New Name")
        
        # Assert
        assert project["name"] == "New Name"
    
    @pytest.mark.asyncio
    async def test_update_project_api_error(self, mock_graphql_client):
        """Test update_project handles API errors."""
        # Arrange
        repo = CwayProjectRepository(mock_graphql_client)
        mock_graphql_client.execute_mutation.side_effect = Exception("API Error")
        
        # Act & Assert
        with pytest.raises(CwayAPIError, match="Failed to update project"):
            await repo.update_project("proj-id", name="Test")
