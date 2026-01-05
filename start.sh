#!/bin/bash
# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/start.sh
# Description: Single-command startup script for MyRAGDB service and web UI
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-04

set -e

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
python -m myragdb.api.server &
SERVER_PID=$!

# Wait for server to start
echo -e "${BLUE}⏳ Waiting for server to start...${NC}"
sleep 3

# Check if server is healthy
if curl -s http://localhost:3003/health > /dev/null 2>&1; then
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
    echo ""
    echo -e "To stop the server, run: ${YELLOW}./stop.sh${NC}"
    echo -e "Or kill process: ${YELLOW}kill $SERVER_PID${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # Save PID to file for stop script
    echo $SERVER_PID > .server.pid
else
    echo -e "${YELLOW}⚠️  Server failed to start. Check logs for errors.${NC}"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi
