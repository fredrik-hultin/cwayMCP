"""Unit tests for WebSocket server."""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

import pytest

from src.utils.websocket_server import (
    WebSocketLogServer,
    get_websocket_server,
    initialize_websocket_server,
    emit_log_to_dashboard,
    emit_flow_to_dashboard
)


class TestWebSocketLogServer:
    """Test WebSocket log server."""
    
    def test_server_initialization(self) -> None:
        """Test that server initializes correctly."""
        server = WebSocketLogServer(port=8081)
        
        assert server.port == 8081
        assert server.sio is not None
        assert server.app is not None
        assert isinstance(server.clients, set)
        assert len(server.clients) == 0
        assert isinstance(server.log_history, list)
        assert isinstance(server.flow_history, list)
        
    def test_server_default_port(self) -> None:
        """Test that server uses default port."""
        server = WebSocketLogServer()
        assert server.port == 8080
        
    async def test_emit_log(self) -> None:
        """Test emitting log messages."""
        server = WebSocketLogServer(port=8081)
        server.sio.emit = AsyncMock()
        
        # Add a mock client
        server.clients.add("test-client-1")
        
        await server.emit_log("INFO", "test-source", "test message", "req-123")
        
        # Verify log was added to history
        assert len(server.log_history) == 1
        assert server.log_history[0]["level"] == "INFO"
        assert server.log_history[0]["source"] == "test-source"
        assert server.log_history[0]["message"] == "test message"
        assert server.log_history[0]["requestId"] == "req-123"
        
        # Verify emit was called
        server.sio.emit.assert_called_once()
        
    async def test_emit_log_history_limit(self) -> None:
        """Test that log history is limited."""
        server = WebSocketLogServer(port=8081)
        server.sio.emit = AsyncMock()
        
        # Add logs beyond limit (1000 triggers trim, then one more)
        for i in range(1001):
            await server.emit_log("INFO", "test", f"message {i}")
            
        # Should be trimmed to 500
        assert len(server.log_history) <= 501  # Last one after trim
        
    async def test_emit_log_without_clients(self) -> None:
        """Test emitting log without connected clients."""
        server = WebSocketLogServer(port=8081)
        server.sio.emit = AsyncMock()
        
        await server.emit_log("INFO", "test", "message")
        
        # Log should be stored but not emitted
        assert len(server.log_history) == 1
        server.sio.emit.assert_not_called()
        
    async def test_emit_flow(self) -> None:
        """Test emitting flow messages."""
        server = WebSocketLogServer(port=8081)
        server.sio.emit = AsyncMock()
        server.clients.add("test-client-1")
        
        await server.emit_flow(
            request_id="req-123",
            step="step-1",
            source="MCP Client",
            target="GraphQL API",
            operation="query",
            status="success",
            duration=0.5,
            details={"query": "projects"}
        )
        
        # Verify flow was added to history
        assert len(server.flow_history) == 1
        assert server.flow_history[0]["requestId"] == "req-123"
        assert server.flow_history[0]["step"] == "step-1"
        assert server.flow_history[0]["status"] == "success"
        assert server.flow_history[0]["duration"] == 0.5
        
        # Verify emit was called
        server.sio.emit.assert_called_once()
        
    async def test_emit_flow_history_limit(self) -> None:
        """Test that flow history is limited."""
        server = WebSocketLogServer(port=8081)
        server.sio.emit = AsyncMock()
        
        # Add flows beyond limit (500 triggers trim, then one more)
        for i in range(501):
            await server.emit_flow(
                request_id=f"req-{i}",
                step="test",
                source="A",
                target="B",
                operation="test",
                status="success"
            )
            
        # Should be trimmed to 250 after hitting limit
        assert len(server.flow_history) <= 251  # Last one after trim
        
    async def test_emit_server_stats(self) -> None:
        """Test emitting server statistics."""
        server = WebSocketLogServer(port=8081)
        server.sio.emit = AsyncMock()
        server.clients.add("test-client-1")
        
        stats = {"requests": 100, "errors": 5}
        await server.emit_server_stats(stats)
        
        server.sio.emit.assert_called_once_with('server_stats', stats)
        
    async def test_emit_server_stats_without_clients(self) -> None:
        """Test emitting stats without clients."""
        server = WebSocketLogServer(port=8081)
        server.sio.emit = AsyncMock()
        
        await server.emit_server_stats({"requests": 100})
        
        server.sio.emit.assert_not_called()
        
    @patch('src.utils.websocket_server.web.AppRunner')
    @patch('src.utils.websocket_server.web.TCPSite')
    async def test_start_server(self, mock_tcp_site: MagicMock, mock_app_runner: MagicMock) -> None:
        """Test starting the server."""
        # Setup mocks
        mock_runner_instance = AsyncMock()
        mock_app_runner.return_value = mock_runner_instance
        
        mock_site_instance = AsyncMock()
        mock_tcp_site.return_value = mock_site_instance
        
        server = WebSocketLogServer(port=8081)
        runner = await server.start_server()
        
        # Verify setup was called
        mock_runner_instance.setup.assert_called_once()
        mock_site_instance.start.assert_called_once()
        assert runner == mock_runner_instance
        
    @patch('src.utils.websocket_server.web.AppRunner')
    async def test_start_server_error(self, mock_app_runner: MagicMock) -> None:
        """Test server start error handling."""
        mock_app_runner.return_value.setup.side_effect = Exception("Setup failed")
        
        server = WebSocketLogServer(port=8081)
        
        with pytest.raises(Exception, match="Setup failed"):
            await server.start_server()


class TestGlobalFunctions:
    """Test global WebSocket functions."""
    
    def test_get_websocket_server_none(self) -> None:
        """Test getting server when none exists."""
        # Reset global state
        import src.utils.websocket_server as ws_module
        ws_module._ws_server = None
        
        result = get_websocket_server()
        assert result is None
        
    @patch('src.utils.websocket_server.WebSocketLogServer')
    async def test_initialize_websocket_server(self, mock_server_class: MagicMock) -> None:
        """Test initializing the WebSocket server."""
        # Reset global state
        import src.utils.websocket_server as ws_module
        ws_module._ws_server = None
        
        mock_server = AsyncMock()
        mock_server.start_server = AsyncMock()
        mock_server_class.return_value = mock_server
        
        result = await initialize_websocket_server(8081)
        
        mock_server_class.assert_called_once_with(8081)
        mock_server.start_server.assert_called_once()
        assert result == mock_server
        
    @patch('src.utils.websocket_server.WebSocketLogServer')
    async def test_initialize_websocket_server_only_once(self, mock_server_class: MagicMock) -> None:
        """Test that server is only initialized once."""
        # Reset global state
        import src.utils.websocket_server as ws_module
        ws_module._ws_server = None
        
        mock_server = AsyncMock()
        mock_server.start_server = AsyncMock()
        mock_server_class.return_value = mock_server
        
        # Initialize twice
        result1 = await initialize_websocket_server(8081)
        result2 = await initialize_websocket_server(8081)
        
        # Should only create once
        mock_server_class.assert_called_once()
        assert result1 == result2
        
    async def test_emit_log_to_dashboard_with_server(self) -> None:
        """Test emitting log to dashboard."""
        import src.utils.websocket_server as ws_module
        
        # Setup mock server
        mock_server = AsyncMock()
        mock_server.emit_log = AsyncMock()
        ws_module._ws_server = mock_server
        
        await emit_log_to_dashboard("INFO", "test", "message", "req-123")
        
        mock_server.emit_log.assert_called_once_with("INFO", "test", "message", "req-123")
        
        # Cleanup
        ws_module._ws_server = None
        
    async def test_emit_log_to_dashboard_without_server(self) -> None:
        """Test emitting log when no server exists."""
        import src.utils.websocket_server as ws_module
        ws_module._ws_server = None
        
        # Should not raise error
        await emit_log_to_dashboard("INFO", "test", "message")
        
    async def test_emit_flow_to_dashboard_with_server(self) -> None:
        """Test emitting flow to dashboard."""
        import src.utils.websocket_server as ws_module
        
        # Setup mock server
        mock_server = AsyncMock()
        mock_server.emit_flow = AsyncMock()
        ws_module._ws_server = mock_server
        
        await emit_flow_to_dashboard(
            request_id="req-123",
            step="test",
            source="A",
            target="B",
            operation="query",
            status="success",
            duration=0.5,
            details={"key": "value"}
        )
        
        mock_server.emit_flow.assert_called_once()
        
        # Cleanup
        ws_module._ws_server = None
        
    async def test_emit_flow_to_dashboard_without_server(self) -> None:
        """Test emitting flow when no server exists."""
        import src.utils.websocket_server as ws_module
        ws_module._ws_server = None
        
        # Should not raise error
        await emit_flow_to_dashboard(
            request_id="req-123",
            step="test",
            source="A",
            target="B",
            operation="query",
            status="success"
        )
