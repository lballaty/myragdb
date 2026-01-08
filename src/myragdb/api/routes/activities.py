# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/api/routes/activities.py
# Description: Activity log endpoints for user action tracking and monitoring
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-08

from fastapi import APIRouter, Query
from typing import List, Dict, Any
import json
from datetime import datetime

router = APIRouter(prefix="/api/v1", tags=["activities"])


@router.get("/activities")
async def get_activities(limit: int = Query(100, ge=1, le=1000)) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get recent activity logs.

    Business Purpose: Provides frontend with activity history for monitoring
    and auditing user actions like searches, reindexing, and LLM operations.

    Args:
        limit: Maximum number of activities to return (default: 100, max: 1000)

    Returns:
        JSON object with 'activities' list containing activity records

    Example:
        GET /api/v1/activities?limit=50
        Response: {
            "activities": [
                {
                    "type": "search",
                    "message": "Searched for 'authentication' in 3 repositories",
                    "severity": "info",
                    "timestampMs": 1704733200000
                },
                ...
            ]
        }
    """
    try:
        # Load activities from localStorage (stored by frontend)
        # In a production system, this would be persisted server-side
        # For now, return empty list since backend doesn't store activities
        # The frontend falls back to localStorage if API returns empty
        activities = []

        return {"activities": activities}

    except Exception as e:
        # Gracefully return empty list on error
        # Frontend will fall back to localStorage
        return {"activities": []}
