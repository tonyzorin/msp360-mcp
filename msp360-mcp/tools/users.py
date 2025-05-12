"""Users tools for MSP360 MCP Server."""
from typing import Dict, List, Any, Optional
import logging
import json
from services.msp360 import msp360_client
from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field
from tools import register_tool

logger = logging.getLogger("msp360_mcp.tools")

class UserParams(BaseModel):
    page: int = 1
    limit: int = 10
    company_id: Optional[str] = None

class UserTools:
    """Tools for interacting with MSP360/CloudBerry user management.
    
    IMPORTANT: This class directly imports the msp360_client from services rather
    than receiving it as a parameter in the __init__ method. This approach is
    critical for STDIO mode operation, as it ensures all tools have access to
    the same client instance without complex dependency injection.
    
    In STDIO mode, the server must initialize quickly and maintain consistent
    state across all requests, making direct imports of singletons preferable
    to parameter-based dependency injection.
    """
    
    def __init__(self):
        """Initialize the user tools."""
        self.client = msp360_client
        self._tool_definitions = {}
        self._register_tools()
        logger.info("UserTools initialized")
        
    def _register_tools(self):
        """Register all user tools with the tool registry."""
        # Define get_users tool
        self._tool_definitions["get_users"] = {
            "description": "Get a list of MSP360 users with optional filtering",
            "function": self.get_users,
            "parameter_descriptions": {
                "params": "JSON string with filter parameters (page, limit, company_id)"
            }
        }
        
        # Define get_user tool
        self._tool_definitions["get_user"] = {
            "description": "Get a specific MSP360 user by ID",
            "function": self.get_user,
            "parameter_descriptions": {
                "user_id": "User ID"
            }
        }
        
        # Don't register tools globally here - let MCPServer handle that
    
    def get_tool_definitions(self) -> Dict[str, Any]:
        """Get definitions of all user tools.
        
        Returns:
            Dictionary of tool definitions
        """
        return self._tool_definitions
        
    async def get_users(self, params: str = '{}') -> Dict[str, Any]:
        """
        Get a list of users with optional filtering.
        
        Args:
            params: JSON string with filter parameters (page, limit, company_id)
            
        Returns:
            Dictionary with users data
        """
        logger.info(f"Getting users with params: {params}")
        
        try:
            # Parse the JSON string to get parameters
            try:
                if params and params.strip():
                    param_dict = json.loads(params)
                else:
                    param_dict = {}
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing parameters JSON: {str(e)}")
                return {
                    "content": [{
                        "type": "text",
                        "text": f"Error parsing parameters: {str(e)}"
                    }],
                    "error": f"Invalid JSON parameters: {str(e)}"
                }
            
            # Extract pagination parameters with defaults
            page = param_dict.get('page', 1)
            limit = param_dict.get('limit', 10)
            
            # Map to API query parameters - updated to match client expectations
            query_params = {}
            
            # We should pass page and limit directly to the client
            # The client will handle conversion to skip/take
            if page is not None:
                query_params['page'] = page
            if limit is not None:
                query_params['limit'] = limit
            
            # Add filters if present
            if 'company_id' in param_dict:
                query_params['companyId'] = param_dict['company_id']
            if 'email' in param_dict:
                query_params['email'] = param_dict['email']
            
            logger.debug(f"Calling get_users with query_params: {query_params}")
            
            # Call the API
            users = await self.client.get_users(params=query_params)
            logger.debug(f"Retrieved users response: {json.dumps(users)[:500] if users else 'None'}")
            
            # Process the response for MCP
            result_content = []
            
            # Handle different response formats
            if isinstance(users, list):
                # Apply limit to the list of users - ensure we don't exceed the limit
                if limit and len(users) > limit:
                    users = users[:limit]
                    
                if not users:
                    result_content.append({
                        "type": "text",
                        "text": "No users found"
                    })
                else:
                    for user in users:
                        user_text = self._format_user_data(user)
                        result_content.append({
                            "type": "text",
                            "text": user_text
                        })
            elif isinstance(users, dict):
                if 'items' in users and isinstance(users['items'], list):
                    items = users['items']
                    # Apply limit to the list of users - ensure we don't exceed the limit
                    if limit and len(items) > limit:
                        items = items[:limit]
                        
                    if not items:
                        result_content.append({
                            "type": "text",
                            "text": "No users found"
                        })
                    else:
                        for user in items:
                            user_text = self._format_user_data(user)
                            result_content.append({
                                "type": "text",
                                "text": user_text
                            })
                else:
                    # For unexpected response formats or empty responses
                    result_content.append({
                        "type": "text",
                        "text": f"Users data: {json.dumps(users, indent=2)}"
                    })
            else:
                # For empty or unexpected responses
                result_content.append({
                    "type": "text",
                    "text": f"No users found or unexpected API response format: {json.dumps(users)[:500] if users else 'None'}"
                })
            
            return {"content": result_content}
        except Exception as e:
            logger.error(f"Error retrieving users: {str(e)}")
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error retrieving users: {str(e)}"
                }],
                "error": f"Failed to retrieve users: {str(e)}"
            }
        
    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """
        Get a specific MSP360 user by ID
        
        Args:
            user_id: The ID of the user to retrieve
            
        Returns:
            Dictionary with user details or error information
        """
        try:
            logger.info(f"Getting user with ID: {user_id}")
            user = await self.client.get_user(user_id)
            logger.debug(f"Retrieved user type: {type(user)}")
            logger.debug(f"Retrieved user keys: {list(user.keys()) if isinstance(user, dict) else 'Not a dict'}")
            
            if not user:
                return {"content": [], "error": f"User with ID {user_id} not found"}
            
            # Format basic user details
            user_details = []
            
            # Process main fields first
            for key in ['ID', 'Email', 'FirstName', 'LastName', 'Company', 'Enabled']:
                if key in user:
                    user_details.append(f"{key}: {user.get(key)}")
            
            # Add other fields except for DestinationList which we'll format specially
            for key, value in user.items():
                if key not in ['ID', 'Email', 'FirstName', 'LastName', 'Company', 'Enabled', 'DestinationList']:
                    user_details.append(f"{key}: {value}")
            
            # Format destinations list separately
            if 'DestinationList' in user:
                destinations = user['DestinationList']
                logger.debug(f"DestinationList type: {type(destinations)}")
                logger.debug(f"DestinationList: {destinations}")
                
                # If destinations is a list
                if isinstance(destinations, list):
                    if destinations:
                        user_details.append("\nDestinations:")
                        for i, dest in enumerate(destinations, 1):
                            if isinstance(dest, dict):
                                user_details.append(f"\nDestination {i}:")
                                user_details.append(f"  ID: {dest.get('ID', 'N/A')}")
                                user_details.append(f"  Account: {dest.get('AccountDisplayName', 'N/A')}")
                                user_details.append(f"  Storage: {dest.get('DestinationDisplayName', 'N/A')}")
                                user_details.append(f"  Path: {dest.get('Destination', 'N/A')}")
                                user_details.append(f"  Current Volume: {self._format_size(dest.get('CurrentVolume', 0))}")
                    else:
                        user_details.append("\nDestinations: None")
                else:
                    # Just add the raw value if it's not a list
                    user_details.append(f"\nDestinationList: {destinations}")
            
            formatted_text = "\n".join(user_details)
            logger.debug(f"Formatted user text length: {len(formatted_text)}")
            logger.debug(f"Formatted user text first 100 chars: {formatted_text[:100]}")
            
            return {"content": [{"type": "text", "text": formatted_text}]}
            
        except Exception as e:
            logger.error(f"Error getting user: {e}", exc_info=True)
            return {"content": [], "error": str(e)}
        
    def _format_size(self, size_bytes: int) -> str:
        """Format bytes into a human-readable string."""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB", "PB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024
            i += 1
        
        return f"{size_bytes:.2f} {size_names[i]}"
        
    def _format_user_data(self, user: Dict[str, Any]) -> str:
        """
        Format user data into a readable text string.
        
        Args:
            user: User data dictionary
            
        Returns:
            Formatted string representation of the user
        """
        # Get the user ID field - it could be 'ID', 'Id', or 'id'
        user_id = user.get('ID', user.get('Id', user.get('id', 'N/A')))
        
        # Basic info
        user_info = [
            f"ID: {user_id}",
            f"Email: {user.get('Email', 'N/A')}"
        ]
        
        # Add name if available
        if 'FirstName' in user or 'LastName' in user:
            first_name = user.get('FirstName', '')
            last_name = user.get('LastName', '')
            name = f"{first_name} {last_name}".strip()
            if name:
                user_info.append(f"Name: {name}")
        
        # Add company info if available
        company = user.get('Company', 'N/A')
        user_info.append(f"Company: {company}")
        
        # Add status/enabled info if available
        if 'Enabled' in user:
            user_info.append(f"Enabled: {user.get('Enabled')}")
        
        # Add storage usage if available
        if 'SpaceUsed' in user:
            space_used = user['SpaceUsed']
            if isinstance(space_used, int):
                # Format in a human-readable way - bytes to KB/MB/GB
                if space_used == 0:
                    formatted_space = "0 B"
                elif space_used < 1024:
                    formatted_space = f"{space_used} B"
                elif space_used < 1024 * 1024:
                    formatted_space = f"{space_used / 1024:.2f} KB"
                elif space_used < 1024 * 1024 * 1024:
                    formatted_space = f"{space_used / (1024 * 1024):.2f} MB"
                else:
                    formatted_space = f"{space_used / (1024 * 1024 * 1024):.2f} GB"
                user_info.append(f"Storage Used: {formatted_space}")
            else:
                user_info.append(f"Storage Used: {space_used}")
        
        # Add notification emails if available
        if 'NotificationEmails' in user:
            notification_emails = user['NotificationEmails']
            if isinstance(notification_emails, list):
                user_info.append(f"NotificationEmails: {', '.join(notification_emails)}")
            else:
                user_info.append(f"NotificationEmails: {notification_emails}")
        
        # Add license info if available
        if 'LicenseManagmentMode' in user:
            user_info.append(f"LicenseManagmentMode: {user.get('LicenseManagmentMode')}")
        
        # Process additional fields but exclude DestinationList for separate processing
        handled_keys = {'ID', 'Id', 'id', 'Email', 'FirstName', 'LastName', 'Company', 
                        'Enabled', 'SpaceUsed', 'NotificationEmails', 'LicenseManagmentMode', 
                        'Destinations', 'DestinationList'}
        
        additional_fields = []
        for key, value in user.items():
            if key not in handled_keys:
                additional_fields.append(f"{key}: {value}")
        
        if additional_fields:
            user_info.append("\nAdditional Information:")
            user_info.extend(additional_fields)
        
        # Process DestinationList if available
        destinations = None
        if 'DestinationList' in user:
            destinations = user['DestinationList']
        elif 'Destinations' in user:
            destinations = user['Destinations']
        
        if destinations:
            if isinstance(destinations, list) and destinations:
                user_info.append("\nDestinations:")
                for idx, dest in enumerate(destinations, 1):
                    if isinstance(dest, dict):
                        user_info.append(f"  {idx}. {dest.get('DestinationDisplayName', 'Unnamed')} ({dest.get('AccountDisplayName', 'Unknown Account')})")
                        
                        # Format size if available
                        volume = dest.get('CurrentVolume', 0)
                        if volume > 0:
                            if volume < 1024:
                                formatted_volume = f"{volume} B"
                            elif volume < 1024 * 1024:
                                formatted_volume = f"{volume / 1024:.2f} KB"
                            elif volume < 1024 * 1024 * 1024:
                                formatted_volume = f"{volume / (1024 * 1024):.2f} MB"
                            else:
                                formatted_volume = f"{volume / (1024 * 1024 * 1024):.2f} GB"
                            user_info.append(f"     Size: {formatted_volume}")
                            
                        # Add path if available
                        if 'Destination' in dest:
                            user_info.append(f"     Path: {dest.get('Destination', 'N/A')}")
                            
                        # Add ID if available
                        if 'ID' in dest:
                            user_info.append(f"     ID: {dest.get('ID', 'N/A')}")
                    else:
                        user_info.append(f"  {idx}. {dest}")
            else:
                user_info.append(f"\nDestinations: {destinations}")
        
        return "\n".join(user_info)
        
    def close(self) -> None:
        """Close any resources."""
        pass 

# No singleton instance here - let MCPServer create it 