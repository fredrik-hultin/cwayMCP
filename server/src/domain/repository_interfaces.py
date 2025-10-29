"""Repository interfaces for domain layer."""

from abc import ABC, abstractmethod
from typing import List, Optional
from .entities import Project, User


class ProjectRepository(ABC):
    """Abstract repository interface for projects."""
    
    @abstractmethod
    async def get_all_projects(self) -> List[Project]:
        """Get all projects."""
        pass
    
    @abstractmethod
    async def get_project_by_id(self, project_id: str) -> Optional[Project]:
        """Get a project by its ID."""
        pass
    
    @abstractmethod
    async def get_active_projects(self) -> List[Project]:
        """Get all active projects."""
        pass
    
    @abstractmethod
    async def get_completed_projects(self) -> List[Project]:
        """Get all completed projects."""
        pass


class UserRepository(ABC):
    """Abstract repository interface for users."""
    
    @abstractmethod
    async def get_all_users(self) -> List[User]:
        """Get all users."""
        pass
    
    @abstractmethod
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get a user by their ID."""
        pass
    
    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by their email address."""
        pass