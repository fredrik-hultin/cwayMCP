#!/usr/bin/env python3
"""Launch script for the Cway MCP server."""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.presentation.cway_mcp_server import main

if __name__ == "__main__":
    main()