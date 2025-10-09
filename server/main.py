#!/usr/bin/env python3
"""
Main entry point for the Cway MCP Server.
This script provides different ways to run the server:
- MCP server only
- MCP server with dashboard
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.presentation.cway_mcp_server import main as mcp_main


def main():
    """Main entry point with command line argument parsing."""
    parser = argparse.ArgumentParser(description="Cway MCP Server")
    parser.add_argument(
        "--mode",
        choices=["mcp", "dashboard"],
        default="mcp",
        help="Server mode: 'mcp' for MCP server only, 'dashboard' for server with dashboard"
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="Host to bind the server to (default: localhost)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the MCP server to (default: 8000)"
    )
    parser.add_argument(
        "--dashboard-port",
        type=int,
        default=8080,
        help="Port for the WebSocket dashboard server (default: 8080)"
    )
    
    args = parser.parse_args()
    
    if args.mode == "dashboard":
        # Import here to avoid loading dashboard dependencies if not needed
        from start_server_with_dashboard import main as dashboard_main
        asyncio.run(dashboard_main())
    else:
        # Run MCP server only
        mcp_main()


if __name__ == "__main__":
    main()