"""Pytest configuration and shared fixtures."""

import asyncio
import pytest
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, Mock

from src.infrastructure.graphql_client import CwayGraphQLClient


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_graphql_client() -> Mock:
    """Mock GraphQL client for testing."""
    client = Mock(spec=CwayGraphQLClient)
    client.execute_query = AsyncMock()
    client.execute_mutation = AsyncMock()
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    client.get_schema = AsyncMock()
    return client


@pytest.fixture
def sample_cway_data() -> dict:
    """Sample Cway data for testing."""
    return {
        "projects": [
            {
                "id": "proj-1",
                "name": "Sample Project",
                "description": "A sample project for testing",
                "status": "ACTIVE",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        ],
        "users": [
            {
                "id": "user-1",
                "email": "test@example.com",
                "name": "Test User",
                "role": "admin"
            }
        ]
    }


@pytest.fixture
def mock_settings() -> Mock:
    """Mock settings for testing."""
    settings = Mock()
    settings.cway_api_url = "https://test.example.com/graphql"
    settings.cway_api_token = "test_token_123"
    settings.request_timeout = 30
    settings.max_retries = 3
    settings.mcp_server_host = "localhost"
    settings.mcp_server_port = 8000
    settings.log_level = "INFO"
    settings.debug = False
    return settings