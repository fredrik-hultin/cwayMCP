"""Updated domain entities based on actual Cway API schema."""

import uuid
from datetime import datetime, date
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum


class ProjectState(Enum):
    """Project state enumeration based on Cway API."""
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    PLANNED = "PLANNED"


@dataclass
class CwayUser:
    """Cway User entity based on actual API schema."""
    
    id: str  # UUID as string
    name: str
    email: str
    username: str
    firstName: str
    lastName: str
    enabled: bool = True
    avatar: bool = False
    acceptedTerms: bool = False
    earlyAccessProgram: bool = False
    isSSO: bool = False
    createdAt: Optional[int] = None  # Unix timestamp
    
    def __post_init__(self) -> None:
        """Validate user after initialization."""
        if not self.id:
            raise ValueError("User ID cannot be empty")
        if not self.email:
            raise ValueError("User email cannot be empty")
            
    @property
    def full_name(self) -> str:
        """Get the full name of the user."""
        if self.firstName and self.lastName:
            return f"{self.firstName} {self.lastName}".strip()
        return self.name or self.username


@dataclass
class PlannerProject:
    """Planner Project entity based on actual API schema."""
    
    id: str  # UUID as string
    name: str
    state: ProjectState
    percentageDone: float = 0.0
    startDate: Optional[date] = None
    endDate: Optional[date] = None
    
    def __post_init__(self) -> None:
        """Validate project after initialization."""
        if not self.id:
            raise ValueError("Project ID cannot be empty")
        if not self.name:
            raise ValueError("Project name cannot be empty")
            
    @property 
    def is_active(self) -> bool:
        """Check if project is active."""
        return self.state == ProjectState.IN_PROGRESS
        
    @property
    def is_completed(self) -> bool:
        """Check if project is completed."""
        return self.state == ProjectState.COMPLETED


@dataclass
class Organisation:
    """Organisation entity based on actual API schema."""
    
    id: str  # UUID as string
    name: str
    description: Optional[str] = None
    active: bool = True
    numberOfUsers: int = 0
    numberOfFullUsers: int = 0
    numberOfLimitedUsers: int = 0
    canAddArtwork: bool = True
    canAddUser: bool = True
    
    def __post_init__(self) -> None:
        """Validate organisation after initialization."""
        if not self.id:
            raise ValueError("Organisation ID cannot be empty")
        if not self.name:
            raise ValueError("Organisation name cannot be empty")


@dataclass
class OrganisationMembership:
    """Organisation membership entity."""
    
    organisationId: str  # UUID as string
    name: str
    permissionGroupId: Optional[str] = None  # UUID as string
    
    def __post_init__(self) -> None:
        """Validate membership after initialization."""
        if not self.organisationId:
            raise ValueError("Organisation ID cannot be empty")
        if not self.name:
            raise ValueError("Organisation name cannot be empty")


@dataclass
class UserTeam:
    """User team entity based on actual API schema."""
    
    id: str  # UUID as string
    name: str
    description: str = ""
    
    def __post_init__(self) -> None:
        """Validate team after initialization."""
        if not self.id:
            raise ValueError("Team ID cannot be empty")
        if not self.name:
            raise ValueError("Team name cannot be empty")


# Helper functions for data conversion
def parse_cway_date(date_str: Optional[str]) -> Optional[date]:
    """Parse Cway date string to date object."""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str).date()
    except ValueError:
        return None


def parse_cway_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """Parse Cway datetime string to datetime object."""
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    except ValueError:
        return None