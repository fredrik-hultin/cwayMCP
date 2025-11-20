"""
Artwork Repository - Handles artwork operations.

Single Responsibility: Artwork data access only.
"""

from typing import Any, Dict, List, Optional
import logging

from src.infrastructure.graphql_client import CwayAPIError
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class ArtworkRepository(BaseRepository):
    """Repository for artwork operations."""
    
    async def get_artwork(self, artwork_id: str) -> Optional[Dict[str, Any]]:
        """Get a single artwork by ID."""
        query = """
        query GetArtwork($id: UUID!) {
            artwork(id: $id) {
                id
                name
                description
                state
                revisions {
                    id
                    comment
                }
            }
        }
        """
        
        try:
            result = await self._execute_query(query, {"id": artwork_id})
            return result.get("artwork")
            
        except Exception as e:
            logger.error(f"Failed to get artwork: {e}")
            raise CwayAPIError(f"Failed to get artwork: {e}")
    
    async def create_artwork(self, project_id: str, name: str, 
                            description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new artwork in a project."""
        mutation = """
        mutation CreateArtwork($input: CreateArtworkInput!) {
            createArtwork(input: $input) {
                id
                artworks {
                    id
                    name
                    state
                }
            }
        }
        """
        
        artwork_input = {
            "projectId": project_id,
            "name": name
        }
        if description:
            artwork_input["description"] = description
        
        try:
            result = await self._execute_mutation(mutation, {"input": artwork_input})
            create_result = result.get("createArtwork", {})
            artworks = create_result.get("artworks", [])
            return artworks[0] if artworks else {}
            
        except Exception as e:
            logger.error(f"Failed to create artwork: {e}")
            raise CwayAPIError(f"Failed to create artwork: {e}")
    
    async def approve_artwork(self, artwork_id: str) -> Optional[Dict[str, Any]]:
        """Approve an artwork."""
        mutation = """
        mutation ApproveArtwork($artworkId: UUID!) {
            approveArtwork(artworkId: $artworkId) {
                id
                name
                state
            }
        }
        """
        
        try:
            result = await self._execute_mutation(mutation, {"artworkId": artwork_id})
            return result.get("approveArtwork")
            
        except Exception as e:
            logger.error(f"Failed to approve artwork: {e}")
            raise CwayAPIError(f"Failed to approve artwork: {e}")
    
    async def reject_artwork(self, artwork_id: str, reason: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Reject an artwork."""
        mutation = """
        mutation RejectArtwork($input: RejectArtworkInput) {
            rejectArtwork(input: $input) {
                id
                name
                state
            }
        }
        """
        
        reject_input = {"artworkId": artwork_id}
        if reason:
            reject_input["reason"] = reason
        
        try:
            result = await self._execute_mutation(mutation, {"input": reject_input})
            return result.get("rejectArtwork")
            
        except Exception as e:
            logger.error(f"Failed to reject artwork: {e}")
            raise CwayAPIError(f"Failed to reject artwork: {e}")
    
    async def get_artworks_to_approve(self) -> List[Dict[str, Any]]:
        """Get all artworks awaiting approval by the current user."""
        query = """
        query GetArtworksToApprove {
            artworksToApprove {
                id
                projectId
                projectName
                name
                description
                state
                status
                created
                startDate
                endDate
                category {
                    id
                    name
                }
                currentRevision {
                    id
                    revisionNumber
                    created
                }
                previewFile {
                    id
                    name
                    fileSize
                    url
                }
            }
        }
        """
        
        try:
            result = await self._execute_query(query, {})
            return result.get("artworksToApprove", [])
            
        except Exception as e:
            logger.error(f"Failed to get artworks to approve: {e}")
            raise CwayAPIError(f"Failed to get artworks to approve: {e}")
    
    async def get_artworks_to_upload(self) -> List[Dict[str, Any]]:
        """Get all artworks where the current user needs to upload a revision."""
        query = """
        query GetArtworksToUpload {
            artworksToUpload {
                id
                projectId
                projectName
                name
                description
                state
                status
                created
                startDate
                endDate
                category {
                    id
                    name
                }
                currentRevision {
                    id
                    revisionNumber
                    created
                }
                previewFile {
                    id
                    name
                    fileSize
                    url
                }
            }
        }
        """
        
        try:
            result = await self._execute_query(query, {})
            return result.get("artworksToUpload", [])
            
        except Exception as e:
            logger.error(f"Failed to get artworks to upload: {e}")
            raise CwayAPIError(f"Failed to get artworks to upload: {e}")
    
    async def get_my_artworks(self) -> Dict[str, Any]:
        """Aggregate all artworks relevant to the current user."""
        try:
            # Get artworks requiring action
            to_approve = await self.get_artworks_to_approve()
            to_upload = await self.get_artworks_to_upload()
            
            return {
                "to_approve": to_approve,
                "to_upload": to_upload,
                "total_count": len(to_approve) + len(to_upload)
            }
            
        except Exception as e:
            logger.error(f"Failed to get user's artworks: {e}")
            raise CwayAPIError(f"Failed to get user's artworks: {e}")
    
    async def submit_artwork_for_review(self, artwork_id: str) -> Dict[str, Any]:
        """Submit artwork for approval review."""
        mutation = """
        mutation SubmitArtworkForReview($artworkId: UUID!) {
            submitArtworkForReview(artworkId: $artworkId) {
                id
                name
                state
                status
            }
        }
        """
        
        try:
            result = await self._execute_mutation(mutation, {"artworkId": artwork_id})
            return result.get("submitArtworkForReview", {})
            
        except Exception as e:
            logger.error(f"Failed to submit artwork for review: {e}")
            raise CwayAPIError(f"Failed to submit artwork for review: {e}")
    
    async def request_artwork_changes(self, artwork_id: str, reason: str) -> Dict[str, Any]:
        """Request changes/revisions on an artwork."""
        mutation = """
        mutation RequestArtworkChanges($input: RequestChangesInput!) {
            requestArtworkChanges(input: $input) {
                id
                name
                state
                status
            }
        }
        """
        
        try:
            result = await self._execute_mutation(mutation, {
                "input": {
                    "artworkId": artwork_id,
                    "reason": reason
                }
            })
            return result.get("requestArtworkChanges", {})
            
        except Exception as e:
            logger.error(f"Failed to request artwork changes: {e}")
            raise CwayAPIError(f"Failed to request artwork changes: {e}")
    
    async def get_artwork_comments(self, artwork_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get artwork comments and feedback."""
        query = """
        query GetArtworkComments($artworkId: UUID!, $limit: Int) {
            artworkComments(artworkId: $artworkId, limit: $limit) {
                id
                text
                author {
                    id
                    name
                    username
                }
                created
                edited
            }
        }
        """
        
        try:
            result = await self._execute_query(query, {
                "artworkId": artwork_id,
                "limit": limit
            })
            return result.get("artworkComments", [])
            
        except Exception as e:
            logger.error(f"Failed to get artwork comments: {e}")
            raise CwayAPIError(f"Failed to get artwork comments: {e}")
    
    async def add_artwork_comment(self, artwork_id: str, text: str) -> Dict[str, Any]:
        """Add a comment to an artwork."""
        mutation = """
        mutation AddArtworkComment($input: AddArtworkCommentInput!) {
            addArtworkComment(input: $input) {
                id
                text
                author {
                    id
                    name
                }
                created
            }
        }
        """
        
        try:
            result = await self._execute_mutation(mutation, {
                "input": {
                    "artworkId": artwork_id,
                    "text": text
                }
            })
            return result.get("addArtworkComment", {})
            
        except Exception as e:
            logger.error(f"Failed to add artwork comment: {e}")
            raise CwayAPIError(f"Failed to add artwork comment: {e}")
    
    async def get_artwork_versions(self, artwork_id: str) -> List[Dict[str, Any]]:
        """Get all versions/revisions of an artwork."""
        query = """
        query GetArtworkVersions($artworkId: UUID!) {
            artworkVersions(artworkId: $artworkId) {
                id
                revisionNumber
                created
                creator {
                    id
                    name
                }
                comment
                files {
                    id
                    name
                    fileSize
                }
            }
        }
        """
        
        try:
            result = await self._execute_query(query, {"artworkId": artwork_id})
            return result.get("artworkVersions", [])
            
        except Exception as e:
            logger.error(f"Failed to get artwork versions: {e}")
            raise CwayAPIError(f"Failed to get artwork versions: {e}")
    
    async def restore_artwork_version(self, artwork_id: str, version_id: str) -> Dict[str, Any]:
        """Restore/rollback artwork to a previous version."""
        mutation = """
        mutation RestoreArtworkVersion($artworkId: UUID!, $versionId: UUID!) {
            restoreArtworkVersion(artworkId: $artworkId, versionId: $versionId) {
                id
                name
                currentRevision {
                    id
                    revisionNumber
                }
            }
        }
        """
        
        try:
            result = await self._execute_mutation(mutation, {
                "artworkId": artwork_id,
                "versionId": version_id
            })
            return result.get("restoreArtworkVersion", {})
            
        except Exception as e:
            logger.error(f"Failed to restore artwork version: {e}")
            raise CwayAPIError(f"Failed to restore artwork version: {e}")
    
    async def assign_artwork(self, artwork_id: str, user_id: str) -> Dict[str, Any]:
        """Assign an artwork to a user."""
        mutation = """
        mutation AssignArtwork($artworkId: UUID!, $userId: UUID!) {
            assignArtwork(artworkId: $artworkId, userId: $userId) {
                id
                name
                assignedTo {
                    id
                    name
                    username
                }
            }
        }
        """
        
        try:
            result = await self._execute_mutation(mutation, {
                "artworkId": artwork_id,
                "userId": user_id
            })
            artwork = result.get("assignArtwork")
            if not artwork:
                raise CwayAPIError("Failed to assign artwork: artwork not found")
            return artwork
            
        except Exception as e:
            logger.error(f"Failed to assign artwork: {e}")
            raise CwayAPIError(f"Failed to assign artwork: {e}")
    
    async def duplicate_artwork(self, artwork_id: str, new_name: Optional[str] = None) -> Dict[str, Any]:
        """Duplicate an artwork with optional new name."""
        mutation = """
        mutation DuplicateArtwork($artworkId: UUID!, $newName: String) {
            duplicateArtwork(artworkId: $artworkId, newName: $newName) {
                id
                name
                projectId
                created
            }
        }
        """
        
        try:
            variables = {"artworkId": artwork_id}
            if new_name:
                variables["newName"] = new_name
            
            result = await self._execute_mutation(mutation, variables)
            artwork = result.get("duplicateArtwork")
            if not artwork:
                raise CwayAPIError("Failed to duplicate artwork: artwork not found")
            return artwork
            
        except Exception as e:
            logger.error(f"Failed to duplicate artwork: {e}")
            raise CwayAPIError(f"Failed to duplicate artwork: {e}")
    
    async def archive_artwork(self, artwork_id: str) -> Dict[str, Any]:
        """Archive an artwork."""
        mutation = """
        mutation ArchiveArtwork($artworkId: UUID!) {
            archiveArtwork(artworkId: $artworkId) {
                id
                name
                archived
                status
            }
        }
        """
        
        try:
            result = await self._execute_mutation(mutation, {"artworkId": artwork_id})
            artwork = result.get("archiveArtwork")
            if not artwork:
                raise CwayAPIError("Failed to archive artwork: artwork not found")
            return artwork
            
        except Exception as e:
            logger.error(f"Failed to archive artwork: {e}")
            raise CwayAPIError(f"Failed to archive artwork: {e}")
    
    async def unarchive_artwork(self, artwork_id: str) -> Dict[str, Any]:
        """Unarchive an artwork."""
        mutation = """
        mutation UnarchiveArtwork($artworkId: UUID!) {
            unarchiveArtwork(artworkId: $artworkId) {
                id
                name
                archived
                status
            }
        }
        """
        
        try:
            result = await self._execute_mutation(mutation, {"artworkId": artwork_id})
            artwork = result.get("unarchiveArtwork")
            if not artwork:
                raise CwayAPIError("Failed to unarchive artwork: artwork not found")
            return artwork
            
        except Exception as e:
            logger.error(f"Failed to unarchive artwork: {e}")
            raise CwayAPIError(f"Failed to unarchive artwork: {e}")
