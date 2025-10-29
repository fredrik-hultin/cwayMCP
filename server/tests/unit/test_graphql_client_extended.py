"""Extended tests for GraphQL client to improve coverage."""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from gql.transport.exceptions import TransportError

from src.infrastructure.graphql_client import CwayGraphQLClient, CwayAPIError


class TestGraphQLClientExtended:
    """Extended GraphQL client tests for edge cases."""
    
    @pytest.mark.asyncio
    async def test_connect_failure(self) -> None:
        """Test connection failure handling."""
        with patch('src.infrastructure.graphql_client.settings') as mock_settings:
            mock_settings.cway_api_url = "https://test.com"
            mock_settings.cway_api_token = "token"
            mock_settings.request_timeout = 30
            
            client = CwayGraphQLClient()
            
            with patch('src.infrastructure.graphql_client.AIOHTTPTransport') as MockTransport:
                MockTransport.side_effect = Exception("Connection error")
                
                with pytest.raises(Exception, match="Connection error"):
                    await client.connect()
    
    @pytest.mark.asyncio
    async def test_execute_query_retry_exponential_backoff(self) -> None:
        """Test exponential backoff in retry logic."""
        with patch('src.infrastructure.graphql_client.settings') as mock_settings:
            mock_settings.max_retries = 3
            
            client = CwayGraphQLClient()
            mock_client = AsyncMock()
            mock_client.execute_async.side_effect = TransportError("Temporary failure")
            client._client = mock_client
            
            with patch('src.infrastructure.graphql_client.gql') as mock_gql:
                with patch('src.infrastructure.graphql_client.asyncio.sleep') as mock_sleep:
                    mock_gql.return_value = "query"
                    
                    with pytest.raises(ConnectionError):
                        await client.execute_query("{ test }")
                    
                    # Verify exponential backoff: 2^0, 2^1
                    calls = mock_sleep.call_args_list
                    assert len(calls) == 2
                    assert calls[0][0][0] == 1  # 2^0
                    assert calls[1][0][0] == 2  # 2^1
    
    @pytest.mark.asyncio
    async def test_execute_query_single_attempt_success(self) -> None:
        """Test successful query on first attempt."""
        with patch('src.infrastructure.graphql_client.settings') as mock_settings:
            mock_settings.max_retries = 1
            
            client = CwayGraphQLClient()
            mock_client = AsyncMock()
            result = {"data": "test"}
            mock_client.execute_async.return_value = result
            client._client = mock_client
            
            with patch('src.infrastructure.graphql_client.gql') as mock_gql:
                mock_gql.return_value = "query"
                
                response = await client.execute_query("{ test }")
                assert response == result
                assert mock_client.execute_async.call_count == 1
    
    @pytest.mark.asyncio
    async def test_get_schema_empty_result(self) -> None:
        """Test schema introspection with empty result."""
        client = CwayGraphQLClient()
        
        with patch.object(client, 'execute_query') as mock_execute:
            mock_execute.return_value = {}  # No __schema key
            
            result = await client.get_schema()
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_execute_mutation_with_error(self) -> None:
        """Test mutation execution that fails."""
        client = CwayGraphQLClient()
        
        with patch.object(client, 'execute_query') as mock_execute:
            mock_execute.side_effect = CwayAPIError("Mutation failed")
            
            with pytest.raises(CwayAPIError, match="Mutation failed"):
                await client.execute_mutation("mutation { test }")
    
    @pytest.mark.asyncio
    async def test_execute_query_with_none_client_then_connect_fails(self) -> None:
        """Test query execution when connect fails during auto-connect."""
        client = CwayGraphQLClient()
        client._client = None
        
        with patch.object(client, 'connect') as mock_connect:
            mock_connect.side_effect = Exception("Connect failed")
            
            with pytest.raises(Exception, match="Connect failed"):
                await client.execute_query("{ test }")


class TestCwayAPIErrorExtended:
    """Extended tests for CwayAPIError."""
    
    def test_error_with_nested_exception(self) -> None:
        """Test CwayAPIError with nested exception."""
        try:
            raise ValueError("Original error")
        except ValueError as e:
            error = CwayAPIError("Wrapped error")
            error.__cause__ = e
            assert str(error) == "Wrapped error"
            assert error.__cause__ is not None
    
    def test_error_inheritance(self) -> None:
        """Test that CwayAPIError inherits from Exception."""
        error = CwayAPIError("Test")
        assert isinstance(error, Exception)
        assert isinstance(error, CwayAPIError)
