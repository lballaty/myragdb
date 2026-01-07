#!/bin/bash
# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/view-app-logs.sh
# Description: View MyRAGDB app bundle logs for troubleshooting
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07

echo "=================================================="
echo "MyRAGDB App Bundle Logs"
echo "=================================================="
echo ""

if [ -f "/tmp/myragdb_app_bundle.log" ]; then
    echo "📄 App Bundle Launcher Log:"
    echo "---"
    tail -100 /tmp/myragdb_app_bundle.log
    echo ""
else
    echo "❌ No app bundle log found at /tmp/myragdb_app_bundle.log"
    echo ""
fi

echo "=================================================="
echo "MyRAGDB Server Logs"
echo "=================================================="
echo ""

if [ -f "/tmp/myragdb_server.log" ]; then
    echo "📄 Server Log (last 50 lines):"
    echo "---"
    tail -50 /tmp/myragdb_server.log
    echo ""
else
    echo "❌ No server log found at /tmp/myragdb_server.log"
    echo ""
fi

echo "=================================================="
echo "MCP Middleware Logs"
echo "=================================================="
echo ""

if [ -f "/tmp/mcp_middleware.log" ]; then
    echo "📄 Middleware Log (last 50 lines):"
    echo "---"
    tail -50 /tmp/mcp_middleware.log
    echo ""
else
    echo "❌ No middleware log found at /tmp/mcp_middleware.log"
    echo ""
fi

echo "=================================================="
echo "To follow logs in real-time:"
echo "  tail -f /tmp/myragdb_app_bundle.log"
echo "  tail -f /tmp/myragdb_server.log"
echo "  tail -f /tmp/mcp_middleware.log"
echo "=================================================="
