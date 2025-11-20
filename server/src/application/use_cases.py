"""Application layer use cases for Cway operations."""

from typing import List, Optional, Union
import logging
from datetime import datetime
import uuid

from ..domain.entities import Project, User, ProjectState
from ..domain.repositories import ProjectRepository, UserRepository


logger = logging.getLogger(__name__)


class ProjectUseCases:
    """Use cases for Project operations."""
    
    def __init__(self, project_repository: ProjectRepository) -> None:
        """Initialize with project repository."""
        self.project_repository = project_repository
        
    async def list_projects(self) -> List[Project]:
        """List all projects."""
        logger.info("Fetching all projects")
        projects = await self.project_repository.get_all()
        logger.info(f"Found {len(projects)} projects")
        return projects
        
    async def get_project(self, project_id: str) -> Optional[Project]:
        """Get a specific project by ID."""
        logger.info(f"Fetching project with ID: {project_id}")
        project = await self.project_repository.get_by_id(project_id)
        if project:
            logger.info(f"Found project: {project.name}")
        else:
            logger.warning(f"Project not found: {project_id}")
        return project
        
    async def create_project(self, name: str, description: Optional[str] = None, 
                           status: Union[str, ProjectState] = ProjectState.ACTIVE) -> Project:
        """Create a new project."""
        logger.info(f"Creating new project: {name}")
        
        # This would typically generate an ID from the API
        # For now, we'll create a placeholder project with UUID
        project = Project(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            status=status,  # Will be converted to enum in __post_init__
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        created_project = await self.project_repository.create(project)
        logger.info(f"Created project: {created_project.id}")
        return created_project
        
    async def update_project(self, project_id: str, name: Optional[str] = None, 
                           description: Optional[str] = None, 
                           status: Optional[Union[str, ProjectState]] = None) -> Optional[Project]:
        """Update an existing project."""
        logger.info(f"Updating project: {project_id}")
        
        # Get existing project
        existing_project = await self.project_repository.get_by_id(project_id)
        if not existing_project:
            logger.warning(f"Project not found for update: {project_id}")
            return None
            
        # Update fields
        updated_project = Project(
            id=existing_project.id,
            name=name or existing_project.name,
            description=description if description is not None else existing_project.description,
            status=status or existing_project.status,  # Will be converted to enum in __post_init__
            created_at=existing_project.created_at,
            updated_at=datetime.now()
        )
        
        result = await self.project_repository.update(updated_project)
        logger.info(f"Updated project: {result.id}")
        return result
        
    async def delete_project(self, project_id: str) -> bool:
        """Delete a project."""
        logger.info(f"Deleting project: {project_id}")
        success = await self.project_repository.delete(project_id)
        if success:
            logger.info(f"Deleted project: {project_id}")
        else:
            logger.warning(f"Failed to delete project: {project_id}")
        return success


class UserUseCases:
    """Use cases for User operations."""
    
    def __init__(self, user_repository: UserRepository) -> None:
        """Initialize with user repository."""
        self.user_repository = user_repository
        
    async def list_users(self) -> List[User]:
        """List all users."""
        logger.info("Fetching all users")
        users = await self.user_repository.get_all()
        logger.info(f"Found {len(users)} users")
        return users
        
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get a specific user by ID."""
        logger.info(f"Fetching user with ID: {user_id}")
        user = await self.user_repository.get_by_id(user_id)
        if user:
            logger.info(f"Found user: {user.email}")
        else:
            logger.warning(f"User not found: {user_id}")
        return user
        
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email address."""
        logger.info(f"Fetching user with email: {email}")
        user = await self.user_repository.get_by_email(email)
        if user:
            logger.info(f"Found user: {user.id}")
        else:
            logger.warning(f"User not found: {email}")
        return user
        
    async def create_user(self, email: str, name: Optional[str] = None, role: str = "user") -> User:
        """Create a new user."""
        logger.info(f"Creating new user: {email}")
        
        # Check if user already exists
        existing_user = await self.user_repository.get_by_email(email)
        if existing_user:
            logger.warning(f"User already exists: {email}")
            raise ValueError(f"User with email {email} already exists")
            
        # Create new user
        user = User(
            id=f"user_{email.split('@')[0]}",
            email=email,
            name=name,
            role=role,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        created_user = await self.user_repository.create(user)
        logger.info(f"Created user: {created_user.id}")
        return created_user