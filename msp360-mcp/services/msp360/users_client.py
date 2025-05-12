"""Users client module for MSP360 API."""
import logging
from typing import Dict, Any, Optional

from .client_base import MSP360ClientBase

logger = logging.getLogger("msp360_mcp.users")

class UsersClient(MSP360ClientBase):
    """Client for user-related MSP360 API endpoints."""
    
    async def get_users(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get a list of users with proper pagination.
        
        Args:
            params: Query parameters for filtering
            
        Returns:
            API response with user data
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
            if 'company_id' in params:
                query_params['companyId'] = params['company_id']
                
            if 'email' in params:
                query_params['email'] = params['email']
                
            if 'search' in params:
                query_params['search'] = params['search']
        
        return await self._make_request(method="GET", endpoint="/api/Users", params=query_params)
    
    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get a specific user by ID.
        
        Args:
            user_id: The ID of the user to retrieve
            
        Returns:
            API response with user data
        """
        return await self._make_request(method="GET", endpoint=f"/api/Users/{user_id}")
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user.
        
        Args:
            user_data: User data dictionary
            
        Returns:
            API response with created user data
        """
        return await self._make_request(method="POST", endpoint="/api/Users", json_data=user_data)
    
    async def update_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing user.
        
        Args:
            user_data: User data dictionary with ID
            
        Returns:
            API response with updated user data
        """
        return await self._make_request(method="PUT", endpoint="/api/Users", json_data=user_data)
    
    async def delete_user(self, user_id: str) -> Dict[str, Any]:
        """Delete a user.
        
        Args:
            user_id: ID of the user to delete
            
        Returns:
            API response confirming deletion
        """
        return await self._make_request(method="DELETE", endpoint=f"/api/Users/{user_id}")
    
    async def authenticate_user(self, auth_data: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate a user with the MSP360 API.
        
        Args:
            auth_data: Authentication data
            
        Returns:
            API response with authentication result
        """
        return await self._make_request(method="POST", endpoint="/api/Users/Authenticate", json_data=auth_data)
    
    async def delete_user_account(self, user_id: str) -> Dict[str, Any]:
        """Delete a user's account.
        
        Args:
            user_id: ID of the user whose account to delete
            
        Returns:
            API response confirming deletion
        """
        return await self._make_request(method="DELETE", endpoint=f"/api/Users/{user_id}/Account")
    
    async def get_user_computers(self, user_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get computers associated with a specific user.
        
        Args:
            user_id: ID of the user
            params: Optional query parameters
            
        Returns:
            API response with computer data
        """
        # Check if params is None first to avoid AttributeError
        if params is None:
            params = {}
        
        # Transform query parameters
        query_params = {}
        
        # Add pagination parameters
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
        
        return await self._make_request(
            method="GET", 
            endpoint=f"/api/Users/{user_id}/Computers", 
            params=query_params
        )
    
    async def delete_user_computers(self, user_id: str) -> Dict[str, Any]:
        """Delete computers associated with a specific user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            API response confirming deletion
        """
        return await self._make_request(method="DELETE", endpoint=f"/api/Users/{user_id}/Computers") 