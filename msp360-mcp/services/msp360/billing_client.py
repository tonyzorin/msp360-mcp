"""Billing client module for MSP360 API."""
import logging
from typing import Dict, Any, Optional

from .client_base import MSP360ClientBase

logger = logging.getLogger("msp360_mcp.billing")

class BillingClient(MSP360ClientBase):
    """Client for billing-related MSP360 API endpoints."""
    
    async def get_billing(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get billing information for the current month.
        
        Args:
            params: Query parameters for filtering
            
        Returns:
            API response with billing data
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
            elif 'skip' in params and 'take' in params:
                # Pass through if already in correct format
                query_params['skip'] = params['skip']
                query_params['take'] = params['take']
        
        return await self._make_request(method="GET", endpoint="/api/Billing", params=query_params)
    
    async def get_filtered_billing(self, filter_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get filtered billing information.
        
        Args:
            filter_data: Filter criteria as a dictionary
            
        Returns:
            API response with filtered billing data
        """
        # POST is used for complex filtering
        return await self._make_request(method="POST", endpoint="/api/Billing", json_data=filter_data)
    
    async def get_billing_details(self, details_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed billing information for backup/restore operations.
        
        Args:
            details_data: Filter data for billing details
            
        Returns:
            API response with billing details
        """
        return await self._make_request(method="POST", endpoint="/api/Billing/Details", json_data=details_data)
    
    async def get_billing_summary(self, summary_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get billing summary information.
        
        Args:
            summary_data: Filter data for billing summary
            
        Returns:
            API response with billing summary
        """
        return await self._make_request(method="POST", endpoint="/api/Billing/Summary", json_data=summary_data)
    
    async def get_billing_storage(self, storage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get storage billing information.
        
        Args:
            storage_data: Filter data for storage billing
            
        Returns:
            API response with storage billing data
        """
        return await self._make_request(method="POST", endpoint="/api/Billing/Storage", json_data=storage_data) 