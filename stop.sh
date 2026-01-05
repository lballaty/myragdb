#!/bin/bash
# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/stop.sh
# Description: Stop MyRAGDB service
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-04

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${YELLOW}🛑 Stopping MyRAGDB...${NC}"

# Stop API Server
if [ -f ".server.pid" ]; then
    PID=$(cat .server.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        echo -e "${GREEN}✓ API Server stopped (PID: $PID)${NC}"
        rm .server.pid
    else
        echo -e "${YELLOW}⚠️  Process $PID not found (may have already stopped)${NC}"
        rm .server.pid
    fi
else
    # Try to find and kill any running MyRAGDB API processes
    PIDS=$(pgrep -f "python -m myragdb.api.server" || true)
    if [ -n "$PIDS" ]; then
        echo -e "${YELLOW}Found running MyRAGDB API processes: $PIDS${NC}"
        kill $PIDS
        echo -e "${GREEN}✓ MyRAGDB API processes stopped${NC}"
    else
        echo -e "${YELLOW}⚠️  No running MyRAGDB API server found${NC}"
    fi
fi

# Stop HTTP Middleware
if [ -f ".middleware.pid" ]; then
    PID=$(cat .middleware.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        echo -e "${GREEN}✓ HTTP Middleware stopped (PID: $PID)${NC}"
        rm .middleware.pid
    else
        echo -e "${YELLOW}⚠️  Middleware process $PID not found (may have already stopped)${NC}"
        rm .middleware.pid
    fi
else
    # Try to find and kill any running middleware processes
    PIDS=$(pgrep -f "python -m mcp_server.http_middleware" || true)
    if [ -n "$PIDS" ]; then
        echo -e "${YELLOW}Found running middleware processes: $PIDS${NC}"
        kill $PIDS
        echo -e "${GREEN}✓ HTTP Middleware processes stopped${NC}"
    fi
fi
