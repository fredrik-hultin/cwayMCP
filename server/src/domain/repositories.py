"""Repository interfaces for domain entities."""

from abc import ABC, abstractmethod
from typing import List, Optional

from .entities import Project, User


class ProjectRepository(ABC):
    """Abstract repository for Project entities."""
    
    @abstractmethod
    async def get_all(self) -> List[Project]:
        """Get all projects."""
        pass
        
    @abstractmethod
    async def get_by_id(self, project_id: str) -> Optional[Project]:
        """Get project by ID."""
        pass
        
    @abstractmethod
    async def create(self, project: Project) -> Project:
        """Create a new project."""
        pass
        
    @abstractmethod
    async def update(self, project: Project) -> Project:
        """Update an existing project."""
        pass
        
    @abstractmethod
    async def delete(self, project_id: str) -> bool:
        """Delete a project by ID."""
        pass


class UserRepository(ABC):
    """Abstract repository for User entities."""
    
    @abstractmethod
    async def get_all(self) -> List[User]:
        """Get all users."""
        pass
        
    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        pass
        
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        pass
        
    @abstractmethod
    async def create(self, user: User) -> User:
        """Create a new user."""
        pass
        
    @abstractmethod
    async def update(self, user: User) -> User:
        """Update an existing user."""
        pass
        
    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """Delete a user by ID."""
        pass