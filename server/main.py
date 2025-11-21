#!/usr/bin/env python3
"""
Cway MCP Server with SSE transport for ChatGPT integration.

This implements the Model Context Protocol over Server-Sent Events (SSE),
which is required for ChatGPT's custom MCP server feature.
"""

import sys
import logging
import asyncio
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import uvicorn

from config.settings import settings
from src.presentation.cway_mcp_server import CwayMCPServer
from src.infrastructure.request_context import set_request_context, clear_request_context


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(settings.log_dir) / "mcp_server.log"),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware to extract and validate Bearer tokens from requests."""
    
    async def dispatch(self, request: Request, call_next):
        """Extract token from Authorization header, query param, or fallback to .env."""
        token = None
        user_identity = None
        user_tokens = None
        
        # Try 1: Extract Bearer token from Authorization header (for ChatGPT)
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            logger.debug(f"Extracted token from Authorization header: {token[:8]}...{token[-8:]}")
        
        # Try 2: Extract token from query parameter (for Warp terminal)
        elif "token" in request.query_params:
            token = request.query_params.get("token")
            logger.debug(f"Extracted token from query parameter: {token[:8]}...{token[-8:]}")
        
        # Token passthrough mode - no validation needed
        # The token will be validated by Cway API when actually used
        if token:
            logger.debug(f"Using token from request: {token[:8]}...{token[-8:]}")
        else:
            # No Authorization header - fall back to static token from .env
            logger.debug("No Authorization header, using fallback token from settings")
            if settings.cway_api_token:
                token = settings.cway_api_token
        
        # Set request context for this async context
        set_request_context(
            token=token,
            user=user_identity,
            user_tokens=user_tokens
        )
        
        try:
            response = await call_next(request)
            return response
        finally:
            clear_request_context()


def create_app():
    """Create the Starlette application."""
    # Create SSE transport
    sse = SseServerTransport("/messages")
    
    async def app_lifespan(app):
        """Lifespan context manager for the Starlette app."""
        logger.info("🚀 Starting MCP server...")
        mcp_server = CwayMCPServer()
        
        # Store in app state
        app.state.mcp_server = mcp_server
        app.state.sse = sse
        
        # Run MCP server in background task
        async def run_mcp():
            logger.info("✅ MCP server background task started")
            async with mcp_server.server.run(
                sse.read_stream,
                sse.write_stream,
                mcp_server.server.create_initialization_options()
            ):
                logger.info("✅ MCP server is running and ready")
                await asyncio.Event().wait()
        
        task = asyncio.create_task(run_mcp())
        
        # Give task a moment to start
        await asyncio.sleep(0.1)
        logger.info("="*60)
        logger.info("✅ MCP Server Ready")
        logger.info(f"SSE Endpoint: http://{settings.mcp_server_host}:{settings.mcp_server_port}/sse")
        logger.info(f"Messages: http://{settings.mcp_server_host}:{settings.mcp_server_port}/messages")
        logger.info("="*60)
        
        yield
        
        logger.info("🛑 Shutting down MCP server...")
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    
    # Create SSE handler
    async def sse_app(scope, receive, send):
        path = scope.get("path", "")
        if path == "/sse":
            # SSE event stream - keep connection alive
            logger.info("🔌 SSE connection established")
            async with sse.connect_sse(scope, receive, send):
                # Connection stays open until client disconnects
                await asyncio.Event().wait()
            logger.info("🔌 SSE connection closed")
        elif path == "/messages":
            await sse.handle_post_message(scope, receive, send)
        else:
            # 404 for unknown paths
            await send({
                'type': 'http.response.start',
                'status': 404,
                'headers': [[b'content-type', b'text/plain']],
            })
            await send({
                'type': 'http.response.body',
                'body': b'Not Found',
            })
    
    app = Starlette(
        routes=[Mount("/", app=sse_app)],
        middleware=[Middleware(AuthenticationMiddleware)],
        lifespan=app_lifespan
    )
    
    return app


if __name__ == "__main__":
    host = settings.mcp_server_host
    port = settings.mcp_server_port
    
    logger.info("="*60)
    logger.info("Cway MCP Server with SSE Transport")
    logger.info("="*60)
    logger.info(f"SSE Endpoint: http://{host}:{port}/sse")
    logger.info(f"Messages Endpoint: http://{host}:{port}/messages")
    logger.info("="*60)
    
    app = create_app()
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=settings.log_level.lower()
    )
