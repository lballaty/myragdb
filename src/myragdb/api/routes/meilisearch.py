# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/api/routes/meilisearch.py
# Description: Meilisearch management and status endpoints
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-06-15

import os
import psutil
import subprocess
import time
import logging
from pathlib import Path
from typing import List
from fastapi import APIRouter, HTTPException
import requests

from myragdb.api.models import (
    MeilisearchStatusResponse,
    MeilisearchStartRequest,
    MeilisearchStartResponse,
    MeilisearchStopResponse,
    MeilisearchLogsResponse
)
from myragdb.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/meilisearch", tags=["meilisearch"])

# Configuration
MEILISEARCH_HOST = os.getenv("MEILISEARCH_HOST", "http://localhost:7700")
MEILISEARCH_PID_FILE = Path.cwd() / ".meilisearch.pid"
MEILISEARCH_LOG_FILE = Path("/tmp/meilisearch.log")
MEILISEARCH_DATA_DIR = Path.cwd() / "data" / "meilisearch"
MEILISEARCH_MASTER_KEY = os.getenv("MEILISEARCH_MASTER_KEY", "myragdb_dev_key_2026")


def is_meilisearch_running() -> bool:
    """Check if Meilisearch process is running."""
    try:
        response = requests.get(f"{MEILISEARCH_HOST}/health", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


def get_meilisearch_pid() -> int | None:
    """Get Meilisearch PID from file or process search."""
    # Try reading from PID file
    if MEILISEARCH_PID_FILE.exists():
        try:
            pid = int(MEILISEARCH_PID_FILE.read_text().strip())
            if psutil.pid_exists(pid):
                return pid
        except Exception:
            pass

    # Try finding by process name
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            if 'meilisearch' in proc.info['name'].lower():
                return proc.info['pid']
    except Exception:
        pass

    return None


@router.get("/status", response_model=MeilisearchStatusResponse)
async def get_meilisearch_status():
    """
    Get Meilisearch status and statistics.

    Returns current running state, document count, and health information.
    """
    try:
        is_running = is_meilisearch_running()

        if not is_running:
            return MeilisearchStatusResponse(
                is_running=False,
                status="stopped",
                message="Meilisearch is not running",
                index_name=settings.meilisearch_index,
                document_count=None,
                uptime_seconds=None,
                version=None
            )

        # Get document count
        try:
            from myragdb.indexers.meilisearch_indexer import MeilisearchIndexer
            indexer = MeilisearchIndexer()
            doc_count = indexer.get_document_count()
        except Exception as e:
            logger.warning(f"Failed to get document count: {e}")
            doc_count = None

        # Get version
        version = None
        try:
            response = requests.get(f"{MEILISEARCH_HOST}/version", timeout=2)
            if response.status_code == 200:
                data = response.json()
                version = data.get("pkgVersion")
        except Exception:
            pass

        # Calculate uptime
        uptime_seconds = None
        pid = get_meilisearch_pid()
        if pid:
            try:
                process = psutil.Process(pid)
                uptime_seconds = time.time() - process.create_time()
            except Exception:
                pass

        return MeilisearchStatusResponse(
            is_running=True,
            status="running",
            message="Meilisearch is healthy and operational",
            index_name=settings.meilisearch_index,
            document_count=doc_count,
            uptime_seconds=uptime_seconds,
            version=version,
            health_check=f"{MEILISEARCH_HOST}/health"
        )

    except Exception as e:
        logger.error(f"Error getting Meilisearch status: {e}")
        return MeilisearchStatusResponse(
            is_running=False,
            status="error",
            message=f"Error checking status: {str(e)}",
            index_name=settings.meilisearch_index
        )


@router.post("/start", response_model=MeilisearchStartResponse)
async def start_meilisearch(request: MeilisearchStartRequest = MeilisearchStartRequest()):
    """
    Start Meilisearch service.

    Starts the Meilisearch process if not already running.
    """
    try:
        # Check if already running
        if is_meilisearch_running():
            pid = get_meilisearch_pid()
            return MeilisearchStartResponse(
                status="success",
                message="Meilisearch is already running",
                is_running=True,
                pid=pid
            )

        # Create data directory
        MEILISEARCH_DATA_DIR.mkdir(parents=True, exist_ok=True)

        # Start Meilisearch process
        process = subprocess.Popen(
            [
                "meilisearch",
                "--db-path", str(MEILISEARCH_DATA_DIR),
                "--master-key", MEILISEARCH_MASTER_KEY,
                "--max-indexing-memory", "34359738368",  # 32 GiB
                "--max-indexing-threads", "10",
                "--http-addr", "127.0.0.1:7700",
                "--log-level", "info"
            ],
            stdout=open(str(MEILISEARCH_LOG_FILE), 'a'),
            stderr=subprocess.STDOUT,
            start_new_session=True
        )

        pid = process.pid
        MEILISEARCH_PID_FILE.write_text(str(pid))

        logger.info(f"Started Meilisearch process (PID: {pid})")

        # Wait for server to be ready if requested
        if request.wait_for_ready:
            start_time = time.time()
            while time.time() - start_time < request.timeout_seconds:
                if is_meilisearch_running():
                    return MeilisearchStartResponse(
                        status="success",
                        message="Meilisearch started successfully",
                        is_running=True,
                        pid=pid
                    )
                time.sleep(1)

            # Timeout
            raise HTTPException(
                status_code=500,
                detail=f"Meilisearch failed to start within {request.timeout_seconds} seconds"
            )

        return MeilisearchStartResponse(
            status="success",
            message="Meilisearch start command executed",
            is_running=True,
            pid=pid
        )

    except subprocess.SubprocessError as e:
        logger.error(f"Failed to start Meilisearch: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start Meilisearch: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error starting Meilisearch: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@router.post("/stop", response_model=MeilisearchStopResponse)
async def stop_meilisearch():
    """
    Stop Meilisearch service.

    Gracefully stops the Meilisearch process.
    """
    try:
        pid = get_meilisearch_pid()

        if not pid:
            return MeilisearchStopResponse(
                status="success",
                message="Meilisearch is not running",
                is_running=False
            )

        try:
            process = psutil.Process(pid)
            process.terminate()

            # Wait for graceful shutdown
            try:
                process.wait(timeout=5)
            except psutil.TimeoutExpired:
                # Force kill if graceful shutdown failed
                process.kill()
                process.wait()

            logger.info(f"Stopped Meilisearch process (PID: {pid})")

            # Clean up PID file
            if MEILISEARCH_PID_FILE.exists():
                MEILISEARCH_PID_FILE.unlink()

        except psutil.NoSuchProcess:
            logger.warning(f"Process {pid} not found, cleaning up PID file")
            if MEILISEARCH_PID_FILE.exists():
                MEILISEARCH_PID_FILE.unlink()

        return MeilisearchStopResponse(
            status="success",
            message="Meilisearch stopped successfully",
            is_running=is_meilisearch_running()
        )

    except Exception as e:
        logger.error(f"Error stopping Meilisearch: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error stopping Meilisearch: {str(e)}"
        )


@router.get("/logs", response_model=MeilisearchLogsResponse)
async def get_meilisearch_logs(lines: int = 50):
    """
    Get recent Meilisearch logs.

    Returns the last N lines from the Meilisearch log file.

    Args:
        lines: Number of log lines to return (default: 50)
    """
    try:
        log_lines: List[str] = []

        if MEILISEARCH_LOG_FILE.exists():
            try:
                with open(MEILISEARCH_LOG_FILE, 'r') as f:
                    all_lines = f.readlines()
                    # Get last N lines
                    log_lines = [line.rstrip('\n') for line in all_lines[-lines:]]
            except Exception as e:
                logger.warning(f"Error reading log file: {e}")
                log_lines = [f"Error reading logs: {str(e)}"]
        else:
            log_lines = ["Log file not found yet"]

        return MeilisearchLogsResponse(
            status="success",
            lines=log_lines,
            total_lines=len(log_lines),
            is_running=is_meilisearch_running()
        )

    except Exception as e:
        logger.error(f"Error getting Meilisearch logs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting logs: {str(e)}"
        )
