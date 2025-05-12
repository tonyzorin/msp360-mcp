"""Destination management tools for MSP360 MCP Server."""
from typing import Dict, Any, Optional, List
import logging
import json
from services.msp360 import msp360_client
from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field
from tools import register_tool
from tools.utils import format_size, parse_params_json, normalize_field_names

logger = logging.getLogger("msp360_mcp.tools")

class DestinationTools:
    """Tools for interacting with MSP360/CloudBerry storage destinations."""
    
    def __init__(self):
        """Initialize the destination tools."""
        self.client = msp360_client
        self._tool_definitions = {}
        self._register_tools()
        logger.info("DestinationTools initialized")
        
    def _register_tools(self):
        """Define all destination tools but don't register them globally."""
        self._tool_definitions["get_user_destinations"] = {
            "description": "Get destinations of a specific MSP360 user",
            "function": self.get_user_destinations,
            "parameter_descriptions": {
                "user_email": "User email"
            }
        }
        
        self._tool_definitions["add_user_destination"] = {
            "description": "Add a destination to a MSP360 user",
            "function": self.add_user_destination,
            "parameter_descriptions": {
                "destination_data": "Destination data in JSON format"
            }
        }
        
        self._tool_definitions["edit_user_destination"] = {
            "description": "Edit a destination of a MSP360 user",
            "function": self.edit_user_destination,
            "parameter_descriptions": {
                "destination_data": "Destination data in JSON format"
            }
        }
        
        self._tool_definitions["delete_user_destination"] = {
            "description": "Delete a destination of a MSP360 user",
            "function": self.delete_user_destination,
            "parameter_descriptions": {
                "destination_id": "Destination ID",
                "user_id": "Optional User ID (required by the API)"
            }
        }
        
    def get_tool_definitions(self) -> Dict[str, Any]:
        """Get definitions of all destination tools.
        
        Returns:
            Dictionary of tool definitions
        """
        return self._tool_definitions
    
    def _format_destinations(self, destinations: List[Dict], user_identifier: str) -> str:
        """Format destinations into readable text.
        
        Args:
            destinations: List of destination dictionaries
            user_identifier: User email or ID for context
            
        Returns:
            Formatted text representation of destinations
        """
        if not destinations:
            return f"No destinations found for user {user_identifier}"
            
        formatted_text = f"Destinations for user {user_identifier}:\n"
        
        for i, dest in enumerate(destinations, 1):
            # Extract the destination ID
            dest_id = dest.get("ID", dest.get("Id", dest.get("id", dest.get("DestinationID", "N/A"))))
            
            # Extract other key information
            display_name = dest.get("DestinationDisplayName", dest.get("DisplayName", "N/A"))
            account_name = dest.get("AccountDisplayName", dest.get("AccountName", dest.get("Account", "N/A")))
            path = dest.get("Destination", dest.get("Path", "N/A"))
            
            # Format output
            formatted_text += f"  {i}. {display_name} ({account_name})\n"
            formatted_text += f"     Path: {path}\n"
            formatted_text += f"     ID: {dest_id}\n"
            
            if i < len(destinations):
                formatted_text += "\n"
                
        return formatted_text
    
    async def get_user_destinations(self, user_email: str) -> Dict[str, Any]:
        """
        Get destinations of a specific user.
        
        Args:
            user_email: User email or ID
            
        Returns:
            Dictionary with destinations
        """
        logger.info(f"Getting destinations for user: {user_email}")
        
        try:
            # Directly call the get_user_destinations method from the client
            destinations = await self.client.get_user_destinations(user_email=user_email)
            
            # If destinations were found, format and return them
            if destinations:
                return {
                    "content": [{
                        "type": "text",
                        "text": self._format_destinations(destinations, user_email)
                    }]
                }
            
            # If no destinations were found
            return {
                "content": [{
                    "type": "text",
                    "text": f"No destinations found for user {user_email}"
                }]
            }
            
        except Exception as e:
            logger.error(f"Error getting destinations: {str(e)}", exc_info=True)
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error getting destinations: {str(e)}"
                }],
                "error": str(e)
            }
    
    async def add_user_destination(self, destination_data: str) -> Dict[str, Any]:
        """
        Add a destination to a user.
        
        Args:
            destination_data: Destination data in JSON format
            
        Returns:
            Dictionary with added destination data
        """
        logger.info(f"Adding destination with data: {destination_data}")
        
        try:
            # Parse the JSON destination data
            parsed_data = parse_params_json(destination_data, {})
            if not parsed_data:
                return {
                    "content": [{
                        "type": "text",
                        "text": "Error parsing JSON destination data: Empty or invalid JSON"
                    }],
                    "error": "Invalid JSON data"
                }
            
            # Validate and normalize field names - the API expects camelCase
            required_fields_map = {
                "userid": "UserID",
                "user_id": "UserID",
                "accountid": "AccountID",
                "account_id": "AccountID",
                "destination": "Destination",
                "packageid": "PackageID",
                "package_id": "PackageID"
            }
            
            normalized_data = normalize_field_names(parsed_data, required_fields_map)
            
            # Check for missing required fields
            missing_fields = []
            for required_key in ["UserID", "AccountID", "Destination", "PackageID"]:
                if required_key not in normalized_data:
                    missing_fields.append(required_key)
            
            if missing_fields:
                error_msg = f"Missing required fields: {', '.join(missing_fields)}"
                logger.error(error_msg)
                return {
                    "content": [{
                        "type": "text",
                        "text": f"{error_msg}\n\nRequired fields: UserID, AccountID, Destination, PackageID"
                    }],
                    "error": error_msg
                }
            
            # Get the account ID and user ID from the normalized data
            account_id = normalized_data.get("AccountID")
            
            # Try different endpoint formats since the API requires specific endpoints
            all_errors = []
            
            # Format 1: Use the /api/Accounts/{accountId}/Destinations endpoint according to Swagger
            try:
                # Make a copy of the data without the AccountID since it's in the URL
                endpoint_data = normalized_data.copy()
                if "AccountID" in endpoint_data:
                    endpoint_data.pop("AccountID")
                
                logger.info(f"Trying Accounts endpoint format: /api/Accounts/{account_id}/Destinations")
                result = await self.client._make_request(
                    method="POST", 
                    endpoint=f"/api/Accounts/{account_id}/Destinations", 
                    json_data=endpoint_data
                )
                
                # If successful, return the result
                return {
                    "content": [{
                        "type": "text",
                        "text": f"Successfully added destination to user. Result: {json.dumps(result, indent=2)}"
                    }]
                }
            except Exception as e:
                error = f"Accounts endpoint failed: {str(e)}"
                all_errors.append(error)
                logger.warning(error)
            
            # Format 2: Try with DestinationDisplayName field if not already provided
            try:
                endpoint_data = normalized_data.copy()
                
                # Ensure there's a display name
                if "DestinationDisplayName" not in endpoint_data:
                    endpoint_data["DestinationDisplayName"] = endpoint_data.get("DestinationDisplayName", f"MCP Created - {endpoint_data['Destination']}")
                
                if "AccountID" in endpoint_data:
                    endpoint_data.pop("AccountID")
                
                logger.info(f"Trying Accounts endpoint with display name: /api/Accounts/{account_id}/Destinations")
                result = await self.client._make_request(
                    method="POST", 
                    endpoint=f"/api/Accounts/{account_id}/Destinations", 
                    json_data=endpoint_data
                )
                
                # If successful, return the result
                return {
                    "content": [{
                        "type": "text",
                        "text": f"Successfully added destination with display name. Result: {json.dumps(result, indent=2)}"
                    }]
                }
            except Exception as e:
                error = f"Accounts endpoint with display name failed: {str(e)}"
                all_errors.append(error)
                logger.warning(error)
            
            # Format 3: Try Accounts/AddDestination endpoint (legacy)
            try:
                logger.info(f"Trying alternative endpoint /api/Accounts/AddDestination directly")
                result = await self.client._make_request(
                    method="POST", 
                    endpoint="/api/Accounts/AddDestination", 
                    json_data=normalized_data
                )
                return {
                    "content": [{
                        "type": "text",
                        "text": f"Successfully added destination using alternative endpoint. Result: {json.dumps(result, indent=2)}"
                    }]
                }
            except Exception as e:
                error = f"Alternative endpoint failed: {str(e)}"
                all_errors.append(error)
                logger.warning(error)
            
            # If all formats failed, return detailed error information
            error_msg = "Failed to add destination. The MSP360 API requires specific endpoint formats."
            error_details = "\n\n".join([f"Attempt {i+1}: {err}" for i, err in enumerate(all_errors)])
            logger.error(f"{error_msg}\n{error_details}")
            
            return {
                "content": [{
                    "type": "text",
                    "text": f"{error_msg}\n\nErrors encountered:\n{error_details}\n\nData provided:\n{json.dumps(normalized_data, indent=2)}"
                }],
                "error": error_msg
            }
        except Exception as e:
            logger.error(f"Error adding destination: {str(e)}", exc_info=True)
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error adding destination: {str(e)}"
                }],
                "error": str(e)
            }
    
    async def edit_user_destination(self, destination_data: str) -> Dict[str, Any]:
        """
        Edit a destination of a user.
        
        Args:
            destination_data: Destination data in JSON format
            
        Returns:
            Dictionary with updated destination data
        """
        logger.info(f"Editing destination with data: {destination_data}")
        
        try:
            # Parse the JSON destination data
            parsed_data = parse_params_json(destination_data, {})
            if not parsed_data:
                return {
                    "content": [{
                        "type": "text",
                        "text": "Invalid JSON destination data: Empty or invalid JSON"
                    }],
                    "error": "Invalid JSON data"
                }
                
            result = await self.client.edit_user_destination(destination_data=parsed_data)
            return {
                "content": [{
                    "type": "text",
                    "text": f"Destination edited successfully: {json.dumps(result, indent=2)}"
                }]
            }
        except Exception as e:
            logger.error(f"Error editing destination: {str(e)}")
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error editing destination: {str(e)}"
                }],
                "error": str(e)
            }
    
    async def delete_user_destination(self, destination_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Delete a destination of a user.
        
        Args:
            destination_id: Destination ID
            user_id: Optional User ID (required by the API)
            
        Returns:
            Dictionary with result
        """
        logger.info(f"Deleting destination with ID: {destination_id}, user_id: {user_id}")
        
        try:
            # Validate destination ID
            if not destination_id or not isinstance(destination_id, str):
                error_msg = "Invalid destination ID. Please provide a valid destination ID."
                logger.error(error_msg)
                return {
                    "content": [{
                        "type": "text",
                        "text": error_msg
                    }],
                    "error": error_msg
                }
            
            # First, if user_id is provided, get the user to find the AccountID
            account_id = None
            if user_id:
                try:
                    user_result = await self.client.get_user(user_id=user_id)
                    if user_result:
                        # Look for AccountID in the user data
                        account_id = user_result.get('AccountID')
                        if account_id:
                            logger.info(f"Found account ID: {account_id} for user ID: {user_id}")
                except Exception as e:
                    logger.warning(f"Error getting user data: {str(e)}")
            
            # Try different approaches based on available information
            error_messages = []
            
            # Attempt 1: If we have account_id, try the account-based endpoint
            if account_id:
                try:
                    logger.info(f"Trying to delete destination using account endpoint: /api/Accounts/{account_id}/Destinations/{destination_id}")
                    result = await self.client._make_request(
                        method="DELETE", 
                        endpoint=f"/api/Accounts/{account_id}/Destinations/{destination_id}"
                    )
                    # If we reach here, it was successful
                    return {
                        "content": [{
                            "type": "text",
                            "text": f"Destination with ID {destination_id} was successfully deleted from account {account_id}."
                        }]
                    }
                except Exception as e:
                    error_messages.append(f"Account endpoint failed: {str(e)}")
                    logger.warning(f"Deleting destination using account endpoint failed: {str(e)}")
            
            # Attempt 2: Try standard Destinations endpoint with UserID parameter
            if user_id:
                try:
                    params = {"UserID": user_id}
                    logger.info(f"Trying standard endpoint with UserID param: /api/Destinations/{destination_id}?UserID={user_id}")
                    result = await self.client._make_request(
                        method="DELETE", 
                        endpoint=f"/api/Destinations/{destination_id}", 
                        params=params
                    )
                    # If we reach here, it was successful
                    return {
                        "content": [{
                            "type": "text",
                            "text": f"Destination with ID {destination_id} was successfully deleted."
                        }]
                    }
                except Exception as e:
                    error_messages.append(f"Standard endpoint with UserID failed: {str(e)}")
                    logger.warning(f"Standard request with UserID parameter failed: {str(e)}")
            
            # Attempt 3: Last resort - try without user ID
            try:
                logger.info(f"Trying destination endpoint without parameters: /api/Destinations/{destination_id}")
                result = await self.client._make_request(
                    method="DELETE", 
                    endpoint=f"/api/Destinations/{destination_id}"
                )
                # If we reach here, it was successful
                return {
                    "content": [{
                        "type": "text",
                        "text": f"Destination with ID {destination_id} was successfully deleted."
                    }]
                }
            except Exception as e:
                error_messages.append(f"Simple endpoint failed: {str(e)}")
                logger.warning(f"Simple endpoint request failed: {str(e)}")
            
            # If we got here, all attempts failed
            error_msg = f"Failed to delete destination. The API requires specific parameters or authorization.\n\nErrors encountered:\n" + "\n".join(error_messages)
            logger.error(error_msg)
            return {
                "content": [{
                    "type": "text",
                    "text": error_msg
                }],
                "error": error_msg
            }
            
        except Exception as e:
            error_msg = f"Error deleting destination: {str(e)}"
            logger.error(error_msg)
            return {
                "content": [{
                    "type": "text",
                    "text": error_msg
                }],
                "error": str(e)
            }
    
    def close(self) -> None:
        """Close resources."""
        logger.info("Closing destination tools resources")

# Create instance for dependency injection
destination_tools = DestinationTools() 