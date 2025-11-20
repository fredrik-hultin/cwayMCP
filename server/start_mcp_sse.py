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
from starlette.routing import Route
import uvicorn

from config.settings import settings
from src.presentation.cway_mcp_server import CwayMCPServer


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
    
    # Create Starlette app with SSE routes
    app = Starlette(
        routes=[
            Route("/sse", endpoint=sse.connect_sse),
            Route("/messages", endpoint=sse.handle_post_message, methods=["POST"]),
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
    
    # Run with uvicorn
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    main()
