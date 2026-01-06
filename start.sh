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

# ============================================================================
# Step 1: Start Meilisearch (required dependency)
# ============================================================================
echo -e "${BLUE}📊 Checking Meilisearch status...${NC}"

# Meilisearch configuration (from start_meilisearch.sh)
MEILI_DATA_DIR="$SCRIPT_DIR/data/meilisearch"
MEILI_MASTER_KEY="myragdb_dev_key_2026"
MEILI_MAX_MEMORY=34359738368  # 32 GiB in bytes
MEILI_INDEX_THREADS=10        # M4 Max optimization

# Check if Meilisearch is already running
if lsof -Pi :7700 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Meilisearch already running on port 7700${NC}"
else
    echo -e "${YELLOW}⚠️  Meilisearch not running. Starting...${NC}"

    # Create data directory
    mkdir -p "$MEILI_DATA_DIR"

    # Start Meilisearch in background
    meilisearch \
      --db-path "$MEILI_DATA_DIR" \
      --master-key "$MEILI_MASTER_KEY" \
      --max-indexing-memory "$MEILI_MAX_MEMORY" \
      --max-indexing-threads "$MEILI_INDEX_THREADS" \
      --http-addr 127.0.0.1:7700 \
      --log-level info >> /tmp/meilisearch.log 2>&1 &

    MEILI_PID=$!
    echo $MEILI_PID > .meilisearch.pid
    echo -e "${GREEN}✓ Meilisearch started (PID: $MEILI_PID)${NC}"

    # Wait for Meilisearch to be ready
    echo -e "${BLUE}⏳ Waiting for Meilisearch to be ready...${NC}"
    MEILI_MAX_RETRIES=10
    MEILI_RETRY_COUNT=0
    MEILI_READY=false

    while [ $MEILI_RETRY_COUNT -lt $MEILI_MAX_RETRIES ]; do
        sleep 1
        if curl -s http://localhost:7700/health > /dev/null 2>&1; then
            MEILI_READY=true
            break
        fi
        MEILI_RETRY_COUNT=$((MEILI_RETRY_COUNT + 1))
        echo -e "${BLUE}  Attempt $MEILI_RETRY_COUNT/$MEILI_MAX_RETRIES...${NC}"
    done

    if [ "$MEILI_READY" = true ]; then
        echo -e "${GREEN}✓ Meilisearch is ready!${NC}"
    else
        echo -e "${YELLOW}⚠️  Meilisearch failed to start after $MEILI_MAX_RETRIES attempts${NC}"
        echo -e "${YELLOW}⚠️  Check logs: tail -f /tmp/meilisearch.log${NC}"
        exit 1
    fi
fi

echo ""

# ============================================================================
# Step 2: Start MyRAGDB Server
# ============================================================================
echo -e "${BLUE}🔧 Preparing MyRAGDB Server...${NC}"

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

    # ============================================================================
    # Step 3: Start MCP HTTP Middleware (Optional - for LLM tool access)
    # ============================================================================
    echo ""
    echo -e "${BLUE}🤖 Starting MCP HTTP Middleware...${NC}"

    # Check if MCP middleware is already running
    MCP_PORT_PID=$(lsof -ti:8093 || true)
    if [ -n "$MCP_PORT_PID" ]; then
        echo -e "${YELLOW}⚠️  MCP middleware already running on port 8093 (PID: $MCP_PORT_PID). Skipping...${NC}"
    else
        # Start MCP middleware in background
        python -m mcp_server.http_middleware >> /tmp/mcp_middleware.log 2>&1 &
        MCP_PID=$!
        echo $MCP_PID > .middleware.pid
        echo -e "${GREEN}✓ MCP middleware started (PID: $MCP_PID)${NC}"

        # Quick health check (don't wait long, it's optional)
        sleep 1
        if lsof -ti:8093 > /dev/null 2>&1; then
            echo -e "${GREEN}✓ MCP middleware is ready on port 8093${NC}"
        else
            echo -e "${YELLOW}⚠️  MCP middleware may not have started (check logs: /tmp/mcp_middleware.log)${NC}"
        fi
    fi

    echo ""
    echo -e "${GREEN}✓ Opening web UI in browser...${NC}"

    # Open browser (works on macOS)
    open http://localhost:3003

    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}MyRAGDB is running!${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "Web UI:        ${BLUE}http://localhost:3003${NC}"
    echo -e "API Server:    ${YELLOW}PID $SERVER_PID${NC} | ${YELLOW}Logs: /tmp/myragdb_server.log${NC}"
    if [ -f ".middleware.pid" ]; then
        MCP_DISPLAY_PID=$(cat .middleware.pid)
        echo -e "MCP Middleware: ${YELLOW}PID $MCP_DISPLAY_PID${NC} | ${BLUE}http://localhost:8093${NC} | ${YELLOW}Logs: /tmp/mcp_middleware.log${NC}"
    fi
    echo ""
    echo -e "To stop all services: ${YELLOW}./stop.sh${NC}"
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
