"""
Unit tests for Phase 3.2 - Advanced Artwork Management Tools.

Tests the following tools:
1. assign_artwork - Assign artwork to user
2. duplicate_artwork - Duplicate artwork with optional new name
3. archive_artwork - Archive an artwork
4. unarchive_artwork - Unarchive an artwork

Total: 4 tools, 16 tests
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
# ASSIGN ARTWORK TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_assign_artwork_success(project_repo, mock_graphql_client):
    """Test successful artwork assignment to user."""
    mock_response = {
        "assignArtwork": {
            "id": "artwork-123",
            "name": "Logo Design",
            "assignedTo": {
                "id": "user-456",
                "username": "designer1",
                "firstName": "John",
                "lastName": "Doe"
            },
            "status": "IN_PROGRESS",
            "updatedAt": "2024-01-15T10:00:00Z"
        }
    }
    
    mock_graphql_client.execute_mutation.return_value = mock_response
    
    result = await project_repo.assign_artwork("artwork-123", "user-456")
    
    assert result["id"] == "artwork-123"
    assert result["assignedTo"]["id"] == "user-456"
    assert result["assignedTo"]["username"] == "designer1"
    assert result["status"] == "IN_PROGRESS"


@pytest.mark.asyncio
async def test_assign_artwork_invalid_artwork(project_repo, mock_graphql_client):
    """Test artwork assignment with invalid artwork ID."""
    mock_graphql_client.execute_mutation.return_value = {"assignArtwork": None}
    
    with pytest.raises(CwayAPIError, match="Failed to assign artwork"):
        await project_repo.assign_artwork("invalid-artwork", "user-456")


@pytest.mark.asyncio
async def test_assign_artwork_invalid_user(project_repo, mock_graphql_client):
    """Test artwork assignment with invalid user ID."""
    mock_graphql_client.execute_mutation.side_effect = Exception("User not found")
    
    with pytest.raises(CwayAPIError, match="Failed to assign artwork"):
        await project_repo.assign_artwork("artwork-123", "invalid-user")


@pytest.mark.asyncio
async def test_assign_artwork_api_error(project_repo, mock_graphql_client):
    """Test artwork assignment with GraphQL API error."""
    mock_graphql_client.execute_mutation.side_effect = Exception("Network timeout")
    
    with pytest.raises(CwayAPIError, match="Failed to assign artwork"):
        await project_repo.assign_artwork("artwork-123", "user-456")


# ============================================================================
# DUPLICATE ARTWORK TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_duplicate_artwork_with_new_name(project_repo, mock_graphql_client):
    """Test successful artwork duplication with new name."""
    mock_response = {
        "duplicateArtwork": {
            "id": "artwork-789",
            "name": "Logo Design (Copy)",
            "description": "Duplicated artwork",
            "status": "DRAFT",
            "projectId": "project-123",
            "createdAt": "2024-01-15T10:00:00Z",
            "updatedAt": "2024-01-15T10:00:00Z"
        }
    }
    
    mock_graphql_client.execute_mutation.return_value = mock_response
    
    result = await project_repo.duplicate_artwork("artwork-123", "Logo Design (Copy)")
    
    assert result["id"] == "artwork-789"
    assert result["name"] == "Logo Design (Copy)"
    assert result["status"] == "DRAFT"


@pytest.mark.asyncio
async def test_duplicate_artwork_without_new_name(project_repo, mock_graphql_client):
    """Test successful artwork duplication without providing new name."""
    mock_response = {
        "duplicateArtwork": {
            "id": "artwork-789",
            "name": "Logo Design - Copy",
            "description": "Duplicated artwork",
            "status": "DRAFT",
            "projectId": "project-123",
            "createdAt": "2024-01-15T10:00:00Z",
            "updatedAt": "2024-01-15T10:00:00Z"
        }
    }
    
    mock_graphql_client.execute_mutation.return_value = mock_response
    
    result = await project_repo.duplicate_artwork("artwork-123")
    
    assert result["id"] == "artwork-789"
    assert "Copy" in result["name"]
    assert result["status"] == "DRAFT"


@pytest.mark.asyncio
async def test_duplicate_artwork_invalid_artwork(project_repo, mock_graphql_client):
    """Test artwork duplication with invalid artwork ID."""
    mock_graphql_client.execute_mutation.return_value = {"duplicateArtwork": None}
    
    with pytest.raises(CwayAPIError, match="Failed to duplicate artwork"):
        await project_repo.duplicate_artwork("invalid-artwork")


@pytest.mark.asyncio
async def test_duplicate_artwork_api_error(project_repo, mock_graphql_client):
    """Test artwork duplication with GraphQL API error."""
    mock_graphql_client.execute_mutation.side_effect = Exception("Database error")
    
    with pytest.raises(CwayAPIError, match="Failed to duplicate artwork"):
        await project_repo.duplicate_artwork("artwork-123", "New Name")


# ============================================================================
# ARCHIVE ARTWORK TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_archive_artwork_success(project_repo, mock_graphql_client):
    """Test successful artwork archiving."""
    mock_response = {
        "archiveArtwork": {
            "id": "artwork-123",
            "name": "Logo Design",
            "archived": True,
            "status": "ARCHIVED",
            "archivedAt": "2024-01-15T10:00:00Z",
            "updatedAt": "2024-01-15T10:00:00Z"
        }
    }
    
    mock_graphql_client.execute_mutation.return_value = mock_response
    
    result = await project_repo.archive_artwork("artwork-123")
    
    assert result["id"] == "artwork-123"
    assert result["archived"] is True
    assert result["status"] == "ARCHIVED"
    assert "archivedAt" in result


@pytest.mark.asyncio
async def test_archive_artwork_already_archived(project_repo, mock_graphql_client):
    """Test archiving an already archived artwork."""
    mock_response = {
        "archiveArtwork": {
            "id": "artwork-123",
            "name": "Logo Design",
            "archived": True,
            "status": "ARCHIVED",
            "archivedAt": "2024-01-14T09:00:00Z",
            "updatedAt": "2024-01-14T09:00:00Z"
        }
    }
    
    mock_graphql_client.execute_mutation.return_value = mock_response
    
    result = await project_repo.archive_artwork("artwork-123")
    
    assert result["archived"] is True
    assert result["status"] == "ARCHIVED"


@pytest.mark.asyncio
async def test_archive_artwork_invalid_artwork(project_repo, mock_graphql_client):
    """Test archiving with invalid artwork ID."""
    mock_graphql_client.execute_mutation.return_value = {"archiveArtwork": None}
    
    with pytest.raises(CwayAPIError, match="Failed to archive artwork"):
        await project_repo.archive_artwork("invalid-artwork")


@pytest.mark.asyncio
async def test_archive_artwork_api_error(project_repo, mock_graphql_client):
    """Test archiving with GraphQL API error."""
    mock_graphql_client.execute_mutation.side_effect = Exception("Permission denied")
    
    with pytest.raises(CwayAPIError, match="Failed to archive artwork"):
        await project_repo.archive_artwork("artwork-123")


# ============================================================================
# UNARCHIVE ARTWORK TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_unarchive_artwork_success(project_repo, mock_graphql_client):
    """Test successful artwork unarchiving."""
    mock_response = {
        "unarchiveArtwork": {
            "id": "artwork-123",
            "name": "Logo Design",
            "archived": False,
            "status": "DRAFT",
            "archivedAt": None,
            "updatedAt": "2024-01-15T10:00:00Z"
        }
    }
    
    mock_graphql_client.execute_mutation.return_value = mock_response
    
    result = await project_repo.unarchive_artwork("artwork-123")
    
    assert result["id"] == "artwork-123"
    assert result["archived"] is False
    assert result["status"] == "DRAFT"
    assert result["archivedAt"] is None


@pytest.mark.asyncio
async def test_unarchive_artwork_already_active(project_repo, mock_graphql_client):
    """Test unarchiving an already active artwork."""
    mock_response = {
        "unarchiveArtwork": {
            "id": "artwork-123",
            "name": "Logo Design",
            "archived": False,
            "status": "IN_PROGRESS",
            "archivedAt": None,
            "updatedAt": "2024-01-10T08:00:00Z"
        }
    }
    
    mock_graphql_client.execute_mutation.return_value = mock_response
    
    result = await project_repo.unarchive_artwork("artwork-123")
    
    assert result["archived"] is False
    assert result["status"] == "IN_PROGRESS"


@pytest.mark.asyncio
async def test_unarchive_artwork_invalid_artwork(project_repo, mock_graphql_client):
    """Test unarchiving with invalid artwork ID."""
    mock_graphql_client.execute_mutation.return_value = {"unarchiveArtwork": None}
    
    with pytest.raises(CwayAPIError, match="Failed to unarchive artwork"):
        await project_repo.unarchive_artwork("invalid-artwork")


@pytest.mark.asyncio
async def test_unarchive_artwork_api_error(project_repo, mock_graphql_client):
    """Test unarchiving with GraphQL API error."""
    mock_graphql_client.execute_mutation.side_effect = Exception("Connection lost")
    
    with pytest.raises(CwayAPIError, match="Failed to unarchive artwork"):
        await project_repo.unarchive_artwork("artwork-123")
