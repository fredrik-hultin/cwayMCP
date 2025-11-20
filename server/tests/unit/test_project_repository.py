"""Unit tests for ProjectRepository.

Focus on:
- Project CRUD and search
- Project collaboration (comments, attachments)
- Team member management
- Error handling
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.infrastructure.repositories.project_repository import ProjectRepository
from src.domain.cway_entities import PlannerProject, ProjectState
from src.infrastructure.graphql_client import CwayAPIError


@pytest.fixture
def mock_graphql_client():
    """Create a mock GraphQL client."""
    client = MagicMock()
    client.execute_query = AsyncMock()
    client.execute_mutation = AsyncMock()
    return client


@pytest.fixture
def project_repository(mock_graphql_client):
    """Create a ProjectRepository with mocked client."""
    repo = ProjectRepository(mock_graphql_client)
    return repo


class TestGetPlannerProjects:
    """Tests for get_planner_projects method."""
    
    @pytest.mark.asyncio
    async def test_get_planner_projects_multiple(self, project_repository, mock_graphql_client):
        """Test getting multiple planner projects."""
        mock_response = {
            "plannerProjects": [
                {
                    "id": "proj-1",
                    "name": "Website Redesign",
                    "state": "IN_PROGRESS",
                    "percentageDone": 45.5,
                    "startDate": "2024-01-01",
                    "endDate": "2024-03-31"
                },
                {
                    "id": "proj-2",
                    "name": "Marketing Campaign",
                    "state": "COMPLETED",
                    "percentageDone": 100.0,
                    "startDate": "2024-01-15",
                    "endDate": "2024-02-28"
                }
            ]
        }
        mock_graphql_client.execute_query.return_value = mock_response
        
        result = await project_repository.get_planner_projects()
        
        assert len(result) == 2
        assert all(isinstance(p, PlannerProject) for p in result)
        assert result[0].name == "Website Redesign"
        assert result[0].state == ProjectState.IN_PROGRESS
        assert result[0].percentageDone == 45.5
        assert result[1].state == ProjectState.COMPLETED
    
    @pytest.mark.asyncio
    async def test_get_planner_projects_empty(self, project_repository, mock_graphql_client):
        """Test when no planner projects exist."""
        mock_graphql_client.execute_query.return_value = {}
        
        result = await project_repository.get_planner_projects()
        
        assert result == []


class TestFindProjectById:
    """Tests for find_project_by_id method."""
    
    @pytest.mark.asyncio
    async def test_find_project_by_id_found(self, project_repository, mock_graphql_client):
        """Test finding existing project by ID."""
        target_id = "proj-2"
        mock_response = {
            "plannerProjects": [
                {
                    "id": "proj-1",
                    "name": "Project A",
                    "state": "IN_PROGRESS",
                    "percentageDone": 30.0
                },
                {
                    "id": target_id,
                    "name": "Project B",
                    "state": "COMPLETED",
                    "percentageDone": 100.0
                }
            ]
        }
        mock_graphql_client.execute_query.return_value = mock_response
        
        result = await project_repository.find_project_by_id(target_id)
        
        assert result is not None
        assert result.id == target_id
        assert result.name == "Project B"
    
    @pytest.mark.asyncio
    async def test_find_project_by_id_not_found(self, project_repository, mock_graphql_client):
        """Test finding non-existent project."""
        mock_response = {
            "plannerProjects": [
                {
                    "id": "proj-1",
                    "name": "Project A",
                    "state": "IN_PROGRESS",
                    "percentageDone": 30.0
                }
            ]
        }
        mock_graphql_client.execute_query.return_value = mock_response
        
        result = await project_repository.find_project_by_id("nonexistent")
        
        assert result is None


class TestGetActiveProjects:
    """Tests for get_active_projects method."""
    
    @pytest.mark.asyncio
    async def test_get_active_projects_filters_correctly(self, project_repository, mock_graphql_client):
        """Test that only IN_PROGRESS projects are returned."""
        mock_response = {
            "plannerProjects": [
                {
                    "id": "proj-1",
                    "name": "Active Project 1",
                    "state": "IN_PROGRESS",
                    "percentageDone": 30.0
                },
                {
                    "id": "proj-2",
                    "name": "Completed Project",
                    "state": "COMPLETED",
                    "percentageDone": 100.0
                },
                {
                    "id": "proj-3",
                    "name": "Active Project 2",
                    "state": "IN_PROGRESS",
                    "percentageDone": 75.0
                }
            ]
        }
        mock_graphql_client.execute_query.return_value = mock_response
        
        result = await project_repository.get_active_projects()
        
        assert len(result) == 2
        assert all(p.state == ProjectState.IN_PROGRESS for p in result)
        assert result[0].name == "Active Project 1"
        assert result[1].name == "Active Project 2"


class TestSearchProjects:
    """Tests for search_projects method."""
    
    @pytest.mark.asyncio
    async def test_search_projects_with_query(self, project_repository, mock_graphql_client):
        """Test searching projects with query string."""
        mock_response = {
            "projects": {
                "projects": [
                    {
                        "id": "proj-1",
                        "name": "Website Design",
                        "description": "New website"
                    },
                    {
                        "id": "proj-2",
                        "name": "Website Development",
                        "description": "Backend work"
                    }
                ],
                "page": 0,
                "totalHits": 2
            }
        }
        mock_graphql_client.execute_query.return_value = mock_response
        
        result = await project_repository.search_projects(query="website")
        
        assert len(result["projects"]) == 2
        assert result["total_hits"] == 2
        assert all("Website" in p["name"] for p in result["projects"])
    
    @pytest.mark.asyncio
    async def test_search_projects_no_results(self, project_repository, mock_graphql_client):
        """Test search with no matching projects."""
        mock_graphql_client.execute_query.return_value = {}
        
        result = await project_repository.search_projects(query="nonexistent")
        
        assert result["projects"] == []
        assert result["total_hits"] == 0


class TestGetProjectComments:
    """Tests for get_project_comments method."""
    
    @pytest.mark.asyncio
    async def test_get_project_comments_multiple(self, project_repository, mock_graphql_client):
        """Test getting project comments."""
        project_id = "proj-123"
        mock_response = {
            "projectComments": [
                {
                    "id": "comment-1",
                    "text": "Looks great!",
                    "author": {
                        "id": "user-1",
                        "name": "John Doe",
                        "username": "john"
                    },
                    "created": "2024-01-01T10:00:00Z",
                    "edited": None
                },
                {
                    "id": "comment-2",
                    "text": "Can we adjust the colors?",
                    "author": {
                        "id": "user-2",
                        "name": "Jane Smith",
                        "username": "jane"
                    },
                    "created": "2024-01-01T11:00:00Z",
                    "edited": "2024-01-01T11:05:00Z"
                }
            ]
        }
        mock_graphql_client.execute_query.return_value = mock_response
        
        result = await project_repository.get_project_comments(project_id)
        
        assert len(result) == 2
        assert result[0]["text"] == "Looks great!"
        assert result[1]["edited"] is not None
        assert result[0]["author"]["username"] == "john"
    
    @pytest.mark.asyncio
    async def test_get_project_comments_empty(self, project_repository, mock_graphql_client):
        """Test project with no comments."""
        mock_graphql_client.execute_query.return_value = {}
        
        result = await project_repository.get_project_comments("proj-123")
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_project_comments_with_limit(self, project_repository, mock_graphql_client):
        """Test getting comments with custom limit."""
        mock_response = {
            "projectComments": [
                {"id": "c1", "text": "Comment 1", "author": {"id": "u1", "name": "User 1", "username": "user1"}, "created": "2024-01-01T10:00:00Z"}
            ]
        }
        mock_graphql_client.execute_query.return_value = mock_response
        
        await project_repository.get_project_comments("proj-123", limit=10)
        
        # Verify limit was passed
        call_args = mock_graphql_client.execute_query.call_args
        assert call_args[0][1]["limit"] == 10


class TestAddProjectComment:
    """Tests for add_project_comment method."""
    
    @pytest.mark.asyncio
    async def test_add_project_comment_success(self, project_repository, mock_graphql_client):
        """Test adding a comment to project."""
        project_id = "proj-123"
        comment_text = "This is a test comment"
        
        mock_response = {
            "addProjectComment": {
                "id": "comment-new",
                "text": comment_text,
                "author": {
                    "id": "user-current",
                    "name": "Current User"
                },
                "created": "2024-01-02T10:00:00Z"
            }
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await project_repository.add_project_comment(project_id, comment_text)
        
        assert result["id"] == "comment-new"
        assert result["text"] == comment_text
        assert "created" in result
    
    @pytest.mark.asyncio
    async def test_add_project_comment_empty_result(self, project_repository, mock_graphql_client):
        """Test adding comment with empty result."""
        mock_graphql_client.execute_mutation.return_value = {}
        
        result = await project_repository.add_project_comment("proj-123", "comment")
        
        assert result == {}


class TestGetProjectAttachments:
    """Tests for get_project_attachments method."""
    
    @pytest.mark.asyncio
    async def test_get_project_attachments_multiple(self, project_repository, mock_graphql_client):
        """Test getting project attachments."""
        project_id = "proj-123"
        mock_response = {
            "projectAttachments": [
                {
                    "id": "attach-1",
                    "name": "design.pdf",
                    "fileSize": 1024000,
                    "mimeType": "application/pdf",
                    "url": "https://example.com/file1",
                    "uploaded": "2024-01-01T10:00:00Z",
                    "uploader": {
                        "id": "user-1",
                        "name": "John Doe"
                    }
                },
                {
                    "id": "attach-2",
                    "name": "mockup.png",
                    "fileSize": 256000,
                    "mimeType": "image/png",
                    "url": "https://example.com/file2",
                    "uploaded": "2024-01-02T10:00:00Z",
                    "uploader": {
                        "id": "user-2",
                        "name": "Jane Smith"
                    }
                }
            ]
        }
        mock_graphql_client.execute_query.return_value = mock_response
        
        result = await project_repository.get_project_attachments(project_id)
        
        assert len(result) == 2
        assert result[0]["name"] == "design.pdf"
        assert result[0]["mimeType"] == "application/pdf"
        assert result[1]["name"] == "mockup.png"
    
    @pytest.mark.asyncio
    async def test_get_project_attachments_empty(self, project_repository, mock_graphql_client):
        """Test project with no attachments."""
        mock_graphql_client.execute_query.return_value = {}
        
        result = await project_repository.get_project_attachments("proj-123")
        
        assert result == []


class TestUploadProjectAttachment:
    """Tests for upload_project_attachment method."""
    
    @pytest.mark.asyncio
    async def test_upload_project_attachment_success(self, project_repository, mock_graphql_client):
        """Test uploading attachment to project."""
        project_id = "proj-123"
        file_id = "file-456"
        file_name = "document.pdf"
        
        mock_response = {
            "attachFileToProject": {
                "id": "attach-new",
                "name": file_name,
                "fileSize": 512000
            }
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await project_repository.upload_project_attachment(project_id, file_id, file_name)
        
        assert result["id"] == "attach-new"
        assert result["name"] == file_name
        assert result["fileSize"] == 512000
    
    @pytest.mark.asyncio
    async def test_upload_project_attachment_empty_result(self, project_repository, mock_graphql_client):
        """Test uploading with empty result."""
        mock_graphql_client.execute_mutation.return_value = {}
        
        result = await project_repository.upload_project_attachment("proj-123", "file-1", "test.pdf")
        
        assert result == {}


class TestAddProjectMember:
    """Tests for add_project_member method."""
    
    @pytest.mark.asyncio
    async def test_add_project_member_with_role(self, project_repository, mock_graphql_client):
        """Test adding project member with role."""
        project_id = "proj-123"
        user_id = "user-456"
        role = "editor"
        
        mock_response = {
            "addProjectMember": {
                "user": {
                    "id": user_id,
                    "name": "New Member",
                    "username": "newmember"
                },
                "role": role
            }
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await project_repository.add_project_member(project_id, user_id, role)
        
        assert result["user"]["id"] == user_id
        assert result["role"] == role
    
    @pytest.mark.asyncio
    async def test_add_project_member_empty_result(self, project_repository, mock_graphql_client):
        """Test adding member with empty result."""
        mock_graphql_client.execute_mutation.return_value = {}
        
        result = await project_repository.add_project_member("proj-123", "user-456", "viewer")
        
        assert result == {}


class TestRemoveProjectMember:
    """Tests for remove_project_member method."""
    
    @pytest.mark.asyncio
    async def test_remove_project_member_success(self, project_repository, mock_graphql_client):
        """Test removing project member."""
        project_id = "proj-123"
        user_id = "user-456"
        
        mock_response = {
            "removeProjectMember": True
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await project_repository.remove_project_member(project_id, user_id)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_remove_project_member_failed(self, project_repository, mock_graphql_client):
        """Test failed member removal."""
        mock_response = {
            "removeProjectMember": False
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await project_repository.remove_project_member("proj-123", "user-456")
        
        assert result is False


class TestUpdateProjectMemberRole:
    """Tests for update_project_member_role method."""
    
    @pytest.mark.asyncio
    async def test_update_project_member_role_success(self, project_repository, mock_graphql_client):
        """Test updating member role."""
        project_id = "proj-123"
        user_id = "user-456"
        new_role = "admin"
        
        mock_response = {
            "updateProjectMemberRole": {
                "user": {
                    "id": user_id,
                    "name": "Test User"
                },
                "role": new_role
            }
        }
        mock_graphql_client.execute_mutation.return_value = mock_response
        
        result = await project_repository.update_project_member_role(project_id, user_id, new_role)
        
        assert result["user"]["id"] == user_id
        assert result["role"] == new_role
    
    @pytest.mark.asyncio
    async def test_update_project_member_role_empty_result(self, project_repository, mock_graphql_client):
        """Test updating role with empty result."""
        mock_graphql_client.execute_mutation.return_value = {}
        
        result = await project_repository.update_project_member_role("proj-123", "user-456", "editor")
        
        assert result == {}


class TestErrorHandling:
    """Tests for error handling across ProjectRepository."""
    
    @pytest.mark.asyncio
    async def test_get_planner_projects_error(self, project_repository, mock_graphql_client):
        """Test error handling in get_planner_projects."""
        mock_graphql_client.execute_query.side_effect = Exception("Database error")
        
        with pytest.raises(CwayAPIError, match="Failed to fetch planner projects"):
            await project_repository.get_planner_projects()
    
    @pytest.mark.asyncio
    async def test_search_projects_error(self, project_repository, mock_graphql_client):
        """Test error handling in search."""
        mock_graphql_client.execute_query.side_effect = Exception("Search timeout")
        
        with pytest.raises(CwayAPIError, match="Failed to search projects"):
            await project_repository.search_projects(query="test")
    
    @pytest.mark.asyncio
    async def test_add_comment_error(self, project_repository, mock_graphql_client):
        """Test error handling when adding comment."""
        mock_graphql_client.execute_mutation.side_effect = Exception("Permission denied")
        
        with pytest.raises(CwayAPIError, match="Failed to add project comment"):
            await project_repository.add_project_comment("proj-123", "comment")
    
    @pytest.mark.asyncio
    async def test_get_attachments_error(self, project_repository, mock_graphql_client):
        """Test error handling when getting attachments."""
        mock_graphql_client.execute_query.side_effect = Exception("Network error")
        
        with pytest.raises(CwayAPIError, match="Failed to get project attachments"):
            await project_repository.get_project_attachments("proj-123")
