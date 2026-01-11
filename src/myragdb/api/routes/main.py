# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/api/routes/main.py
# Description: Main API routes for MyRAGDB - moved to /api/v1 prefix
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-10

from fastapi import APIRouter

# Create main API router with /api/v1 prefix
router = APIRouter(prefix="/api/v1", tags=["main"])

# Note: The main routes (health, search, repositories, etc.) will be moved here
# from server.py to consolidate under /api/v1 prefix for consistency