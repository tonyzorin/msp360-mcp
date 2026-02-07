"""
STDIO mode handler for MSP360 MCP Server.

This module contains functions for handling STDIO-based communication
for MCP, using the JSON-RPC 2.0 protocol over standard input/output.
"""
import asyncio
import inspect
import json
import logging
import sys
from typing import Dict, Any

from mcp_server import MCPServer
from services.msp360 import msp360_client

# Configure logging
logger = logging.getLogger(__name__)


def _build_initialize_response(request_id):
    """Build the standard initialize response."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "protocolVersion": "2024-11-05",
            "serverInfo": {
                "name": "MSP360 MCP Server",
                "version": "1.1.0"
            },
            "capabilities": {
                "tools": {
                    "listChanged": True
                }
            }
        }
    }


async def handle_stdio_mode_async():
    """Handle STDIO communication for MCP in async mode.

    Implements a JSON-RPC 2.0 protocol for communication over standard input/output.
    """
    logger.info("Starting in STDIO mode for MCP (JSON-RPC 2.0 protocol)")

    # Initialize MCP Server for STDIO mode
    mcp_server = MCPServer()
    mcp_server.register_tools()
    logger.info(f"MSP360 MCP Server initialized with {len(mcp_server.registered_tools)} tools")

    # Generate initial token
    logger.info("Attempting to generate initial authentication token for STDIO mode")
    try:
        # Get token_manager from client
        token_manager = msp360_client.token_manager
        await token_manager.generate_token()
        logger.info("Successfully generated initial token for STDIO mode")
    except Exception as e:
        logger.error(f"Failed to generate initial token in STDIO mode: {e}", exc_info=True)

    # Main STDIO loop
    logger.info("Entering main STDIO loop")
    loop = asyncio.get_event_loop()

    try:
        while True:
            request_id = None
            try:
                # Read from stdin without blocking the event loop
                logger.info("Waiting for line from stdin...")
                line = await loop.run_in_executor(None, sys.stdin.readline)

                if not line:
                    logger.warning("Stdin closed (EOF received). Exiting STDIO loop.")
                    break

                # Parse the JSON request
                try:
                    request = json.loads(line)
                    request_id = request.get("id")
                    logger.info(f"Received request: method={request.get('method')}, id={request_id}")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON from stdin: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": f"Parse error: {str(e)}"
                        }
                    }
                    sys.stdout.write(json.dumps(error_response) + "\n")
                    sys.stdout.flush()
                    continue

                # Special case for notifications (no response needed)
                if request.get("method", "").startswith("notifications/"):
                    notification_type = request.get("method").split("/")[1]
                    logger.info(f"Received notification: {notification_type}")

                    # Handle specific notifications
                    if notification_type == "initialized":
                        logger.info("Client initialized and ready for normal operations")

                    # No response needed for notifications
                    continue

                response = None

                # Check for required jsonrpc version field
                if "jsonrpc" not in request or request.get("jsonrpc") != "2.0":
                    # For compatibility with older clients, handle requests without jsonrpc field
                    if request.get("method") == "initialize":
                        response = _build_initialize_response(request_id)
                    else:
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {
                                "code": -32600,
                                "message": "Invalid Request: Missing or invalid jsonrpc version"
                            }
                        }
                elif request.get("method") == "initialize":
                    response = _build_initialize_response(request_id)
                elif request.get("method") in ["getTools", "tools/list"]:
                    # Return available tools
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {"tools": mcp_server.get_tools_definition()}
                    }
                elif request.get("method") in ["invoke", "tools/call", "tools/invoke"]:
                    # Invoke a tool
                    response = await handle_tool_invocation(mcp_server, request, request.get("method"))
                elif request.get("method") == "shutdown":
                    # Handle shutdown - send response before exiting
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": None
                    }
                    sys.stdout.write(json.dumps(response) + "\n")
                    sys.stdout.flush()
                    break
                else:
                    # Unknown method
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {request.get('method')}"
                        }
                    }

                # Send the response
                if response:
                    sys.stdout.write(json.dumps(response) + "\n")
                    sys.stdout.flush()

            except (SystemExit, KeyboardInterrupt):
                logger.info("Received termination signal during STDIO loop")
                break
            except Exception as e:
                # Send an error response
                error_response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }

                sys.stdout.write(json.dumps(error_response) + "\n")
                sys.stdout.flush()
    finally:
        logger.info("Cleaning up MCP server resources")
        mcp_server.close()

async def handle_tool_invocation(mcp_server: MCPServer, request: Dict[str, Any], method: str):
    """Handle tool invocation from various JSON-RPC method patterns.

    Args:
        mcp_server: The MCP server instance
        request: The JSON-RPC request
        method: The method name ('invoke', 'tools/call', 'tools/invoke')

    Returns:
        Dict with the JSON-RPC response
    """
    # Extract tool name from request, with slight variations based on method
    if method == "invoke":
        tool_name = request.get("params", {}).get("name")
        tool_params = request.get("params", {}).get("arguments", {})
    else:  # tools/call or tools/invoke
        tool_name = request.get("params", {}).get("name")
        tool_params = request.get("params", {}).get("parameters", {})
        # Check for arguments field for compatibility with different MCP clients
        if not tool_params and "arguments" in request.get("params", {}):
            tool_params = request.get("params", {}).get("arguments", {})

    # Validate tool name is provided
    if not tool_name:
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {
                "code": -32602,
                "message": "Invalid params: tool name is required"
            }
        }

    logger.info(f"Invoking tool {tool_name} with parameter keys: {list(tool_params.keys())}")

    # Check if tool exists
    if tool_name not in mcp_server.registered_tools:
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {
                "code": -32602,
                "message": f"Tool '{tool_name}' not found"
            }
        }

    # Execute the tool
    try:
        tool = mcp_server.registered_tools[tool_name]
        function = tool["function"]

        # Process parameters
        sig = inspect.signature(function)
        valid_params = {}
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            if param_name in tool_params:
                param_value = tool_params[param_name]
                # Convert string to int for limit and page
                if param_name in ["limit", "page"] and isinstance(param_value, str) and param_value.isdigit():
                    param_value = int(param_value)
                valid_params[param_name] = param_value

        logger.info(f"Executing {tool_name} with parameter keys: {list(valid_params.keys())}")

        # Call the function with error handling for both direct params and args/kwargs format
        try:
            # First try direct function call
            result = function(**valid_params)
        except Exception as e:
            if "sync_wrapperArguments" in str(e) and ("args" in str(e) or "kwargs" in str(e)):
                # If error is about missing args/kwargs format, adapt the parameters
                logger.info(f"Adapting parameters for sync_wrapper: {valid_params}")
                try:
                    # Call with args/kwargs format instead
                    result = function(args=[], kwargs=valid_params)
                except Exception as e2:
                    # If that also fails, raise the new error
                    logger.error(f"Error after adapting parameters: {str(e2)}")
                    raise e2
            else:
                # For any other error, raise it
                raise e

        # Handle different types of results
        if inspect.isasyncgen(result):
            # For streaming responses, collect all items
            items = []
            async for item in result:
                items.append(item)
            result = {"content": items}
            logger.info("Collected all items from async generator")
        else:
            # For regular async functions, await the result
            result = await result
            # Handle regular responses
            if isinstance(result, list):
                    result = {"content": result}
                    logger.info("Wrapped array result in content object for compatibility")
            elif isinstance(result, dict) and "items" in result and "content" not in result:
                # Convert "items" to "content" if needed
                result["content"] = result.pop("items")
                logger.info("Converted items to content in result for compatibility")

        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": result
        }

    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {str(e)}", exc_info=True)
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }
