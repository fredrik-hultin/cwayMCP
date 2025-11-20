"""WebSocket server for real-time log streaming to dashboard."""

import asyncio
import json
import logging
import sys
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
        self.client_info: Dict[str, Dict[str, Any]] = {}  # sid -> {ip, connected_at, user_agent}
        self.log_history: List[Dict[str, Any]] = []
        self.flow_history: List[Dict[str, Any]] = []
        
        self._setup_handlers()
        
    def _setup_handlers(self):
        """Set up WebSocket event handlers."""
        
        @self.sio.event
        async def connect(sid, environ):
            """Handle client connection."""
            # Extract client IP and info
            headers = environ.get('aiohttp.request', {}).headers if 'aiohttp.request' in environ else {}
            remote_addr = environ.get('REMOTE_ADDR', 'unknown')
            
            # Try to get real IP from headers (in case of proxy)
            client_ip = (
                headers.get('X-Forwarded-For', '').split(',')[0].strip() or
                headers.get('X-Real-IP', '') or
                remote_addr
            )
            
            user_agent = headers.get('User-Agent', 'unknown')
            
            self.clients.add(sid)
            self.client_info[sid] = {
                'ip': client_ip,
                'connected_at': datetime.now().isoformat(),
                'user_agent': user_agent
            }
            
            logger.info(f"Dashboard client connected: {sid} from {client_ip}")
            
            # Broadcast updated connection list to all clients
            await self._broadcast_connections()
            
            # Send historical data
            if self.log_history:
                await self.sio.emit('historical_logs', self.log_history[-50:], room=sid)
            if self.flow_history:
                await self.sio.emit('historical_flows', self.flow_history[-20:], room=sid)
            
        @self.sio.event
        async def disconnect(sid):
            """Handle client disconnection."""
            client_ip = self.client_info.get(sid, {}).get('ip', 'unknown')
            self.clients.discard(sid)
            self.client_info.pop(sid, None)
            logger.info(f"Dashboard client disconnected: {sid} from {client_ip}")
            
            # Broadcast updated connection list to all clients
            await self._broadcast_connections()
            
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
        return web.json_response({
            'status': 'healthy',
            'clients': len(self.clients),
            'connections': list(self.client_info.values())
        })
    
    async def _broadcast_connections(self):
        """Broadcast current connection list to all clients."""
        connections_data = [
            {
                'sid': sid,
                'ip': info['ip'],
                'connected_at': info['connected_at'],
                'user_agent': info['user_agent']
            }
            for sid, info in self.client_info.items()
        ]
        
        if self.clients:
            await self.sio.emit('connections_update', {
                'connections': connections_data,
                'total': len(connections_data)
            })
        
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


class WebSocketLogHandler(logging.Handler):
    """Logging handler that forwards log messages to WebSocket dashboard."""
    
    def __init__(self, ws_server: Optional[WebSocketLogServer] = None):
        super().__init__()
        self.ws_server = ws_server
        self._loop = None
        
    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record to the WebSocket server."""
        if not self.ws_server:
            return
            
        try:
            # Format the log message
            log_message = self.format(record)
            
            # Get or create event loop
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # No running loop, try to get the default one
                loop = asyncio.get_event_loop()
                
            # Create a task to emit the log
            if loop and loop.is_running():
                asyncio.create_task(
                    self.ws_server.emit_log(
                        level=record.levelname,
                        source=record.name,
                        message=log_message,
                        request_id=getattr(record, 'request_id', None)
                    )
                )
            else:
                # If no running loop, schedule it
                asyncio.ensure_future(
                    self.ws_server.emit_log(
                        level=record.levelname,
                        source=record.name,
                        message=log_message,
                        request_id=getattr(record, 'request_id', None)
                    ),
                    loop=loop
                )
        except Exception as e:
            # Silently fail to avoid breaking logging
            print(f"WebSocketLogHandler error: {e}", file=sys.stderr)


def add_websocket_handler_to_logger(logger_name: Optional[str] = None):
    """Add WebSocket handler to a logger."""
    if _ws_server:
        target_logger = logging.getLogger(logger_name) if logger_name else logging.getLogger()
        
        # Remove existing WebSocket handlers to avoid duplicates
        for handler in target_logger.handlers[:]:
            if isinstance(handler, WebSocketLogHandler):
                target_logger.removeHandler(handler)
        
        # Add new WebSocket handler
        ws_handler = WebSocketLogHandler(_ws_server)
        ws_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(message)s')
        ws_handler.setFormatter(formatter)
        target_logger.addHandler(ws_handler)
