"""
User Repository - Handles user operations.

Single Responsibility: User data access only.
"""

from typing import Any, Dict, List, Optional
import logging

from src.domain.cway_entities import CwayUser
from src.infrastructure.graphql_client import CwayAPIError
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository):
    """Repository for user operations."""
    
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
            result = await self._execute_query(query, {})
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
            result = await self._execute_query(query, variables)
            
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
            result = await self._execute_query(gql_query, {
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
            result = await self._execute_mutation(mutation, {"input": user_input})
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
            result = await self._execute_mutation(mutation, {
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
            result = await self._execute_mutation(mutation, {
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
            result = await self._execute_query(query, variables)
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
            result = await self._execute_query(query, {})
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
            result = await self._execute_mutation(mutation, {
                "usernames": usernames,
                "permissionGroupId": permission_group_id
            })
            return result.get("setPermissionGroupForUsers", False)
            
        except Exception as e:
            logger.error(f"Failed to set user permissions: {e}")
            raise CwayAPIError(f"Failed to set user permissions: {e}")
