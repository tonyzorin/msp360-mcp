#!/usr/bin/env python3
"""
MCP Client implementation for testing MCP tools.

This module contains a client for interacting with the MCP server,
allowing for easy testing of MCP tools directly without going through the Cursor IDE.
"""

import json
import asyncio
import logging
import aiohttp
from typing import Dict, Any, Optional, Union, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mcp_client")

class MCPClient:
    """
    Client for interacting with the MCP server.
    
    This client can be used to test MCP tools directly without going through the Cursor IDE.
    It supports both HTTP and STDIO modes of communication.
    """
    
    def __init__(self, server_url: str = "http://localhost:51817"):
        """
        Initialize the MCP client.
        
        Args:
            server_url: The URL of the MCP server
        """
        self.server_url = server_url
        self.session = None
        self.message_id = 0
        logger.info(f"MCP Client initialized with server URL: {server_url}")
        
    async def _ensure_session(self):
        """Ensure there is an active HTTP session."""
        if self.session is None:
            self.session = aiohttp.ClientSession()
            
    async def close(self):
        """Close the client and release resources."""
        if self.session:
            await self.session.close()
            self.session = None
    
    def _get_next_message_id(self) -> int:
        """Get the next message ID for a request."""
        self.message_id += 1
        return self.message_id
            
    async def get_tools(self) -> List[Dict[str, Any]]:
        """
        Get the list of available tools from the MCP server.
        
        Returns:
            List of tool definitions
        """
        await self._ensure_session()
        
        try:
            # Create a JSON-RPC request with a numeric ID
            request_data = {
                "jsonrpc": "2.0",
                "id": self._get_next_message_id(),
                "method": "tools/list"
            }
            
            async with self.session.post(f"{self.server_url}/mcp/invoke", json=request_data) as response:
                if response.status == 200:
                    result = await response.json()
                    # Check for JSON-RPC error
                    if "error" in result:
                        error_data = result["error"]
                        logger.error(f"JSON-RPC error: {error_data.get('code')} - {error_data.get('message')}")
                        return []
                    return result.get("result", {}).get("tools", [])
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to get tools. Status: {response.status}, Error: {error_text}")
                    return []
        except Exception as e:
            logger.error(f"Error getting tools: {str(e)}")
            return []
            
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool on the MCP server.
        
        Args:
            tool_name: The name of the tool to call
            params: The parameters to pass to the tool
            
        Returns:
            The result of the tool call
        """
        await self._ensure_session()
        
        try:
            # Create a JSON-RPC request
            request_data = {
                "jsonrpc": "2.0",
                "id": self._get_next_message_id(),
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "parameters": params
                }
            }
            
            logger.info(f"Calling tool {tool_name} with request: {request_data}")
            
            async with self.session.post(f"{self.server_url}/mcp/invoke", json=request_data) as response:
                if response.status == 200:
                    result = await response.json()
                    # Check for JSON-RPC error
                    if "error" in result:
                        error_data = result["error"]
                        logger.error(f"JSON-RPC error: {error_data.get('code')} - {error_data.get('message')}")
                        return {"error": f"JSON-RPC error: {error_data.get('message')}"}
                    return result.get("result", {})
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to call tool. Status: {response.status}, Error: {error_text}")
                    return {"error": f"Failed to call tool: {error_text}"}
        except Exception as e:
            logger.error(f"Error calling tool: {str(e)}")
            return {"error": f"Error calling tool: {str(e)}"}
            
    async def call_streaming_tool(self, tool_name: str, params: Dict[str, Any]):
        """
        Call a streaming tool on the MCP server.
        
        Args:
            tool_name: The name of the tool to call
            params: The parameters to pass to the tool
            
        Yields:
            The streaming results from the tool call
        """
        await self._ensure_session()
        
        try:
            # Create a JSON-RPC request
            request_data = {
                "jsonrpc": "2.0",
                "id": self._get_next_message_id(),
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "parameters": params
                }
            }
            
            logger.info(f"Calling streaming tool {tool_name} with request: {request_data}")
            
            # For SSE streaming, use the SSE endpoint
            headers = {"Accept": "text/event-stream"}
            async with self.session.post(f"{self.server_url}/mcp/invoke", json=request_data, headers=headers) as response:
                if response.status == 200:
                    # Process SSE events
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        
                        # Skip empty lines and comments
                        if not line or line.startswith(':'):
                            continue
                            
                        # Process data lines
                        if line.startswith('data: '):
                            data_str = line[6:]  # Remove 'data: ' prefix
                            try:
                                data = json.loads(data_str)
                                
                                # Handle notifications
                                if "method" in data and data["method"].startswith("notifications/"):
                                    logger.info(f"Received notification: {data}")
                                    continue
                                    
                                # Handle normal responses
                                if "result" in data:
                                    yield data["result"]
                                elif "error" in data:
                                    logger.error(f"Error in streaming response: {data['error']}")
                                    yield {"error": data["error"]}
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to decode streaming result: {data_str}")
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to call streaming tool. Status: {response.status}, Error: {error_text}")
                    yield {"error": f"Failed to call streaming tool: {error_text}"}
        except Exception as e:
            logger.error(f"Error calling streaming tool: {str(e)}")
            yield {"error": f"Error calling streaming tool: {str(e)}"} 