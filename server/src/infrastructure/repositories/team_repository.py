"""
Team Repository - Handles team management and permissions operations.

Single Responsibility: Team and permission data access only.
"""

from typing import Any, Dict, List, Optional
import logging

from src.infrastructure.graphql_client import CwayAPIError
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class TeamRepository(BaseRepository):
    """Repository for team management and permission operations."""
    
    async def get_team_members(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all team members for a project."""
        query = """
        query GetTeamMembers($projectId: UUID!) {
            project(id: $projectId) {
                team {
                    id
                    user {
                        id
                        username
                        firstName
                        lastName
                        email
                    }
                    role
                    addedAt
                }
            }
        }
        """
        
        try:
            result = await self._execute_query(query, {"projectId": project_id})
            project = result.get("project")
            if not project:
                raise CwayAPIError("Failed to get team members: project not found")
            return project.get("team", [])
            
        except Exception as e:
            logger.error(f"Failed to get team members: {e}")
            raise CwayAPIError(f"Failed to get team members: {e}")
    
    async def add_team_member(self, project_id: str, user_id: str, role: Optional[str] = None) -> Dict[str, Any]:
        """Add a user to project team."""
        mutation = """
        mutation AddTeamMember($projectId: UUID!, $userId: UUID!, $role: String) {
            addTeamMember(projectId: $projectId, userId: $userId, role: $role) {
                id
                user {
                    id
                    username
                    firstName
                    lastName
                }
                role
                addedAt
            }
        }
        """
        
        try:
            variables = {"projectId": project_id, "userId": user_id}
            if role:
                variables["role"] = role
            
            result = await self._execute_mutation(mutation, variables)
            team_member = result.get("addTeamMember")
            if not team_member:
                raise CwayAPIError("Failed to add team member: operation failed")
            return team_member
            
        except Exception as e:
            logger.error(f"Failed to add team member: {e}")
            raise CwayAPIError(f"Failed to add team member: {e}")
    
    async def remove_team_member(self, project_id: str, user_id: str) -> Dict[str, Any]:
        """Remove a user from project team."""
        mutation = """
        mutation RemoveTeamMember($projectId: UUID!, $userId: UUID!) {
            removeTeamMember(projectId: $projectId, userId: $userId) {
                success
                message
            }
        }
        """
        
        try:
            result = await self._execute_mutation(mutation, {
                "projectId": project_id,
                "userId": user_id
            })
            response = result.get("removeTeamMember")
            if not response or not response.get("success"):
                raise CwayAPIError("Failed to remove team member: operation failed")
            return response
            
        except Exception as e:
            logger.error(f"Failed to remove team member: {e}")
            raise CwayAPIError(f"Failed to remove team member: {e}")
    
    async def update_team_member_role(self, project_id: str, user_id: str, role: str) -> Dict[str, Any]:
        """Update a team member's role in project."""
        mutation = """
        mutation UpdateTeamMemberRole($projectId: UUID!, $userId: UUID!, $role: String!) {
            updateTeamMemberRole(projectId: $projectId, userId: $userId, role: $role) {
                id
                user {
                    id
                    username
                    firstName
                    lastName
                }
                role
                updatedAt
            }
        }
        """
        
        try:
            result = await self._execute_mutation(mutation, {
                "projectId": project_id,
                "userId": user_id,
                "role": role
            })
            team_member = result.get("updateTeamMemberRole")
            if not team_member:
                raise CwayAPIError("Failed to update team member role: operation failed")
            return team_member
            
        except Exception as e:
            logger.error(f"Failed to update team member role: {e}")
            raise CwayAPIError(f"Failed to update team member role: {e}")
    
    async def get_user_roles(self) -> List[Dict[str, Any]]:
        """Get all available user roles."""
        query = """
        query GetUserRoles {
            userRoles {
                id
                name
                description
                permissions
            }
        }
        """
        
        try:
            result = await self._execute_query(query, {})
            return result.get("userRoles", [])
            
        except Exception as e:
            logger.error(f"Failed to get user roles: {e}")
            raise CwayAPIError(f"Failed to get user roles: {e}")
    
    async def transfer_project_ownership(self, project_id: str, new_owner_id: str) -> Dict[str, Any]:
        """Transfer project ownership to another user."""
        mutation = """
        mutation TransferProjectOwnership($projectId: UUID!, $newOwnerId: UUID!) {
            transferProjectOwnership(projectId: $projectId, newOwnerId: $newOwnerId) {
                id
                name
                owner {
                    id
                    username
                    firstName
                    lastName
                }
                updatedAt
            }
        }
        """
        
        try:
            result = await self._execute_mutation(mutation, {
                "projectId": project_id,
                "newOwnerId": new_owner_id
            })
            project = result.get("transferProjectOwnership")
            if not project:
                raise CwayAPIError("Failed to transfer project ownership: operation failed")
            return project
            
        except Exception as e:
            logger.error(f"Failed to transfer project ownership: {e}")
            raise CwayAPIError(f"Failed to transfer project ownership: {e}")
