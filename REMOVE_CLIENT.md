# 🗑️ Removing the React Client Dashboard

## Overview

The React client dashboard (`client/` directory) is **not required** for ChatGPT Desktop integration or for using the MCP server via stdio. It's only needed if you want the web-based real-time monitoring dashboard.

## Should You Remove It?

**Keep it if:**
- You want a web-based dashboard to monitor MCP server activity
- You're debugging and want to see real-time logs and request flows
- You're using the SSE server mode (not stdio)

**Remove it if:**
- You only use ChatGPT Desktop App (stdio mode)
- You don't need web-based monitoring
- You want to reduce project size and dependencies

## 🚀 Quick Removal

```bash
cd /Users/fredrik.hultin/Developer/cwayMCP

# Remove the client directory
rm -rf client/

# Remove client-related scripts
rm -f start-dashboard.sh

# Optional: Remove docker-compose if you don't use Docker
rm -f docker-compose.yml
```

## 🧹 Detailed Cleanup

### 1. Remove Client Directory

```bash
rm -rf /Users/fredrik.hultin/Developer/cwayMCP/client/
```

This removes:
- All React TypeScript code
- Node.js dependencies
- Build configuration
- ~150MB of node_modules

### 2. Remove Client-Related Scripts

```bash
cd /Users/fredrik.hultin/Developer/cwayMCP

# Remove dashboard startup script
rm -f start-dashboard.sh
```

### 3. Update .gitignore (Optional)

Edit `.gitignore` and remove client-specific entries (lines 325-340):

```bash
# You can remove these lines if desired:
# client/build/
# client/dist/
# client/.next/
# client/out/
# client/node_modules/
# client/.env
# client/.env.local
# client/npm-debug.log*
# client/yarn-debug.log*
# client/yarn-error.log*
```

### 4. Update README (Optional)

The main README.md contains references to the dashboard. You may want to:

1. Remove dashboard-related sections
2. Update quick start instructions to focus on stdio mode
3. Remove references to ports 3001 and 8080

Or simply note that the dashboard has been removed.

## ✅ What Remains

After removal, you'll have a clean MCP server setup:

```
cwayMCP/
├── server/                  # Python MCP Server (KEEP)
│   ├── src/                # Source code
│   ├── main.py            # Entry point
│   ├── .env               # Your configuration
│   └── requirements.txt   # Python dependencies
├── venv/                   # Virtual environment (KEEP)
├── start-mcp.sh           # MCP server launcher (KEEP)
├── register-chatgpt-mcp.sh # ChatGPT registration (KEEP)
├── CHATGPT_SETUP.md       # ChatGPT integration guide (KEEP)
└── README.md              # Project documentation (KEEP)
```

## 🧪 Verify Everything Works

After removal, test that the MCP server still works:

```bash
# Test server startup
./start-mcp.sh

# Press Ctrl+C after confirming it starts

# Register with ChatGPT (if not already done)
./register-chatgpt-mcp.sh

# Test in ChatGPT Desktop
# Try: "Show me all active Cway projects"
```

## 🔄 Restoring the Client

If you later decide you want the dashboard back:

1. Clone the repository fresh, or
2. Use `git checkout client/` to restore from version control

## 📊 Server Modes After Removal

You can still run the server in different modes:

### stdio Mode (for ChatGPT)
```bash
python server/main.py --mode mcp
```

### SSE Mode (HTTP server, no dashboard UI)
```bash
python server/main.py --mode sse --port 8000
```

### Dashboard Mode (will fail without client)
```bash
# Don't use this mode after removing the client
# python server/main.py --mode dashboard
```

## 💡 Alternative: Keep Client But Don't Install Dependencies

If you want to keep the client code but not install Node.js dependencies:

```bash
# Just don't run:
# cd client && npm install

# The client code will remain but won't be functional
```

This keeps the code for reference but avoids the large node_modules directory.

## 🆘 Issues After Removal?

If you encounter problems:

1. **Server won't start**: This shouldn't happen - the server is independent
2. **ChatGPT can't connect**: Check `register-chatgpt-mcp.sh` was run
3. **Missing dependencies**: Run `pip install -r server/requirements.txt`

The client removal should not affect MCP server functionality via stdio.
