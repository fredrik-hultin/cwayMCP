"""
Share Repository - Handles file sharing operations.

Single Responsibility: Share data access only.
"""

from typing import Any, Dict, List, Optional
import logging

from src.infrastructure.graphql_client import CwayAPIError
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class ShareRepository(BaseRepository):
    """Repository for share management operations."""
    
    async def find_shares(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Find all shares."""
        query = """
        query FindShares($paging: Paging) {
            findShares(paging: $paging) {
                shares {
                    id
                    name
                    description
                    created
                    expiresAt
                    downloadCount
                    maxDownloads
                    password
                }
                totalHits
            }
        }
        """
        
        try:
            result = await self._execute_query(query, {
                "paging": {"page": 0, "pageSize": limit}
            })
            shares_data = result.get("findShares", {})
            return shares_data.get("shares", [])
            
        except Exception as e:
            logger.error(f"Failed to find shares: {e}")
            raise CwayAPIError(f"Failed to find shares: {e}")
    
    async def get_share(self, share_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific share by ID."""
        query = """
        query GetShare($id: UUID!) {
            share(id: $id) {
                id
                name
                description
                created
                expiresAt
                downloadCount
                maxDownloads
                password
                files {
                    id
                    name
                    fileSize
                }
            }
        }
        """
        
        try:
            result = await self._execute_query(query, {"id": share_id})
            return result.get("share")
            
        except Exception as e:
            logger.error(f"Failed to get share: {e}")
            raise CwayAPIError(f"Failed to get share: {e}")
    
    async def create_share(self, name: str, file_ids: List[str], 
                          description: Optional[str] = None,
                          expires_at: Optional[str] = None,
                          max_downloads: Optional[int] = None,
                          password: Optional[str] = None) -> Dict[str, Any]:
        """Create a new share."""
        mutation = """
        mutation CreateShare($input: CreateShareInput!) {
            createShare(input: $input) {
                id
                name
                description
                created
                expiresAt
                maxDownloads
            }
        }
        """
        
        try:
            share_input = {
                "name": name,
                "fileIds": file_ids,
                "description": description,
                "expiresAt": expires_at,
                "maxDownloads": max_downloads,
                "password": password
            }
            # Remove None values
            share_input = {k: v for k, v in share_input.items() if v is not None}
            
            result = await self._execute_mutation(mutation, {"input": share_input})
            return result.get("createShare", {})
            
        except Exception as e:
            logger.error(f"Failed to create share: {e}")
            raise CwayAPIError(f"Failed to create share: {e}")
    
    async def delete_share(self, share_id: str) -> bool:
        """Delete a share."""
        mutation = """
        mutation DeleteShare($id: UUID!) {
            deleteShare(id: $id)
        }
        """
        
        try:
            result = await self._execute_mutation(mutation, {"id": share_id})
            return result.get("deleteShare", False)
            
        except Exception as e:
            logger.error(f"Failed to delete share: {e}")
            raise CwayAPIError(f"Failed to delete share: {e}")
