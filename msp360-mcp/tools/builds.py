"""Builds tools for MSP360 MCP Server."""
from typing import Dict, Any, Optional, List
import logging
from services.msp360 import msp360_client
from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field
from tools import register_tool
import json

logger = logging.getLogger("msp360_mcp.tools")

class BuildsTools:
    """Tools for interacting with MSP360/CloudBerry software builds."""
    
    class BuildsParams(BaseModel):
        """Parameters model for filtering builds."""
        page: Optional[int] = Field(1, description="Page number starting from 1")
        limit: Optional[int] = Field(10, description="Number of items per page")
        edition: Optional[str] = Field(None, description="Filter by software edition")
    
    def __init__(self):
        """Initialize the builds tools."""
        self.client = msp360_client
        self._tool_definitions = {}
        self._register_tools()
        
    def _register_tools(self):
        """Register all builds tools with the tool registry."""
        # Define get_builds tool
        self._tool_definitions["get_builds"] = {
            "description": "Get a list of builds available to users",
            "function": self.get_builds,
            "parameter_descriptions": {
                "page": "Page number (default: 1)",
                "limit": "Number of items per page (default: 10)",
                "edition": "Filter by software edition (optional)"
            }
        }
        
        # Define request_custom_builds tool
        self._tool_definitions["request_custom_builds"] = {
            "description": "Request custom builds with specified editions",
            "function": self.request_custom_builds,
            "parameter_descriptions": {
                "build_data": "JSON data with build specifications"
            }
        }
        
        # Define get_available_versions tool
        self._tool_definitions["get_available_versions"] = {
            "description": "Get the latest available versions of builds",
            "function": self.get_available_versions,
            "parameter_descriptions": {
                "params": "Filter parameters (optional)"
            }
        }
        
        # Don't register tools globally here - let MCPServer handle that
        
    def get_tool_definitions(self) -> Dict[str, Any]:
        """Get definitions of all builds tools.
        
        Returns:
            Dictionary of tool definitions
        """
        return self._tool_definitions
        
    async def get_builds(self, page: Optional[int] = 1, limit: Optional[int] = 10, edition: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a list of builds available to users.
        
        Args:
            page: Page number (default: 1)
            limit: Number of items per page (default: 10)
            edition: Filter by software edition (optional)
            
        Returns:
            Dictionary with content array containing builds
        """
        logger.info(f"Getting builds with page={page}, limit={limit}, edition={edition}")
        
        query_params = {}
        
        # Add pagination
        effective_limit = limit if limit is not None else 10 # Default limit if None
        effective_page = page if page is not None else 1   # Default page if None

        query_params["skip"] = (effective_page - 1) * effective_limit
        query_params["take"] = effective_limit
            
        # Add filters
        if edition:
            query_params["edition"] = edition
        
        try:
            # Get the response from the client
            response = await self.client.get_builds(params=query_params)
            
            # Debug the response structure
            logger.info(f"API response type: {type(response)}, content: {response}")
            
            # Process the response into the required MCP format with text items
            result_content = []
            
            # Extract the builds data
            if isinstance(response, list):
                builds_data = response
            elif isinstance(response, dict):
                if 'items' in response and isinstance(response['items'], list):
                    builds_data = response['items']
                elif 'content' in response and isinstance(response['content'], list):
                    builds_data = response['content']
                else:
                    # Make another direct request to get the data
                    logger.info("No items or content array found, trying direct request")
                    async with self.client._client_session() as session:
                        direct_response = await session.get(
                            f"{self.client.base_url}/api/Builds",
                            params=query_params,
                            headers=await self.client.token_manager.get_auth_header()
                        )
                        if direct_response.status_code == 200:
                            data = direct_response.json()
                            if isinstance(data, list):
                                builds_data = data
                            elif isinstance(data, dict) and 'items' in data:
                                builds_data = data['items']
                            else:
                                builds_data = []
                        else:
                            builds_data = []
            else:
                builds_data = []
            
            # Format each build as a text item
            for build in builds_data:
                # Convert build to MCP-compatible text item
                formatted_text = f"Type: {build.get('Type', 'Unknown')}\nVersion: {build.get('Version', 'Unknown')}\nDownload Link: {build.get('DownloadLink', 'N/A')}"
                result_content.append({
                    "type": "text",
                    "text": formatted_text
                })
            
            return {"content": result_content}
            
        except Exception as e:
            logger.error(f"Error retrieving builds: {str(e)}")
            # Return a clear error message as text
            return {"content": [{"type": "text", "text": f"Failed to retrieve builds: {str(e)}"}]}
            
    async def request_custom_builds(self, build_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Request custom builds with specified editions.
        
        Args:
            build_data: JSON data with build specifications
            
        Returns:
            Dictionary with request result
        """
        logger.info(f"Requesting custom builds with data: {build_data}")
        
        try:
            # Parse JSON string if needed
            if isinstance(build_data, str):
                build_data = json.loads(build_data)
                
            # First, get available build versions to provide context
            versions_response = await self.get_available_versions({})
            
            # Try making the actual custom build request
            response = await self.client.request_custom_builds(build_data=build_data)
            
            # Format the response as text
            if isinstance(response, list):
                text_content = "Custom build request submitted successfully:\n\n" + "\n".join([str(item) for item in response])
            elif isinstance(response, dict):
                if 'error' in response:
                    # Handle error response from our improved client
                    text_content = f"Error requesting custom builds: {response.get('error')}\n\n"
                    text_content += f"Details: {response.get('detail', 'No details provided')}\n\n"
                    text_content += "This tool may not be available with your current account permissions.\n"
                    text_content += "Please try the get_builds tool instead to see available builds.\n\n"
                    text_content += "Available build versions:\n"
                    # Include version info for context
                    if isinstance(versions_response, dict) and 'content' in versions_response:
                        for item in versions_response['content']:
                            if 'text' in item:
                                text_content += f"- {item['text']}\n"
                else:
                    # Format success response with all available fields
                    text_content = "Custom build request submitted successfully:\n\n"
                    for key, value in response.items():
                        # Skip text field if we'll handle it specially
                        if key not in ['text']:
                            text_content += f"{key}: {value}\n"
                    
                    # Add text field if present, and any note about truncation
                    if 'text' in response:
                        text_content += f"\nResponse text: {response['text']}\n"
                        
                    if 'note' in response:
                        text_content += f"\n{response['note']}"
            else:
                text_content = f"Custom build request response: {str(response)}"
                
            return {"content": [{"type": "text", "text": text_content}]}
            
        except HTTPException as e:
            logger.error(f"Error requesting custom builds: {str(e)}")
            
            # Provide more helpful information for 500 errors
            if hasattr(e, 'status_code') and e.status_code == 500:
                error_text = "Error requesting custom builds: The server returned a 500 Internal Server Error.\n\n"
                error_text += "This could be due to one of the following reasons:\n"
                error_text += "1. Your account may not have permission to request custom builds\n"
                error_text += "2. The API endpoint may be temporarily unavailable\n"
                error_text += "3. The request format may not match what the server expects\n\n"
                
                # Get available versions for reference
                try:
                    available_versions = await self.client.get_available_versions()
                    if isinstance(available_versions, list):
                        error_text += "Available build types:\n"
                        for ver in available_versions:
                            error_text += f"- Type: {ver.get('Type')}, Version: {ver.get('Version')}\n"
                except Exception:
                    pass
                
                return {"content": [{"type": "text", "text": error_text}]}
            
            return {"content": [{"type": "text", "text": f"Error requesting custom builds: {str(e)}"}]}
        except Exception as e:
            logger.error(f"Error requesting custom builds: {str(e)}")
            error_text = f"Error requesting custom builds: {str(e)}\n\n"
            error_text += "This feature may not be available with your current MSP360 account permissions.\n"
            error_text += "Please try using the get_builds tool instead to see available builds."
            return {"content": [{"type": "text", "text": error_text}]}
            
    async def get_available_versions(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get the latest available versions of builds.
        
        Args:
            params: Filter parameters (optional)
            
        Returns:
            Dictionary with available versions
        """
        logger.info(f"Getting available versions with params: {params}")
        
        try:
            response = await self.client.get_available_versions(params=params)
            
            # Format the response as text
            if isinstance(response, list):
                formatted_items = []
                for item in response:
                    # Check if TypeName is available (from our enhanced client)
                    if 'TypeName' in item:
                        type_display = item.get('TypeName')
                    else:
                        # Fallback to raw Type if TypeName is not available
                        type_value = item.get('Type')
                        type_display = f"Type {type_value}"
                        
                    version = item.get('Version', 'Unknown')
                    formatted_items.append(f"Type: {type_display}, Version: {version}")
                
                text_content = "Available versions:\n\n" + "\n".join(formatted_items)
            elif isinstance(response, dict):
                text_content = "Available versions:\n\n" + "\n".join([f"{key}: {value}" for key, value in response.items()])
            else:
                text_content = f"Available versions response: {str(response)}"
                
            return {"content": [{"type": "text", "text": text_content}]}
            
        except Exception as e:
            logger.error(f"Error retrieving available versions: {str(e)}")
            return {"content": [{"type": "text", "text": f"Error retrieving available versions: {str(e)}"}]}
            
    def close(self) -> None:
        """Close any resources."""
        pass 