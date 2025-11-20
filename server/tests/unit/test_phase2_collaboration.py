"""Unit tests for Phase 2.1 project collaboration tools."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
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


class TestGetProjectMembers:
    """Tests for get_project_members method."""
    
    @pytest.mark.asyncio
    async def test_get_project_members_success(self, project_repo, mock_graphql_client):
        """Test getting project members successfully."""
        mock_graphql_client.execute_query.return_value = {
            "projectMembers": [
                {
                    "user": {"id": "user1", "name": "John Doe", "username": "jdoe", "email": "john@example.com"},
                    "role": "MANAGER",
                    "addedAt": "2024-01-01T00:00:00Z"
                },
                {
                    "user": {"id": "user2", "name": "Jane Smith", "username": "jsmith", "email": "jane@example.com"},
                    "role": "MEMBER",
                    "addedAt": "2024-01-02T00:00:00Z"
                }
            ]
        }
        
        result = await project_repo.get_project_members("proj1")
        
        assert len(result) == 2
        assert result[0]["user"]["name"] == "John Doe"
        assert result[0]["role"] == "MANAGER"
        assert result[1]["user"]["name"] == "Jane Smith"
        
    @pytest.mark.asyncio
    async def test_get_project_members_empty(self, project_repo, mock_graphql_client):
        """Test getting project members when none exist."""
        mock_graphql_client.execute_query.return_value = {"projectMembers": []}
        
        result = await project_repo.get_project_members("proj1")
        
        assert result == []
        
    @pytest.mark.asyncio
    async def test_get_project_members_error(self, project_repo, mock_graphql_client):
        """Test error handling when getting project members."""
        mock_graphql_client.execute_query.side_effect = Exception("API error")
        
        with pytest.raises(CwayAPIError, match="Failed to get project members"):
            await project_repo.get_project_members("proj1")


class TestAddProjectMember:
    """Tests for add_project_member method."""
    
    @pytest.mark.asyncio
    async def test_add_project_member_success(self, project_repo, mock_graphql_client):
        """Test adding project member successfully."""
        mock_graphql_client.execute_mutation.return_value = {
            "addProjectMember": {
                "user": {"id": "user1", "name": "John Doe", "username": "jdoe"},
                "role": "MEMBER"
            }
        }
        
        result = await project_repo.add_project_member("proj1", "user1", "MEMBER")
        
        assert result["user"]["id"] == "user1"
        assert result["role"] == "MEMBER"
        mock_graphql_client.execute_mutation.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_add_project_member_with_custom_role(self, project_repo, mock_graphql_client):
        """Test adding project member with custom role."""
        mock_graphql_client.execute_mutation.return_value = {
            "addProjectMember": {
                "user": {"id": "user1", "name": "John Doe", "username": "jdoe"},
                "role": "MANAGER"
            }
        }
        
        result = await project_repo.add_project_member("proj1", "user1", "MANAGER")
        
        assert result["role"] == "MANAGER"
        
    @pytest.mark.asyncio
    async def test_add_project_member_error(self, project_repo, mock_graphql_client):
        """Test error handling when adding project member."""
        mock_graphql_client.execute_mutation.side_effect = Exception("API error")
        
        with pytest.raises(CwayAPIError, match="Failed to add project member"):
            await project_repo.add_project_member("proj1", "user1")


class TestRemoveProjectMember:
    """Tests for remove_project_member method."""
    
    @pytest.mark.asyncio
    async def test_remove_project_member_success(self, project_repo, mock_graphql_client):
        """Test removing project member successfully."""
        mock_graphql_client.execute_mutation.return_value = {"removeProjectMember": True}
        
        result = await project_repo.remove_project_member("proj1", "user1")
        
        assert result is True
        
    @pytest.mark.asyncio
    async def test_remove_project_member_failed(self, project_repo, mock_graphql_client):
        """Test removing project member when operation fails."""
        mock_graphql_client.execute_mutation.return_value = {"removeProjectMember": False}
        
        result = await project_repo.remove_project_member("proj1", "user1")
        
        assert result is False
        
    @pytest.mark.asyncio
    async def test_remove_project_member_error(self, project_repo, mock_graphql_client):
        """Test error handling when removing project member."""
        mock_graphql_client.execute_mutation.side_effect = Exception("API error")
        
        with pytest.raises(CwayAPIError, match="Failed to remove project member"):
            await project_repo.remove_project_member("proj1", "user1")


class TestUpdateProjectMemberRole:
    """Tests for update_project_member_role method."""
    
    @pytest.mark.asyncio
    async def test_update_member_role_success(self, project_repo, mock_graphql_client):
        """Test updating member role successfully."""
        mock_graphql_client.execute_mutation.return_value = {
            "updateProjectMemberRole": {
                "user": {"id": "user1", "name": "John Doe"},
                "role": "MANAGER"
            }
        }
        
        result = await project_repo.update_project_member_role("proj1", "user1", "MANAGER")
        
        assert result["role"] == "MANAGER"
        assert result["user"]["id"] == "user1"
        
    @pytest.mark.asyncio
    async def test_update_member_role_to_viewer(self, project_repo, mock_graphql_client):
        """Test updating member role to viewer."""
        mock_graphql_client.execute_mutation.return_value = {
            "updateProjectMemberRole": {
                "user": {"id": "user1", "name": "John Doe"},
                "role": "VIEWER"
            }
        }
        
        result = await project_repo.update_project_member_role("proj1", "user1", "VIEWER")
        
        assert result["role"] == "VIEWER"
        
    @pytest.mark.asyncio
    async def test_update_member_role_error(self, project_repo, mock_graphql_client):
        """Test error handling when updating member role."""
        mock_graphql_client.execute_mutation.side_effect = Exception("API error")
        
        with pytest.raises(CwayAPIError, match="Failed to update project member role"):
            await project_repo.update_project_member_role("proj1", "user1", "MANAGER")


class TestGetProjectComments:
    """Tests for get_project_comments method."""
    
    @pytest.mark.asyncio
    async def test_get_project_comments_success(self, project_repo, mock_graphql_client):
        """Test getting project comments successfully."""
        mock_graphql_client.execute_query.return_value = {
            "projectComments": [
                {
                    "id": "comment1",
                    "text": "Great progress!",
                    "author": {"id": "user1", "name": "John", "username": "jdoe"},
                    "created": "2024-01-01T00:00:00Z",
                    "edited": None
                },
                {
                    "id": "comment2",
                    "text": "Need more time",
                    "author": {"id": "user2", "name": "Jane", "username": "jsmith"},
                    "created": "2024-01-02T00:00:00Z",
                    "edited": None
                }
            ]
        }
        
        result = await project_repo.get_project_comments("proj1", limit=50)
        
        assert len(result) == 2
        assert result[0]["text"] == "Great progress!"
        assert result[1]["author"]["name"] == "Jane"
        
    @pytest.mark.asyncio
    async def test_get_project_comments_with_custom_limit(self, project_repo, mock_graphql_client):
        """Test getting project comments with custom limit."""
        mock_graphql_client.execute_query.return_value = {"projectComments": []}
        
        await project_repo.get_project_comments("proj1", limit=10)
        
        # Check that the method was called
        mock_graphql_client.execute_query.assert_called_once()
        # Get the call arguments - second positional arg is the variables dict
        call_args = mock_graphql_client.execute_query.call_args[0]
        variables = call_args[1]  # Second positional argument
        assert variables["limit"] == 10
        
    @pytest.mark.asyncio
    async def test_get_project_comments_error(self, project_repo, mock_graphql_client):
        """Test error handling when getting comments."""
        mock_graphql_client.execute_query.side_effect = Exception("API error")
        
        with pytest.raises(CwayAPIError, match="Failed to get project comments"):
            await project_repo.get_project_comments("proj1")


class TestAddProjectComment:
    """Tests for add_project_comment method."""
    
    @pytest.mark.asyncio
    async def test_add_project_comment_success(self, project_repo, mock_graphql_client):
        """Test adding project comment successfully."""
        mock_graphql_client.execute_mutation.return_value = {
            "addProjectComment": {
                "id": "comment1",
                "text": "New comment",
                "author": {"id": "user1", "name": "John"},
                "created": "2024-01-01T00:00:00Z"
            }
        }
        
        result = await project_repo.add_project_comment("proj1", "New comment")
        
        assert result["id"] == "comment1"
        assert result["text"] == "New comment"
        
    @pytest.mark.asyncio
    async def test_add_project_comment_with_long_text(self, project_repo, mock_graphql_client):
        """Test adding project comment with long text."""
        long_text = "This is a very long comment " * 20
        mock_graphql_client.execute_mutation.return_value = {
            "addProjectComment": {
                "id": "comment1",
                "text": long_text,
                "author": {"id": "user1", "name": "John"},
                "created": "2024-01-01T00:00:00Z"
            }
        }
        
        result = await project_repo.add_project_comment("proj1", long_text)
        
        assert result["text"] == long_text
        
    @pytest.mark.asyncio
    async def test_add_project_comment_error(self, project_repo, mock_graphql_client):
        """Test error handling when adding comment."""
        mock_graphql_client.execute_mutation.side_effect = Exception("API error")
        
        with pytest.raises(CwayAPIError, match="Failed to add project comment"):
            await project_repo.add_project_comment("proj1", "Comment")


class TestGetProjectAttachments:
    """Tests for get_project_attachments method."""
    
    @pytest.mark.asyncio
    async def test_get_project_attachments_success(self, project_repo, mock_graphql_client):
        """Test getting project attachments successfully."""
        mock_graphql_client.execute_query.return_value = {
            "projectAttachments": [
                {
                    "id": "file1",
                    "name": "document.pdf",
                    "fileSize": 1024000,
                    "mimeType": "application/pdf",
                    "url": "https://example.com/file1",
                    "uploaded": "2024-01-01T00:00:00Z",
                    "uploader": {"id": "user1", "name": "John"}
                },
                {
                    "id": "file2",
                    "name": "image.png",
                    "fileSize": 512000,
                    "mimeType": "image/png",
                    "url": "https://example.com/file2",
                    "uploaded": "2024-01-02T00:00:00Z",
                    "uploader": {"id": "user2", "name": "Jane"}
                }
            ]
        }
        
        result = await project_repo.get_project_attachments("proj1")
        
        assert len(result) == 2
        assert result[0]["name"] == "document.pdf"
        assert result[1]["mimeType"] == "image/png"
        
    @pytest.mark.asyncio
    async def test_get_project_attachments_empty(self, project_repo, mock_graphql_client):
        """Test getting attachments when none exist."""
        mock_graphql_client.execute_query.return_value = {"projectAttachments": []}
        
        result = await project_repo.get_project_attachments("proj1")
        
        assert result == []
        
    @pytest.mark.asyncio
    async def test_get_project_attachments_error(self, project_repo, mock_graphql_client):
        """Test error handling when getting attachments."""
        mock_graphql_client.execute_query.side_effect = Exception("API error")
        
        with pytest.raises(CwayAPIError, match="Failed to get project attachments"):
            await project_repo.get_project_attachments("proj1")


class TestUploadProjectAttachment:
    """Tests for upload_project_attachment method."""
    
    @pytest.mark.asyncio
    async def test_upload_project_attachment_success(self, project_repo, mock_graphql_client):
        """Test uploading project attachment successfully."""
        mock_graphql_client.execute_mutation.return_value = {
            "attachFileToProject": {
                "id": "file1",
                "name": "document.pdf",
                "fileSize": 1024000
            }
        }
        
        result = await project_repo.upload_project_attachment("proj1", "file1", "document.pdf")
        
        assert result["id"] == "file1"
        assert result["name"] == "document.pdf"
        
    @pytest.mark.asyncio
    async def test_upload_project_attachment_with_special_chars(self, project_repo, mock_graphql_client):
        """Test uploading attachment with special characters in name."""
        mock_graphql_client.execute_mutation.return_value = {
            "attachFileToProject": {
                "id": "file1",
                "name": "my-file (1) [final].pdf",
                "fileSize": 1024000
            }
        }
        
        result = await project_repo.upload_project_attachment("proj1", "file1", "my-file (1) [final].pdf")
        
        assert result["name"] == "my-file (1) [final].pdf"
        
    @pytest.mark.asyncio
    async def test_upload_project_attachment_error(self, project_repo, mock_graphql_client):
        """Test error handling when uploading attachment."""
        mock_graphql_client.execute_mutation.side_effect = Exception("API error")
        
        with pytest.raises(CwayAPIError, match="Failed to upload project attachment"):
            await project_repo.upload_project_attachment("proj1", "file1", "document.pdf")
