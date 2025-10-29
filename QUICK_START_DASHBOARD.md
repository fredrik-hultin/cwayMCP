# Quick Start: Dashboard with Real-Time Logs

## The Fix

**Problem:** MCP server logs were only writing to files, not appearing in the React dashboard.

**Solution:** Added a custom `WebSocketLogHandler` that forwards Python logging to the WebSocket server, which then broadcasts to the React dashboard.

## How to Use

### Option 1: Test the Integration (Recommended First)

```bash
# Terminal 1: Run the test script
cd server
python3 test_dashboard_logging.py

# Terminal 2: Start React dashboard
cd client
npm start

# Open browser to http://localhost:3001
# You should see test logs appearing in real-time
```

### Option 2: Run Full MCP Server with Dashboard

```bash
# Terminal 1: Start server with dashboard
cd server
python3 start_server_with_dashboard.py

# Terminal 2: Start React dashboard  
cd client
npm start

# Terminal 3: Use MCP server (triggers logs)
# Your MCP client tool here - logs will appear in dashboard
```

### Option 3: Alternative Quick Start Scripts

```bash
# From project root - Server with dashboard
./start-dashboard.sh

# From project root - MCP server only
./start-mcp.sh
```

## What You'll See

When working correctly, you'll see in the dashboard:
- ✅ WebSocket connection status (Connected/Disconnected)
- 📝 Real-time log messages as they happen
- 🎨 Color-coded by level (INFO=green, WARNING=yellow, ERROR=red)
- ⏰ Timestamps for each log entry
- 📦 Source/logger name for each message

## Verify It's Working

1. **Check WebSocket server health:**
   ```bash
   curl http://localhost:8080/health
   # Should return: {"status":"healthy","clients":1}
   ```

2. **Watch server logs:**
   ```bash
   tail -f server/logs/cway_mcp_server.log
   # You should see logs being written
   ```

3. **Check browser console:**
   - Open http://localhost:3001
   - Open browser DevTools (F12)
   - Look for Socket.IO connection messages

## Troubleshooting

### Dashboard shows "Disconnected"
- Ensure WebSocket server is running: `lsof -ti:8080`
- Check for port conflicts
- Restart both server and client

### No logs appearing
- Verify WebSocket handler is attached (look for "🔗 Connecting logging system" message)
- Check log level: `export LOG_LEVEL=DEBUG`
- Make sure server is doing something that generates logs

### "python: command not found"
- Use `python3` instead of `python`
- Check Python version: `python3 --version` (needs 3.11+)

## What Changed

**Files Modified:**
- `server/src/utils/websocket_server.py` - Added `WebSocketLogHandler` class
- `server/start_server_with_dashboard.py` - Attached handlers to loggers

**Files Added:**
- `server/test_dashboard_logging.py` - Test script
- `DASHBOARD_LOGGING.md` - Full documentation
- `QUICK_START_DASHBOARD.md` - This file

## Next Steps

- Read full documentation: [DASHBOARD_LOGGING.md](./DASHBOARD_LOGGING.md)
- Customize which loggers to monitor in `start_server_with_dashboard.py`
- Adjust log levels per environment
- Add your own logging in MCP tools/use cases

## Questions?

See [DASHBOARD_LOGGING.md](./DASHBOARD_LOGGING.md) for:
- Complete architecture explanation
- Configuration options
- Performance tuning
- Future enhancements
