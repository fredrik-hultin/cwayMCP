"""
Unit tests for newly added GraphQL API tools (Phase 1-4).
Tests cover project trends, artwork analytics, AI features, and user management.
"""
import pytest
from unittest.mock import AsyncMock
from src.infrastructure.cway_repositories import (
    CwayUserRepository,
    CwayProjectRepository
)
from src.infrastructure.graphql_client import CwayAPIError


@pytest.fixture
def mock_graphql_client():
    """Create a mock GraphQL client."""
    client = AsyncMock()
    client.execute_query = AsyncMock()
    client.execute_mutation = AsyncMock()
    return client


class TestProjectTrendsTools:
    """Test Phase 1: Project analytics and trends."""
    
    @pytest.mark.asyncio
    async def test_get_monthly_project_trends_success(self, mock_graphql_client):
        """Test retrieving monthly project trends."""
        # Arrange
        repo = CwayProjectRepository(mock_graphql_client)
        mock_graphql_client.execute_query.return_value = {
            "openProjectsCountByMonth": [
                {"month": "2024-01", "count": 5},
                {"month": "2024-02", "count": 8},
                {"month": "2024-03", "count": 12}
            ]
        }
        
        # Act
        trends = await repo.get_monthly_project_trends()
        
        # Assert
        assert len(trends) == 3
        assert trends[0]["month"] == "2024-01"
        assert trends[0]["count"] == 5
        assert trends[2]["count"] == 12
        mock_graphql_client.execute_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_monthly_project_trends_empty(self, mock_graphql_client):
        """Test monthly trends with no data."""
        # Arrange
        repo = CwayProjectRepository(mock_graphql_client)
        mock_graphql_client.execute_query.return_value = {
            "openProjectsCountByMonth": []
        }
        
        # Act
        trends = await repo.get_monthly_project_trends()
        
        # Assert
        assert len(trends) == 0
    
    @pytest.mark.asyncio
    async def test_get_monthly_project_trends_api_error(self, mock_graphql_client):
        """Test monthly trends handles API errors."""
        # Arrange
        repo = CwayProjectRepository(mock_graphql_client)
        mock_graphql_client.execute_query.side_effect = Exception("API Error")
        
        # Act & Assert
        with pytest.raises(CwayAPIError, match="Failed to get monthly project trends"):
            await repo.get_monthly_project_trends()


class TestArtworkAnalyticsTools:
    """Test Phase 2: Artwork analytics and history."""
    
    @pytest.mark.asyncio
    async def test_get_artwork_history_success(self, mock_graphql_client):
        """Test retrieving artwork revision history."""
        # Arrange
        repo = CwayProjectRepository(mock_graphql_client)
        mock_graphql_client.execute_query.return_value = {
            "artworkHistory": [
                {
                    "id": "event-1",
                    "timestamp": "2024-01-15T10:00:00Z",
                    "eventType": "CREATED",
                    "description": "Artwork created",
                    "user": {"username": "artist1", "name": "Artist One"}
                },
                {
                    "id": "event-2",
                    "timestamp": "2024-01-16T14:30:00Z",
                    "eventType": "REVISED",
                    "description": "Revision uploaded",
                    "user": {"username": "artist1", "name": "Artist One"}
                }
            ]
        }
        
        # Act
        history = await repo.get_artwork_history("artwork-123")
        
        # Assert
        assert len(history) == 2
        assert history[0]["eventType"] == "CREATED"
        assert history[1]["eventType"] == "REVISED"
        assert history[0]["user"]["username"] == "artist1"
        mock_graphql_client.execute_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_artwork_history_empty(self, mock_graphql_client):
        """Test artwork history with no events."""
        # Arrange
        repo = CwayProjectRepository(mock_graphql_client)
        mock_graphql_client.execute_query.return_value = {
            "artworkHistory": []
        }
        
        # Act
        history = await repo.get_artwork_history("artwork-123")
        
        # Assert
        assert len(history) == 0
    
    @pytest.mark.asyncio
    async def test_get_artwork_history_api_error(self, mock_graphql_client):
        """Test artwork history handles API errors."""
        # Arrange
        repo = CwayProjectRepository(mock_graphql_client)
        mock_graphql_client.execute_query.side_effect = Exception("API Error")
        
        # Act & Assert
        with pytest.raises(CwayAPIError, match="Failed to get artwork history"):
            await repo.get_artwork_history("artwork-123")


class TestAIFeatureTools:
    """Test Phase 2: AI analysis and summary features."""
    
    @pytest.mark.asyncio
    async def test_analyze_artwork_ai_success(self, mock_graphql_client):
        """Test triggering AI artwork analysis."""
        # Arrange
        repo = CwayProjectRepository(mock_graphql_client)
        mock_graphql_client.execute_mutation.return_value = {
            "artworkAIAnalysis": "thread-abc-123"
        }
        
        # Act
        thread_id = await repo.analyze_artwork_ai("artwork-123")
        
        # Assert
        assert thread_id == "thread-abc-123"
        mock_graphql_client.execute_mutation.assert_called_once()
        call_args = mock_graphql_client.execute_mutation.call_args
        assert call_args[0][1]["artworkId"] == "artwork-123"
    
    @pytest.mark.asyncio
    async def test_analyze_artwork_ai_no_thread_id(self, mock_graphql_client):
        """Test AI analysis with empty response."""
        # Arrange
        repo = CwayProjectRepository(mock_graphql_client)
        mock_graphql_client.execute_mutation.return_value = {
            "artworkAIAnalysis": None
        }
        
        # Act & Assert
        with pytest.raises(CwayAPIError, match="AI analysis returned no thread ID"):
            await repo.analyze_artwork_ai("artwork-123")
    
    @pytest.mark.asyncio
    async def test_analyze_artwork_ai_api_error(self, mock_graphql_client):
        """Test AI analysis handles API errors."""
        # Arrange
        repo = CwayProjectRepository(mock_graphql_client)
        mock_graphql_client.execute_mutation.side_effect = Exception("API Error")
        
        # Act & Assert
        with pytest.raises(CwayAPIError, match="Failed to trigger AI artwork analysis"):
            await repo.analyze_artwork_ai("artwork-123")
    
    @pytest.mark.asyncio
    async def test_generate_project_summary_ai_success(self, mock_graphql_client):
        """Test generating AI project summary."""
        # Arrange
        repo = CwayProjectRepository(mock_graphql_client)
        mock_graphql_client.execute_mutation.return_value = {
            "openAIProjectSummary": "Project is on track. 80% complete with 5 artworks approved."
        }
        
        # Act
        summary = await repo.generate_project_summary_ai("project-123", "PROJECT_MANAGER")
        
        # Assert
        assert "on track" in summary
        assert "80%" in summary
        mock_graphql_client.execute_mutation.assert_called_once()
        call_args = mock_graphql_client.execute_mutation.call_args
        assert call_args[0][1]["projectId"] == "project-123"
        assert call_args[0][1]["audience"] == "PROJECT_MANAGER"
    
    @pytest.mark.asyncio
    async def test_generate_project_summary_ai_different_audience(self, mock_graphql_client):
        """Test AI summary for different audience types."""
        # Arrange
        repo = CwayProjectRepository(mock_graphql_client)
        mock_graphql_client.execute_mutation.return_value = {
            "openAIProjectSummary": "Graphics work is progressing well."
        }
        
        # Act
        summary = await repo.generate_project_summary_ai("project-123", "GRAPHICS_CREATOR")
        
        # Assert
        assert "Graphics" in summary
        call_args = mock_graphql_client.execute_mutation.call_args
        assert call_args[0][1]["audience"] == "GRAPHICS_CREATOR"
    
    @pytest.mark.asyncio
    async def test_generate_project_summary_ai_empty_result(self, mock_graphql_client):
        """Test AI summary with empty response."""
        # Arrange
        repo = CwayProjectRepository(mock_graphql_client)
        mock_graphql_client.execute_mutation.return_value = {
            "openAIProjectSummary": None
        }
        
        # Act & Assert
        with pytest.raises(CwayAPIError, match="AI summary generation returned empty result"):
            await repo.generate_project_summary_ai("project-123")
    
    @pytest.mark.asyncio
    async def test_generate_project_summary_ai_api_error(self, mock_graphql_client):
        """Test AI summary handles API errors."""
        # Arrange
        repo = CwayProjectRepository(mock_graphql_client)
        mock_graphql_client.execute_mutation.side_effect = Exception("API Error")
        
        # Act & Assert
        with pytest.raises(CwayAPIError, match="Failed to generate AI project summary"):
            await repo.generate_project_summary_ai("project-123")


class TestUserManagementTools:
    """Test Phase 4: User and team management."""
    
    @pytest.mark.asyncio
    async def test_find_users_and_teams_success(self, mock_graphql_client):
        """Test searching for users and teams."""
        # Arrange
        repo = CwayUserRepository(mock_graphql_client)
        mock_graphql_client.execute_query.return_value = {
            "findUsersAndTeamsPage": {
                "usersOrTeams": [
                    {
                        "__typename": "User",
                        "id": "user-1",
                        "name": "John Doe",
                        "username": "johndoe",
                        "email": "john@test.com",
                        "firstName": "John",
                        "lastName": "Doe",
                        "enabled": True
                    },
                    {
                        "__typename": "Team",
                        "id": "team-1",
                        "name": "Design Team",
                        "teamLeadUser": {
                            "username": "lead",
                            "name": "Team Lead"
                        }
                    }
                ],
                "page": 0,
                "totalHits": 2
            }
        }
        
        # Act
        result = await repo.find_users_and_teams("design", page=0, size=10)
        
        # Assert
        assert len(result["items"]) == 2
        assert result["items"][0]["__typename"] == "User"
        assert result["items"][1]["__typename"] == "Team"
        assert result["totalHits"] == 2
        assert result["page"] == 0
        mock_graphql_client.execute_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find_users_and_teams_empty(self, mock_graphql_client):
        """Test search with no results."""
        # Arrange
        repo = CwayUserRepository(mock_graphql_client)
        mock_graphql_client.execute_query.return_value = {
            "findUsersAndTeamsPage": {
                "usersOrTeams": [],
                "page": 0,
                "totalHits": 0
            }
        }
        
        # Act
        result = await repo.find_users_and_teams("nonexistent")
        
        # Assert
        assert len(result["items"]) == 0
        assert result["totalHits"] == 0
    
    @pytest.mark.asyncio
    async def test_find_users_and_teams_api_error(self, mock_graphql_client):
        """Test search handles API errors."""
        # Arrange
        repo = CwayUserRepository(mock_graphql_client)
        mock_graphql_client.execute_query.side_effect = Exception("API Error")
        
        # Act & Assert
        with pytest.raises(CwayAPIError, match="Failed to search users and teams"):
            await repo.find_users_and_teams("test")
    
    @pytest.mark.asyncio
    async def test_get_permission_groups_success(self, mock_graphql_client):
        """Test retrieving permission groups."""
        # Arrange
        repo = CwayUserRepository(mock_graphql_client)
        mock_graphql_client.execute_query.return_value = {
            "getPermissionGroups": [
                {
                    "id": "perm-1",
                    "name": "Admin",
                    "description": "Full access",
                    "permissions": ["READ", "WRITE", "DELETE"]
                },
                {
                    "id": "perm-2",
                    "name": "Editor",
                    "description": "Edit access",
                    "permissions": ["READ", "WRITE"]
                }
            ]
        }
        
        # Act
        groups = await repo.get_permission_groups()
        
        # Assert
        assert len(groups) == 2
        assert groups[0]["name"] == "Admin"
        assert len(groups[0]["permissions"]) == 3
        assert groups[1]["name"] == "Editor"
        mock_graphql_client.execute_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_permission_groups_empty(self, mock_graphql_client):
        """Test permission groups with no data."""
        # Arrange
        repo = CwayUserRepository(mock_graphql_client)
        mock_graphql_client.execute_query.return_value = {
            "getPermissionGroups": []
        }
        
        # Act
        groups = await repo.get_permission_groups()
        
        # Assert
        assert len(groups) == 0
    
    @pytest.mark.asyncio
    async def test_get_permission_groups_api_error(self, mock_graphql_client):
        """Test permission groups handles API errors."""
        # Arrange
        repo = CwayUserRepository(mock_graphql_client)
        mock_graphql_client.execute_query.side_effect = Exception("API Error")
        
        # Act & Assert
        with pytest.raises(CwayAPIError, match="Failed to get permission groups"):
            await repo.get_permission_groups()
    
    @pytest.mark.asyncio
    async def test_set_user_permissions_success(self, mock_graphql_client):
        """Test setting user permissions."""
        # Arrange
        repo = CwayUserRepository(mock_graphql_client)
        mock_graphql_client.execute_mutation.return_value = {
            "setPermissionGroupForUsers": True
        }
        
        # Act
        success = await repo.set_user_permissions(
            usernames=["user1", "user2"],
            permission_group_id="perm-123"
        )
        
        # Assert
        assert success is True
        mock_graphql_client.execute_mutation.assert_called_once()
        call_args = mock_graphql_client.execute_mutation.call_args
        assert call_args[0][1]["usernames"] == ["user1", "user2"]
        assert call_args[0][1]["permissionGroupId"] == "perm-123"
    
    @pytest.mark.asyncio
    async def test_set_user_permissions_failure(self, mock_graphql_client):
        """Test failed permission update."""
        # Arrange
        repo = CwayUserRepository(mock_graphql_client)
        mock_graphql_client.execute_mutation.return_value = {
            "setPermissionGroupForUsers": False
        }
        
        # Act
        success = await repo.set_user_permissions(
            usernames=["user1"],
            permission_group_id="invalid"
        )
        
        # Assert
        assert success is False
    
    @pytest.mark.asyncio
    async def test_set_user_permissions_api_error(self, mock_graphql_client):
        """Test permission update handles API errors."""
        # Arrange
        repo = CwayUserRepository(mock_graphql_client)
        mock_graphql_client.execute_mutation.side_effect = Exception("API Error")
        
        # Act & Assert
        with pytest.raises(CwayAPIError, match="Failed to set user permissions"):
            await repo.set_user_permissions(["user1"], "perm-123")
