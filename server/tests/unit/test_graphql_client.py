"""Tests for GraphQL client."""

import json
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from gql.transport.exceptions import TransportError

from src.infrastructure.graphql_client import CwayGraphQLClient, CwayAPIError


class TestCwayGraphQLClient:
    """Test CwayGraphQLClient."""
    
    @pytest.fixture
    def client(self) -> CwayGraphQLClient:
        """Create a GraphQL client for testing."""
        with patch('src.infrastructure.graphql_client.settings') as mock_settings:
            mock_settings.cway_api_url = "https://test-api.cway.com"
            mock_settings.cway_api_token = "test-token-123"
            mock_settings.request_timeout = 30
            mock_settings.max_retries = 3
            return CwayGraphQLClient()
    
    def test_init(self, client: CwayGraphQLClient) -> None:
        """Test client initialization."""
        assert client.api_url == "https://test-api.cway.com"
        assert client.token_provider is not None
        assert client._client is None
        
    def test_init_with_custom_params(self) -> None:
        """Test initialization with custom parameters."""
        client = CwayGraphQLClient("https://custom.com", "custom-token")
        assert client.api_url == "https://custom.com"
        assert client.token_provider is not None
        
    def test_init_with_defaults(self) -> None:
        """Test initialization with settings defaults."""
        with patch('src.infrastructure.graphql_client.settings') as mock_settings:
            mock_settings.cway_api_url = "https://default.com"
            mock_settings.cway_api_token = "default-token"
            mock_settings.auth_method = "static"
            
            client = CwayGraphQLClient()
            assert client.api_url == "https://default.com"
            assert client.token_provider is not None
    
    @pytest.mark.asyncio
    async def test_connect(self, client: CwayGraphQLClient) -> None:
        """Test client connection."""
        with patch('src.infrastructure.graphql_client.AIOHTTPTransport') as MockTransport:
            with patch('src.infrastructure.graphql_client.Client') as MockClient:
                mock_transport = AsyncMock()
                mock_client = AsyncMock()
                MockTransport.return_value = mock_transport
                MockClient.return_value = mock_client
                
                await client.connect()
                
                assert client._client == mock_client
                MockTransport.assert_called_once()
                MockClient.assert_called_once_with(
                    transport=mock_transport,
                    fetch_schema_from_transport=False
                )
    
    @pytest.mark.asyncio 
    async def test_disconnect(self, client: CwayGraphQLClient) -> None:
        """Test client disconnection."""
        mock_client = AsyncMock()
        mock_transport = AsyncMock()
        mock_client.transport = mock_transport
        client._client = mock_client
        
        await client.disconnect()
        
        mock_transport.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_disconnect_no_client(self, client: CwayGraphQLClient) -> None:
        """Test disconnect when no client exists."""
        client._client = None
        
        # Should not raise an exception
        await client.disconnect()
        
        assert client._client is None
        
    @pytest.mark.asyncio
    async def test_disconnect_no_transport(self, client: CwayGraphQLClient) -> None:
        """Test disconnect when client has no transport."""
        mock_client = AsyncMock()
        mock_client.transport = None
        client._client = mock_client
        
        # Should not raise an exception
        await client.disconnect()
        
        assert client._client == mock_client
    
    @pytest.mark.asyncio
    async def test_execute_query_success(self, client: CwayGraphQLClient) -> None:
        """Test successful query execution."""
        query = "{ users { id name } }"
        expected_data = {"users": [{"id": "1", "name": "Test User"}]}
        
        mock_client = AsyncMock()
        mock_client.execute_async.return_value = expected_data
        client._client = mock_client
        
        with patch('src.infrastructure.graphql_client.gql') as mock_gql:
            mock_gql.return_value = "parsed_query"
            
            result = await client.execute_query(query)
            
            assert result == expected_data
            mock_gql.assert_called_once_with(query)
            mock_client.execute_async.assert_called_once_with("parsed_query", variable_values=None)
    
    @pytest.mark.asyncio
    async def test_execute_query_with_variables(self, client: CwayGraphQLClient) -> None:
        """Test query execution with variables."""
        query = "query GetUser($id: String!) { user(id: $id) { id name } }"
        variables = {"id": "user-123"}
        expected_data = {"user": {"id": "user-123", "name": "Test User"}}
        
        mock_client = AsyncMock()
        mock_client.execute_async.return_value = expected_data
        client._client = mock_client
        
        with patch('src.infrastructure.graphql_client.gql') as mock_gql:
            mock_gql.return_value = "parsed_query"
            
            result = await client.execute_query(query, variables)
            
            assert result == expected_data
            mock_client.execute_async.assert_called_once_with("parsed_query", variable_values=variables)
    
    @pytest.mark.asyncio
    async def test_execute_query_auto_connect(self, client: CwayGraphQLClient) -> None:
        """Test query execution auto-connects when not connected."""
        query = "{ users { id } }"
        expected_data = {"users": []}
        
        with patch.object(client, 'connect') as mock_connect:
            mock_client = AsyncMock()
            mock_client.execute_async.return_value = expected_data
            client._client = None  # Not connected initially
            
            # After connect is called, set the client
            async def side_effect():
                client._client = mock_client
            mock_connect.side_effect = side_effect
            
            with patch('src.infrastructure.graphql_client.gql') as mock_gql:
                mock_gql.return_value = "parsed_query"
                
                result = await client.execute_query(query)
                
                assert result == expected_data
                mock_connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_query_transport_error(self, client: CwayGraphQLClient) -> None:
        """Test handling of transport errors with retry logic."""
        query = "{ users { id } }"
        
        mock_client = AsyncMock()
        mock_client.execute_async.side_effect = TransportError("Connection failed")
        client._client = mock_client
        
        with patch('src.infrastructure.graphql_client.gql') as mock_gql:
            with patch('src.infrastructure.graphql_client.asyncio.sleep') as mock_sleep:
                mock_gql.return_value = "parsed_query"
                
                with pytest.raises(ConnectionError, match="Failed to connect to Cway API after 3 attempts"):
                    await client.execute_query(query)
                    
                # Should have retried 3 times
                assert mock_client.execute_async.call_count == 3
                # Should have slept between retries (exponential backoff)
                assert mock_sleep.call_count == 2
    
    @pytest.mark.asyncio
    async def test_execute_query_generic_error(self, client: CwayGraphQLClient) -> None:
        """Test handling of generic exceptions."""
        query = "{ users { id } }"
        
        mock_client = AsyncMock()
        mock_client.execute_async.side_effect = ValueError("Unexpected error")
        client._client = mock_client
        
        with patch('src.infrastructure.graphql_client.gql') as mock_gql:
            mock_gql.return_value = "parsed_query"
            
            with pytest.raises(CwayAPIError, match="GraphQL query failed: Unexpected error"):
                await client.execute_query(query)
    
    @pytest.mark.asyncio
    async def test_execute_mutation(self, client: CwayGraphQLClient) -> None:
        """Test mutation execution."""
        mutation = "mutation CreateUser($input: UserInput!) { createUser(input: $input) { id } }"
        variables = {"input": {"name": "Test User"}}
        expected_data = {"createUser": {"id": "user-123"}}
        
        with patch.object(client, 'execute_query') as mock_execute:
            mock_execute.return_value = expected_data
            
            result = await client.execute_mutation(mutation, variables)
            
            assert result == expected_data
            mock_execute.assert_called_once_with(mutation, variables)
    
    @pytest.mark.asyncio
    async def test_get_schema_success(self, client: CwayGraphQLClient) -> None:
        """Test successful schema introspection."""
        expected_schema = {"types": [{"name": "User", "fields": []}]}
        
        with patch.object(client, 'execute_query') as mock_execute:
            mock_execute.return_value = {"__schema": expected_schema}
            
            result = await client.get_schema()
            
            assert result == expected_schema
            mock_execute.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_get_schema_failure(self, client: CwayGraphQLClient) -> None:
        """Test schema introspection failure."""
        with patch.object(client, 'execute_query') as mock_execute:
            mock_execute.side_effect = Exception("Schema error")
            
            result = await client.get_schema()
            
            assert result is None
            
    @pytest.mark.asyncio
    async def test_context_manager_success(self, client: CwayGraphQLClient) -> None:
        """Test using client as context manager successfully."""
        with patch.object(client, 'connect') as mock_connect:
            with patch.object(client, 'disconnect') as mock_disconnect:
                
                async with client:
                    pass
                
                mock_connect.assert_called_once()
                mock_disconnect.assert_called_once()
                
    @pytest.mark.asyncio
    async def test_context_manager_exception(self, client: CwayGraphQLClient) -> None:
        """Test context manager cleanup on exception."""
        with patch.object(client, 'connect') as mock_connect:
            with patch.object(client, 'disconnect') as mock_disconnect:
                
                try:
                    async with client:
                        raise ValueError("Test exception")
                except ValueError:
                    pass
                
                mock_connect.assert_called_once()
                mock_disconnect.assert_called_once()


class TestCwayAPIError:
    """Test CwayAPIError exception."""
    
    def test_cway_api_error_creation(self) -> None:
        """Test creating CwayAPIError."""
        error = CwayAPIError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)