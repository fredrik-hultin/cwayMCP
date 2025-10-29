#!/bin/bash
# Startup script for Cway MCP Server in SSE mode

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

PROJECT_DIR="/Users/fredrik.hultin/Developer/cwayMCP"
VENV_DIR="$PROJECT_DIR/venv"
SERVER_DIR="$PROJECT_DIR/server"
PYTHON="$VENV_DIR/bin/python"
PID_FILE="$SERVER_DIR/sse-server.pid"
LOG_FILE="$SERVER_DIR/logs/sse-server.log"

# Create logs directory if it doesn't exist
mkdir -p "$SERVER_DIR/logs"

# Function to check if server is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

# Function to start server
start_server() {
    if is_running; then
        echo -e "${YELLOW}Server is already running (PID: $(cat $PID_FILE))${NC}"
        exit 0
    fi
    
    echo -e "${GREEN}Starting Cway MCP Server (SSE mode)...${NC}"
    cd "$SERVER_DIR"
    
    # Start server in background
    nohup "$PYTHON" main.py --mode sse --host localhost --port 8000 >> "$LOG_FILE" 2>&1 &
    SERVER_PID=$!
    
    # Save PID
    echo $SERVER_PID > "$PID_FILE"
    
    # Wait a moment and check if it's running
    sleep 2
    if is_running; then
        echo -e "${GREEN}✓ Server started successfully (PID: $SERVER_PID)${NC}"
        echo -e "${GREEN}✓ Listening on http://localhost:8000/sse${NC}"
        echo -e "${YELLOW}  Logs: $LOG_FILE${NC}"
    else
        echo -e "${RED}✗ Server failed to start. Check logs: $LOG_FILE${NC}"
        exit 1
    fi
}

# Function to stop server
stop_server() {
    if ! is_running; then
        echo -e "${YELLOW}Server is not running${NC}"
        exit 0
    fi
    
    PID=$(cat "$PID_FILE")
    echo -e "${YELLOW}Stopping server (PID: $PID)...${NC}"
    kill "$PID"
    
    # Wait for process to stop
    for i in {1..10}; do
        if ! ps -p "$PID" > /dev/null 2>&1; then
            break
        fi
        sleep 1
    done
    
    # Force kill if still running
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}Force killing server...${NC}"
        kill -9 "$PID"
    fi
    
    rm -f "$PID_FILE"
    echo -e "${GREEN}✓ Server stopped${NC}"
}

# Function to restart server
restart_server() {
    stop_server
    sleep 2
    start_server
}

# Function to show status
show_status() {
    if is_running; then
        PID=$(cat "$PID_FILE")
        echo -e "${GREEN}✓ Server is running (PID: $PID)${NC}"
        echo -e "${GREEN}  URL: http://localhost:8000/sse${NC}"
        echo -e "${YELLOW}  Logs: $LOG_FILE${NC}"
    else
        echo -e "${RED}✗ Server is not running${NC}"
    fi
}

# Function to show logs
show_logs() {
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        echo -e "${RED}No log file found${NC}"
    fi
}

# Main command handler
case "$1" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        restart_server
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start    - Start the SSE server"
        echo "  stop     - Stop the SSE server"
        echo "  restart  - Restart the SSE server"
        echo "  status   - Show server status"
        echo "  logs     - Tail server logs"
        exit 1
        ;;
esac
