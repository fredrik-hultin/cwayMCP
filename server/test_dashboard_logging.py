#!/usr/bin/env python3
"""
Test script to verify that logs are being sent to the dashboard.
This simulates MCP server logging to verify WebSocket integration.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.websocket_server import initialize_websocket_server, add_websocket_handler_to_logger
from config.settings import settings


async def test_dashboard_logging():
    """Test dashboard logging integration."""
    # Initialize logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("🧪 Starting dashboard logging test...")
    
    # Initialize WebSocket server
    logger.info("🌐 Starting WebSocket server on port 8080...")
    ws_server = await initialize_websocket_server(port=8080)
    logger.info("✅ WebSocket server started")
    
    # Attach WebSocket handler to loggers
    logger.info("🔗 Connecting logging system to dashboard...")
    add_websocket_handler_to_logger()  # Root logger
    add_websocket_handler_to_logger(__name__)  # This test logger
    logger.info("✅ Dashboard logging integration complete")
    
    # Test different log levels
    logger.info("=" * 80)
    logger.info("📊 Testing different log levels - check dashboard at http://localhost:3001")
    logger.info("=" * 80)
    
    await asyncio.sleep(1)
    
    test_logger = logging.getLogger("test.component")
    
    logger.debug("🔍 This is a DEBUG message")
    await asyncio.sleep(0.5)
    
    logger.info("ℹ️  This is an INFO message")
    await asyncio.sleep(0.5)
    
    logger.warning("⚠️  This is a WARNING message")
    await asyncio.sleep(0.5)
    
    logger.error("❌ This is an ERROR message")
    await asyncio.sleep(0.5)
    
    # Test with different sources
    test_logger.info("📦 This is from a different logger (test.component)")
    await asyncio.sleep(0.5)
    
    graphql_logger = logging.getLogger("src.infrastructure.graphql_client")
    graphql_logger.info("🔌 Simulating GraphQL client log")
    await asyncio.sleep(0.5)
    
    mcp_logger = logging.getLogger("src.presentation.cway_mcp_server")
    mcp_logger.info("🛠️  Simulating MCP server tool call")
    await asyncio.sleep(0.5)
    
    logger.info("=" * 80)
    logger.info("✅ Test complete! All log messages should appear in the dashboard.")
    logger.info("💡 Open http://localhost:3001 to view the dashboard")
    logger.info("🔄 Server will continue running. Press Ctrl+C to stop.")
    logger.info("=" * 80)
    
    # Keep server running
    try:
        while True:
            await asyncio.sleep(10)
            logger.info("💓 Server heartbeat - still running...")
    except KeyboardInterrupt:
        logger.info("🛑 Test stopped by user")


if __name__ == "__main__":
    try:
        asyncio.run(test_dashboard_logging())
    except KeyboardInterrupt:
        print("\n👋 Test complete!")
        sys.exit(0)
