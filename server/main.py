#!/usr/bin/env python3
"""
Main entry point for the Cway MCP Server.
Supports multiple modes: MCP stdio, REST API, or hybrid.
"""

import sys
import argparse
import logging
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import uvicorn
from config.settings import settings


def run_mcp_mode():
    """Run MCP server in stdio mode."""
    from src.presentation.cway_mcp_server import main as mcp_main
    mcp_main()


def run_rest_mode():
    """Run REST API server."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Cway REST API server...")
    logger.info(f"API Documentation: http://{settings.mcp_server_host}:{settings.mcp_server_port}/docs")
    logger.info(f"OpenAPI Spec: http://{settings.mcp_server_host}:{settings.mcp_server_port}/openapi.json")
    
    uvicorn.run(
        "src.presentation.rest_api:app",
        host=settings.mcp_server_host,
        port=settings.mcp_server_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )


def run_sse_mode():
    """Run SSE server for ChatGPT integration."""
    from start_mcp_sse import main as sse_main
    sse_main()


def run_dashboard_mode():
    """Run with WebSocket dashboard."""
    from start_server_with_dashboard import main as dashboard_main
    dashboard_main()


def main():
    """Main entry point with mode selection."""
    parser = argparse.ArgumentParser(
        description="Cway MCP Server - Multiple modes available"
    )
    parser.add_argument(
        "--mode",
        choices=["mcp", "rest", "sse", "dashboard"],
        default="mcp",
        help="Server mode: mcp (stdio), rest (API), sse (ChatGPT), or dashboard (with WebSocket)"
    )
    
    args = parser.parse_args()
    
    if args.mode == "mcp":
        run_mcp_mode()
    elif args.mode == "rest":
        run_rest_mode()
    elif args.mode == "sse":
        run_sse_mode()
    elif args.mode == "dashboard":
        run_dashboard_mode()


if __name__ == "__main__":
    main()
