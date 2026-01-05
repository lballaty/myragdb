#!/bin/bash
# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/start.sh
# Description: Single-command startup script for MyRAGDB service and web UI
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-04

# Don't exit on errors - we handle them explicitly
set +e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}🚀 Starting MyRAGDB...${NC}"

# Check for and kill any existing process on port 3003
PORT_PID=$(lsof -ti:3003 || true)
if [ -n "$PORT_PID" ]; then
    echo -e "${YELLOW}⚠️  Found existing process on port 3003 (PID: $PORT_PID). Killing...${NC}"
    kill $PORT_PID 2>/dev/null || true
    sleep 1
    # Force kill if still running
    if ps -p $PORT_PID > /dev/null 2>&1; then
        kill -9 $PORT_PID 2>/dev/null || true
    fi
    echo -e "${GREEN}✓ Cleaned up stale process${NC}"
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install -e .
else
    source venv/bin/activate
fi

# Check if indexes exist
if [ ! -d "data/indexes" ]; then
    echo -e "${YELLOW}⚠️  Indexes not found. Running initial indexing...${NC}"
    python scripts/initial_index.py
fi

# Start the server in background
echo -e "${GREEN}✓ Starting MyRAGDB API server on port 3003...${NC}"
python -m myragdb.api.server >> /tmp/myragdb_server.log 2>&1 &
SERVER_PID=$!

# Save PID immediately
echo $SERVER_PID > .server.pid

# Wait for server to start with retries
echo -e "${BLUE}⏳ Waiting for server to start...${NC}"
MAX_RETRIES=10
RETRY_COUNT=0
SERVER_READY=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    sleep 1
    if curl -s http://localhost:3003/health > /dev/null 2>&1; then
        SERVER_READY=true
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -e "${BLUE}  Attempt $RETRY_COUNT/$MAX_RETRIES...${NC}"
done

# Check if server started successfully
if [ "$SERVER_READY" = true ]; then
    echo -e "${GREEN}✓ Server is running!${NC}"
    echo -e "${GREEN}✓ Opening web UI in browser...${NC}"

    # Open browser (works on macOS)
    open http://localhost:3003

    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}MyRAGDB is running!${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "Web UI:  ${BLUE}http://localhost:3003${NC}"
    echo -e "PID:     ${YELLOW}$SERVER_PID${NC}"
    echo -e "Logs:    ${YELLOW}/tmp/myragdb_server.log${NC}"
    echo ""
    echo -e "To stop the server, run: ${YELLOW}./stop.sh${NC}"
    echo -e "Or kill process: ${YELLOW}kill $SERVER_PID${NC}"
    echo -e "View logs: ${YELLOW}tail -f /tmp/myragdb_server.log${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
else
    echo -e "${YELLOW}⚠️  Server failed to start after $MAX_RETRIES attempts${NC}"
    echo -e "${YELLOW}⚠️  The server process is still running in background (PID: $SERVER_PID)${NC}"
    echo -e "${YELLOW}⚠️  Check logs for startup errors: tail -f /tmp/myragdb_server.log${NC}"
    echo ""
    echo -e "${BLUE}Showing last 30 lines of logs:${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    tail -30 /tmp/myragdb_server.log 2>/dev/null || echo -e "${YELLOW}No logs found at /tmp/myragdb_server.log${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "To stop the background server: ${YELLOW}kill $SERVER_PID${NC} or ${YELLOW}./stop.sh${NC}"
    echo -e "To view live logs: ${YELLOW}tail -f /tmp/myragdb_server.log${NC}"
fi
