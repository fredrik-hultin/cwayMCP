# Connecting cwayMCP Server to Warp

## 🚀 Quick Connect

The MCP server is ready to connect to Warp. Here's how:

### Method 1: Using Warp's Settings (Recommended)

1. **Open Warp Settings**
   - Press `Cmd + ,` or go to Warp → Settings

2. **Navigate to MCP Servers**
   - Look for "MCP" or "Model Context Protocol" section
   - Click "Add Server" or "+"

3. **Configure the Server**
   - **Name**: `cway-mcp-server`
   - **Command**: `/Users/fredrik.hultin/Developer/cwayMCP/venv/bin/python`
   - **Args**: 
     ```
     /Users/fredrik.hultin/Developer/cwayMCP/server/main.py
     --mode
     mcp
     ```
   - **Working Directory**: `/Users/fredrik.hultin/Developer/cwayMCP`

4. **Environment Variables** (if needed):
   ```
   PYTHONPATH=/Users/fredrik.hultin/Developer/cwayMCP/server/src
   ```

5. **Save and Enable**

### Method 2: Using the Startup Script

1. **Test the script first**:
   ```bash
   /Users/fredrik.hultin/Developer/cwayMCP/start-mcp.sh
   ```

2. **In Warp Settings**:
   - **Command**: `/Users/fredrik.hultin/Developer/cwayMCP/start-mcp.sh`
   - **Args**: (leave empty)

### Method 3: Manual Configuration File

If Warp supports config file import, use:
```bash
/Users/fredrik.hultin/Developer/cwayMCP/mcp-server-config.json
```

## ✅ Verify Connection

Once connected, test in Warp:

1. **List Available Tools**:
   - The MCP server provides 9 tools
   - Look for: `list_projects`, `get_user`, `find_user_by_email`, etc.

2. **Test a Simple Query**:
   ```
   Use the list_projects tool
   ```

3. **Access Resources**:
   - `cway://projects` - All projects
   - `cway://users` - All users
   - `cway://system/status` - System status

## 🔧 Troubleshooting

### Server Won't Start in Warp

**Check logs:**
```bash
tail -f /Users/fredrik.hultin/Developer/cwayMCP/server/logs/cway-mcp.log
```

**Manual test:**
```bash
cd /Users/fredrik.hultin/Developer/cwayMCP/server
source ../venv/bin/activate
python main.py --mode mcp
```

### Connection Issues

**Verify Python path:**
```bash
/Users/fredrik.hultin/Developer/cwayMCP/venv/bin/python --version
```

**Check API token:**
```bash
grep CWAY_API_TOKEN /Users/fredrik.hultin/Developer/cwayMCP/server/.env
```

### Warp Can't Find the Server

Make sure:
- ✅ Virtual environment exists at `/Users/fredrik.hultin/Developer/cwayMCP/venv`
- ✅ Python is installed: `python --version` (requires 3.9+)
- ✅ Dependencies installed: `pip list | grep gql`
- ✅ `.env` file configured with API token

## 📊 Available Features

Once connected, you can:

### 🔨 Use Tools
- **list_projects** - Get all Cway projects
- **get_project** - Get specific project details
- **get_active_projects** - List active projects only
- **get_completed_projects** - List completed projects
- **list_users** - Get all users
- **get_user** - Get specific user by ID
- **find_user_by_email** - Find user by email
- **get_users_page** - Paginated user list
- **get_system_status** - Check system health

### 📚 Access Resources
- `cway://projects` - All project data
- `cway://users` - All user data
- `cway://projects/active` - Active projects only
- `cway://projects/completed` - Completed projects only
- `cway://system/status` - Connection status

## 🎯 Example Queries

Once connected in Warp, try:

```
"Show me all active Cway projects"
"Find user with email user@example.com"
"Get the status of project <project-id>"
"List all users in the system"
"What's the system status?"
```

## 📝 Configuration Details

**Server Path**: `/Users/fredrik.hultin/Developer/cwayMCP/server/main.py`
**Python Interpreter**: `/Users/fredrik.hultin/Developer/cwayMCP/venv/bin/python`
**Config File**: `/Users/fredrik.hultin/Developer/cwayMCP/mcp-server-config.json`
**Environment File**: `/Users/fredrik.hultin/Developer/cwayMCP/server/.env`

**API Endpoint**: `https://app.cway.se/graphql`
**Token**: Configured in `.env` file

## 🆘 Need Help?

1. **Check the logs**: `server/logs/cway-mcp.log`
2. **Run tests**: `cd server && pytest tests/unit/ -v`
3. **Test connection**: See `INSTALLATION.md`
4. **Server status**: `python main.py --mode mcp` should show connection success

---

**Status**: ✅ Ready to connect!

Your server is configured and tested. Just add it to Warp's MCP settings!
