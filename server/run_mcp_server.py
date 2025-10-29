#!/usr/bin/env python3
"""
MCP Server wrapper that ensures proper stdio handling.
Redirects all logging to stderr and files, keeping stdout clean for MCP protocol.
"""
import sys
import os
import logging

# Ensure logs directory exists
log_dir = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(log_dir, exist_ok=True)

# Configure root logger to ONLY use stderr and file, never stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "mcp_server.log")),
        logging.StreamHandler(sys.stderr)
    ],
    force=True  # Override any existing config
)

# Now import and run the server
if __name__ == "__main__":
    from src.presentation.cway_mcp_server import main
    main()
