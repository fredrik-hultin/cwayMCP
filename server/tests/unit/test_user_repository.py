"""Unit tests for UserRepository.

Focus on:
- User CRUD operations
- Search and pagination
- Permission management
- Error handling
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.infrastructure.repositories.user_repository import UserRepository
from src.domain.cway_entities import CwayUser
from src.infrastructure.graphql_client import CwayAPIError


@pytest.fixture
def mock_graphql_client():
    """Create a mock GraphQL client."""
    client = MagicMock()
    client.execute_query = AsyncMock()
    client.execute_mutation = AsyncMock()
    return client


@pytest.fixture
def user_repository(mock_graphql_client):
    """Create a UserRepository with mocked client."""
    repo = UserRepository(mock_graphql_client)
    return repo


class TestFindAllUsers:
    """Tests for find_all_users method."""
    
    @pytest.mark.asyncio
    async def test_find_all_users_multiple(self, user_repository, mock_graphql_client):
        """Test finding all users returns multiple users."""
        mock_response = {
            "findUsers": [
                {
                    "id": "user-1",
                    "name": "John Doe",
                    "email": "john@example.com",
                    "username": "john",
                    "firstName": "John",
                    "lastName": "Doe",
                    "enabled": True,
                    "avatar": False,
                    "acceptedTerms": True,
                    "earlyAccessProgram": False,
                    "isSSO": False,
                    "createdAt": "2024-01-01T00:00:00Z"
                },
                {
                    "id": "user-2",
                    "name": "Jane Smith",
                    "email": "jane@example.com",
                    "username": "jane",
                    "firstName": "Jane",
                    "lastName": "Smith",
                    "enabled": True,
                    "avatar": True,
                    "acceptedTerms": True,
                    "earlyAccessProgram": True,
                    "isSSO": False,
                    "createdAt": "2024-01-02T00:00:00Z"
                }
            ]
        }
        mock_graphql_client.execute_query.return_value = mock_response
        
        result = await user_repository.find_all_users()
        
        assert len(result) == 2
        assert all(isinstance(user, CwayUser) for user in result)
        assert result[0].username == "john"
        assert result[1].username == "jane"
        assert result[1].earlyAccessProgram is True
    
    @pytest.mark.asyncio
    async def test_find_all_users_empty(self, user_repository, mock_graphql_client):
        """Test finding users when none exist."""
        mock_graphql_client.execute_query.return_value = {}
        
        result = await user_repository.find_all_users()
        
        assert result == []


class TestFindUserById:
    """Tests for find_user_by_id method."""
    
    @pytest.mark.asyncio
    async def test_find_user_by_id_found(self, user_repository, mock_graphql_client):
        """Test finding existing user by ID."""
        target_id = "user-2"
        mock_response = {
            "findUsers": [
                {
                    "id": "user-1",
                    "name": "John Doe",
                    "email": "john@example.com",
                    "username": "john",
                    "firstName": "John",
                    "lastName": "Doe",
                    "enabled": True
                },
                {
                    "id": target_id,
                    "name": "Jane Smith",
                    "email": "jane@example.com",
                    "username": "jane",
                    "firstName": "Jane",
                    "lastName": "Smith",
                    "enabled": True
                }
            ]
        }
        mock_graphql_client.execute_query.return_value = mock_response
        
        result = await user_repository.find_user_by_id(target_id)
        
        assert result is not None
        assert result.id == target_id
        assert result.username == "jane"
    
    @pytest.mark.asyncio
    async def test_find_user_by_id_not_found(self, user_repository, mock_graphql_client):
        """Test finding non-existent user by ID."""
        mock_response = {
            "findUsers": [
                {
                    "id": "user-1",
                    "name": "John Doe",
                    "email": "john@example.com",
                    "username": "john",
                    "firstName": "John",
                    "lastName": "Doe",
                    "enabled": True
                }
            ]
        }
        mock_graphql_client.execute_query.return_value = mock_response
        
        result = await user_repository.find_user_by_id("nonexistent-id")
        
        assert result is None


class TestFindUserByEmail:
    """Tests for find_user_by_email method."""
    
    @pytest.mark.asyncio
    async def test_find_user_by_email_exact_match(self, user_repository, mock_graphql_client):
        """Test finding user by exact email match."""
        target_email = "jane@example.com"
        mock_response = {
            "findUsers": [
                {
                    "id": "user-1",
                    "name": "John Doe",
                    "email": "john@example.com",
                    "username": "john",
                    "firstName": "John",
                    "lastName": "Doe",
                    "enabled": True
                },
                {
                    "id": "user-2",
                    "name": "Jane Smith",
                    "email": target_email,
                    "username": "jane",
                    "firstName": "Jane",
                    "lastName": "Smith",
                    "enabled": True
                }
            ]
        }
        mock_graphql_client.execute_query.return_value = mock_response
        
        result = await user_repository.find_user_by_email(target_email)
        
        assert result is not None
        assert result.email == target_email
        assert result.username == "jane"
    
    @pytest.mark.asyncio
    async def test_find_user_by_email_case_insensitive(self, user_repository, mock_graphql_client):
        """Test email search is case-insensitive."""
        mock_response = {
            "findUsers": [
                {
                    "id": "user-1",
                    "name": "John Doe",
                    "email": "John@Example.COM",
                    "username": "john",
                    "firstName": "John",
                    "lastName": "Doe",
                    "enabled": True
                }
            ]
        }
        mock_graphql_client.execute_query.return_value = mock_response
        
        result = await user_repository.find_user_by_email("john@example.com")
        
        assert result is not None
        assert result.username == "john"


class TestFindUsersPage:
    """Tests for find_users_page method with pagination."""
    
    @pytest.mark.asyncio
    async def test_find_users_page_with_results(self, user_repository, mock_graphql_client):
        """Test paginated user retrieval."""
        mock_response = {
            "findUsersPage": {
                "users": [
                    {
                        "id": "user-1",
                        "name": "John Doe",
                        "email": "john@example.com",
                        "username": "john",
                        "firstName": "John",
                        "lastName": "Doe",
                        "enabled": True
                    }
                ],
                "page": 0,
                "totalHits": 25
            }
        }
        mock_graphql_client.execute_query.return_value = mock_response
        
        result = await user_repository.find_users_page(page=0, size=10)
        
        assert len(result["users"]) == 1
        assert result["page"] == 0
        assert result["totalHits"] == 25
        assert all(isinstance(user, CwayUser) for user in result["users"])
    
    @pytest.mark.asyncio
    async def test_find_users_page_empty(self, user_repository, mock_graphql_client):
        """Test pagination with no results."""
        mock_graphql_client.execute_query.return_value = {}
        
        result = await user_repository.find_users_page()
        
        assert result["users"] == []
        assert result["page"] == 0
        assert result["totalHits"] == 0


class TestSearchUsers:
    """Tests for search_users method."""
    
    @pytest.mark.asyncio
    async def test_search_users_with_query(self, user_repository, mock_graphql_client):
        """Test searching users by username."""
        mock_response = {
            "findUsers": [
                {
                    "id": "user-1",
                    "name": "John Doe",
                    "email": "john@example.com",
                    "username": "john",
                    "firstName": "John",
                    "lastName": "Doe",
                    "enabled": True
                },
                {
                    "id": "user-2",
                    "name": "Johnny Smith",
                    "email": "johnny@example.com",
                    "username": "johnny",
                    "firstName": "Johnny",
                    "lastName": "Smith",
                    "enabled": True
                }
            ]
        }
        mock_graphql_client.execute_query.return_value = mock_response
        
        result = await user_repository.search_users(query="john")
        
        assert len(result) == 2
        assert all(isinstance(user, CwayUser) for user in result)
    
    @pytest.mark.asyncio
    async def test_search_users_no_results(self, user_repository, mock_graphql_client):
        """Test search with no matching users."""
        mock_graphql_client.execute_query.return_value = {}
        
        result = await user_repository.search_users(query="nonexistent")
        
        assert result == []


class TestCreateUser:
    """Tests for create_user method."""
    
    @pytest.mark.asyncio
    async def test_create_user_with_full_name(self, user_repository, mock_graphql_client):
        """Test creating user with first and last name."""
        email = "new@example.com"
        username = "newuser"
        first_name = "New"
        last_name = "User"
        
        mock_response = {
            "createUser": {
                "id": "user-new",
                "name": f"{first_name} {last_name}",
                "email": email,
                "username": username,
                "firstName": first_name,
                "lastName": last_name,
                "enabled": True
            }
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await user_repository.create_user(email, username, first_name, last_name)
        
        assert isinstance(result, CwayUser)
        assert result.email == email
        assert result.username == username
        assert result.firstName == first_name
        assert result.lastName == last_name
    
    @pytest.mark.asyncio
    async def test_create_user_minimal(self, user_repository, mock_graphql_client):
        """Test creating user with just email and username."""
        email = "minimal@example.com"
        username = "minimal"
        
        mock_response = {
            "createUser": {
                "id": "user-minimal",
                "name": username,
                "email": email,
                "username": username,
                "firstName": None,
                "lastName": None,
                "enabled": True
            }
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await user_repository.create_user(email, username)
        
        assert result.email == email
        assert result.username == username
        assert result.firstName is None


class TestUpdateUserName:
    """Tests for update_user_name method."""
    
    @pytest.mark.asyncio
    async def test_update_user_name_both_names(self, user_repository, mock_graphql_client):
        """Test updating both first and last name."""
        username = "testuser"
        first_name = "Updated"
        last_name = "Name"
        
        mock_response = {
            "setUserRealName": {
                "id": "user-1",
                "username": username,
                "firstName": first_name,
                "lastName": last_name,
                "name": f"{first_name} {last_name}",
                "email": "test@example.com",
                "enabled": True
            }
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await user_repository.update_user_name(username, first_name, last_name)
        
        assert result is not None
        assert result.firstName == first_name
        assert result.lastName == last_name
    
    @pytest.mark.asyncio
    async def test_update_user_name_not_found(self, user_repository, mock_graphql_client):
        """Test updating non-existent user."""
        mock_graphql_client.execute_mutation.return_value = {}
        
        result = await user_repository.update_user_name("nonexistent")
        
        assert result is None


class TestDeleteUser:
    """Tests for delete_user method."""
    
    @pytest.mark.asyncio
    async def test_delete_user_success(self, user_repository, mock_graphql_client):
        """Test successful user deletion."""
        username = "userToDelete"
        
        mock_response = {
            "deleteUsers": True
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await user_repository.delete_user(username)
        
        assert result is True
        
        # Verify username was passed as array
        call_args = mock_graphql_client.execute_mutation.call_args
        assert call_args[0][1]["usernames"] == [username]
    
    @pytest.mark.asyncio
    async def test_delete_user_failed(self, user_repository, mock_graphql_client):
        """Test failed user deletion."""
        mock_response = {
            "deleteUsers": False
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await user_repository.delete_user("nonexistent")
        
        assert result is False


class TestFindUsersAndTeams:
    """Tests for find_users_and_teams method."""
    
    @pytest.mark.asyncio
    async def test_find_users_and_teams_mixed(self, user_repository, mock_graphql_client):
        """Test finding both users and teams."""
        mock_response = {
            "findUsersAndTeamsPage": {
                "usersOrTeams": [
                    {
                        "__typename": "User",
                        "id": "user-1",
                        "name": "John Doe",
                        "username": "john",
                        "email": "john@example.com",
                        "firstName": "John",
                        "lastName": "Doe",
                        "enabled": True
                    },
                    {
                        "__typename": "Team",
                        "id": "team-1",
                        "name": "Development Team",
                        "teamLeadUser": {
                            "username": "john",
                            "name": "John Doe"
                        }
                    }
                ],
                "page": 0,
                "totalHits": 2
            }
        }
        mock_graphql_client.execute_query.return_value = mock_response
        
        result = await user_repository.find_users_and_teams(search="dev")
        
        assert len(result["items"]) == 2
        assert result["items"][0]["__typename"] == "User"
        assert result["items"][1]["__typename"] == "Team"
        assert result["totalHits"] == 2
    
    @pytest.mark.asyncio
    async def test_find_users_and_teams_empty(self, user_repository, mock_graphql_client):
        """Test search with no results."""
        mock_graphql_client.execute_query.return_value = {}
        
        result = await user_repository.find_users_and_teams(search="nonexistent")
        
        assert result["items"] == []
        assert result["totalHits"] == 0


class TestGetPermissionGroups:
    """Tests for get_permission_groups method."""
    
    @pytest.mark.asyncio
    async def test_get_permission_groups_multiple(self, user_repository, mock_graphql_client):
        """Test getting all permission groups."""
        mock_response = {
            "getPermissionGroups": [
                {
                    "id": "perm-1",
                    "name": "Admin",
                    "description": "Full system access",
                    "permissions": ["read", "write", "delete", "manage_users"]
                },
                {
                    "id": "perm-2",
                    "name": "Editor",
                    "description": "Can edit content",
                    "permissions": ["read", "write"]
                },
                {
                    "id": "perm-3",
                    "name": "Viewer",
                    "description": "Read-only access",
                    "permissions": ["read"]
                }
            ]
        }
        mock_graphql_client.execute_query.return_value = mock_response
        
        result = await user_repository.get_permission_groups()
        
        assert len(result) == 3
        assert result[0]["name"] == "Admin"
        assert "manage_users" in result[0]["permissions"]
        assert result[2]["permissions"] == ["read"]
    
    @pytest.mark.asyncio
    async def test_get_permission_groups_empty(self, user_repository, mock_graphql_client):
        """Test when no permission groups exist."""
        mock_graphql_client.execute_query.return_value = {}
        
        result = await user_repository.get_permission_groups()
        
        assert result == []


class TestSetUserPermissions:
    """Tests for set_user_permissions method."""
    
    @pytest.mark.asyncio
    async def test_set_user_permissions_single_user(self, user_repository, mock_graphql_client):
        """Test setting permissions for single user."""
        usernames = ["testuser"]
        perm_group_id = "perm-123"
        
        mock_response = {
            "setPermissionGroupForUsers": True
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await user_repository.set_user_permissions(usernames, perm_group_id)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_set_user_permissions_multiple_users(self, user_repository, mock_graphql_client):
        """Test bulk permission update."""
        usernames = ["user1", "user2", "user3"]
        perm_group_id = "perm-editor"
        
        mock_response = {
            "setPermissionGroupForUsers": True
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await user_repository.set_user_permissions(usernames, perm_group_id)
        
        assert result is True
        
        # Verify all usernames were passed
        call_args = mock_graphql_client.execute_mutation.call_args
        assert call_args[0][1]["usernames"] == usernames
    
    @pytest.mark.asyncio
    async def test_set_user_permissions_failed(self, user_repository, mock_graphql_client):
        """Test failed permission update."""
        mock_response = {
            "setPermissionGroupForUsers": False
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await user_repository.set_user_permissions(["user"], "invalid-perm")
        
        assert result is False


class TestErrorHandling:
    """Tests for error handling across UserRepository."""
    
    @pytest.mark.asyncio
    async def test_find_all_users_error(self, user_repository, mock_graphql_client):
        """Test error handling in find_all_users."""
        mock_graphql_client.execute_query.side_effect = Exception("Database error")
        
        with pytest.raises(CwayAPIError, match="Failed to fetch users"):
            await user_repository.find_all_users()
    
    @pytest.mark.asyncio
    async def test_create_user_error(self, user_repository, mock_graphql_client):
        """Test error handling in user creation."""
        mock_graphql_client.execute_mutation.side_effect = Exception("Duplicate username")
        
        with pytest.raises(CwayAPIError, match="Failed to create user"):
            await user_repository.create_user("test@example.com", "duplicate")
    
    @pytest.mark.asyncio
    async def test_search_users_error(self, user_repository, mock_graphql_client):
        """Test error handling in search."""
        mock_graphql_client.execute_query.side_effect = Exception("Search timeout")
        
        with pytest.raises(CwayAPIError, match="Failed to search users"):
            await user_repository.search_users(query="test")
    
    @pytest.mark.asyncio
    async def test_set_permissions_error(self, user_repository, mock_graphql_client):
        """Test error handling in permission updates."""
        mock_graphql_client.execute_mutation.side_effect = Exception("Permission denied")
        
        with pytest.raises(CwayAPIError, match="Failed to set user permissions"):
            await user_repository.set_user_permissions(["user"], "perm-123")
