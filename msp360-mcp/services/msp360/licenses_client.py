"""Licenses client module for MSP360 API."""
import logging
from typing import Dict, Any, Optional, List

from .client_base import MSP360ClientBase

logger = logging.getLogger("msp360_mcp.licenses")

class LicensesClient(MSP360ClientBase):
    """Client for license-related MSP360 API endpoints."""
    
    async def get_licenses(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get a list of licenses.
        
        Args:
            params: Query parameters for filtering
            
        Returns:
            API response with licenses data
        """
        query_params = {}
        
        if params:
            # Handle pagination parameters
            if 'page' in params:
                query_params['page'] = params['page']
            if 'limit' in params:
                query_params['limit'] = params['limit']
                
            # Add company filter if present
            if 'companyId' in params:
                query_params['companyId'] = params['companyId']
            elif 'company_id' in params:
                query_params['companyId'] = params['company_id']
                
            # Add status filter if present
            if 'status' in params:
                query_params['status'] = params['status']
                
            # Add edition filter if present
            if 'edition' in params:
                query_params['edition'] = params['edition']
                
            # Add license type filter if present
            if 'licenseType' in params:
                query_params['licenseType'] = params['licenseType']
            elif 'license_type' in params:
                query_params['licenseType'] = params['license_type']
        
        logger.info(f"Getting licenses with params: {query_params}")
        
        try:
            endpoint = "/api/Licenses"
            result = await self._make_request(method="GET", endpoint=endpoint, params=query_params)
            
            # Return empty array if no licenses returned
            if not result or (isinstance(result, dict) and not result):
                return {"licenses": [], "totalCount": 0}
                
            # If result is directly an array, wrap it in a proper response format
            if isinstance(result, list):
                return {"licenses": result, "totalCount": len(result)}
                
            # Return the result as-is if it's already a proper response format
            return result
            
        except Exception as e:
            logger.error(f"Error in get_licenses API call: {str(e)}")
            # Return empty array instead of raising an exception
            return {"licenses": [], "totalCount": 0, "error": str(e)}
    
    async def get_license(self, license_id: str) -> Dict[str, Any]:
        """Get a specific license by ID.
        
        Args:
            license_id: The ID of the license to retrieve
            
        Returns:
            API response with license data
        """
        if not license_id:
            error_msg = "Missing or empty license ID"
            logger.error(error_msg)
            return {"error": error_msg}
            
        logger.info(f"Getting license with ID: {license_id}")
        return await self._make_request(method="GET", endpoint=f"/api/Licenses/{license_id}")
    
    async def grant_license(self, license_data: Dict[str, Any]) -> Dict[str, Any]:
        """Grant a license to a user.
        
        Args:
            license_data: License data with user assignment information
            
        Returns:
            API response with grant result
        """
        if not license_data:
            error_msg = "Missing or empty license data"
            logger.error(error_msg)
            return {"error": error_msg}
            
        logger.info(f"Granting license with data: {license_data}")
        return await self._make_request(method="POST", endpoint="/api/Licenses/Grant", json_data=license_data)
    
    async def release_license(self, license_data: Dict[str, Any]) -> Dict[str, Any]:
        """Release a license from a user.
        
        Args:
            license_data: License data with release information
            
        Returns:
            API response with release result
        """
        if not license_data:
            error_msg = "Missing or empty license data"
            logger.error(error_msg)
            return {"error": error_msg}
            
        logger.info(f"Releasing license with data: {license_data}")
        return await self._make_request(method="POST", endpoint="/api/Licenses/Release", json_data=license_data)
    
    async def revoke_license(self, license_data: Dict[str, Any]) -> Dict[str, Any]:
        """Revoke a license from a user.
        
        Args:
            license_data: License data with revocation information
            
        Returns:
            API response with revocation result
        """
        if not license_data:
            error_msg = "Missing or empty license data"
            logger.error(error_msg)
            return {"error": error_msg}
            
        logger.info(f"Revoking license with data: {license_data}")
        return await self._make_request(method="POST", endpoint="/api/Licenses/Revoke", json_data=license_data) 