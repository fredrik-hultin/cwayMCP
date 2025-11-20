"""
Unit tests for Phase 3.3 - Team & Permission Management Tools.

Tests the following tools:
1. get_team_members - Get all team members for a project
2. add_team_member - Add user to project team
3. remove_team_member - Remove user from project team
4. update_team_member_role - Update team member's role
5. get_user_roles - Get all available user roles
6. transfer_project_ownership - Transfer project ownership

Total: 6 tools, 24 tests
"""

import pytest
from unittest.mock import AsyncMock

from src.infrastructure.cway_repositories import CwayProjectRepository
from src.infrastructure.graphql_client import CwayAPIError


@pytest.fixture
def mock_graphql_client():
    """Create a mock GraphQL client"""
    mock = AsyncMock()
    mock.execute_query = AsyncMock()
    mock.execute_mutation = AsyncMock()
    return mock


@pytest.fixture
def project_repo(mock_graphql_client):
    """Create a CwayProjectRepository with mocked client"""
    return CwayProjectRepository(mock_graphql_client)


# ============================================================================
# GET_TEAM_MEMBERS TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_get_team_members_success(project_repo, mock_graphql_client):
    """Test successful team members retrieval."""
    mock_response = {
        "project": {
            "team": [
                {
                    "id": "member-1",
                    "user": {
                        "id": "user-1",
                        "username": "john_doe",
                        "firstName": "John",
                        "lastName": "Doe",
                        "email": "john@example.com"
                    },
                    "role": "ADMIN",
                    "addedAt": "2024-01-01T10:00:00Z"
                },
                {
                    "id": "member-2",
                    "user": {
                        "id": "user-2",
                        "username": "jane_smith",
                        "firstName": "Jane",
                        "lastName": "Smith",
                        "email": "jane@example.com"
                    },
                    "role": "MEMBER",
                    "addedAt": "2024-01-05T14:00:00Z"
                }
            ]
        }
    }
    
    mock_graphql_client.execute_query.return_value = mock_response
    
    result = await project_repo.get_team_members("project-123")
    
    assert len(result) == 2
    assert result[0]["user"]["username"] == "john_doe"
    assert result[1]["role"] == "MEMBER"


@pytest.mark.asyncio
async def test_get_team_members_empty(project_repo, mock_graphql_client):
    """Test getting team members when project has no team."""
    mock_response = {"project": {"team": []}}
    mock_graphql_client.execute_query.return_value = mock_response
    
    result = await project_repo.get_team_members("project-123")
    
    assert result == []


@pytest.mark.asyncio
async def test_get_team_members_invalid_project(project_repo, mock_graphql_client):
    """Test getting team members with invalid project ID."""
    mock_graphql_client.execute_query.return_value = {"project": None}
    
    with pytest.raises(CwayAPIError, match="Failed to get team members: project not found"):
        await project_repo.get_team_members("invalid-project")


@pytest.mark.asyncio
async def test_get_team_members_api_error(project_repo, mock_graphql_client):
    """Test getting team members with GraphQL API error."""
    mock_graphql_client.execute_query.side_effect = Exception("Network timeout")
    
    with pytest.raises(CwayAPIError, match="Failed to get team members"):
        await project_repo.get_team_members("project-123")


# ============================================================================
# ADD_TEAM_MEMBER TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_add_team_member_with_role(project_repo, mock_graphql_client):
    """Test successfully adding team member with specific role."""
    mock_response = {
        "addTeamMember": {
            "id": "member-3",
            "user": {
                "id": "user-3",
                "username": "bob_wilson",
                "firstName": "Bob",
                "lastName": "Wilson"
            },
            "role": "EDITOR",
            "addedAt": "2024-01-15T10:00:00Z"
        }
    }
    
    mock_graphql_client.execute_mutation.return_value = mock_response
    
    result = await project_repo.add_team_member("project-123", "user-3", "EDITOR")
    
    assert result["user"]["username"] == "bob_wilson"
    assert result["role"] == "EDITOR"


@pytest.mark.asyncio
async def test_add_team_member_without_role(project_repo, mock_graphql_client):
    """Test successfully adding team member without specifying role."""
    mock_response = {
        "addTeamMember": {
            "id": "member-4",
            "user": {
                "id": "user-4",
                "username": "alice_jones",
                "firstName": "Alice",
                "lastName": "Jones"
            },
            "role": "MEMBER",
            "addedAt": "2024-01-15T11:00:00Z"
        }
    }
    
    mock_graphql_client.execute_mutation.return_value = mock_response
    
    result = await project_repo.add_team_member("project-123", "user-4")
    
    assert result["user"]["username"] == "alice_jones"
    assert result["role"] == "MEMBER"


@pytest.mark.asyncio
async def test_add_team_member_operation_failed(project_repo, mock_graphql_client):
    """Test adding team member when operation fails."""
    mock_graphql_client.execute_mutation.return_value = {"addTeamMember": None}
    
    with pytest.raises(CwayAPIError, match="Failed to add team member: operation failed"):
        await project_repo.add_team_member("project-123", "user-5", "ADMIN")


@pytest.mark.asyncio
async def test_add_team_member_api_error(project_repo, mock_graphql_client):
    """Test adding team member with GraphQL API error."""
    mock_graphql_client.execute_mutation.side_effect = Exception("Permission denied")
    
    with pytest.raises(CwayAPIError, match="Failed to add team member"):
        await project_repo.add_team_member("project-123", "user-5")


# ============================================================================
# REMOVE_TEAM_MEMBER TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_remove_team_member_success(project_repo, mock_graphql_client):
    """Test successfully removing team member."""
    mock_response = {
        "removeTeamMember": {
            "success": True,
            "message": "Team member removed successfully"
        }
    }
    
    mock_graphql_client.execute_mutation.return_value = mock_response
    
    result = await project_repo.remove_team_member("project-123", "user-2")
    
    assert result["success"] is True
    assert "removed successfully" in result["message"]


@pytest.mark.asyncio
async def test_remove_team_member_not_found(project_repo, mock_graphql_client):
    """Test removing team member that doesn't exist."""
    mock_response = {
        "removeTeamMember": {
            "success": False,
            "message": "User not found in project team"
        }
    }
    
    mock_graphql_client.execute_mutation.return_value = mock_response
    
    with pytest.raises(CwayAPIError, match="Failed to remove team member: operation failed"):
        await project_repo.remove_team_member("project-123", "user-999")


@pytest.mark.asyncio
async def test_remove_team_member_operation_failed(project_repo, mock_graphql_client):
    """Test removing team member when operation returns None."""
    mock_graphql_client.execute_mutation.return_value = {"removeTeamMember": None}
    
    with pytest.raises(CwayAPIError, match="Failed to remove team member: operation failed"):
        await project_repo.remove_team_member("project-123", "user-2")


@pytest.mark.asyncio
async def test_remove_team_member_api_error(project_repo, mock_graphql_client):
    """Test removing team member with GraphQL API error."""
    mock_graphql_client.execute_mutation.side_effect = Exception("Database error")
    
    with pytest.raises(CwayAPIError, match="Failed to remove team member"):
        await project_repo.remove_team_member("project-123", "user-2")


# ============================================================================
# UPDATE_TEAM_MEMBER_ROLE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_update_team_member_role_success(project_repo, mock_graphql_client):
    """Test successfully updating team member role."""
    mock_response = {
        "updateTeamMemberRole": {
            "id": "member-1",
            "user": {
                "id": "user-1",
                "username": "john_doe",
                "firstName": "John",
                "lastName": "Doe"
            },
            "role": "ADMIN",
            "updatedAt": "2024-01-15T12:00:00Z"
        }
    }
    
    mock_graphql_client.execute_mutation.return_value = mock_response
    
    result = await project_repo.update_team_member_role("project-123", "user-1", "ADMIN")
    
    assert result["user"]["username"] == "john_doe"
    assert result["role"] == "ADMIN"
    assert "updatedAt" in result


@pytest.mark.asyncio
async def test_update_team_member_role_downgrade(project_repo, mock_graphql_client):
    """Test downgrading team member role."""
    mock_response = {
        "updateTeamMemberRole": {
            "id": "member-1",
            "user": {
                "id": "user-1",
                "username": "john_doe",
                "firstName": "John",
                "lastName": "Doe"
            },
            "role": "VIEWER",
            "updatedAt": "2024-01-15T13:00:00Z"
        }
    }
    
    mock_graphql_client.execute_mutation.return_value = mock_response
    
    result = await project_repo.update_team_member_role("project-123", "user-1", "VIEWER")
    
    assert result["role"] == "VIEWER"


@pytest.mark.asyncio
async def test_update_team_member_role_operation_failed(project_repo, mock_graphql_client):
    """Test updating team member role when operation fails."""
    mock_graphql_client.execute_mutation.return_value = {"updateTeamMemberRole": None}
    
    with pytest.raises(CwayAPIError, match="Failed to update team member role: operation failed"):
        await project_repo.update_team_member_role("project-123", "user-1", "ADMIN")


@pytest.mark.asyncio
async def test_update_team_member_role_api_error(project_repo, mock_graphql_client):
    """Test updating team member role with GraphQL API error."""
    mock_graphql_client.execute_mutation.side_effect = Exception("Connection lost")
    
    with pytest.raises(CwayAPIError, match="Failed to update team member role"):
        await project_repo.update_team_member_role("project-123", "user-1", "ADMIN")


# ============================================================================
# GET_USER_ROLES TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_get_user_roles_success(project_repo, mock_graphql_client):
    """Test successfully retrieving user roles."""
    mock_response = {
        "userRoles": [
            {
                "id": "role-1",
                "name": "ADMIN",
                "description": "Full access to all features",
                "permissions": ["read", "write", "delete", "manage_users"]
            },
            {
                "id": "role-2",
                "name": "EDITOR",
                "description": "Can edit content",
                "permissions": ["read", "write"]
            },
            {
                "id": "role-3",
                "name": "VIEWER",
                "description": "Read-only access",
                "permissions": ["read"]
            }
        ]
    }
    
    mock_graphql_client.execute_query.return_value = mock_response
    
    result = await project_repo.get_user_roles()
    
    assert len(result) == 3
    assert result[0]["name"] == "ADMIN"
    assert len(result[0]["permissions"]) == 4
    assert result[2]["name"] == "VIEWER"


@pytest.mark.asyncio
async def test_get_user_roles_empty(project_repo, mock_graphql_client):
    """Test getting user roles when none exist."""
    mock_graphql_client.execute_query.return_value = {"userRoles": []}
    
    result = await project_repo.get_user_roles()
    
    assert result == []


@pytest.mark.asyncio
async def test_get_user_roles_missing_key(project_repo, mock_graphql_client):
    """Test getting user roles when key is missing."""
    mock_graphql_client.execute_query.return_value = {}
    
    result = await project_repo.get_user_roles()
    
    assert result == []


@pytest.mark.asyncio
async def test_get_user_roles_api_error(project_repo, mock_graphql_client):
    """Test getting user roles with GraphQL API error."""
    mock_graphql_client.execute_query.side_effect = Exception("Timeout")
    
    with pytest.raises(CwayAPIError, match="Failed to get user roles"):
        await project_repo.get_user_roles()


# ============================================================================
# TRANSFER_PROJECT_OWNERSHIP TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_transfer_project_ownership_success(project_repo, mock_graphql_client):
    """Test successfully transferring project ownership."""
    mock_response = {
        "transferProjectOwnership": {
            "id": "project-123",
            "name": "Marketing Campaign",
            "owner": {
                "id": "user-5",
                "username": "new_owner",
                "firstName": "New",
                "lastName": "Owner"
            },
            "updatedAt": "2024-01-15T14:00:00Z"
        }
    }
    
    mock_graphql_client.execute_mutation.return_value = mock_response
    
    result = await project_repo.transfer_project_ownership("project-123", "user-5")
    
    assert result["owner"]["username"] == "new_owner"
    assert result["owner"]["id"] == "user-5"
    assert "updatedAt" in result


@pytest.mark.asyncio
async def test_transfer_project_ownership_to_admin(project_repo, mock_graphql_client):
    """Test transferring project ownership to admin user."""
    mock_response = {
        "transferProjectOwnership": {
            "id": "project-456",
            "name": "Website Redesign",
            "owner": {
                "id": "admin-1",
                "username": "admin_user",
                "firstName": "Admin",
                "lastName": "User"
            },
            "updatedAt": "2024-01-15T15:00:00Z"
        }
    }
    
    mock_graphql_client.execute_mutation.return_value = mock_response
    
    result = await project_repo.transfer_project_ownership("project-456", "admin-1")
    
    assert result["owner"]["username"] == "admin_user"


@pytest.mark.asyncio
async def test_transfer_project_ownership_operation_failed(project_repo, mock_graphql_client):
    """Test transferring project ownership when operation fails."""
    mock_graphql_client.execute_mutation.return_value = {"transferProjectOwnership": None}
    
    with pytest.raises(CwayAPIError, match="Failed to transfer project ownership: operation failed"):
        await project_repo.transfer_project_ownership("project-123", "user-5")


@pytest.mark.asyncio
async def test_transfer_project_ownership_api_error(project_repo, mock_graphql_client):
    """Test transferring project ownership with GraphQL API error."""
    mock_graphql_client.execute_mutation.side_effect = Exception("User not found")
    
    with pytest.raises(CwayAPIError, match="Failed to transfer project ownership"):
        await project_repo.transfer_project_ownership("project-123", "invalid-user")
