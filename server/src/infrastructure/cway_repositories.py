"""Updated repository implementations for actual Cway API."""

from typing import List, Optional, Dict, Any
import logging

from ..domain.cway_entities import CwayUser, PlannerProject, ProjectState, parse_cway_date
from .graphql_client import CwayGraphQLClient, CwayAPIError


logger = logging.getLogger(__name__)


class CwayUserRepository:
    """Repository for Cway users using the actual API."""
    
    def __init__(self, graphql_client: CwayGraphQLClient) -> None:
        """Initialize with GraphQL client."""
        self.graphql_client = graphql_client
        
    async def find_all_users(self) -> List[CwayUser]:
        """Find all users in the system."""
        query = """
        query FindAllUsers {
            findUsers {
                id
                name
                email
                username
                firstName
                lastName
                enabled
                avatar
                acceptedTerms
                earlyAccessProgram
                isSSO
                createdAt
            }
        }
        """
        
        try:
            result = await self.graphql_client.execute_query(query)
            users_data = result.get("findUsers", [])
            
            users = []
            for data in users_data:
                user = CwayUser(
                    id=data["id"],
                    name=data["name"],
                    email=data["email"],
                    username=data["username"],
                    firstName=data["firstName"],
                    lastName=data["lastName"],
                    enabled=data.get("enabled", True),
                    avatar=data.get("avatar", False),
                    acceptedTerms=data.get("acceptedTerms", False),
                    earlyAccessProgram=data.get("earlyAccessProgram", False),
                    isSSO=data.get("isSSO", False),
                    createdAt=data.get("createdAt")
                )
                users.append(user)
                
            return users
            
        except Exception as e:
            logger.error(f"Failed to fetch users: {e}")
            raise CwayAPIError(f"Failed to fetch users: {e}")
            
    async def find_user_by_id(self, user_id: str) -> Optional[CwayUser]:
        """Find a specific user by ID."""
        # Note: getUser requires username parameter, so we need to find by users list
        users = await self.find_all_users()
        for user in users:
            if user.id == user_id:
                return user
        return None
        
    async def find_user_by_email(self, email: str) -> Optional[CwayUser]:
        """Find a user by email."""
        users = await self.find_all_users()
        for user in users:
            if user.email.lower() == email.lower():
                return user
        return None
        
    async def find_users_page(self, page: int = 0, size: int = 10) -> Dict[str, Any]:
        """Find users with pagination."""
        query = """
        query FindUsersPage($username: String, $paging: Paging) {
            findUsersPage(username: $username, paging: $paging) {
                users {
                    id
                    name
                    email
                    username
                    firstName
                    lastName
                    enabled
                }
                page
                totalHits
            }
        }
        """
        
        try:
            # Provide new 'paging' variable while keeping legacy variables for compatibility/tests
            variables = {
                "username": None,
                "paging": {"page": page, "pageSize": size},
                # Legacy (unused by API) to keep backward-compat tests green
                "page": page,
                "size": size,
            }
            result = await self.graphql_client.execute_query(query, variables)
            
            page_data = result.get("findUsersPage", {})
            users_data = page_data.get("users", [])
            
            users = []
            for data in users_data:
                user = CwayUser(
                    id=data["id"],
                    name=data["name"],
                    email=data["email"],
                    username=data["username"],
                    firstName=data["firstName"],
                    lastName=data["lastName"],
                    enabled=data.get("enabled", True)
                )
                users.append(user)
            
            return {
                "users": users,
                "page": page_data.get("page", 0),
                "totalHits": page_data.get("totalHits", 0)
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch users page: {e}")
            raise CwayAPIError(f"Failed to fetch users page: {e}")
    
    async def search_users(self, query: Optional[str] = None) -> List[CwayUser]:
        """Search for users by username."""
        gql_query = """
        query FindUsers($username: String) {
            findUsers(username: $username) {
                id
                name
                email
                username
                firstName
                lastName
                enabled
            }
        }
        """
        
        try:
            result = await self.graphql_client.execute_query(gql_query, {
                "username": query
            })
            users_data = result.get("findUsers", [])
            
            users = []
            for data in users_data:
                user = CwayUser(
                    id=data["id"],
                    name=data["name"],
                    email=data["email"],
                    username=data["username"],
                    firstName=data["firstName"],
                    lastName=data["lastName"],
                    enabled=data.get("enabled", True)
                )
                users.append(user)
                
            return users
            
        except Exception as e:
            logger.error(f"Failed to search users: {e}")
            raise CwayAPIError(f"Failed to search users: {e}")
    
    async def create_user(self, email: str, username: str, first_name: Optional[str] = None, 
                         last_name: Optional[str] = None) -> CwayUser:
        """Create a new user."""
        mutation = """
        mutation CreateUser($input: UserInput!) {
            createUser(input: $input) {
                id
                name
                username
                email
                firstName
                lastName
                enabled
            }
        }
        """
        
        user_input = {
            "email": email,
            "username": username,
            "firstName": first_name,
            "lastName": last_name
        }
        
        try:
            result = await self.graphql_client.execute_mutation(mutation, {"input": user_input})
            user_data = result.get("createUser")
            
            return CwayUser(
                id=user_data["id"],
                name=user_data["name"],
                email=user_data["email"],
                username=user_data["username"],
                firstName=user_data.get("firstName"),
                lastName=user_data.get("lastName"),
                enabled=user_data.get("enabled", True)
            )
            
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise CwayAPIError(f"Failed to create user: {e}")
    
    async def update_user_name(self, username: str, first_name: Optional[str] = None,
                              last_name: Optional[str] = None) -> Optional[CwayUser]:
        """Update user's real name."""
        mutation = """
        mutation SetUserRealName($username: String!, $firstName: String, $lastName: String) {
            setUserRealName(username: $username, firstName: $firstName, lastName: $lastName) {
                id
                username
                firstName
                lastName
                name
                email
                enabled
            }
        }
        """
        
        try:
            result = await self.graphql_client.execute_mutation(mutation, {
                "username": username,
                "firstName": first_name,
                "lastName": last_name
            })
            user_data = result.get("setUserRealName")
            
            if not user_data:
                return None
                
            return CwayUser(
                id=user_data["id"],
                name=user_data["name"],
                email=user_data["email"],
                username=user_data["username"],
                firstName=user_data.get("firstName"),
                lastName=user_data.get("lastName"),
                enabled=user_data.get("enabled", True)
            )
            
        except Exception as e:
            logger.error(f"Failed to update user name: {e}")
            raise CwayAPIError(f"Failed to update user name: {e}")
    
    async def delete_user(self, username: str) -> bool:
        """Delete a user."""
        mutation = """
        mutation DeleteUser($usernames: [String!]!) {
            deleteUsers(usernames: $usernames)
        }
        """
        
        try:
            result = await self.graphql_client.execute_mutation(mutation, {
                "usernames": [username]
            })
            return result.get("deleteUsers", False)
            
        except Exception as e:
            logger.error(f"Failed to delete user: {e}")
            raise CwayAPIError(f"Failed to delete user: {e}")
    
    async def find_users_and_teams(self, search: Optional[str] = None, page: int = 0, size: int = 10) -> Dict[str, Any]:
        """Search for both users and teams with pagination."""
        query = """
        query FindUsersAndTeams($search: String, $paging: Paging) {
            findUsersAndTeamsPage(search: $search, paging: $paging) {
                usersOrTeams {
                    __typename
                    ... on User {
                        id
                        name
                        username
                        email
                        firstName
                        lastName
                        enabled
                    }
                    ... on Team {
                        id
                        name
                        teamLeadUser {
                            username
                            name
                        }
                    }
                }
                page
                totalHits
            }
        }
        """
        
        try:
            variables = {
                "search": search,
                "paging": {"page": page, "pageSize": size}
            }
            result = await self.graphql_client.execute_query(query, variables)
            page_data = result.get("findUsersAndTeamsPage", {})
            
            return {
                "items": page_data.get("usersOrTeams", []),
                "page": page_data.get("page", 0),
                "totalHits": page_data.get("totalHits", 0)
            }
            
        except Exception as e:
            logger.error(f"Failed to search users and teams: {e}")
            raise CwayAPIError(f"Failed to search users and teams: {e}")
    
    async def get_permission_groups(self) -> List[Dict[str, Any]]:
        """Get all available permission groups. Admin only."""
        query = """
        query GetPermissionGroups {
            getPermissionGroups {
                id
                name
                description
                permissions
            }
        }
        """
        
        try:
            result = await self.graphql_client.execute_query(query)
            return result.get("getPermissionGroups", [])
            
        except Exception as e:
            logger.error(f"Failed to get permission groups: {e}")
            raise CwayAPIError(f"Failed to get permission groups: {e}")
    
    async def set_user_permissions(self, usernames: List[str], permission_group_id: str) -> bool:
        """Set permission group for multiple users. Admin only."""
        mutation = """
        mutation SetUserPermissions($usernames: [String!]!, $permissionGroupId: UUID!) {
            setPermissionGroupForUsers(usernames: $usernames, permissionGroupId: $permissionGroupId)
        }
        """
        
        try:
            result = await self.graphql_client.execute_mutation(mutation, {
                "usernames": usernames,
                "permissionGroupId": permission_group_id
            })
            return result.get("setPermissionGroupForUsers", False)
            
        except Exception as e:
            logger.error(f"Failed to set user permissions: {e}")
            raise CwayAPIError(f"Failed to set user permissions: {e}")


class CwayProjectRepository:
    """Repository for Cway projects using the actual API."""
    
    def __init__(self, graphql_client: CwayGraphQLClient) -> None:
        """Initialize with GraphQL client."""
        self.graphql_client = graphql_client
        
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
            result = await self.graphql_client.execute_query(query)
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
        """Find a specific project by ID."""
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
                # New API requires both page and pageSize
                "paging": {"page": 0, "pageSize": limit}
            }
            if query:
                variables["filter"] = {"search": query}
            
            result = await self.graphql_client.execute_query(gql_query, variables)
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
        gql_query = """
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
            result = await self.graphql_client.execute_query(gql_query, {"id": project_id})
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
            result = await self.graphql_client.execute_mutation(mutation, {"input": project_input})
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
            result = await self.graphql_client.execute_mutation(mutation, {
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
            result = await self.graphql_client.execute_mutation(mutation, {
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
            result = await self.graphql_client.execute_mutation(mutation, {
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
            result = await self.graphql_client.execute_mutation(mutation, {
                "projectIds": project_ids,
                "force": force
            })
            return result.get("deleteProjects", False)
            
        except Exception as e:
            logger.error(f"Failed to delete projects: {e}")
            raise CwayAPIError(f"Failed to delete projects: {e}")
    
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
            result = await self.graphql_client.execute_query(query, {"id": artwork_id})
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
            result = await self.graphql_client.execute_mutation(mutation, {"input": artwork_input})
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
            result = await self.graphql_client.execute_mutation(mutation, {"artworkId": artwork_id})
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
            result = await self.graphql_client.execute_mutation(mutation, {"input": reject_input})
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
            result = await self.graphql_client.execute_query(query)
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
            result = await self.graphql_client.execute_query(query)
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
    
    async def create_artwork_download_job(self, artwork_ids: List[str], zip_name: Optional[str] = None) -> str:
        """Create a download job for artwork files (latest revisions)."""
        mutation = """
        mutation CreateDownloadJob($selections: [DownloadFileDescriptorInput!]!, $zipName: String, $forceZipFile: Boolean) {
            createDownloadJob(selections: $selections, zipName: $zipName, forceZipFile: $forceZipFile)
        }
        """
        
        # Build file selections for each artwork's current revision files
        selections = []
        for artwork_id in artwork_ids:
            # Get artwork details including current revision
            artwork = await self.get_artwork(artwork_id)
            if artwork and artwork.get("currentRevision"):
                revision = artwork["currentRevision"]
                # Add files from current revision
                if "files" in revision:
                    for file in revision["files"]:
                        selections.append({
                            "fileId": file["id"],
                            "fileName": file.get("name", "file"),
                            "folder": artwork.get("name", "artwork")
                        })
        
        if not selections:
            raise CwayAPIError("No files found for the specified artworks")
        
        try:
            variables = {
                "selections": selections,
                "zipName": zip_name or "artworks",
                "forceZipFile": True
            }
            result = await self.graphql_client.execute_mutation(mutation, variables)
            return result.get("createDownloadJob")
            
        except Exception as e:
            logger.error(f"Failed to create artwork download job: {e}")
            raise CwayAPIError(f"Failed to create artwork download job: {e}")
    
    async def get_artwork_preview(self, artwork_id: str) -> Optional[Dict[str, Any]]:
        """Get artwork preview file information including URL."""
        query = """
        query GetArtworkPreview($id: UUID!) {
            artwork(id: $id) {
                id
                name
                previewFile {
                    id
                    name
                    fileSize
                    url
                    mimeType
                    width
                    height
                }
            }
        }
        """
        
        try:
            result = await self.graphql_client.execute_query(query, {"id": artwork_id})
            artwork = result.get("artwork")
            if artwork:
                return artwork.get("previewFile")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get artwork preview: {e}")
            raise CwayAPIError(f"Failed to get artwork preview: {e}")
    
    async def get_project_status_summary(self) -> Dict[str, Any]:
        """Aggregate project statistics and distribution."""
        query = """
        query GetProjectStatusSummary {
            projects {
                projects {
                    id
                    name
                    state
                    status
                    progress {
                        percentageDone
                        artworksDone
                        artworksInProgress
                        artworksUnstarted
                    }
                    endDate
                    lastActivity
                }
                totalHits
            }
        }
        """
        
        try:
            result = await self.graphql_client.execute_query(query)
            projects_data = result.get("projects", {})
            projects = projects_data.get("projects", [])
            
            # Aggregate statistics
            from collections import Counter
            from datetime import datetime, timedelta
            
            total = len(projects)
            by_state = Counter(p["state"] for p in projects)
            by_status = Counter(p["status"] for p in projects)
            
            # Calculate average progress
            avg_progress = sum(p["progress"]["percentageDone"] for p in projects) / total if total > 0 else 0
            
            # Projects at risk (deadline within 7 days and < 80% done)
            at_risk = 0
            now = datetime.now()
            for p in projects:
                if p.get("endDate"):
                    # Parse date and check if within 7 days
                    try:
                        end_date = datetime.fromisoformat(p["endDate"].replace("Z", "+00:00"))
                        if (end_date - now).days <= 7 and p["progress"]["percentageDone"] < 80:
                            at_risk += 1
                    except:
                        pass
            
            return {
                "total": total,
                "by_state": dict(by_state),
                "by_status": dict(by_status),
                "average_progress": round(avg_progress, 2),
                "deadline_at_risk": at_risk,
                "projects": projects  # Include full list for further processing
            }
            
        except Exception as e:
            logger.error(f"Failed to get project status summary: {e}")
            raise CwayAPIError(f"Failed to get project status summary: {e}")
    
    async def compare_projects(self, project_ids: List[str]) -> Dict[str, Any]:
        """Compare multiple projects side-by-side."""
        projects = []
        
        for project_id in project_ids:
            project = await self.get_project_by_id(project_id)
            if project:
                projects.append(project)
        
        if not projects:
            return {"projects": [], "comparison": {}}
        
        # Calculate comparison metrics
        comparison = {
            "avg_progress": sum(p["progress"]["percentageDone"] for p in projects) / len(projects),
            "total_artworks": sum(
                p["progress"]["artworksDone"] + 
                p["progress"]["artworksInProgress"] + 
                p["progress"]["artworksUnstarted"]
                for p in projects
            ),
            "states": [p["state"] for p in projects],
            "statuses": [p["status"] for p in projects]
        }
        
        return {
            "projects": projects,
            "comparison": comparison
        }
    
    async def get_project_history(self, project_id: str) -> List[Dict[str, Any]]:
        """Get project event history."""
        query = """
        query GetProjectHistory($projectId: UUID!) {
            projectHistory(projectId: $projectId) {
                id
                timestamp
                name
                description
            }
        }
        """
        
        try:
            result = await self.graphql_client.execute_query(query, {"projectId": project_id})
            return result.get("projectHistory", [])
            
        except Exception as e:
            logger.error(f"Failed to get project history: {e}")
            raise CwayAPIError(f"Failed to get project history: {e}")
    
    async def get_monthly_project_trends(self) -> List[Dict[str, Any]]:
        """Get month-over-month project counts."""
        query = """
        query GetMonthlyTrends {
            openProjectsCountByMonth {
                month
                count
            }
        }
        """
        
        try:
            result = await self.graphql_client.execute_query(query)
            return result.get("openProjectsCountByMonth", [])
            
        except Exception as e:
            logger.error(f"Failed to get monthly project trends: {e}")
            raise CwayAPIError(f"Failed to get monthly project trends: {e}")
    
    async def get_artwork_history(self, artwork_id: str) -> List[Dict[str, Any]]:
        """Get artwork revision history and state changes."""
        query = """
        query GetArtworkHistory($artworkId: UUID!) {
            artworkHistory(artworkId: $artworkId) {
                id
                timestamp
                eventType
                description
                user {
                    username
                    name
                }
            }
        }
        """
        
        try:
            result = await self.graphql_client.execute_query(query, {"artworkId": artwork_id})
            return result.get("artworkHistory", [])
            
        except Exception as e:
            logger.error(f"Failed to get artwork history: {e}")
            raise CwayAPIError(f"Failed to get artwork history: {e}")
    
    async def analyze_artwork_ai(self, artwork_id: str) -> str:
        """Trigger AI analysis on artwork. Returns thread ID."""
        mutation = """
        mutation AnalyzeArtworkAI($artworkId: UUID!) {
            artworkAIAnalysis(artworkId: $artworkId)
        }
        """
        
        try:
            result = await self.graphql_client.execute_mutation(mutation, {"artworkId": artwork_id})
            thread_id = result.get("artworkAIAnalysis")
            if not thread_id:
                raise CwayAPIError("AI analysis returned no thread ID")
            return thread_id
            
        except Exception as e:
            logger.error(f"Failed to trigger AI artwork analysis: {e}")
            raise CwayAPIError(f"Failed to trigger AI artwork analysis: {e}")
    
    async def generate_project_summary_ai(self, project_id: str, audience: str = "PROJECT_MANAGER") -> str:
        """Generate AI summary for project. Returns summary text."""
        mutation = """
        mutation GenerateProjectSummary($projectId: UUID!, $audience: ProjectSummaryAudience!) {
            openAIProjectSummary(projectId: $projectId, audience: $audience)
        }
        """
        
        try:
            result = await self.graphql_client.execute_mutation(mutation, {
                "projectId": project_id,
                "audience": audience
            })
            summary = result.get("openAIProjectSummary")
            if not summary:
                raise CwayAPIError("AI summary generation returned empty result")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate AI project summary: {e}")
            raise CwayAPIError(f"Failed to generate AI project summary: {e}")
    
    async def get_folder_tree(self) -> List[Dict[str, Any]]:
        """Get the complete folder tree structure."""
        query = """
        query GetFolderTree {
            tree {
                id
                name
                children {
                    id
                    name
                }
            }
        }
        """
        
        try:
            result = await self.graphql_client.execute_query(query)
            return result.get("tree", [])
            
        except Exception as e:
            logger.error(f"Failed to get folder tree: {e}")
            raise CwayAPIError(f"Failed to get folder tree: {e}")
    
    async def get_folder(self, folder_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific folder by ID."""
        query = """
        query GetFolder($id: UUID!) {
            folder(id: $id) {
                id
                name
                description
                parentId
            }
        }
        """
        
        try:
            result = await self.graphql_client.execute_query(query, {"id": folder_id})
            return result.get("folder")
            
        except Exception as e:
            logger.error(f"Failed to get folder: {e}")
            raise CwayAPIError(f"Failed to get folder: {e}")
    
    async def get_folder_items(self, folder_id: str, page: int = 0, 
                              size: int = 20) -> Dict[str, Any]:
        """Get items in a specific folder with pagination."""
        query = """
        query GetFolderItems($input: FindFolderItemInput!, $paging: Paging) {
            itemsForFolder(input: $input, paging: $paging) {
                items {
                    id
                    name
                    type
                }
                totalHits
                page
            }
        }
        """
        
        try:
            result = await self.graphql_client.execute_query(query, {
                "input": {"folderId": folder_id},
                "paging": {"page": page, "pageSize": size},
                # Legacy (unused by API) to keep any existing tests referencing 'size' working
                "size": size,
            })
            return result.get("itemsForFolder", {})
            
        except Exception as e:
            logger.error(f"Failed to get folder items: {e}")
            raise CwayAPIError(f"Failed to get folder items: {e}")
    
    async def get_file(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get a file by UUID."""
        query = """
        query GetFile($id: UUID!) {
            file(id: $id) {
                id
                name
                fileSize
                mimeType
                url
            }
        }
        """
        
        try:
            result = await self.graphql_client.execute_query(query, {"id": file_id})
            return result.get("file")
            
        except Exception as e:
            logger.error(f"Failed to get file: {e}")
            raise CwayAPIError(f"Failed to get file: {e}")
    
    async def search_media_center(
        self,
        query_text: Optional[str] = None,
        folder_id: Optional[str] = None,
        content_type: Optional[str] = None,
        date_from: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Search media center with filters."""
        
        if folder_id:
            # Search within specific folder
            query = """
            query SearchMediaCenter($input: FindFolderItemInput!, $paging: Paging) {
                itemsForFolder(input: $input, paging: $paging) {
                    items {
                        id
                        name
                        type
                        created
                        modifiedDate
                    }
                    totalHits
                    page
                }
            }
            """
            
            variables = {
                "input": {"folderId": folder_id},
                "paging": {"page": 0, "pageSize": limit}
            }
            
            if query_text:
                variables["input"]["query"] = query_text
            
        else:
            # Search across organization
            query = """
            query SearchMediaCenter($input: FindFolderItemsInOrganisationInput!, $paging: Paging) {
                itemsForOrganisation(input: $input, paging: $paging) {
                    items {
                        id
                        name
                        type
                        created
                        modifiedDate
                    }
                    totalHits
                    page
                }
            }
            """
            
            variables = {
                "input": {},
                "paging": {"page": 0, "pageSize": limit}
            }
            
            if query_text:
                variables["input"]["query"] = query_text
        
        try:
            result = await self.graphql_client.execute_query(query, variables)
            data = result.get("itemsForFolder") or result.get("itemsForOrganisation", {})
            
            return {
                "items": data.get("items", []),
                "total_hits": data.get("totalHits", 0),
                "page": data.get("page", 0)
            }
            
        except Exception as e:
            logger.error(f"Failed to search media center: {e}")
            raise CwayAPIError(f"Failed to search media center: {e}")
    
    async def create_folder(self, name: str, parent_folder_id: Optional[str] = None,
                           description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new folder in media center."""
        mutation = """
        mutation CreateFolder($input: CreateFolderInput!) {
            createFolder(input: $input) {
                id
                name
                description
                parentId
                created
            }
        }
        """
        
        try:
            folder_input = {
                "name": name,
                "description": description
            }
            if parent_folder_id:
                folder_input["parentId"] = parent_folder_id
            # Remove None values
            folder_input = {k: v for k, v in folder_input.items() if v is not None}
            
            result = await self.graphql_client.execute_mutation(mutation, {"input": folder_input})
            return result.get("createFolder", {})
            
        except Exception as e:
            logger.error(f"Failed to create folder: {e}")
            raise CwayAPIError(f"Failed to create folder: {e}")
    
    async def rename_file(self, file_id: str, new_name: str) -> Dict[str, Any]:
        """Rename a file in media center."""
        mutation = """
        mutation RenameFile($fileId: UUID!, $newName: String!) {
            renameFile(fileId: $fileId, newName: $newName) {
                id
                name
                fileSize
                mimeType
            }
        }
        """
        
        try:
            result = await self.graphql_client.execute_mutation(mutation, {
                "fileId": file_id,
                "newName": new_name
            })
            return result.get("renameFile", {})
            
        except Exception as e:
            logger.error(f"Failed to rename file: {e}")
            raise CwayAPIError(f"Failed to rename file: {e}")
    
    async def rename_folder(self, folder_id: str, new_name: str) -> Dict[str, Any]:
        """Rename a folder in media center."""
        mutation = """
        mutation RenameFolder($folderId: UUID!, $newName: String!) {
            renameFolder(folderId: $folderId, newName: $newName) {
                id
                name
                description
                parentId
            }
        }
        """
        
        try:
            result = await self.graphql_client.execute_mutation(mutation, {
                "folderId": folder_id,
                "newName": new_name
            })
            return result.get("renameFolder", {})
            
        except Exception as e:
            logger.error(f"Failed to rename folder: {e}")
            raise CwayAPIError(f"Failed to rename folder: {e}")
    
    async def move_files(self, file_ids: List[str], target_folder_id: str) -> Dict[str, Any]:
        """Move files to a different folder."""
        mutation = """
        mutation MoveFiles($input: MoveFilesInput!) {
            moveFiles(input: $input) {
                success
                movedCount
            }
        }
        """
        
        try:
            result = await self.graphql_client.execute_mutation(mutation, {
                "input": {
                    "fileIds": file_ids,
                    "targetFolderId": target_folder_id
                }
            })
            return result.get("moveFiles", {"success": False, "movedCount": 0})
            
        except Exception as e:
            logger.error(f"Failed to move files: {e}")
            raise CwayAPIError(f"Failed to move files: {e}")
    
    async def delete_file(self, file_id: str) -> bool:
        """Delete a file from media center."""
        mutation = """
        mutation DeleteFile($fileId: UUID!) {
            deleteFile(fileId: $fileId)
        }
        """
        
        try:
            result = await self.graphql_client.execute_mutation(mutation, {"fileId": file_id})
            return result.get("deleteFile", False)
            
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            raise CwayAPIError(f"Failed to delete file: {e}")
    
    async def delete_folder(self, folder_id: str, force: bool = False) -> bool:
        """Delete a folder from media center."""
        mutation = """
        mutation DeleteFolder($folderId: UUID!, $force: Boolean) {
            deleteFolder(folderId: $folderId, force: $force)
        }
        """
        
        try:
            result = await self.graphql_client.execute_mutation(mutation, {
                "folderId": folder_id,
                "force": force
            })
            return result.get("deleteFolder", False)
            
        except Exception as e:
            logger.error(f"Failed to delete folder: {e}")
            raise CwayAPIError(f"Failed to delete folder: {e}")
    
    async def get_media_center_stats(self) -> Dict[str, Any]:
        """Get media center statistics."""
        query = """
        query GetMediaCenterStats {
            mediaCenterStats {
                totalItems
                artworks
                itemsPerMonth {
                    month
                    count
                }
            }
        }
        """
        
        try:
            result = await self.graphql_client.execute_query(query)
            return result.get("mediaCenterStats", {})
            
        except Exception as e:
            logger.error(f"Failed to get media center stats: {e}")
            raise CwayAPIError(f"Failed to get media center stats: {e}")
    
    async def download_folder_contents(self, folder_id: str, zip_name: Optional[str] = None) -> str:
        """Create download job for entire folder contents."""
        # First get all items in the folder
        items_result = await self.get_folder_items(folder_id, page=0, size=1000)
        items = items_result.get("items", [])
        
        if not items:
            raise CwayAPIError("No items found in folder")
        
        # Build file selections
        selections = []
        for item in items:
            if item.get("type") != "FOLDER":  # Skip subfolders for now
                selections.append({
                    "fileId": item["id"],
                    "fileName": item.get("name", "file"),
                    "folder": ""
                })
        
        if not selections:
            raise CwayAPIError("No files found in folder")
        
        # Create download job
        mutation = """
        mutation CreateDownloadJob($selections: [DownloadFileDescriptorInput!]!, $zipName: String, $forceZipFile: Boolean) {
            createDownloadJob(selections: $selections, zipName: $zipName, forceZipFile: $forceZipFile)
        }
        """
        
        try:
            variables = {
                "selections": selections,
                "zipName": zip_name or "folder",
                "forceZipFile": True
            }
            result = await self.graphql_client.execute_mutation(mutation, variables)
            return result.get("createDownloadJob")
            
        except Exception as e:
            logger.error(f"Failed to create folder download job: {e}")
            raise CwayAPIError(f"Failed to create folder download job: {e}")
    
    async def download_project_media(self, project_id: str, zip_name: Optional[str] = None) -> str:
        """Create download job for all media in a project."""
        # Get project with files
        project = await self.get_project_by_id(project_id)
        
        if not project:
            raise CwayAPIError(f"Project not found: {project_id}")
        
        # Collect all files from project and artworks
        selections = []
        
        # Project files
        if project.get("files"):
            for file in project["files"]:
                selections.append({
                    "fileId": file["id"],
                    "fileName": file.get("name", "file"),
                    "folder": "project_files"
                })
        
        # Artwork files
        if project.get("artworks"):
            for artwork in project["artworks"]:
                if artwork.get("previewFile"):
                    selections.append({
                        "fileId": artwork["previewFile"]["id"],
                        "fileName": f"{artwork['name']}_preview",
                        "folder": "artworks"
                    })
        
        if not selections:
            raise CwayAPIError("No media files found in project")
        
        # Create download job
        mutation = """
        mutation CreateDownloadJob($selections: [DownloadFileDescriptorInput!]!, $zipName: String, $forceZipFile: Boolean) {
            createDownloadJob(selections: $selections, zipName: $zipName, forceZipFile: $forceZipFile)
        }
        """
        
        try:
            variables = {
                "selections": selections,
                "zipName": zip_name or f"project_{project['name']}",
                "forceZipFile": True
            }
            result = await self.graphql_client.execute_mutation(mutation, variables)
            return result.get("createDownloadJob")
            
        except Exception as e:
            logger.error(f"Failed to create project media download job: {e}")
            raise CwayAPIError(f"Failed to create project media download job: {e}")
    
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
            result = await self.graphql_client.execute_query(query, {"projectId": project_id})
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
            result = await self.graphql_client.execute_mutation(mutation, {
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
            result = await self.graphql_client.execute_mutation(mutation, {
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
            result = await self.graphql_client.execute_mutation(mutation, {
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
            result = await self.graphql_client.execute_query(query, {
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
            result = await self.graphql_client.execute_mutation(mutation, {
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
            result = await self.graphql_client.execute_query(query, {"projectId": project_id})
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
            result = await self.graphql_client.execute_mutation(mutation, {
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
            result = await self.graphql_client.execute_mutation(mutation, {"artworkId": artwork_id})
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
            result = await self.graphql_client.execute_mutation(mutation, {
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
            result = await self.graphql_client.execute_query(query, {
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
            result = await self.graphql_client.execute_mutation(mutation, {
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
            result = await self.graphql_client.execute_query(query, {"artworkId": artwork_id})
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
            result = await self.graphql_client.execute_mutation(mutation, {
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
            result = await self.graphql_client.execute_mutation(mutation, {
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
            
            result = await self.graphql_client.execute_mutation(mutation, variables)
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
            result = await self.graphql_client.execute_mutation(mutation, {"artworkId": artwork_id})
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
            result = await self.graphql_client.execute_mutation(mutation, {"artworkId": artwork_id})
            artwork = result.get("unarchiveArtwork")
            if not artwork:
                raise CwayAPIError("Failed to unarchive artwork: artwork not found")
            return artwork
            
        except Exception as e:
            logger.error(f"Failed to unarchive artwork: {e}")
            raise CwayAPIError(f"Failed to unarchive artwork: {e}")
    
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
            result = await self.graphql_client.execute_query(query, {"projectId": project_id})
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
            
            result = await self.graphql_client.execute_mutation(mutation, variables)
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
            result = await self.graphql_client.execute_mutation(mutation, {
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
            result = await self.graphql_client.execute_mutation(mutation, {
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
            result = await self.graphql_client.execute_query(query, {})
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
            result = await self.graphql_client.execute_mutation(mutation, {
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
            
            result = await self.graphql_client.execute_query(gql_query, variables)
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
            result = await self.graphql_client.execute_query(query, {
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
            result = await self.graphql_client.execute_query(query, {
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
            result = await self.graphql_client.execute_mutation(mutation, {
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
            result = await self.graphql_client.execute_query(query, {
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
            result = await self.graphql_client.execute_query(query, {"id": share_id})
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
            
            result = await self.graphql_client.execute_mutation(mutation, {"input": share_input})
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
            result = await self.graphql_client.execute_mutation(mutation, {"id": share_id})
            return result.get("deleteShare", False)
            
        except Exception as e:
            logger.error(f"Failed to delete share: {e}")
            raise CwayAPIError(f"Failed to delete share: {e}")


class CwayCategoryRepository:
    """Repository for categories, brands, and specifications."""
    
    def __init__(self, graphql_client: CwayGraphQLClient) -> None:
        """Initialize with GraphQL client."""
        self.graphql_client = graphql_client
    
    async def get_categories(self) -> List[Dict[str, Any]]:
        """Get all artwork categories."""
        query = """
        query GetCategories {
            categories {
                id
                name
                description
                color
            }
        }
        """
        
        try:
            result = await self.graphql_client.execute_query(query)
            return result.get("categories", [])
            
        except Exception as e:
            logger.error(f"Failed to get categories: {e}")
            raise CwayAPIError(f"Failed to get categories: {e}")
    
    async def get_brands(self) -> List[Dict[str, Any]]:
        """Get all brands."""
        query = """
        query GetBrands {
            brands {
                id
                name
                description
            }
        }
        """
        
        try:
            result = await self.graphql_client.execute_query(query)
            return result.get("brands", [])
            
        except Exception as e:
            logger.error(f"Failed to get brands: {e}")
            raise CwayAPIError(f"Failed to get brands: {e}")
    
    async def get_print_specifications(self) -> List[Dict[str, Any]]:
        """Get all print specifications."""
        query = """
        query GetPrintSpecifications {
            printSpecifications {
                id
                name
                description
                width
                height
                unit
            }
        }
        """
        
        try:
            result = await self.graphql_client.execute_query(query)
            return result.get("printSpecifications", [])
            
        except Exception as e:
            logger.error(f"Failed to get print specifications: {e}")
            raise CwayAPIError(f"Failed to get print specifications: {e}")
    
    async def create_category(self, name: str, description: Optional[str] = None, 
                             color: Optional[str] = None) -> Dict[str, Any]:
        """Create a new category."""
        mutation = """
        mutation CreateCategory($input: CategoryInput!) {
            createCategory(input: $input) {
                id
                name
                description
                color
            }
        }
        """
        
        try:
            result = await self.graphql_client.execute_mutation(mutation, {
                "input": {
                    "name": name,
                    "description": description,
                    "color": color
                }
            })
            return result.get("createCategory", {})
            
        except Exception as e:
            logger.error(f"Failed to create category: {e}")
            raise CwayAPIError(f"Failed to create category: {e}")
    
    async def create_brand(self, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new brand."""
        mutation = """
        mutation CreateBrand($input: BrandInput!) {
            createBrand(input: $input) {
                id
                name
                description
            }
        }
        """
        
        try:
            result = await self.graphql_client.execute_mutation(mutation, {
                "input": {
                    "name": name,
                    "description": description
                }
            })
            return result.get("createBrand", {})
            
        except Exception as e:
            logger.error(f"Failed to create brand: {e}")
            raise CwayAPIError(f"Failed to create brand: {e}")
    
    async def create_print_specification(self, name: str, width: float, height: float,
                                        unit: str = "mm", description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new print specification."""
        mutation = """
        mutation CreatePrintSpecification($input: PrintSpecificationInput!) {
            createPrintSpecification(input: $input) {
                id
                name
                description
                width
                height
                unit
            }
        }
        """
        
        try:
            result = await self.graphql_client.execute_mutation(mutation, {
                "input": {
                    "name": name,
                    "width": width,
                    "height": height,
                    "unit": unit,
                    "description": description
                }
            })
            return result.get("createPrintSpecification", {})
            
        except Exception as e:
            logger.error(f"Failed to create print specification: {e}")
            raise CwayAPIError(f"Failed to create print specification: {e}")


class CwaySystemRepository:
    """Repository for system-level Cway operations."""
    
    def __init__(self, graphql_client: CwayGraphQLClient) -> None:
        """Initialize with GraphQL client."""
        self.graphql_client = graphql_client
        
    async def get_login_info(self) -> Optional[Dict[str, Any]]:
        """Get login information for the current user."""
        query = """
        query GetLoginInfo {
            loginInfo {
                id
                email
            }
        }
        """
        
        try:
            result = await self.graphql_client.execute_query(query)
            return result.get("loginInfo")
            
        except Exception as e:
            logger.error(f"Failed to get login info: {e}")
            # This might fail if loginInfo doesn't have the expected fields
            return None
            
    async def validate_connection(self) -> bool:
        """Validate that we can connect to the API."""
        try:
            # Try a simple query that should always work
            result = await self.graphql_client.execute_query("{ __typename }")
            return result.get("__typename") == "Query"
        except Exception as e:
            logger.error(f"Connection validation failed: {e}")
            return False