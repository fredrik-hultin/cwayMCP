#!/bin/bash
# Start the Cway MCP Server

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment
source "$SCRIPT_DIR/venv/bin/activate"

# Start the MCP server
cd "$SCRIPT_DIR/server"
python main.py --mode mcp
