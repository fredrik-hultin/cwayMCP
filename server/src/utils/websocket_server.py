"""WebSocket server for real-time log streaming to dashboard."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Set, Dict, Any, Optional, List
import socketio
from aiohttp import web
import uuid

logger = logging.getLogger(__name__)


class WebSocketLogServer:
    """WebSocket server for streaming logs and flow data to dashboard."""
    
    def __init__(self, port: int = 8080):
        self.port = port
        self.sio = socketio.AsyncServer(
            cors_allowed_origins="*",
            async_mode='aiohttp'
        )
        self.app = web.Application()
        self.sio.attach(self.app)
        self.clients: Set[str] = set()
        self.log_history: List[Dict[str, Any]] = []
        self.flow_history: List[Dict[str, Any]] = []
        
        self._setup_handlers()
        
    def _setup_handlers(self):
        """Set up WebSocket event handlers."""
        
        @self.sio.event
        async def connect(sid, environ):
            """Handle client connection."""
            self.clients.add(sid)
            logger.info(f"Dashboard client connected: {sid}")
            
            # Send historical data
            if self.log_history:
                await self.sio.emit('historical_logs', self.log_history[-50:], room=sid)
            if self.flow_history:
                await self.sio.emit('historical_flows', self.flow_history[-20:], room=sid)
            
        @self.sio.event
        async def disconnect(sid):
            """Handle client disconnection."""
            self.clients.discard(sid)
            logger.info(f"Dashboard client disconnected: {sid}")
            
        @self.sio.event
        async def request_historical_data(sid):
            """Send historical data to client."""
            logger.debug(f"Sending historical data to {sid}")
            
            if self.log_history:
                await self.sio.emit('historical_logs', self.log_history[-100:], room=sid)
            if self.flow_history:
                await self.sio.emit('historical_flows', self.flow_history[-50:], room=sid)
                
    async def start_server(self):
        """Start the WebSocket server."""
        try:
            # Add health check route
            self.app.router.add_get('/health', self._health_check)
            
            runner = web.AppRunner(self.app)
            await runner.setup()
            
            site = web.TCPSite(runner, 'localhost', self.port)
            await site.start()
            
            logger.info(f"🚀 WebSocket server started on http://localhost:{self.port}")
            return runner
            
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
            raise
            
    async def _health_check(self, request):
        """Health check endpoint."""
        return web.json_response({'status': 'healthy', 'clients': len(self.clients)})
        
    async def emit_log(self, level: str, source: str, message: str, request_id: Optional[str] = None):
        """Emit log message to all connected clients."""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'source': source,
            'message': message,
            'requestId': request_id
        }
        
        # Store in history
        self.log_history.append(log_data)
        if len(self.log_history) > 1000:
            self.log_history = self.log_history[-500:]  # Keep last 500
            
        # Emit to all clients
        if self.clients:
            await self.sio.emit('log_message', log_data)
            
    async def emit_flow(self, request_id: str, step: str, source: str, target: str, 
                       operation: str, status: str, duration: Optional[float] = None, 
                       details: Optional[Dict[str, Any]] = None):
        """Emit flow step to all connected clients."""
        flow_data = {
            'requestId': request_id,
            'step': step,
            'source': source,
            'target': target,
            'operation': operation,
            'status': status,
            'duration': duration,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        
        # Store in history
        self.flow_history.append(flow_data)
        if len(self.flow_history) > 500:
            self.flow_history = self.flow_history[-250:]  # Keep last 250
            
        # Emit to all clients
        if self.clients:
            await self.sio.emit('flow_message', flow_data)
            
    async def emit_server_stats(self, stats: Dict[str, Any]):
        """Emit server statistics to all connected clients."""
        if self.clients:
            await self.sio.emit('server_stats', stats)


# Global WebSocket server instance
_ws_server: Optional[WebSocketLogServer] = None


def get_websocket_server() -> Optional[WebSocketLogServer]:
    """Get the global WebSocket server instance."""
    return _ws_server


async def initialize_websocket_server(port: int = 8080) -> WebSocketLogServer:
    """Initialize and start the WebSocket server."""
    global _ws_server
    
    if _ws_server is None:
        _ws_server = WebSocketLogServer(port)
        await _ws_server.start_server()
        
    return _ws_server


async def emit_log_to_dashboard(level: str, source: str, message: str, request_id: Optional[str] = None):
    """Emit log message to dashboard if WebSocket server is available."""
    if _ws_server:
        await _ws_server.emit_log(level, source, message, request_id)


async def emit_flow_to_dashboard(request_id: str, step: str, source: str, target: str,
                                operation: str, status: str, duration: Optional[float] = None,
                                details: Optional[Dict[str, Any]] = None):
    """Emit flow step to dashboard if WebSocket server is available."""
    if _ws_server:
        await _ws_server.emit_flow(request_id, step, source, target, operation, status, duration, details)