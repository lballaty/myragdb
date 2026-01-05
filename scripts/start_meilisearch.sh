#!/bin/bash
# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/scripts/start_meilisearch.sh
# Description: Start Meilisearch with M4 Max optimized settings (32GB memory, 8-10 threads)
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-04

set -e

# Configuration for M4 Max (128GB RAM)
DATA_DIR="/Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/data/meilisearch"
MASTER_KEY="myragdb_dev_key_2026"
MAX_MEMORY=34359738368  # 32 GiB in bytes
INDEX_THREADS=10        # M4 Max optimization (8-10 threads)

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Meilisearch for MyRAGDB...${NC}"

# Create data directory
mkdir -p "$DATA_DIR"
echo -e "${GREEN}✓ Data directory: $DATA_DIR${NC}"

# Check if Meilisearch is already running
if lsof -Pi :7700 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Meilisearch already running on port 7700${NC}"
    echo -e "${YELLOW}   To restart, run: pkill meilisearch && ./scripts/start_meilisearch.sh${NC}"
    exit 0
fi

# Start Meilisearch
echo -e "${GREEN}✓ Starting Meilisearch with M4 Max optimizations...${NC}"
echo -e "  Max Indexing Memory: 32 GB"
echo -e "  Index Threads: $INDEX_THREADS"
echo -e "  HTTP Address: http://127.0.0.1:7700"
echo ""

meilisearch \
  --db-path "$DATA_DIR" \
  --master-key "$MASTER_KEY" \
  --max-indexing-memory "$MAX_MEMORY" \
  --max-indexing-threads "$INDEX_THREADS" \
  --http-addr 127.0.0.1:7700 \
  --log-level info &

MEILI_PID=$!
echo -e "${GREEN}✓ Meilisearch started (PID: $MEILI_PID)${NC}"

# Wait for Meilisearch to be ready
echo -e "${BLUE}⏳ Waiting for Meilisearch to be ready...${NC}"
sleep 2

# Health check
if curl -s http://localhost:7700/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Meilisearch is ready!${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Meilisearch running successfully${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "URL:        ${BLUE}http://localhost:7700${NC}"
    echo -e "Master Key: ${YELLOW}$MASTER_KEY${NC}"
    echo -e "PID:        ${YELLOW}$MEILI_PID${NC}"
    echo -e "Data:       ${BLUE}$DATA_DIR${NC}"
    echo ""
    echo -e "To stop: ${YELLOW}pkill meilisearch${NC}"
    echo -e "Health:  ${YELLOW}curl http://localhost:7700/health${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # Save PID for reference
    echo $MEILI_PID > .meilisearch.pid
else
    echo -e "${YELLOW}⚠️  Meilisearch started but health check failed${NC}"
    echo -e "${YELLOW}   Check logs or wait a few seconds for initialization${NC}"
    exit 1
fi
