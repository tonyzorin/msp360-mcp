"""Licenses tools for MSP360 MCP Server."""
from typing import Dict, Any, Optional, List
import logging
from services.msp360 import msp360_client
from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field
from tools import register_tool
import json

logger = logging.getLogger("msp360_mcp.tools")

class LicensesTools:
    """Tools for interacting with MSP360/CloudBerry licenses."""
    
    class LicenseParams(BaseModel):
        """Parameters model for filtering licenses."""
        page: Optional[int] = Field(1, description="Page number starting from 1")
        limit: Optional[int] = Field(10, description="Number of items per page")
        user_id: Optional[str] = Field(None, description="Filter by user ID")
        company_id: Optional[str] = Field(None, description="Filter by company ID")
        edition: Optional[str] = Field(None, description="Filter by software edition")
        license_type: Optional[str] = Field(None, description="Filter by license type")
        status: Optional[str] = Field(None, description="Filter by license status")
    
    def __init__(self):
        """Initialize the licenses tools."""
        self.client = msp360_client
        self._tool_definitions = {}
        self._register_tools()
        
    def _register_tools(self):
        """Define all licenses tools but don't register them globally."""
        self._tool_definitions["get_licenses"] = {
            "description": "Get a list of licenses with optional filtering",
            "function": self.get_licenses,
            "parameter_descriptions": {
                "params": "JSON string with filter parameters"
            }
        }
        
        self._tool_definitions["get_license"] = {
            "description": "Get a specific license by ID",
            "function": self.get_license,
            "parameter_descriptions": {
                "license_id": "License ID"
            }
        }
        
        self._tool_definitions["grant_license"] = {
            "description": "Grant a license to a user",
            "function": self.grant_license,
            "parameter_descriptions": {
                "license_data": "JSON data with license and user information"
            }
        }
        
        self._tool_definitions["release_license"] = {
            "description": "Release a license from a user",
            "function": self.release_license,
            "parameter_descriptions": {
                "license_data": "JSON data with license information"
            }
        }
        
        self._tool_definitions["revoke_license"] = {
            "description": "Revoke a license from a user",
            "function": self.revoke_license,
            "parameter_descriptions": {
                "license_data": "JSON data with license information"
            }
        }
            
    def get_tool_definitions(self) -> Dict[str, Any]:
        """Get definitions of all licenses tools.
        
        Returns:
            Dictionary of tool definitions
        """
        return self._tool_definitions
        
    async def get_licenses(self, params: str = '{}') -> Dict[str, Any]:
        """
        Get a list of licenses with optional filtering.
        
        Args:
            params: JSON string with filter parameters
            
        Returns:
            Dictionary with licenses data
        """
        logger.info(f"Getting licenses with params: {params}")
        
        # Parse the JSON string to get parameters
        try:
            if params and params.strip():
                param_dict = json.loads(params)
            else:
                param_dict = {}
            
            # Extract parameters with defaults
            page = param_dict.get('page', 1)
            limit = param_dict.get('limit', 10)
            
            # Additional parameters
            query_params = {}
            if 'company_id' in param_dict:
                query_params['companyId'] = param_dict['company_id']
            if 'status' in param_dict:
                query_params['status'] = param_dict['status']
            
            # Set pagination parameters directly (client will handle conversion)
            query_params['limit'] = 100  # Request a larger number to filter client-side
            query_params['page'] = page
            
            # Call the API to get licenses
            licenses = await self.client.get_licenses(params=query_params)
            
            # Process the response into MCP-compatible format
            result_content = []
            
            # Process the licenses data
            license_list = []
            if isinstance(licenses, list):
                license_list = licenses
            elif isinstance(licenses, dict) and 'licenses' in licenses:
                license_list = licenses.get('licenses', [])
            
            # Apply limit manually if API doesn't respect it
            if len(license_list) > limit:
                logger.info(f"Retrieved {len(license_list)} licenses, limiting to {limit} as requested")
                license_list = license_list[:limit]
            
            # Format the results
            if not license_list:
                result_content.append({
                    "type": "text",
                    "text": "No licenses found"
                })
            else:
                # Format each license as a text item
                for license in license_list:
                    license_info = []
                    for key, value in license.items():
                        license_info.append(f"{key}: {value}")
                    
                    result_content.append({
                        "type": "text",
                        "text": "\n".join(license_info)
                    })
            
            return {"content": result_content}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing parameters JSON: {str(e)}")
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error parsing parameters: {str(e)}"
                }],
                "error": f"Invalid JSON parameters: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error retrieving licenses: {str(e)}")
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error retrieving licenses: {str(e)}"
                }],
                "error": f"Failed to retrieve licenses: {str(e)}"
            }
            
    async def get_license(self, license_id: str) -> Dict[str, Any]:
        """
        Get a specific license by ID.
        
        Args:
            license_id: The ID of the license to retrieve
            
        Returns:
            Dictionary with license data
        """
        logger.info(f"Getting license with ID: {license_id}")
        
        try:
            result = await self.client.get_license(license_id=license_id)
            
            # Format license data
            license_info = []
            if isinstance(result, dict):
                for key, value in result.items():
                    license_info.append(f"{key}: {value}")
                
                return {
                    "content": [{
                        "type": "text",
                        "text": "\n".join(license_info)
                    }]
                }
            else:
                return {
                    "content": [{
                        "type": "text",
                        "text": f"License data: {json.dumps(result)}"
                    }]
                }
        except Exception as e:
            logger.error(f"Error retrieving license {license_id}: {str(e)}")
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error retrieving license {license_id}: {str(e)}"
                }],
                "error": f"Error retrieving license {license_id}: {str(e)}"
            }
            
    async def grant_license(self, license_data: str) -> Dict[str, Any]:
        """Grant a license to a user.
        
        Args:
            license_data: JSON data with license and user information
            
        Returns:
            Dictionary with result information
        """
        logger.info(f"Granting license with data: {license_data}")
        
        try:
            # Parse the JSON string to get data
            if isinstance(license_data, str):
                license_dict = json.loads(license_data)
            else:
                license_dict = license_data
                
            # Call the API to grant the license
            response = await self.client.grant_license(license_dict)
            
            # Process the response
            if isinstance(response, dict):
                if 'status' in response and response['status'] == 'success':
                    formatted_text = f"License granted successfully: {json.dumps(response)}"
                elif 'text' in response:
                    # Try to parse the text field if it contains JSON
                    text_content = response['text']
                    try:
                        if isinstance(text_content, str) and (text_content.startswith('{') or text_content.startswith('[')):
                            parsed_text = json.loads(text_content)
                            formatted_text = f"License grant response: {json.dumps(parsed_text, indent=2)}"
                        else:
                            formatted_text = f"License grant response: {text_content}"
                    except json.JSONDecodeError:
                        formatted_text = f"License grant response: {text_content}"
                else:
                    formatted_text = f"License grant response: {json.dumps(response)}"
            elif isinstance(response, list):
                formatted_text = f"License grant response: {json.dumps(response)}"
            else:
                formatted_text = f"License grant response: {str(response)}"
                
            return {"content": [{"type": "text", "text": formatted_text}]}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing license data JSON: {str(e)}")
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error parsing license data: {str(e)}"
                }],
                "error": f"Invalid JSON: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error granting license: {str(e)}")
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error granting license: {str(e)}"
                }],
                "error": str(e)
            }
            
    async def release_license(self, license_data: str) -> Dict[str, Any]:
        """
        Release a license from a user.
        
        Args:
            license_data: JSON data with license information
            
        Returns:
            Dictionary with release result
        """
        logger.info(f"Releasing license with data: {license_data}")
        
        try:
            # Parse the JSON string
            try:
                parsed_data = json.loads(license_data)
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON license data: {str(e)}")
                return {
                    "content": [{
                        "type": "text",
                        "text": f"Invalid JSON license data: {str(e)}"
                    }],
                    "error": f"Invalid JSON license data: {str(e)}"
                }
                
            result = await self.client.release_license(license_data=parsed_data)
            return {
                "content": [{
                    "type": "text",
                    "text": f"License released successfully: {json.dumps(result)}"
                }]
            }
        except Exception as e:
            logger.error(f"Error releasing license: {str(e)}")
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error releasing license: {str(e)}"
                }],
                "error": f"Error releasing license: {str(e)}"
            }
            
    async def revoke_license(self, license_data: str) -> Dict[str, Any]:
        """
        Revoke a license from a user.
        
        Args:
            license_data: JSON data with license information
            
        Returns:
            Dictionary with revoke result
        """
        logger.info(f"Revoking license with data: {license_data}")
        
        try:
            # Parse the JSON string
            try:
                parsed_data = json.loads(license_data)
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON license data: {str(e)}")
                return {
                    "content": [{
                        "type": "text",
                        "text": f"Invalid JSON license data: {str(e)}"
                    }],
                    "error": f"Invalid JSON license data: {str(e)}"
                }
                
            result = await self.client.revoke_license(license_data=parsed_data)
            return {
                "content": [{
                    "type": "text",
                    "text": f"License revoked successfully: {json.dumps(result)}"
                }]
            }
        except Exception as e:
            logger.error(f"Error revoking license: {str(e)}")
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error revoking license: {str(e)}"
                }],
                "error": f"Error revoking license: {str(e)}"
            }
            
    def close(self) -> None:
        """Close any resources."""
        pass 