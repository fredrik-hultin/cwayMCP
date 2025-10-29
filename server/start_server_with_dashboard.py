#!/usr/bin/env python3
"""
Start the Cway MCP Server with WebSocket dashboard support.
This script starts both the MCP server and the WebSocket server for real-time dashboard updates.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config.settings import settings
from src.utils.logging_config import initialize_logging
from src.utils.websocket_server import initialize_websocket_server
from src.presentation.cway_mcp_server import CwayMCPServer


async def main():
    """Main entry point."""
    # Initialize logging
    initialize_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Starting Cway MCP Server with Dashboard Support")
    
    # Check required environment variables
    if not settings.cway_api_token:
        logger.error("❌ CWAY_API_TOKEN environment variable is required")
        logger.info("💡 Set it with: export CWAY_API_TOKEN='your_token_here'")
        return 1
        
    try:
        # Initialize WebSocket server for dashboard
        logger.info("🌐 Starting WebSocket server for dashboard...")
        ws_server = await initialize_websocket_server(port=8080)
        logger.info("✅ WebSocket server started on http://localhost:8080")
        
        # Initialize MCP server
        logger.info("🔧 Initializing MCP server...")
        mcp_server = CwayMCPServer()
        # The MCP server initializes on first use via _ensure_initialized()
        # Just log that it's ready
        
        logger.info("🎯 All servers initialized successfully!")
        logger.info("📊 Dashboard available at: http://localhost:3001")
        logger.info("🔌 WebSocket server at: http://localhost:8080")
        logger.info("🔑 Using Cway API: %s", settings.cway_api_url)
        logger.info("📝 Log level: %s", settings.log_level)
        logger.info("💡 MCP server ready to handle requests (will connect on first use)")
        
        # Keep the server running
        logger.info("✅ Servers are running. Press Ctrl+C to stop.")
        logger.info("💻 Open http://localhost:3001 in your browser to view the dashboard")
        while True:
            await asyncio.sleep(1)
        
    except KeyboardInterrupt:
        logger.info("🛑 Received shutdown signal")
    except Exception as e:
        logger.error("💥 Server error: %s", e)
        return 1
    finally:
        logger.info("🧹 Cleaning up...")
        
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)