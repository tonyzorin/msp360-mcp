"""
HTTP handlers for MSP360 MCP Server.

This module contains HTTP route handlers for MCP operations,
including tool listing, invocation, and JSON-RPC requests.
"""
import inspect
import json
import logging
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Response, Body
from fastapi.responses import JSONResponse

# Configure logging
logger = logging.getLogger(__name__)

def setup_http_routes(app: FastAPI) -> None:
    """Set up HTTP routes for MCP operations.
    
    Args:
        app: The FastAPI application instance
    """
    @app.get("/mcp/list_tools", 
        tags=["MCP Tools"],
        summary="List all available MCP tools",
        description="Returns a list of all registered MCP tools and their descriptions.",
        response_description="Dictionary with tools definitions")
    async def list_tools():
        """HTTP endpoint to list all available MCP tools."""
        logger.info("HTTP list_tools endpoint accessed")
        return {"tools": app.state.mcp_server.get_tools_definition()}
        
    @app.get("/mcp/tools", 
        tags=["MCP Tools"],
        summary="List all available MCP tools",
        description="Returns a list of all registered MCP tools and their descriptions.",
        response_description="Dictionary with tools definitions")
    async def mcp_tools_list():
        """Endpoint that returns the list of all available MCP tools."""
        logger.info("MCP tools endpoint accessed")
        return {"tools": app.state.mcp_server.get_tools_definition()}

    @app.get("/.well-known/mcp-tools", include_in_schema=False)
    async def mcp_tools():
        """Endpoint for MCP to discover tools."""
        logger.info("MCP tools discovery endpoint accessed")
        return app.state.mcp_server.get_tools_definition()
        
    # Add Cursor-specific endpoint for MCP requests
    @app.post("/mcp/cursor", 
        tags=["MCP Tools"],
        summary="Handle Cursor-specific MCP JSON-RPC 2.0 requests",
        description="Process Cursor-specific MCP JSON-RPC 2.0 requests.",
        response_description="JSON-RPC 2.0 response")
    async def handle_cursor_mcp(request_data: Dict[str, Any] = Body(...)):
        """Process Cursor-specific MCP requests using JSON-RPC 2.0."""
        logger.info(f"Cursor MCP request received: {request_data.get('method', 'unknown method')}")
        
        # Validate it's a proper JSON-RPC 2.0 request
        if "jsonrpc" not in request_data or request_data.get("jsonrpc") != "2.0":
            logger.warning("Invalid JSON-RPC request from Cursor")
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_data.get("id"),
                "error": {
                    "code": -32600,
                    "message": "Invalid Request: Missing or invalid jsonrpc version"
                }
            })
            
        # Extract method and ID
        method = request_data.get("method")
        request_id = request_data.get("id")
        
        # Handle different methods
        if method == "initialize":
            # Initialization request
            logger.info("Cursor initialization request")
            return JSONResponse({
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
                        },
                        "streaming": True
                    }
                }
            })
        elif method == "getTools" or method == "tools/list":
            # Return list of tools
            logger.info("Cursor requested tool list")
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"tools": app.state.mcp_server.get_tools_definition()}
            })
        elif method in ["invoke", "tools/call", "tools/invoke"]:
            # Process tool invocation
            return await handle_tool_invocation(app, request_data, method)
        elif method == "shutdown":
            # Handle shutdown request
            logger.info("Cursor requested shutdown")
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": None
            })
        else:
            # Unknown method
            logger.warning(f"Unknown method from Cursor: {method}")
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            })

    @app.post("/mcp/invoke/{tool_name}", 
        tags=["MCP Tools"],
        summary="Invoke an MCP tool by name",
        description="Invokes a specific MCP tool with the provided parameters.",
        response_description="Tool execution result")
    async def invoke_tool(tool_name: str, params: Dict[str, Any] = {}):
        """Endpoint for invoking MCP tools."""
        logger.info(f"Tool invocation: {tool_name}")
        
        if tool_name not in app.state.mcp_server.registered_tools:
            logger.warning(f"Tool not found: {tool_name}")
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        tool = app.state.mcp_server.registered_tools[tool_name]
        function = tool["function"]
        
        # Only pass parameters that are defined in the function signature
        sig = inspect.signature(function)
        valid_params = {}
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            if param_name in params:
                # Convert string values to integers for 'limit' and 'page' parameters
                if param_name in ['limit', 'page'] and isinstance(params[param_name], str):
                    try:
                        valid_params[param_name] = int(params[param_name])
                    except ValueError:
                        # If conversion fails, use the original value
                        valid_params[param_name] = params[param_name]
                else:
                    valid_params[param_name] = params[param_name]
        
        try:
            logger.info(f"Executing tool {tool_name} with parameters: {valid_params}")
            
            # Execute with error handling for both direct params and args/kwargs format
            try:
                # First try direct function call
                result = await function(**valid_params)
            except Exception as e:
                if "sync_wrapperArguments" in str(e) and ("args" in str(e) or "kwargs" in str(e)):
                    # If error is about missing args/kwargs format, adapt the parameters
                    logger.info(f"Adapting parameters for sync_wrapper: {valid_params}")
                    try:
                        # Call with args/kwargs format instead
                        result = await function(args=[], kwargs=valid_params)
                    except Exception as e2:
                        # If that also fails, raise the new error
                        logger.error(f"Error after adapting parameters: {str(e2)}")
                        raise e2
                else:
                    # For any other error, raise it
                    raise e
            # Ensure array responses are wrapped in a dictionary with "content" key
            if isinstance(result, list):
                result = {"content": result}
                logger.info(f"Wrapped array result in content object for compatibility")
            elif isinstance(result, dict) and "items" in result and "content" not in result:
                # Convert "items" to "content" if needed
                result["content"] = result.pop("items")
                logger.info(f"Converted items to content in result for compatibility")
            return result
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/mcp/invoke", 
        tags=["MCP Tools"],
        summary="Invoke an MCP tool by name in the request body",
        description="Invokes a specific MCP tool with the provided tool name and parameters in the request body.",
        response_description="Tool execution result")
    async def invoke_tool_from_body(request_data: Dict[str, Any] = Body(...)):
        """Endpoint for invoking MCP tools with tool name in the request body."""
        if 'tool' not in request_data:
            logger.warning("Tool name not provided in request body")
            raise HTTPException(status_code=400, detail="Tool name must be provided in the 'tool' field")
            
        tool_name = request_data.get('tool')
        params = request_data.get('params', {})
        
        logger.info(f"Tool invocation from body: {tool_name}")
        
        if tool_name not in app.state.mcp_server.registered_tools:
            logger.warning(f"Tool not found: {tool_name}")
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        tool = app.state.mcp_server.registered_tools[tool_name]
        function = tool["function"]
        
        # Only pass parameters that are defined in the function signature
        sig = inspect.signature(function)
        valid_params = {}
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            if param_name in params:
                # Convert string values to integers for 'limit' and 'page' parameters
                if param_name in ['limit', 'page'] and isinstance(params[param_name], str):
                    try:
                        valid_params[param_name] = int(params[param_name])
                    except ValueError:
                        # If conversion fails, use the original value
                        valid_params[param_name] = params[param_name]
                else:
                    valid_params[param_name] = params[param_name]
        
        try:
            logger.info(f"Executing tool {tool_name} with parameters: {valid_params}")
            
            # Execute with error handling for both direct params and args/kwargs format
            try:
                # First try direct function call
                result = await function(**valid_params)
            except Exception as e:
                if "sync_wrapperArguments" in str(e) and ("args" in str(e) or "kwargs" in str(e)):
                    # If error is about missing args/kwargs format, adapt the parameters
                    logger.info(f"Adapting parameters for sync_wrapper: {valid_params}")
                    try:
                        # Call with args/kwargs format instead
                        result = await function(args=[], kwargs=valid_params)
                    except Exception as e2:
                        # If that also fails, raise the new error
                        logger.error(f"Error after adapting parameters: {str(e2)}")
                        raise e2
                else:
                    # For any other error, raise it
                    raise e
            # Ensure array responses are wrapped in a dictionary with "content" key
            if isinstance(result, list):
                result = {"content": result}
                logger.info(f"Wrapped array result in content object for compatibility")
            elif isinstance(result, dict) and "items" in result and "content" not in result:
                # Convert "items" to "content" if needed
                result["content"] = result.pop("items")
                logger.info(f"Converted items to content in result for compatibility")
            return result
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/mcp/jsonrpc")
    async def mcp_jsonrpc(request: Dict[str, Any]):
        """JSON-RPC compatible endpoint for MCP clients."""
        logger.info(f"JSON-RPC request received: {request.get('method')}")
        
        # Check required JSON-RPC fields
        if "jsonrpc" not in request or request.get("jsonrpc") != "2.0":
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32600,
                    "message": "Invalid Request: Missing or invalid jsonrpc version"
                }
            })
        
        # Check if method is provided
        if "method" not in request:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32600,
                    "message": "Invalid Request: Missing method"
                }
            })
        
        # Process method
        method = request.get("method")
        
        # Handle notifications (no response needed)
        if method.startswith("notifications/"):
            notification_type = method.split("/")[1]
            logger.info(f"Received notification: {notification_type}")
            
            # Handle specific notifications
            if notification_type == "initialized":
                logger.info("Client initialized and ready for normal operations")
            
            # Return empty response for notifications
            return Response(status_code=204)
        
        if method == "initialize":
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "protocolVersion": "0.3.0",
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
            })
        elif method == "getTools":
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {"tools": app.state.mcp_server.get_tools_definition()}
            })
        elif method == "tools/list":
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {"tools": app.state.mcp_server.get_tools_definition()}
            })
        elif method in ["invoke", "tools/call", "tools/invoke"]:
            # Handle all tool invocation methods
            return await handle_tool_invocation(app, request, method)
        else:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            })

async def handle_tool_invocation(app: FastAPI, request: Dict[str, Any], method: str):
    """Handle tool invocation from various JSON-RPC method patterns.
    
    Args:
        app: The FastAPI application
        request: The JSON-RPC request
        method: The method name ('invoke', 'tools/call', 'tools/invoke')
        
    Returns:
        JSONResponse with the result or error
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
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {
                "code": -32602,
                "message": "Invalid params: tool name is required"
            }
        })
    
    logger.info(f"Invoking tool {tool_name} with parameters: {tool_params}")
    
    # Check if tool exists
    if tool_name not in app.state.mcp_server.registered_tools:
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {
                "code": -32602,
                "message": f"Tool '{tool_name}' not found"
            }
        })
    
    # Execute the tool
    try:
        tool = app.state.mcp_server.registered_tools[tool_name]
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
        
        logger.info(f"Executing {tool_name} with valid parameters: {valid_params}")
        
        # Execute with error handling for both direct params and args/kwargs format
        try:
            # First try direct function call
            result = await function(**valid_params)
        except Exception as e:
            if "sync_wrapperArguments" in str(e) and ("args" in str(e) or "kwargs" in str(e)):
                # If error is about missing args/kwargs format, adapt the parameters
                logger.info(f"Adapting parameters for sync_wrapper: {valid_params}")
                try:
                    # Call with args/kwargs format instead
                    result = await function(args=[], kwargs=valid_params)
                except Exception as e2:
                    # If that also fails, raise the new error
                    logger.error(f"Error after adapting parameters: {str(e2)}")
                    raise e2
            else:
                # For any other error, raise it
                raise e
        
        # Ensure array responses are wrapped in a dictionary with "content" key
        if isinstance(result, list):
            result = {"content": result}
            logger.info(f"Wrapped array result in content object for compatibility")
        elif isinstance(result, dict) and "items" in result and "content" not in result:
            # Convert "items" to "content" if needed
            result["content"] = result.pop("items")
            logger.info(f"Converted items to content in result for compatibility")
        
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": result
        })
        
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {str(e)}", exc_info=True)
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }) 