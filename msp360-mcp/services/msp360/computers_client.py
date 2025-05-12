"""Computers client module for MSP360 API."""
import logging
from typing import Dict, Any, Optional
from urllib.parse import quote

from .client_base import MSP360ClientBase

logger = logging.getLogger("msp360_mcp.computers")

class ComputersClient(MSP360ClientBase):
    """Client for computer-related MSP360 API endpoints."""
    
    async def get_computers(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get a list of managed computers/endpoints.
        
        Args:
            params: Query parameters for filtering
            
        Returns:
            API response with computer data
        """
        # Default values
        offset = 0
        count = 10
        query_params = {}
        
        if params:
            logger.info(f"Original params for get_computers: {params}")
            
            # Handle pagination parameters
            if 'page' in params and 'limit' in params:
                page = int(params['page'])
                limit = int(params['limit'])
                # Calculate offset from page/limit
                offset = (page - 1) * limit
                count = limit
            elif 'offset' in params and 'count' in params:
                # Use provided offset and count
                offset = int(params['offset'])
                count = int(params['count'])
                
            # Add other filter parameters to query_params
            if 'companyId' in params:
                query_params['companyId'] = params['companyId']
            elif 'company_id' in params:
                query_params['companyId'] = params['company_id']
                
            # Add user filter if present
            if 'userId' in params:
                query_params['userId'] = params['userId']
            elif 'user_id' in params:
                query_params['userId'] = params['user_id']
                
            # Add search parameter if present
            if 'search' in params:
                query_params['search'] = params['search']
                
            # Add online status filter if present
            if 'online' in params:
                query_params['online'] = params['online']
        
        logger.info(f"Using path parameters: offset={offset}, count={count}")
        logger.info(f"Additional query params: {query_params}")
        
        try:
            # Make the API request with offset and count as path parameters
            endpoint = f"/api/Computers/{offset}/{count}"
            result = await self._make_request(method="GET", endpoint=endpoint, params=query_params)
            logger.info(f"API response type: {type(result)}")
            if isinstance(result, dict):
                logger.info(f"API response keys: {list(result.keys())}")
            return result
        except Exception as e:
            logger.error(f"Error in get_computers API call: {str(e)}")
            raise
    
    async def get_computer(self, hid: str) -> Dict[str, Any]:
        """Get a specific computer by hardware ID (HID).
        
        Args:
            hid: The hardware ID of the computer
            
        Returns:
            API response with computer data
        """
        if not hid:
            error_msg = "Missing or empty hardware ID (hid)"
            logger.error(error_msg)
            return {"error": error_msg}
            
        return await self._make_request(method="GET", endpoint=f"/api/Computers/{hid}")
    
    async def get_computer_plans(self, hid: str) -> Dict[str, Any]:
        """Get backup/restore plans of a specific computer.
        
        Args:
            hid: The hardware ID of the computer
            
        Returns:
            API response with plan data
        """
        if not hid:
            error_msg = "Missing or empty hardware ID (hid)"
            logger.error(error_msg)
            return {"error": error_msg}
            
        return await self._make_request(method="GET", endpoint=f"/api/Computers/{hid}/Plans")
    
    async def remove_computer_authorization(self, hid: str) -> Dict[str, Any]:
        """Remove authorization from a computer.
        
        Args:
            hid: The hardware ID of the computer
            
        Returns:
            API response confirming removal
        """
        if not hid:
            error_msg = "Missing or empty hardware ID (hid)"
            logger.error(error_msg)
            return {"error": error_msg}
            
        # Strip curly braces from HID if present (Windows computers often have HIDs with braces)
        clean_hid = hid.strip('{}')
        
        # Use correct case for API path - matching what works in other methods
        endpoint = f"/api/Computers/{clean_hid}/Authorization"
        
        logger.info(f"Removing authorization for computer {clean_hid}")
        logger.info(f"Using endpoint: {endpoint}")
        
        try:
            return await self._delete(endpoint)
        except Exception as e:
            logger.error(f"Error in remove_computer_authorization API call: {str(e)}")
            if "404" in str(e):
                return {"error": f"Computer with ID '{clean_hid}' not found or authorization endpoint not available", "details": str(e)}
            elif "500" in str(e):
                return {"error": f"Server error when removing authorization. This may be due to a bug in the MSP360 API.", "details": str(e)}
            else:
                raise
    
    async def update_computer_authorization(self, hid: str, auth_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create/update authorization for a computer.
        
        Args:
            hid: The hardware ID of the computer
            auth_data: Optional authorization data containing UserId and/or CompanyId
            
        Returns:
            API response with authorization data
        """
        if not hid:
            error_msg = "Missing or empty hardware ID (hid)"
            logger.error(error_msg)
            return {"error": error_msg}
            
        # Strip curly braces from HID if present (Windows computers often have HIDs with braces)
        clean_hid = hid.strip('{}')
        
        # Use correct case for API path - matching what works in other methods
        endpoint = f"/api/Computers/{clean_hid}/Authorization"
        
        logger.info(f"Updating authorization for computer {clean_hid}")
        logger.info(f"Using endpoint: {endpoint}")
        logger.info(f"Authorization data: {auth_data}")
        
        try:
            if auth_data:
                # Ensure proper capitalization of parameters according to API requirements
                auth_data_capitalized = {}
                for key, value in auth_data.items():
                    # Convert keys like "userId" to "UserId" and "companyId" to "CompanyId"
                    capitalized_key = key[0].upper() + key[1:]
                    auth_data_capitalized[capitalized_key] = value
                
                return await self._post(endpoint, json=auth_data_capitalized)
            else:
                # If no auth data is provided, send an empty body with proper Content-Length header
                headers = {"Content-Length": "0"}
                return await self._post(endpoint, headers=headers)
        except Exception as e:
            logger.error(f"Error in update_computer_authorization API call: {str(e)}")
            if "404" in str(e):
                return {"error": f"Computer with ID '{clean_hid}' not found or authorization endpoint not available", "details": str(e)}
            elif "500" in str(e):
                return {"error": f"Server error when updating authorization. This may be due to a bug in the MSP360 API.", "details": str(e)}
            else:
                raise
    
    async def get_computer_statistics(self, hid: str) -> Dict[str, Any]:
        """Get statistics for a specific computer.
        
        Args:
            hid: The hardware ID of the computer
            
        Returns:
            API response with statistics data
        """
        if not hid:
            error_msg = "Missing or empty hardware ID (hid)"
            logger.error(error_msg)
            return {"error": error_msg}
            
        return await self._make_request(method="GET", endpoint=f"/api/Computers/{hid}/Statistics")
    
    async def get_computer_usage(self, hid: str) -> Dict[str, Any]:
        """Get usage information for a specific computer.
        
        Args:
            hid: The hardware ID of the computer
            
        Returns:
            API response with usage data
        """
        if not hid:
            error_msg = "Missing or empty hardware ID (hid)"
            logger.error(error_msg)
            return {"error": error_msg}
            
        return await self._make_request(method="GET", endpoint=f"/api/Computers/{hid}/Usage") 