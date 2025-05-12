"""Base administrator tools for MSP360 MCP Server."""
from typing import Dict, Any, Optional, List, AsyncGenerator
import logging
import json
from services.msp360 import msp360_client
from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field
from tools.utils import humanize_time, format_json_field, parse_params_json

from .admin_helpers import format_admin_data, format_permissions
from .admin_crud import (
    get_admin_list, 
    get_admin_detail, 
    create_admin_entry, 
    update_admin_entry, 
    delete_admin_entry
)

logger = logging.getLogger("msp360_mcp.tools")

class AdminTools:
    """Tools for interacting with MSP360/CloudBerry administrators."""
    
    class AdminParams(BaseModel):
        """Parameters model for filtering administrators."""
        page: Optional[int] = Field(1, description="Page number starting from 1")
        limit: Optional[int] = Field(10, description="Number of items per page")
        name: Optional[str] = Field(None, description="Filter by administrator name")
    
    def __init__(self):
        """Initialize the admin tools."""
        self.client = msp360_client
        self._tool_definitions = {}
        self._register_tools()
        logger.info("AdminTools initialized")
        
    def _register_tools(self):
        """Register all admin tools with the tool registry."""
        # Define get_admins tool with streaming support
        self._tool_definitions["get_admins"] = {
            "name": "get_admins",
            "description": "Get a list of MSP360 administrators with optional filtering",
            "function": self.get_admins,
            "parameters": {
                "params": {
                    "type": "string",
                    "description": "JSON string with filter parameters (page, limit, name)"
                }
            },
            "streaming": True,
            "parameter_descriptions": {
                "params": "JSON string with filter parameters (page, limit, name)"
            }
        }
        
        # Define get_admin tool
        self._tool_definitions["get_admin"] = {
            "name": "get_admin",
            "description": "Get a specific MSP360 administrator by ID",
            "function": self.get_admin,
            "parameters": {
                "admin_id": {
                    "type": "string",
                    "description": "Administrator ID"
                }
            },
            "parameter_descriptions": {
                "admin_id": "Administrator ID"
            }
        }
        
        # Define create_admin tool
        self._tool_definitions["create_admin"] = {
            "name": "create_admin",
            "description": "Create a new MSP360 administrator",
            "function": self.create_admin,
            "parameters": {
                "admin_data": {
                    "type": "string",
                    "description": "Administrator data in JSON format"
                }
            },
            "parameter_descriptions": {
                "admin_data": "Administrator data in JSON format"
            }
        }
        
        # Define update_admin tool
        self._tool_definitions["update_admin"] = {
            "name": "update_admin",
            "description": "Update an existing MSP360 administrator",
            "function": self.update_admin,
            "parameters": {
                "admin_data": {
                    "type": "string",
                    "description": "Administrator data in JSON format"
                }
            },
            "parameter_descriptions": {
                "admin_data": "Administrator data in JSON format"
            }
        }
        
        # Define delete_admin tool
        self._tool_definitions["delete_admin"] = {
            "name": "delete_admin",
            "description": "Delete a MSP360 administrator by ID",
            "function": self.delete_admin,
            "parameters": {
                "admin_id": {
                    "type": "string",
                    "description": "Administrator ID"
                }
            },
            "parameter_descriptions": {
                "admin_id": "Administrator ID"
            }
        }
    
    def get_tool_definitions(self) -> Dict[str, Any]:
        """Get definitions of all admin tools.
        
        Returns:
            Dictionary of tool definitions
        """
        return self._tool_definitions
    
    async def get_admins(self, params: str = '{}') -> AsyncGenerator[Dict[str, Any], None]:
        """
        Get a list of administrators with optional filtering (streaming).
        
        Args:
            params: JSON string with filter parameters
            
        Yields:
            Dictionary with administrator data, one at a time
        """
        logger.info(f"Getting administrators with params: {params}")
        async for result in get_admin_list(self.client, params):
            yield result
    
    async def get_admin(self, admin_id: str) -> Dict[str, Any]:
        """
        Get a specific administrator by ID.
        
        Args:
            admin_id: Administrator ID
            
        Returns:
            Dictionary with administrator data
        """
        logger.info(f"Getting administrator with ID: {admin_id}")
        return await get_admin_detail(self.client, admin_id)
    
    async def create_admin(self, admin_data: str) -> Dict[str, Any]:
        """
        Create a new administrator.
        
        Args:
            admin_data: Administrator data in JSON format
            
        Returns:
            Dictionary with created administrator data
        """
        logger.info(f"Creating administrator with data: {admin_data}")
        return await create_admin_entry(self.client, admin_data)
    
    async def update_admin(self, admin_data: str) -> Dict[str, Any]:
        """
        Update an existing administrator.
        
        Args:
            admin_data: Administrator data in JSON format
            
        Returns:
            Dictionary with updated administrator data
        """
        logger.info(f"Updating administrator with data: {admin_data}")
        return await update_admin_entry(self.client, admin_data)
    
    async def delete_admin(self, admin_id: str) -> Dict[str, Any]:
        """
        Delete an administrator by ID.
        
        Args:
            admin_id: Administrator ID
            
        Returns:
            Dictionary with result
        """
        logger.info(f"Deleting administrator with ID: {admin_id}")
        return await delete_admin_entry(self.client, admin_id)
    
    def close(self) -> None:
        """Close resources."""
        logger.info("Closing administrator tools resources")

# Create instance for dependency injection
admin_tools = AdminTools() 