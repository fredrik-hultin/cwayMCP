"""Unit tests for ArtworkRepository.

Focus on high-value business logic:
- Approval workflow (approve/reject)
- Version control (get versions, restore)
- Artwork lifecycle (create, archive, duplicate)
- Error handling
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.infrastructure.repositories.artwork_repository import ArtworkRepository
from src.infrastructure.graphql_client import CwayAPIError


@pytest.fixture
def mock_graphql_client():
    """Create a mock GraphQL client."""
    client = MagicMock()
    client.execute_query = AsyncMock()
    client.execute_mutation = AsyncMock()
    return client


@pytest.fixture
def artwork_repository(mock_graphql_client):
    """Create an ArtworkRepository with mocked client."""
    repo = ArtworkRepository(mock_graphql_client)
    return repo


class TestApproveArtwork:
    """Tests for approve_artwork method - critical workflow."""
    
    @pytest.mark.asyncio
    async def test_approve_artwork_success(self, artwork_repository, mock_graphql_client):
        """Test successful artwork approval."""
        artwork_id = "art-123"
        mock_response = {
            "approveArtwork": {
                "id": artwork_id,
                "name": "Test Artwork",
                "state": "approved"
            }
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await artwork_repository.approve_artwork(artwork_id)
        
        assert result["id"] == artwork_id
        assert result["state"] == "approved"
        mock_graphql_client.execute_mutation.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_approve_artwork_not_found(self, artwork_repository, mock_graphql_client):
        """Test error when artwork doesn't exist."""
        artwork_id = "nonexistent-art"
        mock_graphql_client.execute_mutation.return_value = {}
        
        result = await artwork_repository.approve_artwork(artwork_id)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_approve_artwork_already_approved(self, artwork_repository, mock_graphql_client):
        """Test approving already approved artwork (idempotent)."""
        artwork_id = "art-approved"
        mock_response = {
            "approveArtwork": {
                "id": artwork_id,
                "name": "Already Approved",
                "state": "approved"
            }
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await artwork_repository.approve_artwork(artwork_id)
        
        assert result["state"] == "approved"


class TestRejectArtwork:
    """Tests for reject_artwork method - critical workflow."""
    
    @pytest.mark.asyncio
    async def test_reject_artwork_with_reason(self, artwork_repository, mock_graphql_client):
        """Test rejecting artwork with specific reason."""
        artwork_id = "art-123"
        reason = "Colors don't match brand guidelines"
        
        mock_response = {
            "rejectArtwork": {
                "id": artwork_id,
                "name": "Test Artwork",
                "state": "rejected"
            }
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await artwork_repository.reject_artwork(artwork_id, reason)
        
        assert result["id"] == artwork_id
        assert result["state"] == "rejected"
        
        # Verify reason was included in the call
        call_args = mock_graphql_client.execute_mutation.call_args
        assert call_args[0][1]["input"]["reason"] == reason
    
    @pytest.mark.asyncio
    async def test_reject_artwork_without_reason(self, artwork_repository, mock_graphql_client):
        """Test rejecting artwork without providing reason."""
        artwork_id = "art-123"
        
        mock_response = {
            "rejectArtwork": {
                "id": artwork_id,
                "name": "Test Artwork",
                "state": "rejected"
            }
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await artwork_repository.reject_artwork(artwork_id)
        
        assert result["id"] == artwork_id
        assert result["state"] == "rejected"
        
        # Verify reason was not included
        call_args = mock_graphql_client.execute_mutation.call_args
        assert "reason" not in call_args[0][1]["input"] or call_args[0][1]["input"]["reason"] is None


class TestGetArtworkVersions:
    """Tests for get_artwork_versions method - version control."""
    
    @pytest.mark.asyncio
    async def test_get_artwork_versions_multiple(self, artwork_repository, mock_graphql_client):
        """Test getting multiple versions of an artwork."""
        artwork_id = "art-123"
        mock_response = {
            "artworkVersions": [
                {
                    "id": "ver-1",
                    "revisionNumber": 1,
                    "created": "2024-01-01T00:00:00Z",
                    "comment": "Initial version",
                    "status": "archived"
                },
                {
                    "id": "ver-2",
                    "revisionNumber": 2,
                    "created": "2024-01-02T00:00:00Z",
                    "comment": "Updated colors",
                    "status": "archived"
                },
                {
                    "id": "ver-3",
                    "revisionNumber": 3,
                    "created": "2024-01-03T00:00:00Z",
                    "comment": "Final version",
                    "status": "current"
                }
            ]
        }
        mock_graphql_client.execute_query.return_value = mock_response
        
        result = await artwork_repository.get_artwork_versions(artwork_id)
        
        assert len(result) == 3
        assert result[0]["revisionNumber"] == 1
        assert result[2]["status"] == "current"
        assert result[2]["revisionNumber"] == 3
    
    @pytest.mark.asyncio
    async def test_get_artwork_versions_single(self, artwork_repository, mock_graphql_client):
        """Test artwork with only one version."""
        artwork_id = "art-new"
        mock_response = {
            "artworkVersions": [
                {
                    "id": "ver-1",
                    "revisionNumber": 1,
                    "created": "2024-01-01T00:00:00Z",
                    "comment": "Initial version",
                    "status": "current"
                }
            ]
        }
        mock_graphql_client.execute_query.return_value = mock_response
        
        result = await artwork_repository.get_artwork_versions(artwork_id)
        
        assert len(result) == 1
        assert result[0]["status"] == "current"


class TestRestoreArtworkVersion:
    """Tests for restore_artwork_version method - version control."""
    
    @pytest.mark.asyncio
    async def test_restore_version_success(self, artwork_repository, mock_graphql_client):
        """Test successful version restoration."""
        artwork_id = "art-123"
        version_id = "ver-2"
        
        mock_response = {
            "restoreArtworkVersion": {
                "id": artwork_id,
                "name": "Test Artwork",
                "currentRevision": {
                    "id": version_id,
                    "revisionNumber": 2
                }
            }
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await artwork_repository.restore_artwork_version(artwork_id, version_id)
        
        assert result["id"] == artwork_id
        assert result["currentRevision"]["id"] == version_id
        assert result["currentRevision"]["revisionNumber"] == 2
    
    @pytest.mark.asyncio
    async def test_restore_version_not_found(self, artwork_repository, mock_graphql_client):
        """Test error when version doesn't exist."""
        artwork_id = "art-123"
        version_id = "nonexistent-ver"
        mock_graphql_client.execute_mutation.return_value = {}
        
        result = await artwork_repository.restore_artwork_version(artwork_id, version_id)
        
        assert result == {}


class TestCreateArtwork:
    """Tests for create_artwork method."""
    
    @pytest.mark.asyncio
    async def test_create_artwork_with_description(self, artwork_repository, mock_graphql_client):
        """Test creating artwork with description."""
        project_id = "proj-123"
        name = "New Artwork"
        description = "Test description"
        
        mock_response = {
            "createArtwork": {
                "id": "batch-1",
                "artworks": [
                    {
                        "id": "art-new",
                        "name": name,
                        "state": "draft"
                    }
                ]
            }
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await artwork_repository.create_artwork(project_id, name, description)
        
        assert result["id"] == "art-new"
        assert result["name"] == name
        assert result["state"] == "draft"
    
    @pytest.mark.asyncio
    async def test_create_artwork_without_description(self, artwork_repository, mock_graphql_client):
        """Test creating artwork without description."""
        project_id = "proj-123"
        name = "Simple Artwork"
        
        mock_response = {
            "createArtwork": {
                "id": "batch-1",
                "artworks": [
                    {
                        "id": "art-simple",
                        "name": name,
                        "state": "draft"
                    }
                ]
            }
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await artwork_repository.create_artwork(project_id, name)
        
        assert result["id"] == "art-simple"
        assert result["name"] == name


class TestDuplicateArtwork:
    """Tests for duplicate_artwork method."""
    
    @pytest.mark.asyncio
    async def test_duplicate_with_new_name(self, artwork_repository, mock_graphql_client):
        """Test duplicating artwork with new name."""
        artwork_id = "art-original"
        new_name = "Copy of Artwork"
        
        mock_response = {
            "duplicateArtwork": {
                "id": "art-copy",
                "name": new_name,
                "projectId": "proj-123",
                "created": "2024-01-05T00:00:00Z"
            }
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await artwork_repository.duplicate_artwork(artwork_id, new_name)
        
        assert result["id"] == "art-copy"
        assert result["name"] == new_name
        assert result["id"] != artwork_id  # Different ID
    
    @pytest.mark.asyncio
    async def test_duplicate_without_new_name(self, artwork_repository, mock_graphql_client):
        """Test duplicating with auto-generated name."""
        artwork_id = "art-original"
        
        mock_response = {
            "duplicateArtwork": {
                "id": "art-copy",
                "name": "Artwork (Copy)",
                "projectId": "proj-123",
                "created": "2024-01-05T00:00:00Z"
            }
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await artwork_repository.duplicate_artwork(artwork_id)
        
        assert result["id"] == "art-copy"
        assert "(Copy)" in result["name"]
    
    @pytest.mark.asyncio
    async def test_duplicate_not_found(self, artwork_repository, mock_graphql_client):
        """Test error when original artwork doesn't exist."""
        artwork_id = "nonexistent-art"
        mock_graphql_client.execute_mutation.return_value = {}
        
        with pytest.raises(CwayAPIError, match="artwork not found"):
            await artwork_repository.duplicate_artwork(artwork_id)


class TestArchiveArtwork:
    """Tests for archive_artwork method."""
    
    @pytest.mark.asyncio
    async def test_archive_artwork_success(self, artwork_repository, mock_graphql_client):
        """Test successful artwork archiving."""
        artwork_id = "art-old"
        
        mock_response = {
            "archiveArtwork": {
                "id": artwork_id,
                "name": "Old Artwork",
                "archived": True,
                "status": "archived"
            }
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await artwork_repository.archive_artwork(artwork_id)
        
        assert result["id"] == artwork_id
        assert result["archived"] is True
        assert result["status"] == "archived"
    
    @pytest.mark.asyncio
    async def test_archive_artwork_not_found(self, artwork_repository, mock_graphql_client):
        """Test error when artwork doesn't exist."""
        artwork_id = "nonexistent-art"
        mock_graphql_client.execute_mutation.return_value = {}
        
        with pytest.raises(CwayAPIError, match="artwork not found"):
            await artwork_repository.archive_artwork(artwork_id)


class TestUnarchiveArtwork:
    """Tests for unarchive_artwork method."""
    
    @pytest.mark.asyncio
    async def test_unarchive_artwork_success(self, artwork_repository, mock_graphql_client):
        """Test successful artwork unarchiving."""
        artwork_id = "art-archived"
        
        mock_response = {
            "unarchiveArtwork": {
                "id": artwork_id,
                "name": "Restored Artwork",
                "archived": False,
                "status": "active"
            }
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await artwork_repository.unarchive_artwork(artwork_id)
        
        assert result["id"] == artwork_id
        assert result["archived"] is False
        assert result["status"] == "active"


class TestAssignArtwork:
    """Tests for assign_artwork method."""
    
    @pytest.mark.asyncio
    async def test_assign_artwork_success(self, artwork_repository, mock_graphql_client):
        """Test successful artwork assignment."""
        artwork_id = "art-123"
        user_id = "user-456"
        
        mock_response = {
            "assignArtwork": {
                "id": artwork_id,
                "name": "Test Artwork",
                "assignedTo": {
                    "id": user_id,
                    "name": "John Doe",
                    "username": "john"
                }
            }
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await artwork_repository.assign_artwork(artwork_id, user_id)
        
        assert result["id"] == artwork_id
        assert result["assignedTo"]["id"] == user_id
        assert result["assignedTo"]["username"] == "john"
    
    @pytest.mark.asyncio
    async def test_assign_artwork_not_found(self, artwork_repository, mock_graphql_client):
        """Test error when artwork doesn't exist."""
        artwork_id = "nonexistent-art"
        user_id = "user-456"
        mock_graphql_client.execute_mutation.return_value = {}
        
        with pytest.raises(CwayAPIError, match="artwork not found"):
            await artwork_repository.assign_artwork(artwork_id, user_id)


class TestGetArtworksToApprove:
    """Tests for get_artworks_to_approve method."""
    
    @pytest.mark.asyncio
    async def test_get_artworks_to_approve_multiple(self, artwork_repository, mock_graphql_client):
        """Test getting multiple artworks awaiting approval."""
        mock_response = {
            "artworksToApprove": [
                {
                    "id": "art-1",
                    "projectId": "proj-1",
                    "projectName": "Project A",
                    "name": "Artwork 1",
                    "state": "pending_approval",
                    "status": "awaiting_review"
                },
                {
                    "id": "art-2",
                    "projectId": "proj-2",
                    "projectName": "Project B",
                    "name": "Artwork 2",
                    "state": "pending_approval",
                    "status": "awaiting_review"
                }
            ]
        }
        mock_graphql_client.execute_query.return_value = mock_response
        
        result = await artwork_repository.get_artworks_to_approve()
        
        assert len(result) == 2
        assert all(art["state"] == "pending_approval" for art in result)
    
    @pytest.mark.asyncio
    async def test_get_artworks_to_approve_empty(self, artwork_repository, mock_graphql_client):
        """Test when no artworks need approval."""
        mock_graphql_client.execute_query.return_value = {}
        
        result = await artwork_repository.get_artworks_to_approve()
        
        assert result == []


class TestErrorHandling:
    """Tests for error handling across ArtworkRepository."""
    
    @pytest.mark.asyncio
    async def test_query_error_propagation(self, artwork_repository, mock_graphql_client):
        """Test that query errors are properly wrapped."""
        artwork_id = "art-123"
        mock_graphql_client.execute_query.side_effect = Exception("Network timeout")
        
        with pytest.raises(CwayAPIError, match="Failed to get artwork"):
            await artwork_repository.get_artwork(artwork_id)
    
    @pytest.mark.asyncio
    async def test_mutation_error_propagation(self, artwork_repository, mock_graphql_client):
        """Test that mutation errors are properly handled."""
        artwork_id = "art-123"
        mock_graphql_client.execute_mutation.side_effect = Exception("Permission denied")
        
        with pytest.raises(CwayAPIError, match="Failed to approve artwork"):
            await artwork_repository.approve_artwork(artwork_id)
