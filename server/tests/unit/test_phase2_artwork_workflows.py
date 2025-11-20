"""Unit tests for Phase 2.2 artwork workflow tools."""

import pytest
from unittest.mock import AsyncMock
from src.infrastructure.cway_repositories import CwayProjectRepository
from src.infrastructure.graphql_client import CwayAPIError


@pytest.fixture
def mock_graphql_client():
    """Create a mock GraphQL client."""
    client = AsyncMock()
    return client


@pytest.fixture
def project_repo(mock_graphql_client):
    """Create a CwayProjectRepository with mocked client."""
    return CwayProjectRepository(mock_graphql_client)


class TestSubmitArtworkForReview:
    """Tests for submit_artwork_for_review method."""
    
    @pytest.mark.asyncio
    async def test_submit_artwork_success(self, project_repo, mock_graphql_client):
        """Test submitting artwork for review successfully."""
        mock_graphql_client.execute_mutation.return_value = {
            "submitArtworkForReview": {
                "id": "artwork1",
                "name": "Logo Design",
                "state": "PENDING_APPROVAL",
                "status": "SUBMITTED"
            }
        }
        
        result = await project_repo.submit_artwork_for_review("artwork1")
        
        assert result["id"] == "artwork1"
        assert result["state"] == "PENDING_APPROVAL"
        assert result["status"] == "SUBMITTED"
        
    @pytest.mark.asyncio
    async def test_submit_artwork_state_transition(self, project_repo, mock_graphql_client):
        """Test artwork state changes after submission."""
        mock_graphql_client.execute_mutation.return_value = {
            "submitArtworkForReview": {
                "id": "artwork1",
                "name": "Banner",
                "state": "AWAITING_APPROVAL",
                "status": "IN_REVIEW"
            }
        }
        
        result = await project_repo.submit_artwork_for_review("artwork1")
        
        assert result["state"] == "AWAITING_APPROVAL"
        
    @pytest.mark.asyncio
    async def test_submit_artwork_error(self, project_repo, mock_graphql_client):
        """Test error handling when submitting artwork."""
        mock_graphql_client.execute_mutation.side_effect = Exception("API error")
        
        with pytest.raises(CwayAPIError, match="Failed to submit artwork for review"):
            await project_repo.submit_artwork_for_review("artwork1")


class TestRequestArtworkChanges:
    """Tests for request_artwork_changes method."""
    
    @pytest.mark.asyncio
    async def test_request_changes_success(self, project_repo, mock_graphql_client):
        """Test requesting artwork changes successfully."""
        mock_graphql_client.execute_mutation.return_value = {
            "requestArtworkChanges": {
                "id": "artwork1",
                "name": "Logo",
                "state": "CHANGES_REQUESTED",
                "status": "REVISION_NEEDED"
            }
        }
        
        result = await project_repo.request_artwork_changes("artwork1", "Please adjust colors")
        
        assert result["id"] == "artwork1"
        assert result["state"] == "CHANGES_REQUESTED"
        
    @pytest.mark.asyncio
    async def test_request_changes_with_detailed_reason(self, project_repo, mock_graphql_client):
        """Test requesting changes with detailed feedback."""
        detailed_reason = "1. Adjust logo colors to brand guidelines\n2. Increase font size\n3. Fix alignment"
        mock_graphql_client.execute_mutation.return_value = {
            "requestArtworkChanges": {
                "id": "artwork1",
                "name": "Brochure",
                "state": "CHANGES_REQUESTED",
                "status": "REVISION_NEEDED"
            }
        }
        
        result = await project_repo.request_artwork_changes("artwork1", detailed_reason)
        
        assert result["state"] == "CHANGES_REQUESTED"
        call_args = mock_graphql_client.execute_mutation.call_args[0]
        variables = call_args[1]
        assert variables["input"]["reason"] == detailed_reason
        
    @pytest.mark.asyncio
    async def test_request_changes_error(self, project_repo, mock_graphql_client):
        """Test error handling when requesting changes."""
        mock_graphql_client.execute_mutation.side_effect = Exception("API error")
        
        with pytest.raises(CwayAPIError, match="Failed to request artwork changes"):
            await project_repo.request_artwork_changes("artwork1", "Changes needed")


class TestGetArtworkComments:
    """Tests for get_artwork_comments method."""
    
    @pytest.mark.asyncio
    async def test_get_artwork_comments_success(self, project_repo, mock_graphql_client):
        """Test getting artwork comments successfully."""
        mock_graphql_client.execute_query.return_value = {
            "artworkComments": [
                {
                    "id": "comment1",
                    "text": "Looks great!",
                    "author": {"id": "user1", "name": "John", "username": "jdoe"},
                    "created": "2024-01-01T00:00:00Z",
                    "edited": None
                },
                {
                    "id": "comment2",
                    "text": "Please fix the colors",
                    "author": {"id": "user2", "name": "Jane", "username": "jsmith"},
                    "created": "2024-01-02T00:00:00Z",
                    "edited": "2024-01-02T01:00:00Z"
                }
            ]
        }
        
        result = await project_repo.get_artwork_comments("artwork1", limit=50)
        
        assert len(result) == 2
        assert result[0]["text"] == "Looks great!"
        assert result[1]["edited"] is not None
        
    @pytest.mark.asyncio
    async def test_get_artwork_comments_empty(self, project_repo, mock_graphql_client):
        """Test getting comments when none exist."""
        mock_graphql_client.execute_query.return_value = {"artworkComments": []}
        
        result = await project_repo.get_artwork_comments("artwork1")
        
        assert result == []
        
    @pytest.mark.asyncio
    async def test_get_artwork_comments_with_limit(self, project_repo, mock_graphql_client):
        """Test getting comments with custom limit."""
        mock_graphql_client.execute_query.return_value = {"artworkComments": []}
        
        await project_repo.get_artwork_comments("artwork1", limit=20)
        
        call_args = mock_graphql_client.execute_query.call_args[0]
        variables = call_args[1]
        assert variables["limit"] == 20
        
    @pytest.mark.asyncio
    async def test_get_artwork_comments_error(self, project_repo, mock_graphql_client):
        """Test error handling when getting comments."""
        mock_graphql_client.execute_query.side_effect = Exception("API error")
        
        with pytest.raises(CwayAPIError, match="Failed to get artwork comments"):
            await project_repo.get_artwork_comments("artwork1")


class TestAddArtworkComment:
    """Tests for add_artwork_comment method."""
    
    @pytest.mark.asyncio
    async def test_add_artwork_comment_success(self, project_repo, mock_graphql_client):
        """Test adding artwork comment successfully."""
        mock_graphql_client.execute_mutation.return_value = {
            "addArtworkComment": {
                "id": "comment1",
                "text": "Great work!",
                "author": {"id": "user1", "name": "John"},
                "created": "2024-01-01T00:00:00Z"
            }
        }
        
        result = await project_repo.add_artwork_comment("artwork1", "Great work!")
        
        assert result["id"] == "comment1"
        assert result["text"] == "Great work!"
        
    @pytest.mark.asyncio
    async def test_add_artwork_comment_with_long_text(self, project_repo, mock_graphql_client):
        """Test adding comment with long text."""
        long_text = "This is detailed feedback. " * 50
        mock_graphql_client.execute_mutation.return_value = {
            "addArtworkComment": {
                "id": "comment1",
                "text": long_text,
                "author": {"id": "user1", "name": "John"},
                "created": "2024-01-01T00:00:00Z"
            }
        }
        
        result = await project_repo.add_artwork_comment("artwork1", long_text)
        
        assert result["text"] == long_text
        
    @pytest.mark.asyncio
    async def test_add_artwork_comment_with_special_chars(self, project_repo, mock_graphql_client):
        """Test adding comment with special characters."""
        comment_text = "Please update: @designer #important ⭐"
        mock_graphql_client.execute_mutation.return_value = {
            "addArtworkComment": {
                "id": "comment1",
                "text": comment_text,
                "author": {"id": "user1", "name": "John"},
                "created": "2024-01-01T00:00:00Z"
            }
        }
        
        result = await project_repo.add_artwork_comment("artwork1", comment_text)
        
        assert result["text"] == comment_text
        
    @pytest.mark.asyncio
    async def test_add_artwork_comment_error(self, project_repo, mock_graphql_client):
        """Test error handling when adding comment."""
        mock_graphql_client.execute_mutation.side_effect = Exception("API error")
        
        with pytest.raises(CwayAPIError, match="Failed to add artwork comment"):
            await project_repo.add_artwork_comment("artwork1", "Comment")


class TestGetArtworkVersions:
    """Tests for get_artwork_versions method."""
    
    @pytest.mark.asyncio
    async def test_get_artwork_versions_success(self, project_repo, mock_graphql_client):
        """Test getting artwork versions successfully."""
        mock_graphql_client.execute_query.return_value = {
            "artworkVersions": [
                {
                    "id": "version1",
                    "revisionNumber": 1,
                    "created": "2024-01-01T00:00:00Z",
                    "creator": {"id": "user1", "name": "John"},
                    "comment": "Initial version",
                    "files": [{"id": "file1", "name": "logo_v1.png", "fileSize": 1024}]
                },
                {
                    "id": "version2",
                    "revisionNumber": 2,
                    "created": "2024-01-02T00:00:00Z",
                    "creator": {"id": "user1", "name": "John"},
                    "comment": "Updated colors",
                    "files": [{"id": "file2", "name": "logo_v2.png", "fileSize": 2048}]
                },
                {
                    "id": "version3",
                    "revisionNumber": 3,
                    "created": "2024-01-03T00:00:00Z",
                    "creator": {"id": "user2", "name": "Jane"},
                    "comment": "Final version",
                    "files": [{"id": "file3", "name": "logo_v3.png", "fileSize": 3072}]
                }
            ]
        }
        
        result = await project_repo.get_artwork_versions("artwork1")
        
        assert len(result) == 3
        assert result[0]["revisionNumber"] == 1
        assert result[2]["revisionNumber"] == 3
        assert result[2]["creator"]["name"] == "Jane"
        
    @pytest.mark.asyncio
    async def test_get_artwork_versions_single_version(self, project_repo, mock_graphql_client):
        """Test getting single version artwork."""
        mock_graphql_client.execute_query.return_value = {
            "artworkVersions": [
                {
                    "id": "version1",
                    "revisionNumber": 1,
                    "created": "2024-01-01T00:00:00Z",
                    "creator": {"id": "user1", "name": "John"},
                    "comment": "Initial version",
                    "files": []
                }
            ]
        }
        
        result = await project_repo.get_artwork_versions("artwork1")
        
        assert len(result) == 1
        assert result[0]["revisionNumber"] == 1
        
    @pytest.mark.asyncio
    async def test_get_artwork_versions_error(self, project_repo, mock_graphql_client):
        """Test error handling when getting versions."""
        mock_graphql_client.execute_query.side_effect = Exception("API error")
        
        with pytest.raises(CwayAPIError, match="Failed to get artwork versions"):
            await project_repo.get_artwork_versions("artwork1")


class TestRestoreArtworkVersion:
    """Tests for restore_artwork_version method."""
    
    @pytest.mark.asyncio
    async def test_restore_artwork_version_success(self, project_repo, mock_graphql_client):
        """Test restoring artwork version successfully."""
        mock_graphql_client.execute_mutation.return_value = {
            "restoreArtworkVersion": {
                "id": "artwork1",
                "name": "Logo Design",
                "currentRevision": {
                    "id": "version2",
                    "revisionNumber": 2
                }
            }
        }
        
        result = await project_repo.restore_artwork_version("artwork1", "version2")
        
        assert result["id"] == "artwork1"
        assert result["currentRevision"]["revisionNumber"] == 2
        
    @pytest.mark.asyncio
    async def test_restore_to_earlier_version(self, project_repo, mock_graphql_client):
        """Test restoring to an earlier version."""
        mock_graphql_client.execute_mutation.return_value = {
            "restoreArtworkVersion": {
                "id": "artwork1",
                "name": "Banner",
                "currentRevision": {
                    "id": "version1",
                    "revisionNumber": 1
                }
            }
        }
        
        result = await project_repo.restore_artwork_version("artwork1", "version1")
        
        assert result["currentRevision"]["revisionNumber"] == 1
        
    @pytest.mark.asyncio
    async def test_restore_artwork_version_error(self, project_repo, mock_graphql_client):
        """Test error handling when restoring version."""
        mock_graphql_client.execute_mutation.side_effect = Exception("API error")
        
        with pytest.raises(CwayAPIError, match="Failed to restore artwork version"):
            await project_repo.restore_artwork_version("artwork1", "version1")
    
    @pytest.mark.asyncio
    async def test_restore_with_invalid_version_id(self, project_repo, mock_graphql_client):
        """Test restoring with invalid version ID."""
        mock_graphql_client.execute_mutation.side_effect = Exception("Version not found")
        
        with pytest.raises(CwayAPIError):
            await project_repo.restore_artwork_version("artwork1", "invalid_version")
