"""
SSE mode handler for MSP360 MCP Server.

This module contains functions for handling Server-Sent Events (SSE) based communication
for MCP, using the JSON-RPC 2.0 protocol over HTTP streaming.
"""
import inspect
import json
import logging
from typing import Dict, Any, AsyncGenerator, List, Optional, Union

from mcp_server import MCPServer

# Configure logging
logger = logging.getLogger(__name__)

class SSEHandler:
    """Handler for Server-Sent Events (SSE) communication with MCP."""
    
    def __init__(self, mcp_server: MCPServer):
        """Initialize the SSE handler.
        
        Args:
            mcp_server: The MCP server instance
        """
        self.mcp_server = mcp_server
        
    async def handle_sse_request(self, request_data: Dict[str, Any]) -> AsyncGenerator[bytes, None]:
        """Handle SSE-based MCP requests.
        
        Args:
            request_data: The JSON-RPC request data
            
        Yields:
            Formatted SSE events as bytes
        """
        try:
            # Log the received request
            logger.info(f"Received SSE request: {request_data}")
            
            # Ensure valid JSON-RPC version
            if "jsonrpc" not in request_data or request_data.get("jsonrpc") != "2.0":
                yield self._format_sse_error(
                    request_data.get("id"), 
                    -32600, 
                    "Invalid Request: Missing or invalid jsonrpc version"
                )
                return
                
            # Extract method and request ID
            method = request_data.get("method")
            request_id = request_data.get("id")
            
            # Handle initialization request
            if method == "initialize":
                # Send initialization response
                response = {
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
                }
                yield self._format_sse_event(response)
                return
                
            # Handle tools listing
            elif method in ["getTools", "tools/list"]:
                # Get tool definitions
                tools_def = self.mcp_server.get_tools_definition()
                
                # Format in the expected MCP structure for Cursor
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"tools": tools_def}
                }
                yield self._format_sse_event(response)
                return
                
            # Handle tool invocation
            elif method in ["invoke", "tools/call", "tools/invoke"]:
                async for event in self._handle_tool_invocation(request_data, method):
                    yield event
                return
                
            # Handle shutdown request
            elif method == "shutdown":
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": None
                }
                yield self._format_sse_event(response)
                return
                
            # Unknown method
            else:
                yield self._format_sse_error(
                    request_id, 
                    -32601, 
                    f"Method not found: {method}"
                )
                return
                
        except Exception as e:
            # Handle any unexpected errors
            logger.error(f"Error in SSE handler: {e}", exc_info=True)
            yield self._format_sse_error(
                request_data.get("id") if "request_data" in locals() else None,
                -32603,
                f"Internal error: {str(e)}"
            )
    
    async def _handle_tool_invocation(self, request: Dict[str, Any], method: str) -> AsyncGenerator[bytes, None]:
        """Handle tool invocation via SSE.
        
        Args:
            request: The JSON-RPC request
            method: The method name
            
        Yields:
            Formatted SSE events
        """
        request_id = request.get("id")
        
        # Extract tool name from request based on method
        if method == "invoke":
            tool_name = request.get("params", {}).get("name")
            tool_params = request.get("params", {}).get("arguments", {})
        else:  # tools/call or tools/invoke
            tool_name = request.get("params", {}).get("name")
            tool_params = request.get("params", {}).get("parameters", {})
            # Check for arguments field for compatibility
            if not tool_params and "arguments" in request.get("params", {}):
                tool_params = request.get("params", {}).get("arguments", {})
                
        # Validate tool name is provided
        if not tool_name:
            yield self._format_sse_error(
                request_id,
                -32602,
                "Invalid params: tool name is required"
            )
            return
        
        logger.info(f"Invoking tool {tool_name} with parameters: {tool_params}")
        
        # Check if tool exists
        if tool_name not in self.mcp_server.registered_tools:
            yield self._format_sse_error(
                request_id,
                -32602,
                f"Tool '{tool_name}' not found"
            )
            return
        
        # Execute the tool
        try:
            tool = self.mcp_server.registered_tools[tool_name]
            function = tool["function"]
            
            # Process parameters (same as in stdio_handler)
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
            
            # Call the function
            result = function(**valid_params)
            
            # Handle different types of results
            if inspect.isasyncgen(result):
                # For streaming responses, yield events for each item
                sequence = 0
                async for item in result:
                    sequence += 1
                    # For compatibility with different result formats
                    if isinstance(item, dict) and "content" not in item and "items" in item:
                        item["content"] = item.pop("items")
                        
                    yield self._format_sse_event({
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "partial": True,
                        "sequence": sequence,
                        "result": item
                    })
                
                # Final event to indicate completion
                yield self._format_sse_event({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "partial": False,
                    "sequence": sequence + 1,
                    "result": {"complete": True}
                })
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
                
                # Format as per Cursor's expected format
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
                
                # Send single complete response
                yield self._format_sse_event(response)
                
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {str(e)}", exc_info=True)
            yield self._format_sse_error(
                request_id,
                -32603,
                f"Internal error: {str(e)}"
            )
    
    def _format_sse_event(self, data: Dict[str, Any]) -> bytes:
        """Format data as an SSE event.
        
        Args:
            data: The data to format
            
        Returns:
            Formatted SSE event as bytes
        """
        json_str = json.dumps(data)
        return f"data: {json_str}\n\n".encode('utf-8')
    
    def _format_sse_error(self, request_id: Any, code: int, message: str) -> bytes:
        """Format an error as an SSE event.
        
        Args:
            request_id: The request ID
            code: The error code
            message: The error message
            
        Returns:
            Formatted SSE error event as bytes
        """
        error_data = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }
        return self._format_sse_event(error_data) 