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
        mutation DeleteUsers($usernames: [String!]!) {
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
                items {
                    id
                    name
                    description
                    createdAt
                }
                totalHits
            }
        }
        """
        
        try:
            variables = {
                "paging": {"size": limit}
            }
            if query:
                variables["filter"] = {"search": query}
            
            result = await self.graphql_client.execute_query(gql_query, variables)
            projects_data = result.get("projects", {})
            
            return {
                "projects": projects_data.get("items", []),
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
                createdAt
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
                createdAt
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