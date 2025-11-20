"""Unit tests for TeamRepository.

Focus on critical business logic:
- Team member operations
- Role management
- Ownership transfer
- Error handling
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.infrastructure.repositories.team_repository import TeamRepository
from src.infrastructure.graphql_client import CwayAPIError


@pytest.fixture
def mock_graphql_client():
    """Create a mock GraphQL client."""
    client = MagicMock()
    client.execute_query = AsyncMock()
    client.execute_mutation = AsyncMock()
    return client


@pytest.fixture
def team_repository(mock_graphql_client):
    """Create a TeamRepository with mocked client."""
    repo = TeamRepository(mock_graphql_client)
    return repo


class TestGetTeamMembers:
    """Tests for get_team_members method."""
    
    @pytest.mark.asyncio
    async def test_get_team_members_success(self, team_repository, mock_graphql_client):
        """Test successful retrieval of team members."""
        project_id = "proj-123"
        mock_response = {
            "project": {
                "team": [
                    {
                        "id": "tm-1",
                        "user": {
                            "id": "user-1",
                            "username": "john",
                            "firstName": "John",
                            "lastName": "Doe",
                            "email": "john@example.com"
                        },
                        "role": "owner",
                        "addedAt": "2024-01-01T00:00:00Z"
                    },
                    {
                        "id": "tm-2",
                        "user": {
                            "id": "user-2",
                            "username": "jane",
                            "firstName": "Jane",
                            "lastName": "Smith",
                            "email": "jane@example.com"
                        },
                        "role": "member",
                        "addedAt": "2024-01-02T00:00:00Z"
                    }
                ]
            }
        }
        mock_graphql_client.execute_query.return_value = mock_response
        
        result = await team_repository.get_team_members(project_id)
        
        assert len(result) == 2
        assert result[0]["user"]["username"] == "john"
        assert result[0]["role"] == "owner"
        assert result[1]["user"]["username"] == "jane"
        assert result[1]["role"] == "member"
        mock_graphql_client.execute_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_team_members_project_not_found(self, team_repository, mock_graphql_client):
        """Test error when project not found."""
        project_id = "nonexistent-proj"
        mock_graphql_client.execute_query.return_value = {}
        
        with pytest.raises(CwayAPIError, match="project not found"):
            await team_repository.get_team_members(project_id)
    
    @pytest.mark.asyncio
    async def test_get_team_members_empty_team(self, team_repository, mock_graphql_client):
        """Test project with no team members."""
        project_id = "proj-123"
        mock_response = {"project": {"team": []}}
        mock_graphql_client.execute_query.return_value = mock_response
        
        result = await team_repository.get_team_members(project_id)
        
        assert result == []


class TestAddTeamMember:
    """Tests for add_team_member method."""
    
    @pytest.mark.asyncio
    async def test_add_team_member_with_role(self, team_repository, mock_graphql_client):
        """Test adding team member with specific role."""
        project_id = "proj-123"
        user_id = "user-456"
        role = "editor"
        
        mock_response = {
            "addTeamMember": {
                "id": "tm-new",
                "user": {
                    "id": user_id,
                    "username": "newuser",
                    "firstName": "New",
                    "lastName": "User"
                },
                "role": role,
                "addedAt": "2024-01-03T00:00:00Z"
            }
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await team_repository.add_team_member(project_id, user_id, role)
        
        assert result["user"]["id"] == user_id
        assert result["role"] == role
        mock_graphql_client.execute_mutation.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_team_member_without_role(self, team_repository, mock_graphql_client):
        """Test adding team member without specifying role (default role)."""
        project_id = "proj-123"
        user_id = "user-456"
        
        mock_response = {
            "addTeamMember": {
                "id": "tm-new",
                "user": {
                    "id": user_id,
                    "username": "newuser",
                    "firstName": "New",
                    "lastName": "User"
                },
                "role": "member",  # Default role
                "addedAt": "2024-01-03T00:00:00Z"
            }
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await team_repository.add_team_member(project_id, user_id)
        
        assert result["user"]["id"] == user_id
        assert result["role"] == "member"
    
    @pytest.mark.asyncio
    async def test_add_team_member_operation_failed(self, team_repository, mock_graphql_client):
        """Test error when add operation fails."""
        project_id = "proj-123"
        user_id = "user-456"
        mock_graphql_client.execute_mutation.return_value = {}
        
        with pytest.raises(CwayAPIError, match="operation failed"):
            await team_repository.add_team_member(project_id, user_id)


class TestRemoveTeamMember:
    """Tests for remove_team_member method."""
    
    @pytest.mark.asyncio
    async def test_remove_team_member_success(self, team_repository, mock_graphql_client):
        """Test successful team member removal."""
        project_id = "proj-123"
        user_id = "user-456"
        
        mock_response = {
            "removeTeamMember": {
                "success": True,
                "message": "User removed from project team"
            }
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await team_repository.remove_team_member(project_id, user_id)
        
        assert result["success"] is True
        assert "removed" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_remove_team_member_not_found(self, team_repository, mock_graphql_client):
        """Test error when user not in team."""
        project_id = "proj-123"
        user_id = "nonexistent-user"
        mock_graphql_client.execute_mutation.return_value = {
            "removeTeamMember": {"success": False, "message": "User not found"}
        }
        
        with pytest.raises(CwayAPIError, match="operation failed"):
            await team_repository.remove_team_member(project_id, user_id)


class TestUpdateTeamMemberRole:
    """Tests for update_team_member_role method."""
    
    @pytest.mark.asyncio
    async def test_update_role_success(self, team_repository, mock_graphql_client):
        """Test successful role update."""
        project_id = "proj-123"
        user_id = "user-456"
        new_role = "admin"
        
        mock_response = {
            "updateTeamMemberRole": {
                "id": "tm-1",
                "user": {
                    "id": user_id,
                    "username": "testuser",
                    "firstName": "Test",
                    "lastName": "User"
                },
                "role": new_role,
                "updatedAt": "2024-01-04T00:00:00Z"
            }
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await team_repository.update_team_member_role(project_id, user_id, new_role)
        
        assert result["user"]["id"] == user_id
        assert result["role"] == new_role
        assert "updatedAt" in result
    
    @pytest.mark.asyncio
    async def test_update_role_invalid_role(self, team_repository, mock_graphql_client):
        """Test error with invalid role."""
        project_id = "proj-123"
        user_id = "user-456"
        invalid_role = "superadmin"
        mock_graphql_client.execute_mutation.return_value = {}
        
        with pytest.raises(CwayAPIError, match="operation failed"):
            await team_repository.update_team_member_role(project_id, user_id, invalid_role)


class TestGetUserRoles:
    """Tests for get_user_roles method."""
    
    @pytest.mark.asyncio
    async def test_get_user_roles_success(self, team_repository, mock_graphql_client):
        """Test successful retrieval of available roles."""
        mock_response = {
            "userRoles": [
                {
                    "id": "role-1",
                    "name": "owner",
                    "description": "Project owner",
                    "permissions": ["read", "write", "delete", "manage_team"]
                },
                {
                    "id": "role-2",
                    "name": "editor",
                    "description": "Can edit content",
                    "permissions": ["read", "write"]
                },
                {
                    "id": "role-3",
                    "name": "viewer",
                    "description": "Read-only access",
                    "permissions": ["read"]
                }
            ]
        }
        mock_graphql_client.execute_query.return_value = mock_response
        
        result = await team_repository.get_user_roles()
        
        assert len(result) == 3
        assert result[0]["name"] == "owner"
        assert "manage_team" in result[0]["permissions"]
        assert result[2]["name"] == "viewer"
        assert result[2]["permissions"] == ["read"]
    
    @pytest.mark.asyncio
    async def test_get_user_roles_empty(self, team_repository, mock_graphql_client):
        """Test when no roles are defined."""
        mock_graphql_client.execute_query.return_value = {}
        
        result = await team_repository.get_user_roles()
        
        assert result == []


class TestTransferProjectOwnership:
    """Tests for transfer_project_ownership method."""
    
    @pytest.mark.asyncio
    async def test_transfer_ownership_success(self, team_repository, mock_graphql_client):
        """Test successful ownership transfer."""
        project_id = "proj-123"
        new_owner_id = "user-789"
        
        mock_response = {
            "transferProjectOwnership": {
                "id": project_id,
                "name": "Test Project",
                "owner": {
                    "id": new_owner_id,
                    "username": "newowner",
                    "firstName": "New",
                    "lastName": "Owner"
                },
                "updatedAt": "2024-01-05T00:00:00Z"
            }
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await team_repository.transfer_project_ownership(project_id, new_owner_id)
        
        assert result["id"] == project_id
        assert result["owner"]["id"] == new_owner_id
        assert result["owner"]["username"] == "newowner"
        assert "updatedAt" in result
    
    @pytest.mark.asyncio
    async def test_transfer_ownership_new_owner_not_found(self, team_repository, mock_graphql_client):
        """Test error when new owner doesn't exist."""
        project_id = "proj-123"
        new_owner_id = "nonexistent-user"
        mock_graphql_client.execute_mutation.return_value = {}
        
        with pytest.raises(CwayAPIError, match="operation failed"):
            await team_repository.transfer_project_ownership(project_id, new_owner_id)
    
    @pytest.mark.asyncio
    async def test_transfer_ownership_same_user(self, team_repository, mock_graphql_client):
        """Test transferring ownership to current owner (edge case)."""
        project_id = "proj-123"
        current_owner_id = "user-current"
        
        mock_response = {
            "transferProjectOwnership": {
                "id": project_id,
                "name": "Test Project",
                "owner": {
                    "id": current_owner_id,
                    "username": "currentowner",
                    "firstName": "Current",
                    "lastName": "Owner"
                },
                "updatedAt": "2024-01-05T00:00:00Z"
            }
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await team_repository.transfer_project_ownership(project_id, current_owner_id)
        
        assert result["owner"]["id"] == current_owner_id


class TestErrorHandling:
    """Tests for error handling across TeamRepository."""
    
    @pytest.mark.asyncio
    async def test_graphql_client_error_propagation(self, team_repository, mock_graphql_client):
        """Test that GraphQL client errors are properly wrapped."""
        project_id = "proj-123"
        mock_graphql_client.execute_query.side_effect = Exception("Network error")
        
        with pytest.raises(CwayAPIError, match="Failed to get team members"):
            await team_repository.get_team_members(project_id)
    
    @pytest.mark.asyncio
    async def test_mutation_error_propagation(self, team_repository, mock_graphql_client):
        """Test that mutation errors are properly handled."""
        project_id = "proj-123"
        user_id = "user-456"
        mock_graphql_client.execute_mutation.side_effect = Exception("Permission denied")
        
        with pytest.raises(CwayAPIError, match="Failed to add team member"):
            await team_repository.add_team_member(project_id, user_id)
