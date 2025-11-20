# 🤖 ChatGPT Desktop App Integration Guide

## Overview

The ChatGPT desktop app only supports MCP servers via **stdio** (standard input/output), not HTTP/SSE. This guide shows how to configure the Cway MCP Server for ChatGPT desktop app integration.

## ✅ Prerequisites

- Python 3.9+ with pip
- Virtual environment (recommended)
- Cway API Access Token (Bearer token)
- ChatGPT Desktop App installed

## 🚀 Quick Setup

### 1. Project Setup

```bash
# Navigate to project root
cd /Users/fredrik.hultin/Developer/cwayMCP

# Create and activate virtual environment (if not already done)
python -m venv venv
source venv/bin/activate  # On macOS/Linux

# Install server dependencies
cd server && pip install -r requirements.txt && cd ..
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example server/.env

# Edit server/.env and add your Cway API token:
# CWAY_API_TOKEN=your_bearer_token_here
```

### 3. Test Server

```bash
# Test the server runs in stdio mode
./start-mcp.sh

# Or manually:
source venv/bin/activate
cd server && python main.py
```

Press `Ctrl+C` to stop the test.

## 🔧 ChatGPT Desktop Configuration

### Option 1: Using the Registration Script (Recommended)

```bash
# This script configures ChatGPT Desktop to use the MCP server
./register-chatgpt-mcp.sh
```

### Option 2: Manual Configuration

1. Open ChatGPT Desktop App
2. Go to **Settings** → **Features** → **Model Context Protocol**
3. Add a new server with these settings:

**Server Name:** `cway`

**Configuration:**
```json
{
  "command": "/Users/fredrik.hultin/Developer/cwayMCP/venv/bin/python",
  "args": [
    "/Users/fredrik.hultin/Developer/cwayMCP/server/main.py"
  ],
  "cwd": "/Users/fredrik.hultin/Developer/cwayMCP",
  "env": {
    "PYTHONPATH": "/Users/fredrik.hultin/Developer/cwayMCP/server/src"
  },
  "envFile": "/Users/fredrik.hultin/Developer/cwayMCP/server/.env"
}
```

4. Save and restart ChatGPT Desktop

## 📊 Available Features

### Resources

- `cway://projects` - All Cway planner projects
- `cway://users` - All Cway users
- `cway://projects/active` - Currently active projects
- `cway://projects/completed` - Completed projects
- `cway://system/status` - System connection status
- `cway://kpis/dashboard` - KPI dashboard with health scores
- `cway://kpis/project-health` - Project health scores
- `cway://kpis/critical-projects` - Projects requiring attention
- `cway://temporal-kpis/dashboard` - Temporal analysis dashboard
- `cway://temporal-kpis/stagnation-alerts` - Stagnation risk alerts

### Tools

- `list_projects` - Retrieve all projects
- `get_project` - Get specific project by ID
- `get_active_projects` - List active projects
- `get_completed_projects` - List completed projects
- `list_users` - Retrieve all users
- `get_user` - Get specific user by ID
- `find_user_by_email` - Find user by email
- `get_system_status` - Check system health
- `search_projects` - Search projects with query
- `search_users` - Search users by username
- `create_project` - Create a new project
- `update_project` - Update existing project
- `create_user` - Create a new user
- `analyze_project_velocity` - Analyze project velocity trends
- `get_stagnation_alerts` - Get projects at risk of stagnation

## 🧪 Testing the Integration

Once configured, try these prompts in ChatGPT:

1. **"Show me all active Cway projects"**
2. **"What are the critical projects that need attention?"**
3. **"Find user by email: user@example.com"**
4. **"Show me the temporal KPI dashboard"**
5. **"What projects are at risk of stagnation?"**

## 🔍 Troubleshooting

### Server Not Starting

```bash
# Check virtual environment
ls venv/bin/python

# Check dependencies
source venv/bin/activate
pip list | grep mcp

# Check environment file
cat server/.env
```

### ChatGPT Can't Connect

1. **Verify paths** - Ensure all paths in the configuration are absolute
2. **Check permissions** - Ensure the server files are executable
3. **Test manually** - Run `./start-mcp.sh` to verify server starts
4. **Check logs** - Look in `server/logs/mcp_server.log` for errors

### API Connection Issues

```bash
# Test API connectivity
source venv/bin/activate
cd server
python -c "
from config.settings import settings
print(f'API URL: {settings.cway_api_url}')
print(f'Token configured: {bool(settings.cway_api_token)}')
"
```

## 📁 Project Structure

```
cwayMCP/
├── server/                  # Python MCP Server
│   ├── src/                # Source code (Clean Architecture)
│   ├── main.py            # Entry point
│   ├── .env               # Your API credentials
│   └── requirements.txt   # Python dependencies
├── venv/                   # Virtual environment
├── start-mcp.sh           # Quick start script
└── register-chatgpt-mcp.sh # ChatGPT registration script
```

## 🚫 Client Dashboard (Not Needed for ChatGPT)

The React client dashboard (`client/` directory) is **not required** for ChatGPT Desktop integration. The ChatGPT app only communicates via stdio, not through a web interface.

If you don't need the dashboard for other purposes, you can safely ignore or remove the `client/` directory.

## 📚 Additional Resources

- [MCP Specification](https://modelcontextprotocol.io/)
- [ChatGPT Desktop MCP Documentation](https://help.openai.com/en/articles/model-context-protocol)
- Project README: [../README.md](README.md)

## 🆘 Getting Help

If you encounter issues:

1. Check `server/logs/mcp_server.log` for error messages
2. Verify environment variables in `server/.env`
3. Ensure virtual environment is activated
4. Test the server manually with `./start-mcp.sh`

## 🔐 Security Notes

- Keep your `CWAY_API_TOKEN` secure and never commit it to version control
- The `.env` file is already in `.gitignore`
- Use environment-specific tokens for development vs production
