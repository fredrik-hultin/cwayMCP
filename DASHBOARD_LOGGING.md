# Dashboard Logging Integration

## Overview

The Cway MCP Server now forwards all Python logging messages to the React dashboard in real-time via WebSocket connection.

## How It Works

### Architecture

1. **WebSocket Server** (`src/utils/websocket_server.py`)
   - Runs on port 8080
   - Handles Socket.IO connections from the React dashboard
   - Provides `emit_log()` method to broadcast log messages

2. **WebSocketLogHandler** (Custom logging handler)
   - Extends Python's `logging.Handler`
   - Intercepts log records from Python's logging system
   - Forwards them asynchronously to the WebSocket server

3. **Integration** (`start_server_with_dashboard.py`)
   - Initializes WebSocket server
   - Attaches `WebSocketLogHandler` to relevant loggers
   - Connects Python logging → WebSocket → React dashboard

### Log Flow

```
MCP Server Code
    ↓
Python logger.info("message")
    ↓
WebSocketLogHandler.emit()
    ↓
WebSocket Server.emit_log()
    ↓
Socket.IO (port 8080)
    ↓
React Dashboard (port 3001)
    ↓
Display in UI
```

## Usage

### Starting the Server with Dashboard

```bash
# Terminal 1: Start server with WebSocket dashboard
cd server
python3 start_server_with_dashboard.py

# Terminal 2: Start React dashboard
cd client
npm start
```

### Testing the Integration

```bash
# Run the test script to verify logging
cd server
python3 test_dashboard_logging.py
```

This will:
- Start the WebSocket server
- Send test log messages at different levels (DEBUG, INFO, WARNING, ERROR)
- Display them in the dashboard at http://localhost:3001

## Configuration

### Loggers Monitored

The following loggers have WebSocket handlers attached:

- **Root logger** - Captures all logs from any module
- `src.presentation.cway_mcp_server` - MCP server operations
- `src.infrastructure.graphql_client` - GraphQL API calls
- `src.application` - Application layer use cases

### Adding More Loggers

To monitor additional loggers, add them in `start_server_with_dashboard.py`:

```python
add_websocket_handler_to_logger('your.logger.name')
```

## Dashboard Features

### Real-Time Log Streaming

- All log messages appear instantly in the dashboard
- Color-coded by log level (DEBUG=cyan, INFO=green, WARNING=yellow, ERROR=red)
- Shows timestamp, source, and message

### Log History

- Dashboard receives last 50 logs on connection
- Maintains up to 1000 logs in memory
- Request more with `request_historical_data` event

### Filtering

The React dashboard can filter logs by:
- Log level
- Source/logger name
- Time range

## Technical Details

### Async Handling

The `WebSocketLogHandler` handles async operations gracefully:

```python
# Gets the current event loop
loop = asyncio.get_running_loop()

# Creates a task without blocking the logger
asyncio.create_task(
    self.ws_server.emit_log(...)
)
```

This ensures logging never blocks the MCP server's main operations.

### Error Resilience

If the WebSocket server is unavailable:
- Logs still write to files and console
- No errors are raised
- Handler fails silently to avoid breaking the application

### Socket.IO Events

**Emitted by server:**
- `log_message` - Single log entry
- `historical_logs` - Batch of past logs
- `flow_message` - Request flow tracking
- `server_stats` - Server metrics

**Received from client:**
- `connect` - Client connected
- `disconnect` - Client disconnected
- `request_historical_data` - Request log history

## Troubleshooting

### Logs not appearing in dashboard

1. **Check WebSocket server is running:**
   ```bash
   curl http://localhost:8080/health
   ```
   Should return: `{"status":"healthy","clients":0}`

2. **Verify React dashboard connected:**
   - Open browser console at http://localhost:3001
   - Look for Socket.IO connection messages

3. **Check server logs:**
   ```bash
   tail -f server/logs/cway_mcp_server.log
   ```

### Dashboard shows "Disconnected"

- Ensure WebSocket server is running on port 8080
- Check for port conflicts: `lsof -ti:8080`
- Verify CORS settings allow connection from localhost:3001

### Performance Issues

If logging causes performance problems:

1. **Reduce log level:**
   ```bash
   export LOG_LEVEL=INFO  # Instead of DEBUG
   ```

2. **Disable specific loggers:**
   ```python
   # Remove handlers from verbose loggers
   logging.getLogger('verbose.logger').handlers.clear()
   ```

3. **Limit WebSocket handler:**
   ```python
   ws_handler.setLevel(logging.WARNING)  # Only warnings and errors
   ```

## Future Enhancements

- [ ] Log filtering in the dashboard
- [ ] Export logs to file from dashboard
- [ ] Request ID tracking across distributed logs
- [ ] Performance metrics visualization
- [ ] Alert notifications for ERROR level logs
- [ ] Log search functionality
- [ ] Multiple dashboard clients simultaneously

## Related Files

- `server/src/utils/websocket_server.py` - WebSocket server and handler
- `server/start_server_with_dashboard.py` - Integration setup
- `server/test_dashboard_logging.py` - Test script
- `client/src/services/websocketService.ts` - React dashboard client
- `client/src/components/SimpleDashboard.tsx` - Dashboard UI
