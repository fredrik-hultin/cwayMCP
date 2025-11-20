"""Pydantic models for REST API requests and responses with OpenAPI documentation."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr, field_validator
from enum import Enum


class ProjectStateEnum(str, Enum):
    """Project state enumeration for API."""
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    PLANNED = "PLANNED"
    DELIVERED = "DELIVERED"


class UserRoleEnum(str, Enum):
    """User role enumeration for API."""
    admin = "admin"
    user = "user"
    viewer = "viewer"
    reviewer = "reviewer"
    manager = "manager"


# Request Models
class ProjectCreateRequest(BaseModel):
    """Request model for creating a new project."""
    
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(None, max_length=2000, description="Project description")
    status: Optional[ProjectStateEnum] = Field(
        default=ProjectStateEnum.IN_PROGRESS,
        description="Project status"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "New Marketing Campaign",
                    "description": "Q4 2024 marketing campaign project",
                    "status": "IN_PROGRESS"
                }
            ]
        }
    }


class ProjectUpdateRequest(BaseModel):
    """Request model for updating an existing project."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(None, max_length=2000, description="Project description")
    status: Optional[ProjectStateEnum] = Field(None, description="Project status")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Updated Project Name",
                    "status": "COMPLETED"
                }
            ]
        }
    }


class UserCreateRequest(BaseModel):
    """Request model for creating a new user."""
    
    email: EmailStr = Field(..., description="User email address")
    name: Optional[str] = Field(None, max_length=255, description="User full name")
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Username")
    role: Optional[UserRoleEnum] = Field(default=UserRoleEnum.user, description="User role")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "john.doe@example.com",
                    "name": "John Doe",
                    "username": "johndoe",
                    "role": "user"
                }
            ]
        }
    }


# Response Models
class ProjectResponse(BaseModel):
    """Response model for a single project."""
    
    id: str = Field(..., description="Unique project ID (UUID)")
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    state: ProjectStateEnum = Field(..., description="Current project state")
    percentageDone: float = Field(0.0, ge=0.0, le=1.0, description="Completion percentage (0.0 to 1.0)")
    startDate: Optional[str] = Field(None, description="Project start date (ISO format)")
    endDate: Optional[str] = Field(None, description="Project end date (ISO format)")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "name": "Marketing Campaign",
                    "description": "Q4 2024 campaign",
                    "state": "IN_PROGRESS",
                    "percentageDone": 0.65,
                    "startDate": "2024-01-01",
                    "endDate": "2024-12-31"
                }
            ]
        }
    }


class ProjectListResponse(BaseModel):
    """Response model for list of projects."""
    
    projects: List[ProjectResponse] = Field(..., description="List of projects")
    total: int = Field(..., description="Total number of projects")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "projects": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "name": "Project 1",
                            "state": "IN_PROGRESS",
                            "percentageDone": 0.5
                        }
                    ],
                    "total": 1
                }
            ]
        }
    }


class UserResponse(BaseModel):
    """Response model for a single user."""
    
    id: str = Field(..., description="Unique user ID (UUID)")
    email: str = Field(..., description="User email address")
    name: str = Field(..., description="User full name")
    username: str = Field(..., description="Username")
    firstName: str = Field(..., description="First name")
    lastName: str = Field(..., description="Last name")
    enabled: bool = Field(True, description="Whether user is enabled")
    avatar: bool = Field(False, description="Whether user has avatar")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "987e6543-e21b-12d3-a456-426614174000",
                    "email": "john.doe@example.com",
                    "name": "John Doe",
                    "username": "johndoe",
                    "firstName": "John",
                    "lastName": "Doe",
                    "enabled": True,
                    "avatar": False
                }
            ]
        }
    }


class UserListResponse(BaseModel):
    """Response model for list of users."""
    
    users: List[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "users": [
                        {
                            "id": "987e6543-e21b-12d3-a456-426614174000",
                            "email": "john.doe@example.com",
                            "name": "John Doe",
                            "username": "johndoe",
                            "firstName": "John",
                            "lastName": "Doe",
                            "enabled": True,
                            "avatar": False
                        }
                    ],
                    "total": 1
                }
            ]
        }
    }


class SystemStatusResponse(BaseModel):
    """Response model for system status."""
    
    status: str = Field(..., description="System status")
    connected: bool = Field(..., description="Whether connected to Cway API")
    api_url: str = Field(..., description="Cway API URL")
    timestamp: str = Field(..., description="Current server timestamp")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "healthy",
                    "connected": True,
                    "api_url": "https://app.cway.se/graphql",
                    "timestamp": "2024-11-20T15:30:00Z"
                }
            ]
        }
    }


class ProjectHealthScoreResponse(BaseModel):
    """Response model for project health score."""
    
    project_id: str = Field(..., description="Project ID")
    project_name: str = Field(..., description="Project name")
    health_score: float = Field(..., ge=0.0, le=100.0, description="Health score (0-100)")
    risk_level: str = Field(..., description="Risk level (LOW, MEDIUM, HIGH, CRITICAL)")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Detailed health metrics")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "project_id": "123e4567-e89b-12d3-a456-426614174000",
                    "project_name": "Marketing Campaign",
                    "health_score": 75.5,
                    "risk_level": "LOW",
                    "metrics": {
                        "completion_rate": 0.65,
                        "on_schedule": True
                    }
                }
            ]
        }
    }


class StagnationAlertResponse(BaseModel):
    """Response model for stagnation alert."""
    
    project_id: str = Field(..., description="Project ID")
    project_name: str = Field(..., description="Project name")
    urgency_score: int = Field(..., ge=1, le=10, description="Urgency score (1-10)")
    days_since_activity: int = Field(..., description="Days since last activity")
    recommendations: List[str] = Field(default_factory=list, description="Action recommendations")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "project_id": "123e4567-e89b-12d3-a456-426614174000",
                    "project_name": "Stale Project",
                    "urgency_score": 8,
                    "days_since_activity": 45,
                    "recommendations": [
                        "Schedule project review meeting",
                        "Reassess project priorities"
                    ]
                }
            ]
        }
    }


class ErrorResponse(BaseModel):
    """Standard error response model."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    correlation_id: Optional[str] = Field(None, description="Request correlation ID for debugging")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "error": "NotFoundError",
                    "message": "Project not found",
                    "detail": "No project exists with ID: 123",
                    "correlation_id": "req_abc123"
                }
            ]
        }
    }


class MessageResponse(BaseModel):
    """Generic message response."""
    
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Operation completed successfully",
                    "data": {"item_id": "123"}
                }
            ]
        }
    }
