#!/usr/bin/env python3
"""
MCP Server with SSE transport for ChatGPT custom MCP connector integration.

This implements the Model Context Protocol over Server-Sent Events (SSE),
which is required for ChatGPT's custom MCP server feature.

NOTE: This is different from the REST API (rest_api.py) which is for
ChatGPT GPT custom actions, not MCP.
"""

import sys
import logging
import asyncio
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import uvicorn

from config.settings import settings
from src.presentation.cway_mcp_server import CwayMCPServer
from src.infrastructure.request_context import set_request_context, clear_request_context
from src.infrastructure.user_identity import get_identity_extractor
from src.infrastructure.token_store import get_token_store


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(settings.log_dir) / "mcp_sse.log"),
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
        
        # Validate token if we have one (from either source)
        if token:
            try:
                # Validate token and get user identity
                identity_extractor = get_identity_extractor()
                user_identity = await identity_extractor.get_user_identity(token)
                logger.info(f"Authenticated user: {user_identity.user_id} (org: {user_identity.org_name})")
                
                # Load all registered tokens for this user
                token_store = get_token_store()
                user_tokens = token_store.get_user_tokens(user_identity.user_id)
                
                # Include the primary token in user_tokens if not already present
                if user_identity.org_name not in user_tokens:
                    user_tokens[user_identity.org_name] = token
                
                logger.debug(f"Loaded {len(user_tokens)} org tokens for user {user_identity.user_id}")
                
            except Exception as e:
                logger.error(f"Token validation failed: {e}")
                # Continue without user identity - will fall back to .env token
        
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
            # Process request
            response = await call_next(request)
            return response
        finally:
            # Clear request context after request completes
            clear_request_context()


def create_server():
    """Create and configure the MCP server instance."""
    return CwayMCPServer()


async def app_lifespan(app):
    """Lifespan context manager for the Starlette app."""
    # Create MCP server and transport on startup
    mcp_server = create_server()
    sse = SseServerTransport("/messages")
    
    # Store in app state
    app.state.mcp_server = mcp_server
    app.state.sse = sse
    
    # Run MCP server in background
    async def run_mcp():
        async with mcp_server.server.run(
            sse.read_stream,
            sse.write_stream,
            mcp_server.server.create_initialization_options()
        ):
            await asyncio.Event().wait()
    
    task = asyncio.create_task(run_mcp())
    
    yield
    
    # Cleanup on shutdown
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


def create_app():
    """Create the Starlette application."""
    # Create SSE transport  
    sse = SseServerTransport("/messages")
    
    # Create wrapper app for SSE handlers
    async def sse_app(scope, receive, send):
        path = scope.get("path", "")
        if path == "/sse":
            # connect_sse returns a context manager
            handler = sse.connect_sse(scope, receive, send)
            async with handler:
                pass  # The context manager handles the SSE connection
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
    
    # Wrap with middleware
    from starlette.applications import Starlette
    app = Starlette(
        routes=[
            Mount("/", app=sse_app)
        ],
        middleware=[
            Middleware(AuthenticationMiddleware)
        ],
        lifespan=app_lifespan
    )
    
    return app


def main():
    """
    Run the MCP server with SSE transport.
    
    This creates an HTTP server that:
    1. Serves SSE connections at /sse
    2. Receives JSON-RPC messages at /messages (POST)
    3. Follows the MCP protocol specification
    """
    host = settings.mcp_server_host
    port = settings.mcp_server_port
    
    logger.info("="*60)
    logger.info("Starting Cway MCP Server with SSE Transport")
    logger.info("="*60)
    logger.info(f"SSE Endpoint: http://{host}:{port}/sse")
    logger.info(f"Messages Endpoint: http://{host}:{port}/messages")
    logger.info(f"")
    logger.info("For ChatGPT Custom MCP Connector:")
    logger.info(f"  MCP Server URL: http://{host}:{port}/sse")
    logger.info(f"  Authentication: None (use OAuth if needed)")
    logger.info("="*60)
    
    # Create and run app
    app = create_app()
    
    # Run with uvicorn (no reload support with app instance)
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    main()
