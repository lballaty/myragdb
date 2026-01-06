#!/bin/bash
# Helper script to open web UI

# Check if services are running
if lsof -Pi :3003 -sTCP:LISTEN -t >/dev/null 2>&1; then
    # Services running - just open browser
    open "http://localhost:3003"
else
    # Services not running - show message
    osascript -e 'display dialog "MyRAGDB services are not running. Please launch MyRAGDB.app first." buttons {"OK"} default button "OK" with icon caution'
fi
