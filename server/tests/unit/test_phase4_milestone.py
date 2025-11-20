"""
Unit tests for Phase 4 - 100-Tool Milestone: Search & Activity Tools.

Tests the following tools:
1. search_artworks - Search artworks with filters and pagination
2. get_project_timeline - Get chronological event timeline
3. get_user_activity - Get user activity history
4. bulk_update_artwork_status - Batch update artwork status

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
# SEARCH_ARTWORKS TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_search_artworks_with_all_filters(project_repo, mock_graphql_client):
    """Test searching artworks with all filters applied."""
    mock_response = {
        "searchArtworks": {
            "artworks": [
                {
                    "id": "artwork-1",
                    "name": "Logo Design",
                    "description": "Company logo",
                    "status": "APPROVED",
                    "projectId": "project-123",
                    "created": "2024-01-01T10:00:00Z",
                    "updated": "2024-01-15T14:00:00Z"
                },
                {
                    "id": "artwork-2",
                    "name": "Logo Variant",
                    "description": "Alternative logo",
                    "status": "APPROVED",
                    "projectId": "project-123",
                    "created": "2024-01-02T11:00:00Z",
                    "updated": "2024-01-16T15:00:00Z"
                }
            ],
            "totalHits": 2,
            "page": 0
        }
    }
    
    mock_graphql_client.execute_query.return_value = mock_response
    
    result = await project_repo.search_artworks(
        query="logo",
        project_id="project-123",
        status="APPROVED",
        limit=50,
        page=0
    )
    
    assert len(result["artworks"]) == 2
    assert result["totalHits"] == 2
    assert result["artworks"][0]["name"] == "Logo Design"


@pytest.mark.asyncio
async def test_search_artworks_no_filters(project_repo, mock_graphql_client):
    """Test searching artworks without filters."""
    mock_response = {
        "searchArtworks": {
            "artworks": [],
            "totalHits": 0,
            "page": 0
        }
    }
    
    mock_graphql_client.execute_query.return_value = mock_response
    
    result = await project_repo.search_artworks()
    
    assert result["artworks"] == []
    assert result["totalHits"] == 0


@pytest.mark.asyncio
async def test_search_artworks_with_pagination(project_repo, mock_graphql_client):
    """Test searching artworks with pagination."""
    mock_response = {
        "searchArtworks": {
            "artworks": [{"id": f"artwork-{i}", "name": f"Artwork {i}"} for i in range(10)],
            "totalHits": 25,
            "page": 1
        }
    }
    
    mock_graphql_client.execute_query.return_value = mock_response
    
    result = await project_repo.search_artworks(limit=10, page=1)
    
    assert len(result["artworks"]) == 10
    assert result["totalHits"] == 25
    assert result["page"] == 1


@pytest.mark.asyncio
async def test_search_artworks_api_error(project_repo, mock_graphql_client):
    """Test searching artworks with GraphQL API error."""
    mock_graphql_client.execute_query.side_effect = Exception("Search failed")
    
    with pytest.raises(CwayAPIError, match="Failed to search artworks"):
        await project_repo.search_artworks(query="test")


# ============================================================================
# GET_PROJECT_TIMELINE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_get_project_timeline_success(project_repo, mock_graphql_client):
    """Test successfully retrieving project timeline."""
    mock_response = {
        "projectTimeline": [
            {
                "id": "event-1",
                "eventType": "PROJECT_CREATED",
                "description": "Project was created",
                "timestamp": "2024-01-01T10:00:00Z",
                "actor": {
                    "id": "user-1",
                    "username": "john_doe",
                    "firstName": "John",
                    "lastName": "Doe"
                },
                "metadata": {}
            },
            {
                "id": "event-2",
                "eventType": "ARTWORK_ADDED",
                "description": "Artwork 'Logo' was added",
                "timestamp": "2024-01-02T11:00:00Z",
                "actor": {
                    "id": "user-2",
                    "username": "jane_smith",
                    "firstName": "Jane",
                    "lastName": "Smith"
                },
                "metadata": {"artworkId": "artwork-1"}
            }
        ]
    }
    
    mock_graphql_client.execute_query.return_value = mock_response
    
    result = await project_repo.get_project_timeline("project-123")
    
    assert len(result) == 2
    assert result[0]["eventType"] == "PROJECT_CREATED"
    assert result[1]["actor"]["username"] == "jane_smith"


@pytest.mark.asyncio
async def test_get_project_timeline_empty(project_repo, mock_graphql_client):
    """Test getting timeline for project with no events."""
    mock_graphql_client.execute_query.return_value = {"projectTimeline": []}
    
    result = await project_repo.get_project_timeline("project-123")
    
    assert result == []


@pytest.mark.asyncio
async def test_get_project_timeline_with_limit(project_repo, mock_graphql_client):
    """Test getting project timeline with custom limit."""
    mock_response = {
        "projectTimeline": [{"id": f"event-{i}", "eventType": "EVENT"} for i in range(50)]
    }
    
    mock_graphql_client.execute_query.return_value = mock_response
    
    result = await project_repo.get_project_timeline("project-123", limit=50)
    
    assert len(result) == 50


@pytest.mark.asyncio
async def test_get_project_timeline_api_error(project_repo, mock_graphql_client):
    """Test getting project timeline with GraphQL API error."""
    mock_graphql_client.execute_query.side_effect = Exception("Timeline unavailable")
    
    with pytest.raises(CwayAPIError, match="Failed to get project timeline"):
        await project_repo.get_project_timeline("project-123")


# ============================================================================
# GET_USER_ACTIVITY TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_get_user_activity_success(project_repo, mock_graphql_client):
    """Test successfully retrieving user activity."""
    mock_response = {
        "userActivity": [
            {
                "id": "activity-1",
                "activityType": "ARTWORK_CREATED",
                "description": "Created artwork 'Logo Design'",
                "timestamp": "2024-01-15T10:00:00Z",
                "projectId": "project-123",
                "projectName": "Marketing Campaign",
                "artworkId": "artwork-1",
                "artworkName": "Logo Design",
                "metadata": {}
            },
            {
                "id": "activity-2",
                "activityType": "PROJECT_UPDATED",
                "description": "Updated project details",
                "timestamp": "2024-01-14T09:00:00Z",
                "projectId": "project-123",
                "projectName": "Marketing Campaign",
                "artworkId": None,
                "artworkName": None,
                "metadata": {}
            }
        ]
    }
    
    mock_graphql_client.execute_query.return_value = mock_response
    
    result = await project_repo.get_user_activity("user-1")
    
    assert len(result) == 2
    assert result[0]["activityType"] == "ARTWORK_CREATED"
    assert result[0]["projectName"] == "Marketing Campaign"


@pytest.mark.asyncio
async def test_get_user_activity_with_custom_days(project_repo, mock_graphql_client):
    """Test getting user activity with custom day range."""
    mock_response = {
        "userActivity": [{"id": "activity-1", "activityType": "LOGIN"}]
    }
    
    mock_graphql_client.execute_query.return_value = mock_response
    
    result = await project_repo.get_user_activity("user-1", days=7, limit=50)
    
    assert len(result) == 1


@pytest.mark.asyncio
async def test_get_user_activity_empty(project_repo, mock_graphql_client):
    """Test getting activity for inactive user."""
    mock_graphql_client.execute_query.return_value = {"userActivity": []}
    
    result = await project_repo.get_user_activity("user-999")
    
    assert result == []


@pytest.mark.asyncio
async def test_get_user_activity_api_error(project_repo, mock_graphql_client):
    """Test getting user activity with GraphQL API error."""
    mock_graphql_client.execute_query.side_effect = Exception("User not found")
    
    with pytest.raises(CwayAPIError, match="Failed to get user activity"):
        await project_repo.get_user_activity("invalid-user")


# ============================================================================
# BULK_UPDATE_ARTWORK_STATUS TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_bulk_update_artwork_status_success(project_repo, mock_graphql_client):
    """Test successfully bulk updating artwork status."""
    mock_response = {
        "bulkUpdateArtworkStatus": {
            "updatedArtworks": [
                {
                    "id": "artwork-1",
                    "name": "Logo Design",
                    "status": "APPROVED",
                    "updated": "2024-01-15T10:00:00Z"
                },
                {
                    "id": "artwork-2",
                    "name": "Banner",
                    "status": "APPROVED",
                    "updated": "2024-01-15T10:00:01Z"
                },
                {
                    "id": "artwork-3",
                    "name": "Poster",
                    "status": "APPROVED",
                    "updated": "2024-01-15T10:00:02Z"
                }
            ],
            "successCount": 3,
            "failedCount": 0
        }
    }
    
    mock_graphql_client.execute_mutation.return_value = mock_response
    
    result = await project_repo.bulk_update_artwork_status(
        ["artwork-1", "artwork-2", "artwork-3"],
        "APPROVED"
    )
    
    assert len(result["updatedArtworks"]) == 3
    assert result["successCount"] == 3
    assert result["failedCount"] == 0
    assert result["updatedArtworks"][0]["status"] == "APPROVED"


@pytest.mark.asyncio
async def test_bulk_update_artwork_status_partial_failure(project_repo, mock_graphql_client):
    """Test bulk update with some failures."""
    mock_response = {
        "bulkUpdateArtworkStatus": {
            "updatedArtworks": [
                {
                    "id": "artwork-1",
                    "name": "Logo Design",
                    "status": "IN_PROGRESS",
                    "updated": "2024-01-15T10:00:00Z"
                }
            ],
            "successCount": 1,
            "failedCount": 2
        }
    }
    
    mock_graphql_client.execute_mutation.return_value = mock_response
    
    result = await project_repo.bulk_update_artwork_status(
        ["artwork-1", "artwork-2", "artwork-3"],
        "IN_PROGRESS"
    )
    
    assert result["successCount"] == 1
    assert result["failedCount"] == 2


@pytest.mark.asyncio
async def test_bulk_update_artwork_status_operation_failed(project_repo, mock_graphql_client):
    """Test bulk update when operation fails."""
    mock_graphql_client.execute_mutation.return_value = {"bulkUpdateArtworkStatus": None}
    
    with pytest.raises(CwayAPIError, match="Failed to bulk update artwork status: operation failed"):
        await project_repo.bulk_update_artwork_status(["artwork-1"], "APPROVED")


@pytest.mark.asyncio
async def test_bulk_update_artwork_status_api_error(project_repo, mock_graphql_client):
    """Test bulk update with GraphQL API error."""
    mock_graphql_client.execute_mutation.side_effect = Exception("Permission denied")
    
    with pytest.raises(CwayAPIError, match="Failed to bulk update artwork status"):
        await project_repo.bulk_update_artwork_status(["artwork-1"], "APPROVED")
