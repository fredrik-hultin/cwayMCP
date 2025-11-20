"""Integration tests for REST API endpoints."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import status

from src.presentation.rest_api import app
from config.settings import settings


@pytest_asyncio.fixture
async def client():
    """Create async HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
def auth_headers():
    """Create authentication headers."""
    return {"Authorization": f"Bearer {settings.cway_api_token}"}


class TestHealthEndpoints:
    """Test health and status endpoints."""
    
    @pytest.mark.asyncio
    async def test_health_check_no_auth(self, client):
        """Test health check endpoint without authentication."""
        response = await client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "status" in data
        assert "connected" in data
        assert "api_url" in data
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = await client.get("/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Cway MCP REST API"
        assert "documentation" in data


class TestAuthentication:
    """Test authentication and authorization."""
    
    @pytest.mark.asyncio
    async def test_missing_token(self, client):
        """Test endpoint without authentication token."""
        response = await client.get("/api/projects")
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    @pytest.mark.asyncio
    async def test_invalid_token(self, client):
        """Test endpoint with invalid token."""
        response = await client.get(
            "/api/projects",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_valid_token(self, client, auth_headers):
        """Test endpoint with valid token."""
        response = await client.get("/api/projects", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK


class TestProjectEndpoints:
    """Test project-related endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_projects(self, client, auth_headers):
        """Test listing all projects."""
        response = await client.get("/api/projects", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "projects" in data
        assert "total" in data
        assert isinstance(data["projects"], list)
        assert data["total"] >= 0
    
    @pytest.mark.asyncio
    async def test_get_project_invalid_id(self, client, auth_headers):
        """Test getting project with invalid ID."""
        response = await client.get(
            "/api/projects/invalid-uuid-123",
            headers=auth_headers
        )
        # Should return 404 or 500 depending on validation
        assert response.status_code in [
            status.HTTP_404_NOT_FOUND,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ]
    
    @pytest.mark.asyncio
    async def test_get_active_projects(self, client, auth_headers):
        """Test getting active projects."""
        response = await client.get(
            "/api/projects/filter/active",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "projects" in data
        assert "total" in data
        
        # Verify all projects are active
        for project in data["projects"]:
            assert project["state"] == "IN_PROGRESS"
    
    @pytest.mark.asyncio
    async def test_get_completed_projects(self, client, auth_headers):
        """Test getting completed projects."""
        response = await client.get(
            "/api/projects/filter/completed",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "projects" in data
        assert "total" in data
        
        # Verify all projects are completed
        for project in data["projects"]:
            assert project["state"] == "COMPLETED"


class TestUserEndpoints:
    """Test user-related endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_users(self, client, auth_headers):
        """Test listing all users."""
        response = await client.get("/api/users", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert isinstance(data["users"], list)
        assert data["total"] >= 0
    
    @pytest.mark.asyncio
    async def test_get_user_invalid_id(self, client, auth_headers):
        """Test getting user with invalid ID."""
        response = await client.get(
            "/api/users/invalid-uuid-123",
            headers=auth_headers
        )
        # Should return 404 or 500 depending on validation
        assert response.status_code in [
            status.HTTP_404_NOT_FOUND,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ]
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, client, auth_headers):
        """Test getting user by email that doesn't exist."""
        response = await client.get(
            "/api/users/by-email/nonexistent@example.com",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestSystemEndpoints:
    """Test system-related endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_system_status(self, client, auth_headers):
        """Test getting system status."""
        response = await client.get("/api/system/status", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "status" in data
        assert "connected" in data
        assert "api_url" in data
        assert "timestamp" in data


class TestKPIEndpoints:
    """Test KPI-related endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_kpi_dashboard(self, client, auth_headers):
        """Test getting KPI dashboard."""
        response = await client.get("/api/kpis/dashboard", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        # Dashboard should return comprehensive metrics
        assert isinstance(data, dict)
    
    @pytest.mark.asyncio
    async def test_get_project_health(self, client, auth_headers):
        """Test getting project health scores."""
        response = await client.get(
            "/api/kpis/project-health",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)
        
        # Verify health score structure
        for score in data:
            assert "project_id" in score
            assert "project_name" in score
            assert "health_score" in score
            assert "risk_level" in score
            assert 0 <= score["health_score"] <= 100
    
    @pytest.mark.asyncio
    async def test_get_critical_projects(self, client, auth_headers):
        """Test getting critical projects."""
        response = await client.get(
            "/api/kpis/critical-projects",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)


class TestTemporalKPIEndpoints:
    """Test temporal KPI endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_temporal_dashboard(self, client, auth_headers):
        """Test getting temporal KPI dashboard."""
        response = await client.get(
            "/api/temporal-kpis/dashboard",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, dict)
    
    @pytest.mark.asyncio
    async def test_get_temporal_dashboard_with_params(self, client, auth_headers):
        """Test temporal dashboard with custom analysis period."""
        response = await client.get(
            "/api/temporal-kpis/dashboard?analysis_period_days=30",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
    
    @pytest.mark.asyncio
    async def test_get_stagnation_alerts(self, client, auth_headers):
        """Test getting stagnation alerts."""
        response = await client.get(
            "/api/temporal-kpis/stagnation-alerts",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)
        
        # Verify stagnation alert structure
        for alert in data:
            assert "project_id" in alert
            assert "project_name" in alert
            assert "urgency_score" in alert
            assert "days_since_activity" in alert
            assert "recommendations" in alert
            assert 1 <= alert["urgency_score"] <= 10
    
    @pytest.mark.asyncio
    async def test_get_stagnation_alerts_with_threshold(self, client, auth_headers):
        """Test stagnation alerts with custom urgency threshold."""
        response = await client.get(
            "/api/temporal-kpis/stagnation-alerts?min_urgency_score=8",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        # All alerts should have urgency >= 8
        for alert in data:
            assert alert["urgency_score"] >= 8


class TestOpenAPIDocumentation:
    """Test OpenAPI documentation endpoints."""
    
    @pytest.mark.asyncio
    async def test_openapi_json(self, client):
        """Test OpenAPI JSON endpoint."""
        response = await client.get("/openapi.json")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
        assert data["info"]["title"] == "Cway MCP REST API"
    
    @pytest.mark.asyncio
    async def test_docs_ui(self, client):
        """Test Swagger UI documentation."""
        response = await client.get("/docs")
        assert response.status_code == status.HTTP_200_OK
    
    @pytest.mark.asyncio
    async def test_redoc_ui(self, client):
        """Test ReDoc documentation."""
        response = await client.get("/redoc")
        assert response.status_code == status.HTTP_200_OK


class TestCORSHeaders:
    """Test CORS middleware configuration."""
    
    @pytest.mark.asyncio
    async def test_cors_headers_present(self, client, auth_headers):
        """Test that CORS headers are present in responses."""
        response = await client.get("/api/projects", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        # Check for CORS headers
        assert "access-control-allow-origin" in response.headers


class TestErrorHandling:
    """Test error handling and responses."""
    
    @pytest.mark.asyncio
    async def test_404_not_found(self, client, auth_headers):
        """Test 404 error response."""
        response = await client.get(
            "/api/nonexistent-endpoint",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.asyncio
    async def test_method_not_allowed(self, client, auth_headers):
        """Test 405 method not allowed."""
        # Try POST on GET-only endpoint
        response = await client.post(
            "/api/projects",
            headers=auth_headers,
            json={"name": "Test"}
        )
        # May be 405 or 404 depending on routing
        assert response.status_code in [
            status.HTTP_404_NOT_FOUND,
            status.HTTP_405_METHOD_NOT_ALLOWED
        ]


class TestResponseModels:
    """Test response model validation."""
    
    @pytest.mark.asyncio
    async def test_project_response_structure(self, client, auth_headers):
        """Test project response matches expected structure."""
        response = await client.get("/api/projects", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        if data["total"] > 0:
            project = data["projects"][0]
            # Verify required fields
            assert "id" in project
            assert "name" in project
            assert "state" in project
            assert "percentageDone" in project
            # Verify types
            assert isinstance(project["percentageDone"], (int, float))
            assert 0 <= project["percentageDone"] <= 1
    
    @pytest.mark.asyncio
    async def test_user_response_structure(self, client, auth_headers):
        """Test user response matches expected structure."""
        response = await client.get("/api/users", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        if data["total"] > 0:
            user = data["users"][0]
            # Verify required fields
            assert "id" in user
            assert "email" in user
            assert "name" in user
            assert "username" in user
            assert "firstName" in user
            assert "lastName" in user
            # Verify types
            assert isinstance(user["enabled"], bool)
            assert isinstance(user["avatar"], bool)
