"""CRUD operations for administrator management."""
from typing import Dict, Any, Optional, List, AsyncGenerator
import logging
import json
from services.msp360 import msp360_client
from tools.utils import parse_params_json, normalize_field_names
from .admin_helpers import format_admin_data

logger = logging.getLogger("msp360_mcp.tools")

async def get_admin_list(client, params_str: str) -> AsyncGenerator[Dict[str, Any], None]:
    """Get a list of administrators with filtering options.
    
    Args:
        client: MSP360 API client
        params_str: JSON string with filter parameters
        
    Yields:
        Dictionary with administrator data for MCP, one at a time
    """
    # Parse the JSON string to get parameters
    try:
        param_dict = parse_params_json(params_str, {})
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in params: {e}")
        yield {"type": "text", "text": f"Invalid JSON in params: {e}"}
        return
    
    try:
        # Get administrators from the API
        result = await client.get_administrators(param_dict)
        
        # Log the raw API response for debugging
        logger.info("Raw API response structure:")
        logger.info(f"Response type: {type(result)}")
        if isinstance(result, dict):
            logger.info(f"Response keys: {list(result.keys())}")
            if 'items' in result and result['items']:
                sample_admin = result['items'][0]
                logger.info(f"Sample admin fields: {list(sample_admin.keys())}")
                logger.info(f"Sample admin raw data: {json.dumps(sample_admin, indent=2)}")
        
        # Format the response
        if not result or not isinstance(result, dict):
            logger.warning("Empty or invalid response from API")
            yield {"type": "text", "text": "No administrators found"}
            return
            
        admins = result.get('items', [])
        total_count = result.get('totalCount', len(admins))
        
        # Yield total count first
        yield {"type": "text", "text": f"Total administrators: {total_count}"}
        
        # Format and yield each administrator's data
        for admin in admins:
            try:
                formatted_text = format_admin_data(admin)
                yield {"type": "text", "text": formatted_text}
            except Exception as e:
                logger.error(f"Error formatting admin data: {e}")
                continue
        
    except Exception as e:
        logger.error(f"Error in get_admin_list: {e}")
        yield {"type": "text", "text": f"Error retrieving administrators: {str(e)}"}

async def get_admin_detail(client, admin_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific administrator.
    
    Args:
        client: MSP360 API client
        admin_id: Administrator ID
        
    Returns:
        Dictionary with administrator data for MCP
    """
    try:
        # Call the API to get administrator details
        admin = await client.get_administrator(admin_id=admin_id)
        
        # Debug: Log the raw response structure if available
        logger.debug(f"Raw administrator response type: {type(admin)}")
        if admin:
            logger.debug(f"Raw administrator response keys: {list(admin.keys()) if isinstance(admin, dict) else 'Not a dict'}")
        
        # If no administrator was found
        if not admin:
            return {
                "content": [{
                    "type": "text",
                    "text": f"No administrator found with ID: {admin_id}"
                }]
            }
        
        # Format the administrator data
        formatted_text = format_admin_data(admin)
        
        return {
            "content": [{
                "type": "text",
                "text": formatted_text
            }]
        }
        
    except Exception as e:
        logger.error(f"Error retrieving administrator {admin_id}: {str(e)}", exc_info=True)
        return {
            "content": [{
                "type": "text",
                "text": f"Error retrieving administrator: {str(e)}"
            }],
            "error": str(e)
        }

async def create_admin_entry(client, admin_data_str: str) -> Dict[str, Any]:
    """Create a new administrator.
    
    Args:
        client: MSP360 API client
        admin_data_str: JSON string with administrator data
        
    Returns:
        Dictionary with result for MCP
    """
    try:
        # Parse the JSON data
        try:
            admin_data = json.loads(admin_data_str)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing admin data JSON: {str(e)}")
            return {
                "content": [{
                    "type": "text",
                    "text": f"Invalid JSON data: {str(e)}"
                }],
                "error": f"Invalid JSON data: {str(e)}"
            }
        
        # Check for required fields
        required_fields = ["Name", "Email", "Password", "Role"]
        field_mapping = {
            "name": "Name", 
            "email": "Email", 
            "password": "Password",
            "role": "Role",
            "adminname": "Name",
            "adminemail": "Email",
            "adminpassword": "Password",
            "adminrole": "Role"
        }
        
        # Normalize field names
        normalized_data = normalize_field_names(admin_data, field_mapping)
        
        # Check for missing required fields
        missing_fields = []
        for field in required_fields:
            if field not in normalized_data:
                missing_fields.append(field)
        
        if missing_fields:
            error_msg = f"Missing required fields: {', '.join(missing_fields)}"
            logger.error(error_msg)
            return {
                "content": [{
                    "type": "text",
                    "text": f"{error_msg}\n\nRequired fields: {', '.join(required_fields)}"
                }],
                "error": error_msg
            }
        
        # Create the administrator
        result = await client.create_administrator(admin_data=normalized_data)
        
        # Return the result
        return {
            "content": [{
                "type": "text",
                "text": f"Administrator created successfully: {json.dumps(result, indent=2)}"
            }]
        }
        
    except Exception as e:
        logger.error(f"Error creating administrator: {str(e)}", exc_info=True)
        return {
            "content": [{
                "type": "text",
                "text": f"Error creating administrator: {str(e)}"
            }],
            "error": str(e)
        }

async def update_admin_entry(client, admin_data_str: str) -> Dict[str, Any]:
    """Update an existing administrator.
    
    Args:
        client: MSP360 API client
        admin_data_str: JSON string with administrator data
        
    Returns:
        Dictionary with result for MCP
    """
    try:
        # Parse the JSON data
        try:
            admin_data = json.loads(admin_data_str)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing admin data JSON: {str(e)}")
            return {
                "content": [{
                    "type": "text",
                    "text": f"Invalid JSON data: {str(e)}"
                }],
                "error": f"Invalid JSON data: {str(e)}"
            }
        
        # Check for ID field which is required for update
        field_mapping = {
            "id": "ID", 
            "adminid": "ID",
            "admin_id": "ID"
        }
        
        # Normalize field names
        normalized_data = normalize_field_names(admin_data, field_mapping)
        
        # Check if ID is present
        if "ID" not in normalized_data:
            error_msg = "Missing required field: ID"
            logger.error(error_msg)
            return {
                "content": [{
                    "type": "text",
                    "text": "Administrator ID is required for update"
                }],
                "error": error_msg
            }
        
        # Update the administrator
        result = await client.update_administrator(admin_data=normalized_data)
        
        # Return the result
        return {
            "content": [{
                "type": "text",
                "text": f"Administrator updated successfully: {json.dumps(result, indent=2)}"
            }]
        }
        
    except Exception as e:
        logger.error(f"Error updating administrator: {str(e)}", exc_info=True)
        return {
            "content": [{
                "type": "text",
                "text": f"Error updating administrator: {str(e)}"
            }],
            "error": str(e)
        }

async def delete_admin_entry(client, admin_id: str) -> Dict[str, Any]:
    """Delete an administrator.
    
    Args:
        client: MSP360 API client
        admin_id: Administrator ID
        
    Returns:
        Dictionary with result for MCP
    """
    try:
        # Delete the administrator
        result = await client.delete_administrator(admin_id=admin_id)
        
        # Return the result
        return {
            "content": [{
                "type": "text",
                "text": f"Administrator with ID {admin_id} was successfully deleted"
            }]
        }
        
    except Exception as e:
        logger.error(f"Error deleting administrator: {str(e)}", exc_info=True)
        return {
            "content": [{
                "type": "text",
                "text": f"Error deleting administrator: {str(e)}"
            }],
            "error": str(e)
        } 