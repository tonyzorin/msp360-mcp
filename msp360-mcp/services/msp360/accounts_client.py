"""Accounts client module for MSP360 API."""
import logging
from typing import Dict, Any, Optional

from .client_base import MSP360ClientBase

logger = logging.getLogger("msp360_mcp.accounts")

class AccountsClient(MSP360ClientBase):
    """Client for account-related MSP360 API endpoints."""
    
    async def get_accounts(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get a list of accounts.
        
        Args:
            params: Query parameters for filtering
            
        Returns:
            API response with account data
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
        
        return await self._make_request(method="GET", endpoint="/api/Accounts", params=query_params)
    
    async def get_account(self, account_id: str) -> Dict[str, Any]:
        """Get a specific account by ID.
        
        Args:
            account_id: The ID of the account to retrieve
            
        Returns:
            API response with account data
        """
        return await self._make_request(method="GET", endpoint=f"/api/Accounts/{account_id}")
    
    async def create_account(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new account.
        
        Args:
            account_data: Account data
            
        Returns:
            API response with created account data
        """
        return await self._make_request(method="POST", endpoint="/api/Accounts", json_data=account_data)
    
    async def update_account(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing account.
        
        Args:
            account_data: Account data with ID
            
        Returns:
            API response with updated account data
        """
        return await self._make_request(method="PUT", endpoint="/api/Accounts", json_data=account_data)
    
    async def delete_account(self, account_id: str) -> Dict[str, Any]:
        """Delete an account.
        
        Args:
            account_id: ID of the account to delete
            
        Returns:
            API response confirming deletion
        """
        return await self._make_request(method="DELETE", endpoint=f"/api/Accounts/{account_id}") 