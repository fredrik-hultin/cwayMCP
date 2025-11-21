"""GraphQL repository implementations for Cway API (updated to new schema)."""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import logging

from ..domain.entities import Project, User, ProjectState
from ..domain.repositories import ProjectRepository, UserRepository
from .graphql_client import CwayGraphQLClient, CwayAPIError


logger = logging.getLogger(__name__)


def _parse_datetime_maybe(value: Optional[Union[str, int, float]]) -> datetime:
    """Parse various datetime representations from API to datetime.
    - ISO strings are parsed via fromisoformat (with Z handled)
    - Unix timestamps (seconds or ms) are converted appropriately
    - None falls back to now
    """
    if value is None:
        return datetime.now()
    # Epoch numeric
    if isinstance(value, (int, float)):
        try:
            # Heuristic: treat > 10^12 as ms
            ts = float(value)
            if ts > 1_000_000_000_000:  # ms
                ts /= 1000.0
            return datetime.fromtimestamp(ts)
        except Exception:
            return datetime.now()
    # ISO string
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except Exception:
            logger.warning(f"Failed to parse datetime string: {value}")
            return datetime.now()
    return datetime.now()


class GraphQLProjectRepository(ProjectRepository):
    """GraphQL implementation of ProjectRepository aligned with new API."""
    
    def __init__(self, graphql_client: CwayGraphQLClient) -> None:
        self.graphql_client = graphql_client
        
    async def get_all(self) -> List[Project]:
        """Get first page of projects using new paginated API."""
        query = """
        query GetProjects($paging: Paging) {
            projects(paging: $paging) {
                projects {
                    id
                    name
                    description
                    state
                }
                page
                totalHits
            }
        }
        """
        
        try:
            result = await self.graphql_client.execute_query(query, {"paging": {"page": 0, "pageSize": 100}})
            projects_page = result.get("projects", {})
            items = projects_page.get("projects", []) or projects_page.get("items", [])
            projects: List[Project] = []
            for data in items:
                status_str = (data.get("state") or "ACTIVE")
                project = Project(
                    id=data["id"],
                    name=data["name"],
                    description=data.get("description"),
                    status=status_str,  # Project.__post_init__ will coerce string -> enum
                    created_at=_parse_datetime_maybe(None),
                    updated_at=_parse_datetime_maybe(None),
                )
                projects.append(project)
            return projects
        except Exception as e:
            logger.error(f"Failed to fetch projects: {e}")
            raise CwayAPIError(f"Failed to fetch projects: {e}")
            
    async def get_by_id(self, project_id: str) -> Optional[Project]:
        """Get project by ID using new schema."""
        query = """
        query GetProject($id: UUID!) {
            project(id: $id) {
                id
                name
                description
                state
                lastActivity
            }
        }
        """
        
        try:
            result = await self.graphql_client.execute_query(query, {"id": project_id})
            data = result.get("project")
            if not data:
                return None
            return Project(
                id=data["id"],
                name=data["name"],
                description=data.get("description"),
                status=data.get("state", "ACTIVE"),
                created_at=_parse_datetime_maybe(data.get("lastActivity")),
                updated_at=_parse_datetime_maybe(data.get("lastActivity")),
            )
        except Exception as e:
            logger.error(f"Failed to fetch project {project_id}: {e}")
            raise CwayAPIError(f"Failed to fetch project: {e}")
            
    async def create(self, project: Project) -> Project:
        """Create a new project (fields available in new schema)."""
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
            "name": project.name,
            "description": project.description,
        }
        
        try:
            result = await self.graphql_client.execute_mutation(mutation, {"input": project_input})
            created = result.get("createProject") or {}
            return Project(
                id=created.get("id"),
                name=created.get("name", project.name),
                description=created.get("description"),
                status="ACTIVE",
                created_at=_parse_datetime_maybe(None),
                updated_at=_parse_datetime_maybe(None),
            )
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            raise CwayAPIError(f"Failed to create project: {e}")
            
    async def update(self, project: Project) -> Project:
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
        
        project_input = {
            "name": project.name,
            "description": project.description,
        }
        
        try:
            result = await self.graphql_client.execute_mutation(
                mutation, {"id": project.id, "input": project_input}
            )
            updated = result.get("updateProject") or {}
            return Project(
                id=updated.get("id", project.id),
                name=updated.get("name", project.name),
                description=updated.get("description", project.description),
                status=project.status,
                created_at=project.created_at,
                updated_at=_parse_datetime_maybe(None),
            )
        except Exception as e:
            logger.error(f"Failed to update project: {e}")
            raise CwayAPIError(f"Failed to update project: {e}")
            
    async def delete(self, project_id: str) -> bool:
        """Delete a project. If API lacks this exact mutation in new schema, return False gracefully."""
        mutation = """
        mutation DeleteProject($id: UUID!) {
            deleteProject(id: $id) {
                success
            }
        }
        """
        try:
            result = await self.graphql_client.execute_mutation(mutation, {"id": project_id})
            return result.get("deleteProject", {}).get("success", False)
        except Exception:
            # Some schemas may not support deleteProject; treat as not deleted
            return False


class GraphQLUserRepository(UserRepository):
    """GraphQL implementation of UserRepository aligned with new API."""
    
    def __init__(self, graphql_client: CwayGraphQLClient) -> None:
        self.graphql_client = graphql_client
        
    async def get_all(self) -> List[User]:
        """Get users using findUsersPage paging."""
        query = """
        query GetUsers($paging: Paging) {
            findUsersPage(paging: $paging) {
                users {
                    id
                    email
                    name
                    username
                    createdAt
                }
                page
                totalHits
            }
        }
        """
        
        try:
            result = await self.graphql_client.execute_query(query, {"paging": {"page": 0, "pageSize": 100}})
            page = result.get("findUsersPage", {})
            users_data = page.get("users", [])
            users: List[User] = []
            for data in users_data:
                users.append(
                    User(
                        id=data["id"],
                        email=data.get("email", ""),
                        name=data.get("name") or data.get("username"),
                        role="user",
                        created_at=_parse_datetime_maybe(data.get("createdAt")),
                        updated_at=_parse_datetime_maybe(data.get("createdAt")),
                    )
                )
            return users
        except Exception as e:
            logger.error(f"Failed to fetch users: {e}")
            raise CwayAPIError(f"Failed to fetch users: {e}")
            
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID by scanning page (no direct query by ID in new API)."""
        users = await self.get_all()
        for u in users:
            if u.id == user_id:
                return u
        return None
            
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email using findUsers and filtering client-side."""
        query = """
        query FindUsers($username: String) {
            findUsers(username: $username) {
                id
                email
                name
                username
                createdAt
            }
        }
        """
        try:
            # API supports username search; to search by email, request all and filter locally
            result = await self.graphql_client.execute_query(query, {"username": None})
            for data in result.get("findUsers", []) or []:
                if data.get("email", "").lower() == email.lower():
                    return User(
                        id=data["id"],
                        email=data.get("email", ""),
                        name=data.get("name") or data.get("username"),
                        role="user",
                        created_at=_parse_datetime_maybe(data.get("createdAt")),
                        updated_at=_parse_datetime_maybe(data.get("createdAt")),
                    )
            return None
        except Exception as e:
            logger.error(f"Failed to fetch user by email {email}: {e}")
            raise CwayAPIError(f"Failed to fetch user by email: {e}")
            
    async def create(self, user: User) -> User:
        """Create a new user (fields available may differ)."""
        mutation = """
        mutation CreateUser($input: UserInput!) {
            createUser(input: $input) {
                id
                email
                name
            }
        }
        """
        user_input = {
            "email": user.email,
            "username": user.name or user.email,
        }
        try:
            result = await self.graphql_client.execute_mutation(mutation, {"input": user_input})
            data = result.get("createUser") or {}
            return User(
                id=data.get("id"),
                email=data.get("email", user.email),
                name=data.get("name") or user.name,
                role="user",
                created_at=_parse_datetime_maybe(None),
                updated_at=_parse_datetime_maybe(None),
            )
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise CwayAPIError(f"Failed to create user: {e}")
            
    async def update(self, user: User) -> User:
        """Update an existing user (best-effort with new schema)."""
        mutation = """
        mutation UpdateUser($username: String!, $firstName: String, $lastName: String) {
            setUserRealName(username: $username, firstName: $firstName, lastName: $lastName) {
                id
                email
                name
                username
                createdAt
            }
        }
        """
        try:
            # Using setUserRealName as a representative update operation
            variables = {"username": user.name or user.email, "firstName": None, "lastName": None}
            result = await self.graphql_client.execute_mutation(mutation, variables)
            data = result.get("setUserRealName") or {}
            return User(
                id=data.get("id", user.id),
                email=data.get("email", user.email),
                name=data.get("name") or data.get("username") or user.name,
                role="user",
                created_at=_parse_datetime_maybe(data.get("createdAt")),
                updated_at=_parse_datetime_maybe(None),
            )
        except Exception as e:
            logger.error(f"Failed to update user: {e}")
            raise CwayAPIError(f"Failed to update user: {e}")
            
    async def delete(self, user_id: str) -> bool:
        """Delete user (no direct mutation in new schema here; return False)."""
        return False
