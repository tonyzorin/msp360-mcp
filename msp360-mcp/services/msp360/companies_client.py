"""Companies client module for MSP360 API."""
import logging
from typing import Dict, Any, Optional

from .client_base import MSP360ClientBase

logger = logging.getLogger("msp360_mcp.companies")

class CompaniesClient(MSP360ClientBase):
    """Client for company-related MSP360 API endpoints."""
    
    async def get_companies(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get a list of companies with proper pagination.
        
        Args:
            params: Query parameters for filtering
            
        Returns:
            API response with company data
        """
        # Transform pagination parameters from page/limit to skip/take
        query_params = {}
        
        if params:
            # Handle pagination parameters
            if 'page' in params and 'limit' in params:
                page = int(params['page'])
                limit = int(params['limit'])
                # MSP360 API uses skip/take for pagination
                skip = (page - 1) * limit
                query_params['take'] = limit
                query_params['skip'] = skip
            elif 'skip' in params and 'take' in params:
                # Pass through if already in correct format
                query_params['skip'] = params['skip']
                query_params['take'] = params['take']
                
            # Add other filter parameters
            if 'name' in params:
                query_params['name'] = params['name']
        
        return await self._make_request(method="GET", endpoint="/api/Companies", params=query_params)
    
    async def get_company(self, company_id: str) -> Dict[str, Any]:
        """Get a specific company by ID.
        
        Args:
            company_id: The ID of the company to retrieve
            
        Returns:
            API response with company data
        """
        return await self._make_request(method="GET", endpoint=f"/api/Companies/{company_id}")
    
    async def create_company(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new company.
        
        Args:
            company_data: Company data dictionary
            
        Returns:
            API response with created company data
        """
        return await self._make_request(method="POST", endpoint="/api/Companies", json_data=company_data)
    
    async def update_company(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing company.
        
        Args:
            company_data: Company data dictionary with ID
            
        Returns:
            API response with updated company data
        """
        return await self._make_request(method="PUT", endpoint="/api/Companies", json_data=company_data)
    
    async def delete_company(self, company_id: str) -> Dict[str, Any]:
        """Delete a company.
        
        Args:
            company_id: ID of the company to delete
            
        Returns:
            API response confirming deletion
        """
        return await self._make_request(method="DELETE", endpoint=f"/api/Companies/{company_id}")
    
    async def get_company_storage_usage(self, company_id: str) -> Dict[str, Any]:
        """Get storage usage for a specific company.
        
        Args:
            company_id: ID of the company
            
        Returns:
            API response with storage usage data
        """
        return await self._make_request(method="GET", endpoint=f"/api/Companies/{company_id}/StorageUsage")
    
    async def get_company_users(self, company_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get users associated with a specific company.
        
        Args:
            company_id: ID of the company
            params: Optional query parameters
            
        Returns:
            API response with user data
        """
        # Transform pagination parameters
        query_params = {}
        
        if params:
            # Handle pagination parameters
            if 'page' in params and 'limit' in params:
                page = int(params['page'])
                limit = int(params['limit'])
                # MSP360 API uses skip/take for pagination
                skip = (page - 1) * limit
                query_params['take'] = limit
                query_params['skip'] = skip
        
        return await self._make_request(
            method="GET", 
            endpoint=f"/api/Companies/{company_id}/Users", 
            params=query_params
        ) 