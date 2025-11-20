"""FastAPI REST API implementation for Cway MCP Server."""

import logging
import uuid
from datetime import datetime
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.settings import settings
from ..infrastructure.graphql_client import CwayGraphQLClient, CwayAPIError
from ..infrastructure.cway_repositories import (
    CwayUserRepository,
    CwayProjectRepository,
    CwaySystemRepository
)
from ..application.kpi_use_cases import KPIUseCases
from ..application.temporal_kpi_use_cases import TemporalKPICalculator
from .rest_models import (
    ProjectCreateRequest,
    ProjectUpdateRequest,
    UserCreateRequest,
    ProjectResponse,
    ProjectListResponse,
    UserResponse,
    UserListResponse,
    SystemStatusResponse,
    ProjectHealthScoreResponse,
    StagnationAlertResponse,
    ErrorResponse,
    MessageResponse,
    ProjectStateEnum
)

# Set up logging
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()


# Dependency injection
class APIContext:
    """Context manager for API dependencies."""
    
    def __init__(self):
        self.graphql_client: Optional[CwayGraphQLClient] = None
        self.user_repo: Optional[CwayUserRepository] = None
        self.project_repo: Optional[CwayProjectRepository] = None
        self.system_repo: Optional[CwaySystemRepository] = None
        self.kpi_use_cases: Optional[KPIUseCases] = None
        self.temporal_kpi_calculator: Optional[TemporalKPICalculator] = None
    
    async def initialize(self):
        """Initialize all dependencies."""
        logger.info("Initializing API context...")
        
        self.graphql_client = CwayGraphQLClient()
        await self.graphql_client.connect()
        
        # Initialize repositories
        self.user_repo = CwayUserRepository(self.graphql_client)
        self.project_repo = CwayProjectRepository(self.graphql_client)
        self.system_repo = CwaySystemRepository(self.graphql_client)
        
        # Initialize use cases
        self.kpi_use_cases = KPIUseCases(self.project_repo)
        self.temporal_kpi_calculator = TemporalKPICalculator(self.project_repo)
        
        logger.info("API context initialized successfully")
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.graphql_client:
            await self.graphql_client.disconnect()
            logger.info("API context cleaned up")


# Global context instance
api_context = APIContext()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    # Startup
    await api_context.initialize()
    yield
    # Shutdown
    await api_context.cleanup()


# Create FastAPI app
app = FastAPI(
    title="Cway MCP REST API",
    description="REST API for Cway integration with OpenAPI documentation for ChatGPT GPT actions",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Authentication
async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """Verify bearer token authentication."""
    token = credentials.credentials
    
    # Compare with the API token from settings
    if token != settings.cway_api_token:
        logger.warning(f"Invalid authentication token attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token


# Error handlers
@app.exception_handler(CwayAPIError)
async def cway_api_error_handler(request, exc: CwayAPIError):
    """Handle Cway API errors."""
    logger.error(f"Cway API error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={
            "error": "CwayAPIError",
            "message": str(exc),
            "detail": "Error communicating with Cway API"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "detail": str(exc) if settings.debug else None
        }
    )


# Health check endpoint (no authentication required)
@app.get("/health", response_model=SystemStatusResponse, tags=["System"])
async def health_check():
    """Health check endpoint."""
    try:
        is_connected = api_context.graphql_client is not None
        
        return SystemStatusResponse(
            status="healthy" if is_connected else "degraded",
            connected=is_connected,
            api_url=settings.cway_api_url,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return SystemStatusResponse(
            status="unhealthy",
            connected=False,
            api_url=settings.cway_api_url,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )


# Project endpoints
@app.get(
    "/api/projects",
    response_model=ProjectListResponse,
    tags=["Projects"],
    summary="List all projects",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        502: {"model": ErrorResponse, "description": "Cway API Error"}
    }
)
async def list_projects(token: str = Depends(verify_token)):
    """Retrieve all Cway planner projects."""
    try:
        logger.info("Fetching all projects")
        projects = await api_context.project_repo.get_planner_projects()
        
        project_responses = [
            ProjectResponse(
                id=p.id,
                name=p.name,
                description=None,
                state=ProjectStateEnum(p.state.value),
                percentageDone=p.percentageDone,
                startDate=p.startDate.isoformat() if p.startDate else None,
                endDate=p.endDate.isoformat() if p.endDate else None
            )
            for p in projects
        ]
        
        return ProjectListResponse(
            projects=project_responses,
            total=len(project_responses)
        )
    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get(
    "/api/projects/{project_id}",
    response_model=ProjectResponse,
    tags=["Projects"],
    summary="Get project by ID",
    responses={
        404: {"model": ErrorResponse, "description": "Project not found"},
        401: {"model": ErrorResponse, "description": "Unauthorized"}
    }
)
async def get_project(project_id: str, token: str = Depends(verify_token)):
    """Retrieve a specific project by ID."""
    try:
        logger.info(f"Fetching project: {project_id}")
        project = await api_context.project_repo.get_planner_project_by_id(project_id)
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project not found: {project_id}"
            )
        
        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=None,
            state=ProjectStateEnum(project.state.value),
            percentageDone=project.percentageDone,
            startDate=project.startDate.isoformat() if project.startDate else None,
            endDate=project.endDate.isoformat() if project.endDate else None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get(
    "/api/projects/filter/active",
    response_model=ProjectListResponse,
    tags=["Projects"],
    summary="Get active projects"
)
async def get_active_projects(token: str = Depends(verify_token)):
    """Retrieve all active (in progress) projects."""
    try:
        projects = await api_context.project_repo.get_planner_projects()
        active_projects = [p for p in projects if p.is_active]
        
        project_responses = [
            ProjectResponse(
                id=p.id,
                name=p.name,
                description=None,
                state=ProjectStateEnum(p.state.value),
                percentageDone=p.percentageDone,
                startDate=p.startDate.isoformat() if p.startDate else None,
                endDate=p.endDate.isoformat() if p.endDate else None
            )
            for p in active_projects
        ]
        
        return ProjectListResponse(
            projects=project_responses,
            total=len(project_responses)
        )
    except Exception as e:
        logger.error(f"Error getting active projects: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get(
    "/api/projects/filter/completed",
    response_model=ProjectListResponse,
    tags=["Projects"],
    summary="Get completed projects"
)
async def get_completed_projects(token: str = Depends(verify_token)):
    """Retrieve all completed projects."""
    try:
        projects = await api_context.project_repo.get_planner_projects()
        completed_projects = [p for p in projects if p.is_completed]
        
        project_responses = [
            ProjectResponse(
                id=p.id,
                name=p.name,
                description=None,
                state=ProjectStateEnum(p.state.value),
                percentageDone=p.percentageDone,
                startDate=p.startDate.isoformat() if p.startDate else None,
                endDate=p.endDate.isoformat() if p.endDate else None
            )
            for p in completed_projects
        ]
        
        return ProjectListResponse(
            projects=project_responses,
            total=len(project_responses)
        )
    except Exception as e:
        logger.error(f"Error getting completed projects: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# User endpoints
@app.get(
    "/api/users",
    response_model=UserListResponse,
    tags=["Users"],
    summary="List all users"
)
async def list_users(token: str = Depends(verify_token)):
    """Retrieve all Cway users."""
    try:
        logger.info("Fetching all users")
        users = await api_context.user_repo.get_users()
        
        user_responses = [
            UserResponse(
                id=u.id,
                email=u.email,
                name=u.name,
                username=u.username,
                firstName=u.firstName,
                lastName=u.lastName,
                enabled=u.enabled,
                avatar=u.avatar
            )
            for u in users
        ]
        
        return UserListResponse(
            users=user_responses,
            total=len(user_responses)
        )
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get(
    "/api/users/{user_id}",
    response_model=UserResponse,
    tags=["Users"],
    summary="Get user by ID",
    responses={
        404: {"model": ErrorResponse, "description": "User not found"}
    }
)
async def get_user(user_id: str, token: str = Depends(verify_token)):
    """Retrieve a specific user by ID."""
    try:
        logger.info(f"Fetching user: {user_id}")
        user = await api_context.user_repo.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {user_id}"
            )
        
        return UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            username=user.username,
            firstName=user.firstName,
            lastName=user.lastName,
            enabled=user.enabled,
            avatar=user.avatar
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get(
    "/api/users/by-email/{email}",
    response_model=UserResponse,
    tags=["Users"],
    summary="Get user by email",
    responses={
        404: {"model": ErrorResponse, "description": "User not found"}
    }
)
async def get_user_by_email(email: str, token: str = Depends(verify_token)):
    """Retrieve a user by email address."""
    try:
        logger.info(f"Fetching user by email: {email}")
        users = await api_context.user_repo.get_users()
        user = next((u for u in users if u.email.lower() == email.lower()), None)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found with email: {email}"
            )
        
        return UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            username=user.username,
            firstName=user.firstName,
            lastName=user.lastName,
            enabled=user.enabled,
            avatar=user.avatar
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user by email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# System endpoints
@app.get(
    "/api/system/status",
    response_model=SystemStatusResponse,
    tags=["System"],
    summary="Get system status"
)
async def get_system_status(token: str = Depends(verify_token)):
    """Get Cway system connection status."""
    try:
        status_info = await api_context.system_repo.get_system_status()
        
        return SystemStatusResponse(
            status="healthy" if status_info.get("connected") else "degraded",
            connected=status_info.get("connected", False),
            api_url=settings.cway_api_url,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return SystemStatusResponse(
            status="unhealthy",
            connected=False,
            api_url=settings.cway_api_url,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )


# KPI endpoints
@app.get(
    "/api/kpis/dashboard",
    tags=["KPIs"],
    summary="Get KPI dashboard",
    description="Comprehensive system KPI dashboard with health scores"
)
async def get_kpi_dashboard(token: str = Depends(verify_token)):
    """Get comprehensive KPI dashboard."""
    try:
        dashboard = await api_context.kpi_use_cases.get_system_dashboard()
        return dashboard
    except Exception as e:
        logger.error(f"Error getting KPI dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get(
    "/api/kpis/project-health",
    response_model=List[ProjectHealthScoreResponse],
    tags=["KPIs"],
    summary="Get project health scores"
)
async def get_project_health(token: str = Depends(verify_token)):
    """Get health scores for all projects."""
    try:
        health_scores = await api_context.kpi_use_cases.get_all_project_health_scores()
        
        return [
            ProjectHealthScoreResponse(
                project_id=score.project_id,
                project_name=score.project_name,
                health_score=score.health_score,
                risk_level=score.risk_level,
                metrics=score.metrics
            )
            for score in health_scores
        ]
    except Exception as e:
        logger.error(f"Error getting project health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get(
    "/api/kpis/critical-projects",
    response_model=List[ProjectHealthScoreResponse],
    tags=["KPIs"],
    summary="Get critical projects"
)
async def get_critical_projects(token: str = Depends(verify_token)):
    """Get projects requiring immediate attention."""
    try:
        critical = await api_context.kpi_use_cases.get_critical_projects()
        
        return [
            ProjectHealthScoreResponse(
                project_id=score.project_id,
                project_name=score.project_name,
                health_score=score.health_score,
                risk_level=score.risk_level,
                metrics=score.metrics
            )
            for score in critical
        ]
    except Exception as e:
        logger.error(f"Error getting critical projects: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Temporal KPI endpoints
@app.get(
    "/api/temporal-kpis/dashboard",
    tags=["Temporal KPIs"],
    summary="Get temporal KPI dashboard"
)
async def get_temporal_dashboard(
    analysis_period_days: int = 90,
    token: str = Depends(verify_token)
):
    """Get comprehensive temporal analysis dashboard."""
    try:
        dashboard = await api_context.temporal_kpi_calculator.calculate_temporal_dashboard(
            analysis_period_days=analysis_period_days
        )
        return dashboard
    except Exception as e:
        logger.error(f"Error getting temporal dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get(
    "/api/temporal-kpis/stagnation-alerts",
    response_model=List[StagnationAlertResponse],
    tags=["Temporal KPIs"],
    summary="Get stagnation alerts"
)
async def get_stagnation_alerts(
    min_urgency_score: int = 5,
    token: str = Depends(verify_token)
):
    """Get projects at risk of stagnation."""
    try:
        alerts = await api_context.temporal_kpi_calculator.get_stagnation_alerts(
            min_urgency_score=min_urgency_score
        )
        
        return [
            StagnationAlertResponse(
                project_id=alert.project_id,
                project_name=alert.project_name,
                urgency_score=alert.urgency_score,
                days_since_activity=alert.days_since_last_activity,
                recommendations=alert.recommendations
            )
            for alert in alerts
        ]
    except Exception as e:
        logger.error(f"Error getting stagnation alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Cway MCP REST API",
        "version": "1.0.0",
        "documentation": "/docs",
        "openapi_spec": "/openapi.json",
        "health_check": "/health"
    }
