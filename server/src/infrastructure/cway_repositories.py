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
        query FindUsersPage($page: Int!, $size: Int!) {
            findUsersPage(page: $page, size: $size) {
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
            result = await self.graphql_client.execute_query(query, {
                "page": page,
                "size": size
            })
            
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