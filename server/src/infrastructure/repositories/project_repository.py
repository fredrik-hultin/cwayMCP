"""
Project Repository - Handles project operations.

Single Responsibility: Project data access only.
"""

from typing import Any, Dict, List, Optional
import logging

from src.domain.cway_entities import PlannerProject, ProjectState, parse_cway_date
from src.infrastructure.graphql_client import CwayAPIError
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class ProjectRepository(BaseRepository):
    """Repository for project operations."""
    
    async def get_planner_projects(self) -> List[PlannerProject]:
        """Get all planner projects."""
        query = """
        query GetPlannerProjects {
            plannerProjects {
                id
                name
                state
                percentageDone
                startDate
                endDate
            }
        }
        """
        
        try:
            result = await self._execute_query(query, {})
            projects_data = result.get("plannerProjects", [])
            
            projects = []
            for data in projects_data:
                project = PlannerProject(
                    id=data["id"],
                    name=data["name"],
                    state=ProjectState(data["state"]),
                    percentageDone=data.get("percentageDone", 0.0),
                    startDate=parse_cway_date(data.get("startDate")),
                    endDate=parse_cway_date(data.get("endDate"))
                )
                projects.append(project)
                
            return projects
            
        except Exception as e:
            logger.error(f"Failed to fetch planner projects: {e}")
            raise CwayAPIError(f"Failed to fetch planner projects: {e}")
            
    async def find_project_by_id(self, project_id: str) -> Optional[PlannerProject]:
        """Find a specific planner project by ID."""
        projects = await self.get_planner_projects()
        for project in projects:
            if project.id == project_id:
                return project
        return None
        
    async def get_projects_by_state(self, state: ProjectState) -> List[PlannerProject]:
        """Get projects filtered by state."""
        projects = await self.get_planner_projects()
        return [p for p in projects if p.state == state]
        
    async def get_active_projects(self) -> List[PlannerProject]:
        """Get all active (in progress) projects."""
        return await self.get_projects_by_state(ProjectState.IN_PROGRESS)
        
    async def get_completed_projects(self) -> List[PlannerProject]:
        """Get all completed projects."""
        return await self.get_projects_by_state(ProjectState.COMPLETED)
    
    async def search_projects(self, query: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
        """Search for projects."""
        gql_query = """
        query SearchProjects($filter: ProjectFilter, $paging: Paging) {
            projects(filter: $filter, paging: $paging) {
                projects {
                    id
                    name
                    description
                }
                page
                totalHits
            }
        }
        """
        
        try:
            variables = {
                "paging": {"page": 0, "pageSize": limit}
            }
            if query:
                variables["filter"] = {"search": query}
            
            result = await self._execute_query(gql_query, variables)
            projects_data = result.get("projects", {})
            
            # Support both old (items) and new (projects) shapes
            items = projects_data.get("items") or projects_data.get("projects") or []
            return {
                "projects": items,
                "total_hits": projects_data.get("totalHits", 0)
            }
            
        except Exception as e:
            logger.error(f"Failed to search projects: {e}")
            raise CwayAPIError(f"Failed to search projects: {e}")
    
    async def get_project_by_id(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get a regular project by ID (not planner project)."""
        query = """
        query GetProject($id: UUID!) {
            project(id: $id) {
                id
                name
                description
                state
                status
                orderNo
                refOrderNo
                notes
                created
                startDate
                endDate
                lastActivity
                orderer {
                    id
                    name
                    username
                    email
                }
                projectManager {
                    id
                    name
                    username
                    email
                }
                progress {
                    artworksDone
                    percentageDone
                    artworksInProgress
                    percentageInProgress
                    artworksUnstarted
                    percentageUnstarted
                }
                artworks {
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
                    approvalDate
                    deliveryDate
                    category {
                        id
                        name
                    }
                    orderer {
                        id
                        name
                        username
                        email
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
                    }
                }
            }
        }
        """
        
        try:
            result = await self._execute_query(query, {"id": project_id})
            return result.get("project")
            
        except Exception as e:
            logger.error(f"Failed to get project: {e}")
            raise CwayAPIError(f"Failed to get project: {e}")
    
    async def create_project(self, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new project."""
        mutation = """
        mutation CreateProject($input: ProjectInput!) {
            createProject(input: $input) {
                id
                name
                description
            }
        }
        """
        
        project_input = {
            "name": name,
            "description": description
        }
        
        try:
            result = await self._execute_mutation(mutation, {"input": project_input})
            return result.get("createProject", {})
            
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            raise CwayAPIError(f"Failed to create project: {e}")
    
    async def update_project(self, project_id: str, name: Optional[str] = None,
                           description: Optional[str] = None) -> Dict[str, Any]:
        """Update an existing project."""
        mutation = """
        mutation UpdateProject($id: UUID!, $input: ProjectInput!) {
            updateProject(id: $id, input: $input) {
                id
                name
                description
            }
        }
        """
        
        project_input = {}
        if name:
            project_input["name"] = name
        if description:
            project_input["description"] = description
        
        try:
            result = await self._execute_mutation(mutation, {
                "id": project_id,
                "input": project_input
            })
            return result.get("updateProject", {})
            
        except Exception as e:
            logger.error(f"Failed to update project: {e}")
            raise CwayAPIError(f"Failed to update project: {e}")
    
    async def close_projects(self, project_ids: List[str], force: bool = False) -> bool:
        """Close one or more projects."""
        mutation = """
        mutation CloseProjects($projectIds: [UUID!]!, $force: Boolean) {
            closeProjects(projectIds: $projectIds, force: $force)
        }
        """
        
        try:
            result = await self._execute_mutation(mutation, {
                "projectIds": project_ids,
                "force": force
            })
            return result.get("closeProjects", False)
            
        except Exception as e:
            logger.error(f"Failed to close projects: {e}")
            raise CwayAPIError(f"Failed to close projects: {e}")
    
    async def reopen_projects(self, project_ids: List[str]) -> bool:
        """Reopen closed projects."""
        mutation = """
        mutation ReopenProjects($projectIds: [UUID!]!) {
            reopenProjects(projectIds: $projectIds)
        }
        """
        
        try:
            result = await self._execute_mutation(mutation, {
                "projectIds": project_ids
            })
            return result.get("reopenProjects", False)
            
        except Exception as e:
            logger.error(f"Failed to reopen projects: {e}")
            raise CwayAPIError(f"Failed to reopen projects: {e}")
    
    async def delete_projects(self, project_ids: List[str], force: bool = False) -> bool:
        """Delete one or more projects."""
        mutation = """
        mutation DeleteProjects($projectIds: [UUID!]!, $force: Boolean) {
            deleteProjects(projectIds: $projectIds, force: $force)
        }
        """
        
        try:
            result = await self._execute_mutation(mutation, {
                "projectIds": project_ids,
                "force": force
            })
            return result.get("deleteProjects", False)
            
        except Exception as e:
            logger.error(f"Failed to delete projects: {e}")
            raise CwayAPIError(f"Failed to delete projects: {e}")
    
    async def get_project_members(self, project_id: str) -> List[Dict[str, Any]]:
        """Get list of project team members."""
        query = """
        query GetProjectMembers($projectId: UUID!) {
            projectMembers(projectId: $projectId) {
                user {
                    id
                    name
                    username
                    email
                }
                role
                addedAt
            }
        }
        """
        
        try:
            result = await self._execute_query(query, {"projectId": project_id})
            return result.get("projectMembers", [])
            
        except Exception as e:
            logger.error(f"Failed to get project members: {e}")
            raise CwayAPIError(f"Failed to get project members: {e}")
    
    async def add_project_member(self, project_id: str, user_id: str, role: str = "MEMBER") -> Dict[str, Any]:
        """Add a user to a project team."""
        mutation = """
        mutation AddProjectMember($input: AddProjectMemberInput!) {
            addProjectMember(input: $input) {
                user {
                    id
                    name
                    username
                }
                role
            }
        }
        """
        
        try:
            result = await self._execute_mutation(mutation, {
                "input": {
                    "projectId": project_id,
                    "userId": user_id,
                    "role": role
                }
            })
            return result.get("addProjectMember", {})
            
        except Exception as e:
            logger.error(f"Failed to add project member: {e}")
            raise CwayAPIError(f"Failed to add project member: {e}")
    
    async def remove_project_member(self, project_id: str, user_id: str) -> bool:
        """Remove a user from a project team."""
        mutation = """
        mutation RemoveProjectMember($projectId: UUID!, $userId: UUID!) {
            removeProjectMember(projectId: $projectId, userId: $userId)
        }
        """
        
        try:
            result = await self._execute_mutation(mutation, {
                "projectId": project_id,
                "userId": user_id
            })
            return result.get("removeProjectMember", False)
            
        except Exception as e:
            logger.error(f"Failed to remove project member: {e}")
            raise CwayAPIError(f"Failed to remove project member: {e}")
    
    async def update_project_member_role(self, project_id: str, user_id: str, role: str) -> Dict[str, Any]:
        """Update a project member's role."""
        mutation = """
        mutation UpdateProjectMemberRole($input: UpdateProjectMemberInput!) {
            updateProjectMemberRole(input: $input) {
                user {
                    id
                    name
                }
                role
            }
        }
        """
        
        try:
            result = await self._execute_mutation(mutation, {
                "input": {
                    "projectId": project_id,
                    "userId": user_id,
                    "role": role
                }
            })
            return result.get("updateProjectMemberRole", {})
            
        except Exception as e:
            logger.error(f"Failed to update project member role: {e}")
            raise CwayAPIError(f"Failed to update project member role: {e}")
    
    async def get_project_comments(self, project_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get project comments/discussions."""
        query = """
        query GetProjectComments($projectId: UUID!, $limit: Int) {
            projectComments(projectId: $projectId, limit: $limit) {
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
                "projectId": project_id,
                "limit": limit
            })
            return result.get("projectComments", [])
            
        except Exception as e:
            logger.error(f"Failed to get project comments: {e}")
            raise CwayAPIError(f"Failed to get project comments: {e}")
    
    async def add_project_comment(self, project_id: str, text: str) -> Dict[str, Any]:
        """Add a comment to a project."""
        mutation = """
        mutation AddProjectComment($input: AddProjectCommentInput!) {
            addProjectComment(input: $input) {
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
                    "projectId": project_id,
                    "text": text
                }
            })
            return result.get("addProjectComment", {})
            
        except Exception as e:
            logger.error(f"Failed to add project comment: {e}")
            raise CwayAPIError(f"Failed to add project comment: {e}")
    
    async def get_project_attachments(self, project_id: str) -> List[Dict[str, Any]]:
        """Get list of project attachments."""
        query = """
        query GetProjectAttachments($projectId: UUID!) {
            projectAttachments(projectId: $projectId) {
                id
                name
                fileSize
                mimeType
                url
                uploaded
                uploader {
                    id
                    name
                }
            }
        }
        """
        
        try:
            result = await self._execute_query(query, {"projectId": project_id})
            return result.get("projectAttachments", [])
            
        except Exception as e:
            logger.error(f"Failed to get project attachments: {e}")
            raise CwayAPIError(f"Failed to get project attachments: {e}")
    
    async def upload_project_attachment(self, project_id: str, file_id: str, name: str) -> Dict[str, Any]:
        """Attach an uploaded file to a project."""
        mutation = """
        mutation AttachFileToProject($input: AttachFileInput!) {
            attachFileToProject(input: $input) {
                id
                name
                fileSize
            }
        }
        """
        
        try:
            result = await self._execute_mutation(mutation, {
                "input": {
                    "projectId": project_id,
                    "fileId": file_id,
                    "name": name
                }
            })
            return result.get("attachFileToProject", {})
            
        except Exception as e:
            logger.error(f"Failed to upload project attachment: {e}")
            raise CwayAPIError(f"Failed to upload project attachment: {e}")
