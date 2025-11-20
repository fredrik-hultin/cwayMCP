"""
Search Repository - Handles search and activity tracking operations.

Single Responsibility: Search, timeline, and activity data access only.
"""

from typing import Any, Dict, List, Optional
import logging

from src.infrastructure.graphql_client import CwayAPIError
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class SearchRepository(BaseRepository):
    """Repository for search and activity tracking operations."""
    
    async def search_artworks(self, query: Optional[str] = None, project_id: Optional[str] = None,
                             status: Optional[str] = None, limit: int = 50, page: int = 0) -> Dict[str, Any]:
        """Search artworks with filters and pagination."""
        gql_query = """
        query SearchArtworks($query: String, $projectId: UUID, $status: String, $paging: Paging) {
            searchArtworks(query: $query, projectId: $projectId, status: $status, paging: $paging) {
                artworks {
                    id
                    name
                    description
                    status
                    projectId
                    created
                    updated
                }
                totalHits
                page
            }
        }
        """
        
        try:
            variables = {
                "paging": {"page": page, "pageSize": limit}
            }
            if query:
                variables["query"] = query
            if project_id:
                variables["projectId"] = project_id
            if status:
                variables["status"] = status
            
            result = await self._execute_query(gql_query, variables)
            return result.get("searchArtworks", {"artworks": [], "totalHits": 0, "page": 0})
            
        except Exception as e:
            logger.error(f"Failed to search artworks: {e}")
            raise CwayAPIError(f"Failed to search artworks: {e}")
    
    async def get_project_timeline(self, project_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get chronological event timeline for project."""
        query = """
        query GetProjectTimeline($projectId: UUID!, $limit: Int) {
            projectTimeline(projectId: $projectId, limit: $limit) {
                id
                eventType
                description
                timestamp
                actor {
                    id
                    username
                    firstName
                    lastName
                }
                metadata
            }
        }
        """
        
        try:
            result = await self._execute_query(query, {
                "projectId": project_id,
                "limit": limit
            })
            return result.get("projectTimeline", [])
            
        except Exception as e:
            logger.error(f"Failed to get project timeline: {e}")
            raise CwayAPIError(f"Failed to get project timeline: {e}")
    
    async def get_user_activity(self, user_id: str, days: int = 30, limit: int = 100) -> List[Dict[str, Any]]:
        """Get user activity history."""
        query = """
        query GetUserActivity($userId: UUID!, $days: Int, $limit: Int) {
            userActivity(userId: $userId, days: $days, limit: $limit) {
                id
                activityType
                description
                timestamp
                projectId
                projectName
                artworkId
                artworkName
                metadata
            }
        }
        """
        
        try:
            result = await self._execute_query(query, {
                "userId": user_id,
                "days": days,
                "limit": limit
            })
            return result.get("userActivity", [])
            
        except Exception as e:
            logger.error(f"Failed to get user activity: {e}")
            raise CwayAPIError(f"Failed to get user activity: {e}")
    
    async def bulk_update_artwork_status(self, artwork_ids: List[str], status: str) -> Dict[str, Any]:
        """Batch update status for multiple artworks."""
        mutation = """
        mutation BulkUpdateArtworkStatus($artworkIds: [UUID!]!, $status: String!) {
            bulkUpdateArtworkStatus(artworkIds: $artworkIds, status: $status) {
                updatedArtworks {
                    id
                    name
                    status
                    updated
                }
                successCount
                failedCount
            }
        }
        """
        
        try:
            result = await self._execute_mutation(mutation, {
                "artworkIds": artwork_ids,
                "status": status
            })
            response = result.get("bulkUpdateArtworkStatus")
            if not response:
                raise CwayAPIError("Failed to bulk update artwork status: operation failed")
            return response
            
        except Exception as e:
            logger.error(f"Failed to bulk update artwork status: {e}")
            raise CwayAPIError(f"Failed to bulk update artwork status: {e}")
