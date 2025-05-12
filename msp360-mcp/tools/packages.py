"""Packages tools for MSP360 MCP Server."""
from typing import Dict, Any, Optional, List
import logging
import json
from services.msp360 import msp360_client
from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field
from tools import register_tool

logger = logging.getLogger("msp360_mcp.tools")

class PackageTools:
    """Tools for interacting with MSP360/CloudBerry software packages."""
    
    class PackageParams(BaseModel):
        """Parameters model for filtering packages."""
        page: Optional[int] = Field(1, description="Page number starting from 1")
        limit: Optional[int] = Field(10, description="Number of items per page")
        name: Optional[str] = Field(None, description="Filter by package name")
    
    def __init__(self):
        """Initialize the package tools."""
        self.client = msp360_client
        self._tool_definitions = {}
        self._register_tools()
        
    def _register_tools(self):
        """Register all package tools with the tool registry."""
        # Define get_packages tool
        self._tool_definitions["get_packages"] = {
            "description": "Get a list of MSP360 software packages with optional filtering",
            "function": self.get_packages,
            "parameter_descriptions": {
                "params": "params parameter"
            }
        }
        
        # Define get_package tool
        self._tool_definitions["get_package"] = {
            "description": "Get a specific MSP360 software package by ID",
            "function": self.get_package,
            "parameter_descriptions": {
                "package_id": "Package ID"
            }
        }
        
        # Don't register tools globally here - let MCPServer handle that
    
    def get_tool_definitions(self) -> Dict[str, Any]:
        """Get definitions of all package tools.
        
        Returns:
            Dictionary of tool definitions
        """
        return self._tool_definitions
        
    async def get_packages(self, params: str = '{}') -> Dict[str, Any]:
        """
        Get a list of software packages with optional filtering.
        
        Args:
            params: Filter parameters as a JSON string
            
        Returns:
            Dictionary with packages data
        """
        logger.info(f"Getting packages with params: {params}")
        
        # Parse the JSON string to get parameters
        try:
            if params and params.strip():
                param_dict = json.loads(params)
            else:
                param_dict = {}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing parameters JSON: {str(e)}")
            return {"content": [], "error": f"Invalid JSON parameters: {str(e)}"}
        
        query_params = {}
        
        # Add pagination
        page = param_dict.get('page', 1)
        limit = param_dict.get('limit', 10)
        
        # Add pagination to query params
        query_params["page"] = page
        query_params["limit"] = limit
        
        # Add filters
        name = param_dict.get('name')
        if name:
            query_params["name"] = name
        
        try:
            response = await self.client.get_packages(params=query_params)
            
            # Debug: Log the raw response structure and content
            logger.info(f"Raw response type: {type(response)}")
            if isinstance(response, list):
                logger.info(f"Raw response is a list with {len(response)} items")
                if response:
                    logger.info(f"First item keys: {list(response[0].keys())}")
                    logger.info(f"First item: {json.dumps(response[0], indent=2)}")
            elif isinstance(response, dict):
                logger.info(f"Raw response is a dict with keys: {list(response.keys())}")
                if 'items' in response:
                    logger.info(f"Contains 'items' list with {len(response['items'])} items")
                    if response['items']:
                        logger.info(f"First item keys: {list(response['items'][0].keys())}")
                        logger.info(f"First item: {json.dumps(response['items'][0], indent=2)}")
            else:
                logger.info(f"Raw response: {response}")
            
            # Process packages into a content array format for MCP
            result_content = []
            
            # Extract the packages data
            if isinstance(response, list):
                packages_data = response
            elif isinstance(response, dict):
                if 'items' in response and isinstance(response['items'], list):
                    packages_data = response['items']
                elif 'content' in response and isinstance(response['content'], list):
                    packages_data = response['content']
                else:
                    packages_data = []
            else:
                packages_data = []
            
            logger.info(f"Retrieved {len(packages_data)} packages")
            
            # Apply limit directly in case the API didn't respect it
            if limit and isinstance(limit, int) and limit > 0 and len(packages_data) > limit:
                packages_data = packages_data[:limit]
                logger.info(f"Applied limit {limit}, reduced to {len(packages_data)} packages")
            
            # Format each package as a text item
            for package in packages_data:
                # Explicitly log all keys for debugging
                logger.info(f"Package keys: {list(package.keys())}")
                
                # Extract the ID properly, checking multiple possible key formats
                package_id = 'N/A'
                
                # Check for various possible ID field names
                possible_id_fields = ['Id', 'ID', 'id', 'PackageId', 'PackageID', 'packageId', 'packageID']
                for id_field in possible_id_fields:
                    if id_field in package and package[id_field] is not None:
                        package_id = package[id_field]
                        logger.info(f"Found ID in field {id_field}: {package_id}")
                        break
                
                # Convert package to MCP-compatible text item
                formatted_text = f"ID: {package_id}\nName: {package.get('Name', 'N/A')}"
                
                # Add Cost information if available
                if 'Cost' in package:
                    formatted_text += f"\nCost: {package.get('Cost', 0)}"
                
                # Add Description
                formatted_text += f"\nDescription: {package.get('Description', '')}"
                
                # Add Storage Limit if available
                if 'StorageLimit' in package:
                    storage_limit = package.get('StorageLimit')
                    if storage_limit == 0:
                        formatted_text += f"\nStorage Limit: Unlimited"
                    else:
                        # Format storage limit in GB
                        formatted_limit = f"{storage_limit} GB"
                        formatted_text += f"\nStorage Limit: {formatted_limit}"
                
                # Add Enabled status
                if 'Enabled' in package:
                    formatted_text += f"\nEnabled: {package.get('Enabled', True)}"
                
                # Add Restore Limit information if available
                if 'UseRestoreLimit' in package and package.get('UseRestoreLimit'):
                    formatted_text += f"\nUse Restore Limit: Yes"
                    if 'RestoreLimit' in package:
                        formatted_text += f"\nRestore Limit: {package.get('RestoreLimit', 0)} GB"
                    
                    # Add Glacier Restore information if available
                    if 'isGlacierRestoreLimit' in package and package.get('isGlacierRestoreLimit'):
                        formatted_text += f"\nGlacier Restore Limit: Yes"
                        if 'GlacierRestoreType' in package:
                            glacier_type = package.get('GlacierRestoreType', 0)
                            glacier_type_name = "Standard"
                            if glacier_type == 1:
                                glacier_type_name = "Expedited"
                            elif glacier_type == 2:
                                glacier_type_name = "Bulk"
                            formatted_text += f"\nGlacier Restore Type: {glacier_type_name}"
                
                result_content.append({
                    "type": "text",
                    "text": formatted_text
                })
            
            return {"content": result_content}
        except Exception as e:
            logger.error(f"Error retrieving packages: {str(e)}")
            return {"content": [], "error": str(e)}
            
    async def get_package(self, package_id: str) -> Dict[str, Any]:
        """
        Get a specific software package by ID.
        
        Args:
            package_id: The ID of the package to retrieve
            
        Returns:
            Dictionary with package data
        """
        logger.info(f"Getting package with ID: {package_id}")
        
        try:
            # Call the MSP360 API to get the package details
            package = await self.client.get_package(package_id=package_id)
            logger.debug(f"Retrieved package data: {json.dumps(package)[:500] if package else 'None'}")
            
            # Process the package data into MCP-compatible format
            result_content = []
            
            # Handle empty or null response
            if package is None or (isinstance(package, dict) and not package):
                logger.warning(f"No package data found for ID: {package_id}")
                return {
                    "content": [{
                        "type": "text",
                        "text": f"No package data found for ID: {package_id}"
                    }],
                    "error": f"Package not found: {package_id}"
                }
            
            # Format package as a text item
            if isinstance(package, dict):
                # Extract key information from the package
                formatted_text = f"Package: {package.get('Name', 'N/A')}\n"
                
                # Extract ID, ensuring it's properly displayed
                package_id_value = package.get('Id', package_id)
                if package_id_value is None:
                    package_id_value = "N/A"
                formatted_text += f"ID: {package_id_value}\n"
                
                # Add additional information
                formatted_text += f"Description: {package.get('Description', 'N/A')}\n"
                
                # Add Cost information instead of Price
                formatted_text += f"Cost: {package.get('Cost', 0)}"
                
                # Add Storage Limit if available
                if 'StorageLimit' in package:
                    storage_limit = package.get('StorageLimit')
                    if storage_limit == 0:
                        formatted_text += f"\nStorage Limit: Unlimited"
                    else:
                        # Format storage limit in GB
                        formatted_limit = f"{storage_limit} GB"
                        formatted_text += f"\nStorage Limit: {formatted_limit}"
                
                # Add Enabled status
                if 'Enabled' in package:
                    formatted_text += f"\nEnabled: {package.get('Enabled', True)}"
                
                # Add Restore Limit information if available
                if 'UseRestoreLimit' in package and package.get('UseRestoreLimit'):
                    formatted_text += f"\nUse Restore Limit: Yes"
                    if 'RestoreLimit' in package:
                        formatted_text += f"\nRestore Limit: {package.get('RestoreLimit', 0)} GB"
                    
                        # Add Glacier Restore information if available
                        if 'isGlacierRestoreLimit' in package and package.get('isGlacierRestoreLimit'):
                            formatted_text += f"\nGlacier Restore Limit: Yes"
                            if 'GlacierRestoreType' in package:
                                glacier_type = package.get('GlacierRestoreType', 0)
                                glacier_type_name = "Standard"
                                if glacier_type == 1:
                                    glacier_type_name = "Expedited"
                                elif glacier_type == 2:
                                    glacier_type_name = "Bulk"
                                formatted_text += f"\nGlacier Restore Type: {glacier_type_name}"
                
                if 'Features' in package and package['Features']:
                    formatted_text += "\n\nFeatures:"
                    for feature in package['Features']:
                        formatted_text += f"\n- {feature}"
                
                result_content.append({
                    "type": "text",
                    "text": formatted_text
                })
            elif isinstance(package, list) and len(package) > 0:
                # If API returned a list, take the first item (assuming it's the requested package)
                first_package = package[0]
                formatted_text = f"Package: {first_package.get('Name', 'N/A')}\n"
                formatted_text += f"ID: {first_package.get('Id', package_id)}\n"
                formatted_text += f"Description: {first_package.get('Description', 'N/A')}\n"
                formatted_text += f"Cost: {first_package.get('Cost', 0)}"
                
                # Add Storage Limit if available
                if 'StorageLimit' in first_package:
                    storage_limit = first_package.get('StorageLimit')
                    if storage_limit == 0:
                        formatted_text += f"\nStorage Limit: Unlimited"
                    else:
                        # Format storage limit in GB
                        formatted_limit = f"{storage_limit} GB"
                        formatted_text += f"\nStorage Limit: {formatted_limit}"
                
                # Add other relevant fields
                if 'Enabled' in first_package:
                    formatted_text += f"\nEnabled: {first_package.get('Enabled', True)}"
                
                result_content.append({
                    "type": "text",
                    "text": formatted_text
                })
            else:
                # Fallback for unexpected response format
                result_content.append({
                    "type": "text",
                    "text": f"Unexpected package data format for ID {package_id}: {json.dumps(package)[:500]}"
                })
            
            return {"content": result_content}
        except HTTPException as e:
            # Handle API errors
            error_message = f"Error retrieving package {package_id}: {e.status_code}: {e.detail}"
            logger.error(error_message)
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error: {error_message}"
                }],
                "error": error_message
            }
        except Exception as e:
            error_message = f"Error retrieving package {package_id}: {str(e)}"
            logger.error(error_message)
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error: {error_message}"
                }],
                "error": error_message
            }
            
    def close(self) -> None:
        """Close any resources."""
        pass

# No singleton instance here - let MCPServer create it 