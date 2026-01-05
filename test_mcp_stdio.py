# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/test_mcp_stdio.py
# Description: Test MCP server via stdio protocol
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-05

"""
Test the MCP server by launching it as a subprocess and communicating via stdio.
This simulates how Claude Code would actually use the MCP server.
"""

import asyncio
import json
import sys

async def test_mcp_server():
    """Test MCP server via stdio communication."""
    print("="*60)
    print("MCP Server stdio Test")
    print("="*60)

    # Start the MCP server as a subprocess
    print("\n1. Starting MCP server subprocess...")
    try:
        process = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "mcp_server.server",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd="/Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb"
        )
        print("   ✓ MCP server process started (PID: {})".format(process.pid))
    except Exception as e:
        print(f"   ✗ Failed to start MCP server: {e}")
        return False

    try:
        # Send initialize request
        print("\n2. Sending initialize request...")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }

        request_json = json.dumps(init_request) + "\n"
        process.stdin.write(request_json.encode())
        await process.stdin.drain()
        print("   ✓ Initialize request sent")

        # Read response with timeout
        print("\n3. Waiting for initialize response...")
        try:
            response_line = await asyncio.wait_for(
                process.stdout.readline(),
                timeout=5.0
            )

            if response_line:
                response = json.loads(response_line.decode())
                print("   ✓ Received initialize response:")
                print(f"     Protocol version: {response.get('result', {}).get('protocolVersion', 'N/A')}")
                print(f"     Server name: {response.get('result', {}).get('serverInfo', {}).get('name', 'N/A')}")
            else:
                print("   ✗ No response received")
                return False

        except asyncio.TimeoutError:
            print("   ✗ Timeout waiting for response")
            return False

        # Send tools/list request
        print("\n4. Requesting tool list...")
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }

        request_json = json.dumps(tools_request) + "\n"
        process.stdin.write(request_json.encode())
        await process.stdin.drain()
        print("   ✓ tools/list request sent")

        # Read tools response
        print("\n5. Waiting for tools list response...")
        try:
            response_line = await asyncio.wait_for(
                process.stdout.readline(),
                timeout=5.0
            )

            if response_line:
                response = json.loads(response_line.decode())
                tools = response.get('result', {}).get('tools', [])
                print(f"   ✓ Received {len(tools)} tools:")
                for i, tool in enumerate(tools[:5], 1):
                    print(f"     {i}. {tool['name']}")
                if len(tools) > 5:
                    print(f"     ... and {len(tools) - 5} more")
            else:
                print("   ✗ No response received")
                return False

        except asyncio.TimeoutError:
            print("   ✗ Timeout waiting for response")
            return False

        print("\n" + "="*60)
        print("✓ MCP Server stdio Test PASSED")
        print("="*60)
        print("\nThe MCP server successfully:")
        print("- Started as a subprocess")
        print("- Accepted JSON-RPC messages via stdin")
        print("- Responded with valid JSON via stdout")
        print("- Listed all available tools")
        print("\nClaude Code will be able to communicate with it!")

        return True

    except Exception as e:
        print(f"\n✗ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        print("\n6. Cleaning up...")
        try:
            process.terminate()
            await asyncio.wait_for(process.wait(), timeout=2.0)
            print("   ✓ MCP server process terminated")
        except:
            process.kill()
            print("   ✓ MCP server process killed")

if __name__ == "__main__":
    result = asyncio.run(test_mcp_server())
    sys.exit(0 if result else 1)
