#!/bin/bash
# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/manage.sh
# Description: Management wrapper for MyRAGDB service (start/stop/status)
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-05

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

COMMAND="${1:-}"

if [ -z "$COMMAND" ]; then
    echo "Usage: $0 <start|stop|status>"
    exit 1
fi

case "$COMMAND" in
    start)
        exec "$SCRIPT_DIR/start.sh"
        ;;
    stop)
        exec "$SCRIPT_DIR/stop.sh"
        ;;
    status)
        if [ -f ".server.pid" ]; then
            PID=$(cat .server.pid)
            if ps -p $PID > /dev/null 2>&1; then
                echo "MyRAGDB is running (PID: $PID)"
                exit 0
            else
                echo "MyRAGDB process not found (stale PID: $PID)"
                exit 1
            fi
        else
            # Try to find any running MyRAGDB processes
            PIDS=$(pgrep -f "python -m myragdb.api.server" || true)
            if [ -n "$PIDS" ]; then
                echo "MyRAGDB is running (PID(s): $PIDS)"
                exit 0
            else
                echo "MyRAGDB is not running"
                exit 1
            fi
        fi
        ;;
    *)
        echo "Unknown command: $COMMAND"
        echo "Usage: $0 <start|stop|status>"
        exit 1
        ;;
esac
