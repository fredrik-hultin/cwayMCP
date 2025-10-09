"""Domain entities for Cway integration."""

import re
from datetime import datetime
from typing import Optional
from dataclasses import dataclass


@dataclass
class CwayEntity:
    """Base entity for all Cway domain objects."""
    
    id: str
    created_at: datetime
    updated_at: datetime
    
    def __post_init__(self) -> None:
        """Validate entity after initialization."""
        if not self.id:
            raise ValueError("Entity ID cannot be empty")
            
    def __eq__(self, other: object) -> bool:
        """Compare entities by ID."""
        if not isinstance(other, CwayEntity):
            return NotImplemented
        return self.id == other.id
        
    def __hash__(self) -> int:
        """Hash entities by ID for use in sets and dicts."""
        return hash(self.id)


@dataclass  
class Project(CwayEntity):
    """Project entity representing a Cway project."""
    
    name: str
    description: Optional[str] = None
    status: str = "active"
    
    VALID_STATUSES = {"active", "inactive", "archived"}
    
    def __post_init__(self) -> None:
        """Validate project after initialization."""
        super().__post_init__()
        
        if not self.name:
            raise ValueError("Project name cannot be empty")
            
        if self.status not in self.VALID_STATUSES:
            raise ValueError(f"Status must be one of {self.VALID_STATUSES}, got: {self.status}")


@dataclass
class User(CwayEntity):
    """User entity representing a Cway user."""
    
    email: str
    name: Optional[str] = None
    role: str = "user"
    
    VALID_ROLES = {"admin", "user", "viewer"}
    EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    def __post_init__(self) -> None:
        """Validate user after initialization."""
        super().__post_init__()
        
        if not self.email:
            raise ValueError("User email cannot be empty")
            
        if not self.EMAIL_REGEX.match(self.email):
            raise ValueError(f"Invalid email format: {self.email}")
            
        if self.role not in self.VALID_ROLES:
            raise ValueError(f"Role must be one of {self.VALID_ROLES}, got: {self.role}")