"""GraphQL repository implementations for Cway API."""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from ..domain.entities import Project, User
from ..domain.repositories import ProjectRepository, UserRepository
from .graphql_client import CwayGraphQLClient, CwayAPIError


logger = logging.getLogger(__name__)


def _parse_datetime(dt_str: str) -> datetime:
    """Parse ISO datetime string to datetime object."""
    try:
        # Handle different datetime formats from GraphQL
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    except ValueError:
        # Fallback to current time if parsing fails
        logger.warning(f"Failed to parse datetime: {dt_str}")
        return datetime.now()


class GraphQLProjectRepository(ProjectRepository):
    """GraphQL implementation of ProjectRepository."""
    
    def __init__(self, graphql_client: CwayGraphQLClient) -> None:
        """Initialize with GraphQL client."""
        self.graphql_client = graphql_client
        
    async def get_all(self) -> List[Project]:
        """Get all projects from Cway API."""
        query = """
        query GetProjects {
            projects {
                id
                name
                description
                status
                createdAt
                updatedAt
            }
        }
        """
        
        try:
            result = await self.graphql_client.execute_query(query)
            projects_data = result.get("projects", [])
            
            projects = []
            for data in projects_data:
                project = Project(
                    id=data["id"],
                    name=data["name"],
                    description=data.get("description"),
                    status=data.get("status", "active"),
                    created_at=_parse_datetime(data["createdAt"]),
                    updated_at=_parse_datetime(data["updatedAt"])
                )
                projects.append(project)
                
            return projects
            
        except Exception as e:
            logger.error(f"Failed to fetch projects: {e}")
            raise CwayAPIError(f"Failed to fetch projects: {e}")
            
    async def get_by_id(self, project_id: str) -> Optional[Project]:
        """Get project by ID from Cway API."""
        query = """
        query GetProject($id: ID!) {
            project(id: $id) {
                id
                name
                description
                status
                createdAt
                updatedAt
            }
        }
        """
        
        try:
            result = await self.graphql_client.execute_query(query, {"id": project_id})
            project_data = result.get("project")
            
            if not project_data:
                return None
                
            return Project(
                id=project_data["id"],
                name=project_data["name"],
                description=project_data.get("description"),
                status=project_data.get("status", "active"),
                created_at=_parse_datetime(project_data["createdAt"]),
                updated_at=_parse_datetime(project_data["updatedAt"])
            )
            
        except Exception as e:
            logger.error(f"Failed to fetch project {project_id}: {e}")
            raise CwayAPIError(f"Failed to fetch project: {e}")
            
    async def create(self, project: Project) -> Project:
        """Create a new project in Cway API."""
        mutation = """
        mutation CreateProject($input: ProjectInput!) {
            createProject(input: $input) {
                id
                name
                description
                status
                createdAt
                updatedAt
            }
        }
        """
        
        project_input = {
            "name": project.name,
            "description": project.description,
            "status": project.status
        }
        
        try:
            result = await self.graphql_client.execute_mutation(mutation, {"input": project_input})
            created_data = result.get("createProject")
            
            return Project(
                id=created_data["id"],
                name=created_data["name"],
                description=created_data.get("description"),
                status=created_data.get("status", "active"),
                created_at=_parse_datetime(created_data["createdAt"]),
                updated_at=_parse_datetime(created_data["updatedAt"])
            )
            
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            raise CwayAPIError(f"Failed to create project: {e}")
            
    async def update(self, project: Project) -> Project:
        """Update an existing project in Cway API."""
        mutation = """
        mutation UpdateProject($id: ID!, $input: ProjectInput!) {
            updateProject(id: $id, input: $input) {
                id
                name
                description
                status
                createdAt
                updatedAt
            }
        }
        """
        
        project_input = {
            "name": project.name,
            "description": project.description,
            "status": project.status
        }
        
        try:
            result = await self.graphql_client.execute_mutation(
                mutation, 
                {"id": project.id, "input": project_input}
            )
            updated_data = result.get("updateProject")
            
            return Project(
                id=updated_data["id"],
                name=updated_data["name"],
                description=updated_data.get("description"),
                status=updated_data.get("status", "active"),
                created_at=_parse_datetime(updated_data["createdAt"]),
                updated_at=_parse_datetime(updated_data["updatedAt"])
            )
            
        except Exception as e:
            logger.error(f"Failed to update project: {e}")
            raise CwayAPIError(f"Failed to update project: {e}")
            
    async def delete(self, project_id: str) -> bool:
        """Delete a project from Cway API."""
        mutation = """
        mutation DeleteProject($id: ID!) {
            deleteProject(id: $id) {
                success
            }
        }
        """
        
        try:
            result = await self.graphql_client.execute_mutation(mutation, {"id": project_id})
            return result.get("deleteProject", {}).get("success", False)
            
        except Exception as e:
            logger.error(f"Failed to delete project: {e}")
            raise CwayAPIError(f"Failed to delete project: {e}")


class GraphQLUserRepository(UserRepository):
    """GraphQL implementation of UserRepository."""
    
    def __init__(self, graphql_client: CwayGraphQLClient) -> None:
        """Initialize with GraphQL client."""
        self.graphql_client = graphql_client
        
    async def get_all(self) -> List[User]:
        """Get all users from Cway API."""
        query = """
        query GetUsers {
            users {
                id
                email
                name
                role
                createdAt
                updatedAt
            }
        }
        """
        
        try:
            result = await self.graphql_client.execute_query(query)
            users_data = result.get("users", [])
            
            users = []
            for data in users_data:
                user = User(
                    id=data["id"],
                    email=data["email"],
                    name=data.get("name"),
                    role=data.get("role", "user"),
                    created_at=_parse_datetime(data["createdAt"]),
                    updated_at=_parse_datetime(data["updatedAt"])
                )
                users.append(user)
                
            return users
            
        except Exception as e:
            logger.error(f"Failed to fetch users: {e}")
            raise CwayAPIError(f"Failed to fetch users: {e}")
            
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID from Cway API."""
        query = """
        query GetUser($id: ID!) {
            user(id: $id) {
                id
                email
                name
                role
                createdAt
                updatedAt
            }
        }
        """
        
        try:
            result = await self.graphql_client.execute_query(query, {"id": user_id})
            user_data = result.get("user")
            
            if not user_data:
                return None
                
            return User(
                id=user_data["id"],
                email=user_data["email"],
                name=user_data.get("name"),
                role=user_data.get("role", "user"),
                created_at=_parse_datetime(user_data["createdAt"]),
                updated_at=_parse_datetime(user_data["updatedAt"])
            )
            
        except Exception as e:
            logger.error(f"Failed to fetch user {user_id}: {e}")
            raise CwayAPIError(f"Failed to fetch user: {e}")
            
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email from Cway API."""
        query = """
        query GetUserByEmail($email: String!) {
            userByEmail(email: $email) {
                id
                email
                name
                role
                createdAt
                updatedAt
            }
        }
        """
        
        try:
            result = await self.graphql_client.execute_query(query, {"email": email})
            user_data = result.get("userByEmail")
            
            if not user_data:
                return None
                
            return User(
                id=user_data["id"],
                email=user_data["email"],
                name=user_data.get("name"),
                role=user_data.get("role", "user"),
                created_at=_parse_datetime(user_data["createdAt"]),
                updated_at=_parse_datetime(user_data["updatedAt"])
            )
            
        except Exception as e:
            logger.error(f"Failed to fetch user by email {email}: {e}")
            raise CwayAPIError(f"Failed to fetch user by email: {e}")
            
    async def create(self, user: User) -> User:
        """Create a new user in Cway API."""
        mutation = """
        mutation CreateUser($input: UserInput!) {
            createUser(input: $input) {
                id
                email
                name
                role
                createdAt
                updatedAt
            }
        }
        """
        
        user_input = {
            "email": user.email,
            "name": user.name,
            "role": user.role
        }
        
        try:
            result = await self.graphql_client.execute_mutation(mutation, {"input": user_input})
            created_data = result.get("createUser")
            
            return User(
                id=created_data["id"],
                email=created_data["email"],
                name=created_data.get("name"),
                role=created_data.get("role", "user"),
                created_at=_parse_datetime(created_data["createdAt"]),
                updated_at=_parse_datetime(created_data["updatedAt"])
            )
            
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise CwayAPIError(f"Failed to create user: {e}")
            
    async def update(self, user: User) -> User:
        """Update an existing user in Cway API."""
        mutation = """
        mutation UpdateUser($id: ID!, $input: UserInput!) {
            updateUser(id: $id, input: $input) {
                id
                email
                name
                role
                createdAt
                updatedAt
            }
        }
        """
        
        user_input = {
            "email": user.email,
            "name": user.name,
            "role": user.role
        }
        
        try:
            result = await self.graphql_client.execute_mutation(
                mutation,
                {"id": user.id, "input": user_input}
            )
            updated_data = result.get("updateUser")
            
            return User(
                id=updated_data["id"],
                email=updated_data["email"],
                name=updated_data.get("name"),
                role=updated_data.get("role", "user"),
                created_at=_parse_datetime(updated_data["createdAt"]),
                updated_at=_parse_datetime(updated_data["updatedAt"])
            )
            
        except Exception as e:
            logger.error(f"Failed to update user: {e}")
            raise CwayAPIError(f"Failed to update user: {e}")
            
    async def delete(self, user_id: str) -> bool:
        """Delete a user from Cway API."""
        mutation = """
        mutation DeleteUser($id: ID!) {
            deleteUser(id: $id) {
                success
            }
        }
        """
        
        try:
            result = await self.graphql_client.execute_mutation(mutation, {"id": user_id})
            return result.get("deleteUser", {}).get("success", False)
            
        except Exception as e:
            logger.error(f"Failed to delete user: {e}")
            raise CwayAPIError(f"Failed to delete user: {e}")