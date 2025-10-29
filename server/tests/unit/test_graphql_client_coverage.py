"""
Additional tests for GraphQL client to increase coverage.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from gql.transport.exceptions import TransportQueryError, TransportServerError
from src.infrastructure.graphql_client import CwayGraphQLClient, CwayAPIError


class TestCwayGraphQLClientConnection:
    """Test GraphQL client connection handling."""
    
    @pytest.mark.asyncio
    async def test_connect_success(self):
        """Test successful connection."""
        # Arrange
        with patch('src.infrastructure.graphql_client.AIOHTTPTransport') as mock_transport:
            with patch('src.infrastructure.graphql_client.Client') as mock_client_class:
                client = CwayGraphQLClient("https://test.api/graphql", "test-token")
                
                # Act
                await client.connect()
                
                # Assert
                mock_transport.assert_called_once()
                mock_client_class.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_failure(self):
        """Test connection failure."""
        # Arrange
        with patch('src.infrastructure.graphql_client.AIOHTTPTransport') as mock_transport:
            mock_transport.side_effect = Exception("Connection failed")
            client = CwayGraphQLClient("https://test.api/graphql", "test-token")
            
            # Act & Assert
            with pytest.raises(Exception, match="Connection failed"):
                await client.connect()
    
    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnection."""
        # Arrange
        with patch('src.infrastructure.graphql_client.AIOHTTPTransport'):
            with patch('src.infrastructure.graphql_client.Client') as mock_client_class:
                mock_client = MagicMock()
                mock_transport = AsyncMock()
                mock_client.transport = mock_transport
                mock_client_class.return_value = mock_client
                
                client = CwayGraphQLClient("https://test.api/graphql", "test-token")
                await client.connect()
                
                # Act
                await client.disconnect()
                
                # Assert
                mock_transport.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test using client as async context manager."""
        # Arrange
        with patch('src.infrastructure.graphql_client.AIOHTTPTransport'):
            with patch('src.infrastructure.graphql_client.Client') as mock_client_class:
                mock_client = MagicMock()
                mock_transport = AsyncMock()
                mock_client.transport = mock_transport
                mock_client_class.return_value = mock_client
                
                client = CwayGraphQLClient("https://test.api/graphql", "test-token")
                
                # Act
                async with client:
                    # Assert - client should be connected
                    assert client._client is not None
                
                # Assert disconnect was called
                mock_transport.close.assert_called_once()


class TestCwayGraphQLClientQueries:
    """Test GraphQL query execution."""
    
    @pytest.mark.asyncio
    async def test_execute_query_auto_connect(self):
        """Test query execution with auto-connection."""
        # Arrange
        with patch('src.infrastructure.graphql_client.AIOHTTPTransport'):
            with patch('src.infrastructure.graphql_client.Client') as mock_client_class:
                with patch('src.infrastructure.graphql_client.gql') as mock_gql:
                    mock_client = AsyncMock()
                    mock_client.execute_async = AsyncMock(return_value={"data": "test"})
                    mock_client_class.return_value = mock_client
                    
                    client = CwayGraphQLClient("https://test.api/graphql", "test-token")
                    
                    # Act
                    result = await client.execute_query("{ test }")
                    
                    # Assert
                    assert result == {"data": "test"}
                    mock_client.execute_async.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_query_with_variables(self):
        """Test query execution with variables."""
        # Arrange
        with patch('src.infrastructure.graphql_client.AIOHTTPTransport'):
            with patch('src.infrastructure.graphql_client.Client') as mock_client_class:
                with patch('src.infrastructure.graphql_client.gql'):
                    mock_client = AsyncMock()
                    mock_client.execute_async = AsyncMock(return_value={"data": "test"})
                    mock_client_class.return_value = mock_client
                    
                    client = CwayGraphQLClient("https://test.api/graphql", "test-token")
                    await client.connect()
                    
                    # Act
                    result = await client.execute_query("{ test }", {"var": "value"})
                    
                    # Assert
                    assert result == {"data": "test"}
    
    @pytest.mark.asyncio
    async def test_execute_query_retry_on_transport_error(self):
        """Test query retries on transport error."""
        # Arrange
        with patch('src.infrastructure.graphql_client.AIOHTTPTransport'):
            with patch('src.infrastructure.graphql_client.Client') as mock_client_class:
                with patch('src.infrastructure.graphql_client.gql'):
                    from gql.transport.exceptions import TransportError
                    
                    mock_client = AsyncMock()
                    # Fail twice, then succeed
                    mock_client.execute_async = AsyncMock(
                        side_effect=[
                            TransportError("Error 1"),
                            TransportError("Error 2"),
                            {"data": "success"}
                        ]
                    )
                    mock_client_class.return_value = mock_client
                    
                    client = CwayGraphQLClient("https://test.api/graphql", "test-token")
                    await client.connect()
                    
                    # Act
                    result = await client.execute_query("{ test }")
                    
                    # Assert
                    assert result == {"data": "success"}
                    assert mock_client.execute_async.call_count == 3
    
    @pytest.mark.asyncio
    async def test_execute_query_max_retries_exceeded(self):
        """Test query fails after max retries."""
        # Arrange  
        with patch('src.infrastructure.graphql_client.AIOHTTPTransport'):
            with patch('src.infrastructure.graphql_client.Client') as mock_client_class:
                with patch('src.infrastructure.graphql_client.gql'):
                    with patch('src.infrastructure.graphql_client.settings') as mock_settings:
                        from gql.transport.exceptions import TransportError
                        
                        mock_settings.max_retries = 2
                        mock_client = AsyncMock()
                        mock_client.execute_async = AsyncMock(side_effect=TransportError("Persistent error"))
                        mock_client_class.return_value = mock_client
                        
                        client = CwayGraphQLClient("https://test.api/graphql", "test-token")
                        await client.connect()
                        
                        # Act & Assert
                        with pytest.raises(ConnectionError, match="Failed to connect"):
                            await client.execute_query("{ test }")
    
    @pytest.mark.asyncio
    async def test_execute_query_unexpected_error(self):
        """Test query handles unexpected errors."""
        # Arrange
        with patch('src.infrastructure.graphql_client.AIOHTTPTransport'):
            with patch('src.infrastructure.graphql_client.Client') as mock_client_class:
                with patch('src.infrastructure.graphql_client.gql'):
                    mock_client = AsyncMock()
                    mock_client.execute_async = AsyncMock(side_effect=ValueError("Unexpected"))
                    mock_client_class.return_value = mock_client
                    
                    client = CwayGraphQLClient("https://test.api/graphql", "test-token")
                    await client.connect()
                    
                    # Act & Assert
                    with pytest.raises(CwayAPIError, match="GraphQL query failed"):
                        await client.execute_query("{ test }")


class TestCwayGraphQLClientMutations:
    """Test GraphQL mutation execution."""
    
    @pytest.mark.asyncio
    async def test_execute_mutation(self):
        """Test mutation execution."""
        # Arrange
        with patch('src.infrastructure.graphql_client.AIOHTTPTransport'):
            with patch('src.infrastructure.graphql_client.Client') as mock_client_class:
                with patch('src.infrastructure.graphql_client.gql'):
                    mock_client = AsyncMock()
                    mock_client.execute_async = AsyncMock(return_value={"mutate": "success"})
                    mock_client_class.return_value = mock_client
                    
                    client = CwayGraphQLClient("https://test.api/graphql", "test-token")
                    await client.connect()
                    
                    # Act
                    result = await client.execute_mutation("mutation { test }")
                    
                    # Assert
                    assert result == {"mutate": "success"}
    
    @pytest.mark.asyncio
    async def test_execute_mutation_with_variables(self):
        """Test mutation with variables."""
        # Arrange
        with patch('src.infrastructure.graphql_client.AIOHTTPTransport'):
            with patch('src.infrastructure.graphql_client.Client') as mock_client_class:
                with patch('src.infrastructure.graphql_client.gql'):
                    mock_client = AsyncMock()
                    mock_client.execute_async = AsyncMock(return_value={"mutate": "success"})
                    mock_client_class.return_value = mock_client
                    
                    client = CwayGraphQLClient("https://test.api/graphql", "test-token")
                    await client.connect()
                    
                    # Act
                    result = await client.execute_mutation(
                        "mutation($input: Input!) { test(input: $input) }",
                        {"input": {"field": "value"}}
                    )
                    
                    # Assert
                    assert result == {"mutate": "success"}


class TestCwayGraphQLClientSchema:
    """Test schema introspection."""
    
    @pytest.mark.asyncio
    async def test_get_schema_success(self):
        """Test getting schema via introspection."""
        # Arrange
        with patch('src.infrastructure.graphql_client.AIOHTTPTransport'):
            with patch('src.infrastructure.graphql_client.Client') as mock_client_class:
                with patch('src.infrastructure.graphql_client.gql'):
                    mock_client = AsyncMock()
                    mock_schema = {
                        "__schema": {
                            "types": [{"name": "Query"}]
                        }
                    }
                    mock_client.execute_async = AsyncMock(return_value=mock_schema)
                    mock_client_class.return_value = mock_client
                    
                    client = CwayGraphQLClient("https://test.api/graphql", "test-token")
                    await client.connect()
                    
                    # Act
                    result = await client.get_schema()
                    
                    # Assert
                    assert result == {"types": [{"name": "Query"}]}
    
    @pytest.mark.asyncio
    async def test_get_schema_failure(self):
        """Test schema introspection failure."""
        # Arrange
        with patch('src.infrastructure.graphql_client.AIOHTTPTransport'):
            with patch('src.infrastructure.graphql_client.Client') as mock_client_class:
                with patch('src.infrastructure.graphql_client.gql'):
                    mock_client = AsyncMock()
                    mock_client.execute_async = AsyncMock(side_effect=Exception("Schema error"))
                    mock_client_class.return_value = mock_client
                    
                    client = CwayGraphQLClient("https://test.api/graphql", "test-token")
                    await client.connect()
                    
                    # Act
                    result = await client.get_schema()
                    
                    # Assert
                    assert result is None


class TestCwayAPIError:
    """Test CwayAPIError exception."""
    
    def test_cway_api_error_creation(self):
        """Test creating CwayAPIError."""
        # Act
        error = CwayAPIError("Test error message")
        
        # Assert
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)
    
    def test_cway_api_error_raise(self):
        """Test raising CwayAPIError."""
        # Act & Assert
        with pytest.raises(CwayAPIError, match="Test error"):
            raise CwayAPIError("Test error")
