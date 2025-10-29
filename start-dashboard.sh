#!/bin/bash

# Start script for Cway MCP Server with Dashboard
# This script starts both the backend server and React dashboard

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_DIR="$PROJECT_ROOT/server"
CLIENT_DIR="$PROJECT_ROOT/client"

echo -e "${BLUE}🚀 Starting Cway MCP Server with Dashboard${NC}"
echo ""

# Check if .env exists
if [ ! -f "$SERVER_DIR/.env" ]; then
    echo -e "${YELLOW}⚠️  Warning: $SERVER_DIR/.env file not found${NC}"
    echo "Please copy .env.example to .env and configure your CWAY_API_TOKEN"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    echo -e "${YELLOW}⚠️  Warning: Virtual environment not found${NC}"
    echo "Please run: python -m venv venv && source venv/bin/activate && pip install -r server/requirements.txt"
    exit 1
fi

# Check if node_modules exists
if [ ! -d "$CLIENT_DIR/node_modules" ]; then
    echo -e "${YELLOW}⚠️  Warning: Node modules not found${NC}"
    echo "Installing client dependencies..."
    cd "$CLIENT_DIR"
    npm install
    cd "$PROJECT_ROOT"
fi

echo -e "${GREEN}✓ Pre-flight checks passed${NC}"
echo ""

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Shutting down servers...${NC}"
    jobs -p | xargs -r kill 2>/dev/null || true
    wait 2>/dev/null || true
    echo -e "${GREEN}✓ Servers stopped${NC}"
    exit 0
}

trap cleanup EXIT INT TERM

# Start backend server with dashboard
echo -e "${BLUE}📡 Starting backend server on http://localhost:8080${NC}"
cd "$PROJECT_ROOT"
source venv/bin/activate
cd "$SERVER_DIR"
python main.py --mode dashboard > /tmp/cway-backend.log 2>&1 &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 3

# Check if backend is still running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Backend server failed to start. Check /tmp/cway-backend.log${NC}"
    cat /tmp/cway-backend.log
    exit 1
fi

echo -e "${GREEN}✓ Backend server started (PID: $BACKEND_PID)${NC}"
echo ""

# Start React dashboard
echo -e "${BLUE}🎨 Starting React dashboard on http://localhost:3001${NC}"
cd "$CLIENT_DIR"
PORT=3001 npm start > /tmp/cway-frontend.log 2>&1 &
FRONTEND_PID=$!

echo -e "${GREEN}✓ React dashboard started (PID: $FRONTEND_PID)${NC}"
echo ""
echo -e "${GREEN}✨ All systems ready!${NC}"
echo ""
echo -e "Access points:"
echo -e "  ${BLUE}• React Dashboard:${NC}  http://localhost:3001"
echo -e "  ${BLUE}• WebSocket Server:${NC} http://localhost:8080"
echo -e "  ${BLUE}• Health Check:${NC}     http://localhost:8080/health"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all servers${NC}"
echo ""
echo "Logs:"
echo "  Backend:  tail -f /tmp/cway-backend.log"
echo "  Frontend: tail -f /tmp/cway-frontend.log"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
