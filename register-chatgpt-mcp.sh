#!/bin/bash

# Register Cway MCP Server with ChatGPT Desktop App
# This script adds the MCP server configuration to ChatGPT's settings

set -e

PROJECT_DIR="/Users/fredrik.hultin/Developer/cwayMCP"
CHATGPT_CONFIG_DIR="$HOME/Library/Application Support/ChatGPT"
MCP_CONFIG_FILE="$CHATGPT_CONFIG_DIR/mcp_settings.json"

echo "🤖 Registering Cway MCP Server with ChatGPT Desktop App..."

# Ensure ChatGPT config directory exists
if [ ! -d "$CHATGPT_CONFIG_DIR" ]; then
    echo "❌ ChatGPT Desktop App configuration directory not found"
    echo "💡 Please ensure ChatGPT Desktop App is installed and has been run at least once"
    exit 1
fi

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

# Test that the server can start
echo "🧪 Testing server startup..."
cd "$PROJECT_DIR"
source venv/bin/activate
timeout 5 python "$PROJECT_DIR/server/main.py" --mode mcp &> /tmp/cway-test.log || true

if grep -q "Error" /tmp/cway-test.log; then
    echo "⚠️  Warning: Server test produced errors. Check /tmp/cway-test.log"
    echo "Continuing with registration anyway..."
fi

# Create or update MCP servers configuration
cat > "$MCP_CONFIG_FILE" << EOF
{
  "mcpServers": {
    "cway": {
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

echo "✅ Cway MCP Server registered with ChatGPT Desktop App!"
echo "📍 Configuration saved to: $MCP_CONFIG_FILE"
echo ""
echo "🎯 Next steps:"
echo "1. Restart ChatGPT Desktop App"
echo "2. Go to Settings → Features → Model Context Protocol"
echo "3. The 'cway' server should appear in the list"
echo "4. Enable the server if it's not already enabled"
echo ""
echo "🧪 Test with these prompts in ChatGPT:"
echo "  • 'Show me all active Cway projects'"
echo "  • 'What are the critical projects that need attention?'"
echo "  • 'Show me the temporal KPI dashboard'"
echo "  • 'What projects are at risk of stagnation?'"
echo ""
echo "🔍 Available resources:"
echo "  • cway://projects - All Cway planner projects"
echo "  • cway://users - All Cway users"
echo "  • cway://projects/active - Currently active projects"
echo "  • cway://projects/completed - Completed projects"
echo "  • cway://system/status - System connection status"
echo "  • cway://kpis/dashboard - KPI dashboard with health scores"
echo "  • cway://temporal-kpis/dashboard - Temporal analysis"
echo ""
echo "🛠️ Available tools:"
echo "  • list_projects - Retrieve all projects"
echo "  • get_project - Get specific project by ID"
echo "  • list_users - Retrieve all users"
echo "  • get_user - Get specific user by ID"
echo "  • find_user_by_email - Find user by email"
echo "  • get_system_status - Check system health"
echo "  • analyze_project_velocity - Analyze velocity trends"
echo "  • get_stagnation_alerts - Get stagnation risks"
echo ""
echo "📚 For detailed documentation, see: CHATGPT_SETUP.md"
