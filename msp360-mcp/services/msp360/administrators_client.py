"""Administrators client module for MSP360 API."""
import logging
from typing import Dict, Any, Optional, List
import json

from .client_base import MSP360ClientBase

logger = logging.getLogger("msp360_mcp.administrators")

class AdministratorsClient(MSP360ClientBase):
    """Client for administrator-related MSP360 API endpoints."""
    
    async def get_administrators(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get a list of administrators.
        
        Args:
            params: Query parameters for filtering
            
        Returns:
            API response with administrators data
        """
        query_params = {}
        
        if params:
            # Handle pagination parameters
            if 'page' in params:
                query_params['page'] = params['page']
            if 'limit' in params:
                query_params['limit'] = params['limit']
                
            # Add other filter parameters
            if 'name' in params:
                query_params['name'] = params['name']
        
        logger.info(f"Getting administrators with params: {query_params}")
        
        try:
            endpoint = "/api/Administrators"
            result = await self._make_request(method="GET", endpoint=endpoint, params=query_params)
            
            # Debug log the raw response
            logger.debug(f"Raw API response type: {type(result)}")
            logger.debug(f"Raw API response: {json.dumps(result, indent=2)}")
            
            # Return empty array if no administrators returned
            if not result or (isinstance(result, dict) and not result):
                logger.debug("No administrators found in response")
                return {"items": [], "totalCount": 0}
                
            # If result is directly an array, wrap it in a proper response format
            if isinstance(result, list):
                logger.debug("Response is a list, wrapping in standard format")
                return {"items": result, "totalCount": len(result)}
                
            # If result is a dictionary, normalize the keys
            if isinstance(result, dict):
                # Check for various possible key names
                items = None
                total = 0
                
                # Try different possible key names for items
                for key in ['Items', 'items', 'Administrators', 'administrators', 'admins']:
                    if key in result:
                        items = result[key]
                        logger.debug(f"Found administrators under key: {key}")
                        break
                
                # Try different possible key names for total count
                for key in ['TotalCount', 'totalCount', 'total', 'Total']:
                    if key in result:
                        total = result[key]
                        logger.debug(f"Found total count under key: {key}")
                        break
                
                # If we found items, normalize each administrator object
                if items is not None:
                    normalized_items = []
                    for admin in items:
                        if isinstance(admin, dict):
                            # Normalize the administrator object keys
                            normalized_admin = {
                                'AdminID': admin.get('AdminID') or admin.get('Id') or admin.get('id'),
                                'Email': admin.get('Email') or admin.get('email'),
                                'FirstName': admin.get('FirstName') or admin.get('firstName'),
                                'LastName': admin.get('LastName') or admin.get('lastName'),
                                'Enabled': admin.get('Enabled', True),
                                'LastLogin': admin.get('LastLogin') or admin.get('lastLogin'),
                                'DateCreated': admin.get('DateCreated') or admin.get('dateCreated'),
                                'AccessToCompaniesMode': admin.get('AccessToCompaniesMode', 0),
                                'AccountType': admin.get('AccountType', 2)  # Default to regular admin
                            }
                            normalized_items.append(normalized_admin)
                    
                    logger.debug(f"First normalized administrator data: {json.dumps(normalized_items[0], indent=2) if normalized_items else 'No items'}")
                    return {"items": normalized_items, "totalCount": total or len(normalized_items)}
            
            # If we couldn't normalize the response, return it as-is
            logger.debug("Returning raw response as-is")
            return result
            
        except Exception as e:
            logger.error(f"Error in get_administrators API call: {str(e)}")
            # Return empty array instead of raising an exception
            return {"items": [], "totalCount": 0, "error": str(e)}
    
    async def get_administrator(self, admin_id: str) -> Dict[str, Any]:
        """Get a specific administrator by ID.
        
        Args:
            admin_id: The ID of the administrator to retrieve
            
        Returns:
            API response with administrator data
        """
        if not admin_id:
            error_msg = "Missing or empty administrator ID"
            logger.error(error_msg)
            return {"error": error_msg}
            
        logger.info(f"Getting administrator with ID: {admin_id}")
        return await self._make_request(method="GET", endpoint=f"/api/Administrators/{admin_id}")
    
    async def create_administrator(self, admin_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new administrator.
        
        Args:
            admin_data: Administrator data to create
            
        Returns:
            API response with creation result
        """
        if not admin_data:
            error_msg = "Missing or empty administrator data"
            logger.error(error_msg)
            return {"error": error_msg}
            
        logger.info(f"Creating administrator with data: {admin_data}")
        return await self._make_request(method="POST", endpoint="/api/Administrators", json_data=admin_data)
    
    async def update_administrator(self, admin_id: str, admin_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing administrator.
        
        Args:
            admin_id: ID of the administrator to update
            admin_data: Administrator data to update
            
        Returns:
            API response with update result
        """
        if not admin_id:
            error_msg = "Missing or empty administrator ID"
            logger.error(error_msg)
            return {"error": error_msg}
            
        if not admin_data:
            error_msg = "Missing or empty administrator data"
            logger.error(error_msg)
            return {"error": error_msg}
            
        logger.info(f"Updating administrator {admin_id} with data: {admin_data}")
        return await self._make_request(
            method="PUT", 
            endpoint=f"/api/Administrators/{admin_id}",
            json_data=admin_data
        )
    
    async def delete_administrator(self, admin_id: str) -> Dict[str, Any]:
        """Delete an administrator.
        
        Args:
            admin_id: ID of the administrator to delete
            
        Returns:
            API response with deletion result
        """
        if not admin_id:
            error_msg = "Missing or empty administrator ID"
            logger.error(error_msg)
            return {"error": error_msg}
            
        logger.info(f"Deleting administrator with ID: {admin_id}")
        return await self._make_request(method="DELETE", endpoint=f"/api/Administrators/{admin_id}") 