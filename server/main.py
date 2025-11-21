#!/usr/bin/env python3
"""
Main entry point for the Cway MCP Server (SSE mode only).

This starts the MCP server with SSE transport for ChatGPT integration.
"""

import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from start_mcp_sse import main as sse_main


if __name__ == "__main__":
    sse_main()
