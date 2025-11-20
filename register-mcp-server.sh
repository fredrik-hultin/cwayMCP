#!/bin/bash

# Register Cway MCP Server with Warp
# This script adds the MCP server configuration to Warp's settings

set -e

PROJECT_DIR="/Users/fredrik.hultin/Developer/cwayMCP"
WARP_CONFIG_DIR="$HOME/.config/warp-terminal"
MCP_CONFIG_FILE="$WARP_CONFIG_DIR/mcp_servers.json"

echo "🔧 Registering Cway MCP Server with Warp..."

# Ensure Warp config directory exists
mkdir -p "$WARP_CONFIG_DIR"

# Check if virtual environment exists
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo "❌ Virtual environment not found at $PROJECT_DIR/venv"
    echo "💡 Please run: python -m venv venv && source venv/bin/activate && pip install -r server/requirements.txt"
    exit 1
fi

# Check if .env file exists
if [ ! -f "$PROJECT_DIR/server/.env" ]; then
    echo "❌ Environment file not found at $PROJECT_DIR/server/.env"
    echo "💡 Please copy .env.example to server/.env and configure CWAY_API_TOKEN"
    exit 1
fi

# Create or update MCP servers configuration
cat > "$MCP_CONFIG_FILE" << EOF
{
  "mcpServers": {
    "cway": {
      "name": "Cway MCP Server",
      "description": "MCP server for Cway GraphQL API integration (stdio mode)",
      "command": "$PROJECT_DIR/venv/bin/python",
      "args": [
        "$PROJECT_DIR/server/main.py"
      ],
      "cwd": "$PROJECT_DIR",
      "env": {
        "PYTHONPATH": "$PROJECT_DIR/server/src"
      },
      "envFile": "$PROJECT_DIR/server/.env"
    }
  }
}
EOF

echo "✅ Cway MCP Server registered with Warp!"
echo "📍 Configuration saved to: $MCP_CONFIG_FILE"
echo ""
echo "🎯 Next steps:"
echo "1. Restart Warp terminal"
echo "2. The MCP server should now be available in Warp's MCP settings"
echo "3. You can start the server with: python server/main.py --mode mcp"
echo "4. Or with dashboard: python server/main.py --mode dashboard"
echo ""
echo "🔍 Available resources:"
echo "  • cway://projects - All Cway planner projects"
echo "  • cway://users - All Cway users"  
echo "  • cway://projects/active - Currently active projects"
echo "  • cway://projects/completed - Completed projects"
echo "  • cway://system/status - System connection status"
echo ""
echo "🛠️ Available tools:"
echo "  • list_projects - Retrieve all projects"
echo "  • get_project - Get specific project by ID"
echo "  • list_users - Retrieve all users"
echo "  • get_user - Get specific user by ID"
echo "  • find_user_by_email - Find user by email"
echo "  • get_system_status - Check system health"
echo ""
echo "📊 Dashboard available at: http://localhost:3001 (when using --mode dashboard)"