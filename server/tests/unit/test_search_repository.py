"""Unit tests for SearchRepository.

Focus on critical operations:
- Search with filters and pagination
- Bulk artwork status updates
- Project timeline tracking
- Error handling
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.infrastructure.repositories.search_repository import SearchRepository
from src.infrastructure.graphql_client import CwayAPIError


@pytest.fixture
def mock_graphql_client():
    """Create a mock GraphQL client."""
    client = MagicMock()
    client.execute_query = AsyncMock()
    client.execute_mutation = AsyncMock()
    return client


@pytest.fixture
def search_repository(mock_graphql_client):
    """Create a SearchRepository with mocked client."""
    repo = SearchRepository(mock_graphql_client)
    return repo


class TestSearchArtworks:
    """Tests for search_artworks method."""
    
    @pytest.mark.asyncio
    async def test_search_with_all_filters(self, search_repository, mock_graphql_client):
        """Test search with query, project, status, and pagination."""
        mock_response = {
            "searchArtworks": {
                "artworks": [
                    {
                        "id": "art-1",
                        "name": "Logo Design",
                        "status": "approved",
                        "projectId": "proj-123"
                    },
                    {
                        "id": "art-2",
                        "name": "Logo Variant",
                        "status": "approved",
                        "projectId": "proj-123"
                    }
                ],
                "totalHits": 2,
                "page": 0
            }
        }
        mock_graphql_client.execute_query.return_value = mock_response
        
        result = await search_repository.search_artworks(
            query="logo",
            project_id="proj-123",
            status="approved",
            limit=50,
            page=0
        )
        
        assert len(result["artworks"]) == 2
        assert result["totalHits"] == 2
        assert result["page"] == 0
        assert all(art["status"] == "approved" for art in result["artworks"])
    
    @pytest.mark.asyncio
    async def test_search_without_filters(self, search_repository, mock_graphql_client):
        """Test search without any filters (get all)."""
        mock_response = {
            "searchArtworks": {
                "artworks": [
                    {"id": "art-1", "name": "Art 1"},
                    {"id": "art-2", "name": "Art 2"},
                    {"id": "art-3", "name": "Art 3"}
                ],
                "totalHits": 3,
                "page": 0
            }
        }
        mock_graphql_client.execute_query.return_value = mock_response
        
        result = await search_repository.search_artworks()
        
        assert len(result["artworks"]) == 3
        assert result["totalHits"] == 3
    
    @pytest.mark.asyncio
    async def test_search_with_pagination(self, search_repository, mock_graphql_client):
        """Test search with pagination parameters."""
        mock_response = {
            "searchArtworks": {
                "artworks": [
                    {"id": "art-11", "name": "Art 11"},
                    {"id": "art-12", "name": "Art 12"}
                ],
                "totalHits": 25,
                "page": 1
            }
        }
        mock_graphql_client.execute_query.return_value = mock_response
        
        result = await search_repository.search_artworks(limit=10, page=1)
        
        assert result["page"] == 1
        assert result["totalHits"] == 25
        assert len(result["artworks"]) == 2  # Partial page
    
    @pytest.mark.asyncio
    async def test_search_no_results(self, search_repository, mock_graphql_client):
        """Test search with no matching results."""
        mock_graphql_client.execute_query.return_value = {}
        
        result = await search_repository.search_artworks(query="nonexistent")
        
        assert result["artworks"] == []
        assert result["totalHits"] == 0
        assert result["page"] == 0
    
    @pytest.mark.asyncio
    async def test_search_error_handling(self, search_repository, mock_graphql_client):
        """Test error handling in search."""
        mock_graphql_client.execute_query.side_effect = Exception("Search service unavailable")
        
        with pytest.raises(CwayAPIError, match="Failed to search artworks"):
            await search_repository.search_artworks(query="test")


class TestBulkUpdateArtworkStatus:
    """Tests for bulk_update_artwork_status method - critical batch operation."""
    
    @pytest.mark.asyncio
    async def test_bulk_update_success_all(self, search_repository, mock_graphql_client):
        """Test successful bulk update of all artworks."""
        artwork_ids = ["art-1", "art-2", "art-3"]
        new_status = "approved"
        
        mock_response = {
            "bulkUpdateArtworkStatus": {
                "updatedArtworks": [
                    {"id": "art-1", "name": "Art 1", "status": "approved", "updated": "2024-01-01T00:00:00Z"},
                    {"id": "art-2", "name": "Art 2", "status": "approved", "updated": "2024-01-01T00:00:00Z"},
                    {"id": "art-3", "name": "Art 3", "status": "approved", "updated": "2024-01-01T00:00:00Z"}
                ],
                "successCount": 3,
                "failedCount": 0
            }
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await search_repository.bulk_update_artwork_status(artwork_ids, new_status)
        
        assert result["successCount"] == 3
        assert result["failedCount"] == 0
        assert len(result["updatedArtworks"]) == 3
        assert all(art["status"] == "approved" for art in result["updatedArtworks"])
    
    @pytest.mark.asyncio
    async def test_bulk_update_partial_success(self, search_repository, mock_graphql_client):
        """Test bulk update with some failures."""
        artwork_ids = ["art-1", "art-2", "art-invalid"]
        new_status = "rejected"
        
        mock_response = {
            "bulkUpdateArtworkStatus": {
                "updatedArtworks": [
                    {"id": "art-1", "name": "Art 1", "status": "rejected", "updated": "2024-01-01T00:00:00Z"},
                    {"id": "art-2", "name": "Art 2", "status": "rejected", "updated": "2024-01-01T00:00:00Z"}
                ],
                "successCount": 2,
                "failedCount": 1
            }
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await search_repository.bulk_update_artwork_status(artwork_ids, new_status)
        
        assert result["successCount"] == 2
        assert result["failedCount"] == 1
        assert len(result["updatedArtworks"]) == 2
    
    @pytest.mark.asyncio
    async def test_bulk_update_single_artwork(self, search_repository, mock_graphql_client):
        """Test bulk update with single artwork (edge case)."""
        artwork_ids = ["art-1"]
        new_status = "in_progress"
        
        mock_response = {
            "bulkUpdateArtworkStatus": {
                "updatedArtworks": [
                    {"id": "art-1", "name": "Art 1", "status": "in_progress", "updated": "2024-01-01T00:00:00Z"}
                ],
                "successCount": 1,
                "failedCount": 0
            }
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await search_repository.bulk_update_artwork_status(artwork_ids, new_status)
        
        assert result["successCount"] == 1
        assert len(result["updatedArtworks"]) == 1
    
    @pytest.mark.asyncio
    async def test_bulk_update_operation_failed(self, search_repository, mock_graphql_client):
        """Test error when bulk operation fails completely."""
        artwork_ids = ["art-1", "art-2"]
        new_status = "approved"
        mock_graphql_client.execute_mutation.return_value = {}
        
        with pytest.raises(CwayAPIError, match="operation failed"):
            await search_repository.bulk_update_artwork_status(artwork_ids, new_status)
    
    @pytest.mark.asyncio
    async def test_bulk_update_empty_list(self, search_repository, mock_graphql_client):
        """Test bulk update with empty artwork list."""
        artwork_ids = []
        new_status = "approved"
        
        mock_response = {
            "bulkUpdateArtworkStatus": {
                "updatedArtworks": [],
                "successCount": 0,
                "failedCount": 0
            }
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await search_repository.bulk_update_artwork_status(artwork_ids, new_status)
        
        assert result["successCount"] == 0
        assert result["updatedArtworks"] == []


class TestGetProjectTimeline:
    """Tests for get_project_timeline method."""
    
    @pytest.mark.asyncio
    async def test_get_timeline_multiple_events(self, search_repository, mock_graphql_client):
        """Test getting project timeline with multiple events."""
        project_id = "proj-123"
        mock_response = {
            "projectTimeline": [
                {
                    "id": "evt-1",
                    "eventType": "created",
                    "description": "Project created",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "actor": {
                        "id": "user-1",
                        "username": "john",
                        "firstName": "John",
                        "lastName": "Doe"
                    },
                    "metadata": {}
                },
                {
                    "id": "evt-2",
                    "eventType": "artwork_added",
                    "description": "Artwork 'Logo' added",
                    "timestamp": "2024-01-02T00:00:00Z",
                    "actor": {
                        "id": "user-2",
                        "username": "jane",
                        "firstName": "Jane",
                        "lastName": "Smith"
                    },
                    "metadata": {"artwork_id": "art-1"}
                },
                {
                    "id": "evt-3",
                    "eventType": "status_changed",
                    "description": "Status changed to Active",
                    "timestamp": "2024-01-03T00:00:00Z",
                    "actor": {
                        "id": "user-1",
                        "username": "john",
                        "firstName": "John",
                        "lastName": "Doe"
                    },
                    "metadata": {"old_status": "draft", "new_status": "active"}
                }
            ]
        }
        mock_graphql_client.execute_query.return_value = mock_response
        
        result = await search_repository.get_project_timeline(project_id)
        
        assert len(result) == 3
        assert result[0]["eventType"] == "created"
        assert result[1]["eventType"] == "artwork_added"
        assert result[2]["eventType"] == "status_changed"
        assert all("actor" in evt for evt in result)
    
    @pytest.mark.asyncio
    async def test_get_timeline_with_limit(self, search_repository, mock_graphql_client):
        """Test timeline retrieval with custom limit."""
        project_id = "proj-123"
        mock_response = {
            "projectTimeline": [
                {"id": "evt-1", "eventType": "created", "timestamp": "2024-01-01T00:00:00Z"},
                {"id": "evt-2", "eventType": "updated", "timestamp": "2024-01-02T00:00:00Z"}
            ]
        }
        mock_graphql_client.execute_query.return_value = mock_response
        
        result = await search_repository.get_project_timeline(project_id, limit=2)
        
        assert len(result) == 2
        
        # Verify limit was passed to GraphQL
        call_args = mock_graphql_client.execute_query.call_args
        assert call_args[0][1]["limit"] == 2
    
    @pytest.mark.asyncio
    async def test_get_timeline_empty(self, search_repository, mock_graphql_client):
        """Test timeline for new project with no events."""
        project_id = "proj-new"
        mock_graphql_client.execute_query.return_value = {}
        
        result = await search_repository.get_project_timeline(project_id)
        
        assert result == []


class TestGetUserActivity:
    """Tests for get_user_activity method."""
    
    @pytest.mark.asyncio
    async def test_get_user_activity_multiple(self, search_repository, mock_graphql_client):
        """Test getting user activity across multiple projects."""
        user_id = "user-123"
        mock_response = {
            "userActivity": [
                {
                    "id": "act-1",
                    "activityType": "artwork_approved",
                    "description": "Approved artwork 'Logo'",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "projectId": "proj-1",
                    "projectName": "Project A",
                    "artworkId": "art-1",
                    "artworkName": "Logo",
                    "metadata": {}
                },
                {
                    "id": "act-2",
                    "activityType": "comment_added",
                    "description": "Commented on project",
                    "timestamp": "2024-01-02T00:00:00Z",
                    "projectId": "proj-2",
                    "projectName": "Project B",
                    "artworkId": None,
                    "artworkName": None,
                    "metadata": {"comment": "Looks good"}
                }
            ]
        }
        mock_graphql_client.execute_query.return_value = mock_response
        
        result = await search_repository.get_user_activity(user_id, days=30)
        
        assert len(result) == 2
        assert result[0]["activityType"] == "artwork_approved"
        assert result[1]["activityType"] == "comment_added"
        assert all("projectName" in act for act in result)
    
    @pytest.mark.asyncio
    async def test_get_user_activity_with_custom_params(self, search_repository, mock_graphql_client):
        """Test user activity with custom days and limit."""
        user_id = "user-123"
        mock_response = {"userActivity": []}
        mock_graphql_client.execute_query.return_value = mock_response
        
        result = await search_repository.get_user_activity(user_id, days=7, limit=10)
        
        # Verify parameters were passed correctly
        call_args = mock_graphql_client.execute_query.call_args
        assert call_args[0][1]["userId"] == user_id
        assert call_args[0][1]["days"] == 7
        assert call_args[0][1]["limit"] == 10
    
    @pytest.mark.asyncio
    async def test_get_user_activity_empty(self, search_repository, mock_graphql_client):
        """Test user with no recent activity."""
        user_id = "user-inactive"
        mock_graphql_client.execute_query.return_value = {}
        
        result = await search_repository.get_user_activity(user_id)
        
        assert result == []


class TestErrorHandling:
    """Tests for error handling across SearchRepository."""
    
    @pytest.mark.asyncio
    async def test_search_network_error(self, search_repository, mock_graphql_client):
        """Test handling of network errors."""
        mock_graphql_client.execute_query.side_effect = Exception("Network timeout")
        
        with pytest.raises(CwayAPIError, match="Failed to search artworks"):
            await search_repository.search_artworks(query="test")
    
    @pytest.mark.asyncio
    async def test_bulk_update_permission_error(self, search_repository, mock_graphql_client):
        """Test handling of permission errors in bulk operations."""
        artwork_ids = ["art-1", "art-2"]
        status = "approved"
        mock_graphql_client.execute_mutation.side_effect = Exception("Permission denied")
        
        with pytest.raises(CwayAPIError, match="Failed to bulk update artwork status"):
            await search_repository.bulk_update_artwork_status(artwork_ids, status)
    
    @pytest.mark.asyncio
    async def test_timeline_error_propagation(self, search_repository, mock_graphql_client):
        """Test that timeline errors are properly wrapped."""
        project_id = "proj-123"
        mock_graphql_client.execute_query.side_effect = Exception("Database error")
        
        with pytest.raises(CwayAPIError, match="Failed to get project timeline"):
            await search_repository.get_project_timeline(project_id)
    
    @pytest.mark.asyncio
    async def test_user_activity_error_propagation(self, search_repository, mock_graphql_client):
        """Test that user activity errors are properly handled."""
        user_id = "user-123"
        mock_graphql_client.execute_query.side_effect = Exception("User not found")
        
        with pytest.raises(CwayAPIError, match="Failed to get user activity"):
            await search_repository.get_user_activity(user_id)
